#!/usr/bin/env python3
"""
Script to check if ESMA has updated the Interim MiCA Register.
Uses Playwright to scrape the last update date from the ESMA website
and compares it with the latest CSV file in data/cleaned/.
"""
import sys
import os
import re
from pathlib import Path
from glob import glob
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.models import RegisterType
from app.utils.file_utils import get_latest_csv_for_register, extract_date_from_filename, get_base_data_dir


def _parse_last_update_from_text(text):
    """Parse ESMA 'Last update' date from page text."""
    if not text:
        return None
    match = re.search(
        r'Last\s*update(?:\s|:|-)*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})',
        text,
        re.IGNORECASE
    )
    if not match:
        return None

    day = int(match.group(1))
    month_name = match.group(2)
    year = int(match.group(3))
    month_map = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    month = month_map.get(month_name.lower())
    if not month:
        return None
    return datetime(year, month, day)


def _strip_html_tags(text):
    """Return text with HTML tags removed for robust date parsing."""
    if not text:
        return ""
    no_script = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    no_style = re.sub(r"<style[^>]*>.*?</style>", " ", no_script, flags=re.IGNORECASE | re.DOTALL)
    no_tags = re.sub(r"<[^>]+>", " ", no_style)
    return re.sub(r"\s+", " ", no_tags).strip()


def _get_playwright_chromium_executables():
    """Return local Playwright Chromium executable paths, newest first."""
    cache_dir = Path.home() / "Library" / "Caches" / "ms-playwright"
    if not cache_dir.exists():
        return []

    candidates = [
        "chromium_headless_shell-*/chrome-headless-shell-mac-arm64/chrome-headless-shell",
        "chromium_headless_shell-*/chrome-headless-shell-mac-x64/chrome-headless-shell",
        "chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
    ]
    results = []
    for pattern in candidates:
        matches = sorted(cache_dir.glob(pattern), reverse=True)
        for match in matches:
            results.append(str(match))
    return results


def get_latest_csv_date(register_type: RegisterType = RegisterType.CASP, quiet=False):
    """Get the date from the newest CSV file for a register.

    Args:
        register_type: Register type to check (default: CASP for backward compatibility)
        quiet: If True, don't print warnings to stdout

    Returns:
        Tuple of (datetime object, file path) or (None, None) if not found
    """
    base_dir = get_base_data_dir() / "cleaned"

    # Use file_utils for consistent detection
    latest_file = get_latest_csv_for_register(
        register_type,
        base_dir,
        file_stage="cleaned",
        prefer_llm=True
    )

    if latest_file:
        # Extract date from filename
        file_date = extract_date_from_filename(latest_file.name)
        if file_date:
            # Convert date to datetime for backward compatibility
            date_obj = datetime(file_date.year, file_date.month, file_date.day)
            return date_obj, str(latest_file)
    
    return None, None


def get_esma_update_date(quiet=False):
    """Scrape the last update date from ESMA website using Playwright.
    
    Args:
        quiet: If True, suppress non-critical output
        
    Returns:
        datetime object or None if failed
    """
    url = "https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica#InterimMiCARegister"
    
    # Fast path: fetch static HTML first (works in cron/sandbox without browser).
    try:
        import requests
        response = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0 (compatible; MiCARegisterUpdater/1.0)"}
        )
        response.raise_for_status()
        parsed_date = _parse_last_update_from_text(response.text)
        if not parsed_date:
            parsed_date = _parse_last_update_from_text(_strip_html_tags(response.text))
        if parsed_date:
            if not quiet:
                print("Found ESMA update date via direct HTTP fetch.")
            return parsed_date
    except Exception as request_error:
        if not quiet:
            print(f"Direct HTTP fetch failed: {request_error}")

    use_playwright_fallback = os.getenv("ESMA_USE_PLAYWRIGHT_FALLBACK", "0").lower() in {"1", "true", "yes"}
    if not use_playwright_fallback:
        if not quiet:
            print("Skipping Playwright fallback (set ESMA_USE_PLAYWRIGHT_FALLBACK=1 to enable).")
        return None

    with sync_playwright() as p:
        # Launch browser (headless by default)
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as e:
            browser = None
            fallback_executables = _get_playwright_chromium_executables()
            for fallback_executable in fallback_executables:
                try:
                    if not quiet:
                        print(f"Default Playwright launch failed; trying fallback: {fallback_executable}")
                    browser = p.chromium.launch(headless=True, executable_path=fallback_executable)
                    break
                except Exception as fallback_error:
                    if not quiet:
                        print(f"Fallback launch failed: {fallback_error}")
                    browser = None
            if browser is None:
                if not quiet:
                    print(f"Error launching browser: {e}")
                    print("\nIf this is your first time using Playwright, you may need to install browsers:")
                    print("  python3 -m playwright install chromium")
                return None
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # Navigate to the page
            if not quiet:
                print(f"Navigating to ESMA website...")
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for the page to load and scroll to the section if needed
            page.wait_for_timeout(2000)  # Give page time to render
            
            # Try to find the "Last update" text
            # The text appears as: "Last update: 23 December 2025"
            # We'll search for text containing "Last update"
            if not quiet:
                print("Searching for 'Last update' text...")
            
            # Try multiple selectors to find the date
            selectors = [
                "text=Last update",
                "text=Last update:",
                "em:has-text('Last update')",
                "*:has-text('Last update')",
            ]
            
            last_update_text = None
            for selector in selectors:
                try:
                    element = page.locator(selector).first
                    if element.count() > 0:
                        # Get the text content
                        last_update_text = element.text_content(timeout=5000)
                        if last_update_text and "Last update" in last_update_text:
                            if not quiet:
                                print(f"Found update text: {last_update_text}")
                            break
                except PlaywrightTimeoutError:
                    continue
            
            # If not found with selectors, try to get all text and search
            if not last_update_text:
                if not quiet:
                    print("Trying alternative method: searching page content...")
                page_content = page.content()
                # Look for pattern like "Last update: 23 December 2025" or "<em>Last update: 23 December 2025</em>"
                match = re.search(r'Last update:\s*(\d{1,2}\s+\w+\s+\d{4})', page_content, re.IGNORECASE)
                if match:
                    last_update_text = f"Last update: {match.group(1)}"
                    if not quiet:
                        print(f"Found update text in page content: {last_update_text}")
            
            if not last_update_text:
                # Take a screenshot for debugging
                screenshot_path = Path(__file__).parent.parent / "esma_page_screenshot.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                if not quiet:
                    print(f"Could not find 'Last update' text. Screenshot saved to {screenshot_path}")
                return None
            
            # Parse the date from the text
            esma_date = _parse_last_update_from_text(last_update_text)
            if not esma_date:
                if not quiet:
                    print(f"Could not parse date from text: {last_update_text}")
                return None
            return esma_date
            
        except Exception as e:
            if not quiet:
                print(f"Error while scraping ESMA website: {e}")
            # Take a screenshot for debugging
            try:
                screenshot_path = Path(__file__).parent.parent / "esma_page_error.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                if not quiet:
                    print(f"Screenshot saved to {screenshot_path}")
            except:
                pass
            return None
        finally:
            browser.close()


def main():
    """Main function to check for updates."""
    print("=" * 60)
    print("ESMA MiCA Register Update Checker")
    print("=" * 60)
    
    # Get latest CSV file date
    csv_date, csv_file = get_latest_csv_date()
    if not csv_date:
        print("Error: Could not find any CSV files in data/cleaned/")
        print("Expected format: CASPYYYYMMDD_clean.csv")
        sys.exit(1)
    
    print(f"\nLatest CSV file: {csv_file}")
    print(f"CSV file date: {csv_date.strftime('%d %B %Y')}")
    
    # Get ESMA website update date
    print("\nChecking ESMA website...")
    esma_date = get_esma_update_date()
    
    if not esma_date:
        print("\nError: Could not retrieve update date from ESMA website")
        sys.exit(1)
    
    print(f"ESMA last update: {esma_date.strftime('%d %B %Y')}")
    
    # Compare dates
    print("\n" + "=" * 60)
    if esma_date > csv_date:
        days_diff = (esma_date - csv_date).days
        print(f"⚠️  UPDATE AVAILABLE!")
        print(f"ESMA has updated the register {days_diff} day(s) after your latest CSV file.")
        print(f"Your CSV is from: {csv_date.strftime('%d %B %Y')}")
        print(f"ESMA update is from: {esma_date.strftime('%d %B %Y')}")
        sys.exit(1)  # Exit with error code to indicate update available
    elif esma_date == csv_date:
        print("✅ Your CSV file is up to date!")
        print(f"Both dates match: {esma_date.strftime('%d %B %Y')}")
        sys.exit(0)
    else:
        days_diff = (csv_date - esma_date).days
        print(f"⚠️  WARNING: Your CSV file is newer than ESMA website!")
        print(f"This might indicate:")
        print(f"  - ESMA website hasn't been updated yet")
        print(f"  - There's a date parsing issue")
        print(f"  - Your CSV file date is incorrect")
        print(f"\nCSV date: {csv_date.strftime('%d %B %Y')}")
        print(f"ESMA date: {esma_date.strftime('%d %B %Y')}")
        print(f"Difference: {days_diff} day(s)")
        sys.exit(0)


if __name__ == "__main__":
    main()
