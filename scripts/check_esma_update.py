#!/usr/bin/env python3
"""
Script to check if ESMA has updated the Interim MiCA Register.
Uses Playwright to scrape the last update date from the ESMA website
and compares it with the latest CSV file in data/cleaned/.
"""
import sys
import re
from pathlib import Path
from glob import glob
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def get_latest_csv_date(quiet=False):
    """Get the date from the newest CSV file in data/cleaned/.
    
    Args:
        quiet: If True, don't print warnings to stdout
        
    Returns:
        Tuple of (datetime object, file path) or (None, None) if not found
    """
    base_paths = [
        Path(__file__).parent.parent / "data" / "cleaned",
        Path("/app/data/cleaned"),  # Docker container
    ]
    
    date_pattern = re.compile(r'CASP(\d{8})_clean(?:\.csv|_llm\.csv)$')
    newest_date = None
    newest_file = None
    
    for base_path in base_paths:
        if base_path.exists():
            # Check both _clean.csv and _clean_llm.csv files
            for pattern_suffix in ["*_clean.csv", "*_clean_llm.csv"]:
                pattern = str(base_path / pattern_suffix)
                for file_path in glob(pattern):
                    match = date_pattern.search(file_path)
                    if match:
                        file_date_str = match.group(1)  # YYYYMMDD
                        if newest_date is None or file_date_str > newest_date:
                            newest_date = file_date_str
                            newest_file = file_path
    
    if newest_date:
        # Parse YYYYMMDD format
        try:
            date_obj = datetime.strptime(newest_date, "%Y%m%d")
            return date_obj, newest_file
        except ValueError:
            if not quiet:
                print(f"Warning: Could not parse date from filename: {newest_date}")
            return None, newest_file
    
    return None, None


def get_esma_update_date(quiet=False):
    """Scrape the last update date from ESMA website using Playwright.
    
    Args:
        quiet: If True, suppress non-critical output
        
    Returns:
        datetime object or None if failed
    """
    url = "https://www.esma.europa.eu/esmas-activities/digital-finance-and-innovation/markets-crypto-assets-regulation-mica#InterimMiCARegister"
    
    with sync_playwright() as p:
        # Launch browser (headless by default)
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as e:
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
            # Format: "Last update: 23 December 2025" or "Last update: 23 December 2025"
            date_match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', last_update_text)
            if not date_match:
                if not quiet:
                    print(f"Could not parse date from text: {last_update_text}")
                return None
            
            day = int(date_match.group(1))
            month_name = date_match.group(2)
            year = int(date_match.group(3))
            
            # Convert month name to number
            month_map = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12
            }
            month = month_map.get(month_name.lower())
            if not month:
                if not quiet:
                    print(f"Unknown month name: {month_name}")
                return None
            
            esma_date = datetime(year, month, day)
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

