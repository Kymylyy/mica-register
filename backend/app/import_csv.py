import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from .models import Entity, Service, PassportCountry
from typing import List, Optional


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse date from DD/MM/YYYY format"""
    if not date_str or pd.isna(date_str) or date_str.strip() == "":
        return None
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
    except (ValueError, AttributeError):
        return None


def parse_pipe_separated(value: Optional[str]) -> List[str]:
    """Parse pipe-separated values, handling spaces and empty values"""
    if not value or pd.isna(value) or value.strip() == "":
        return []
    # Split by pipe, strip whitespace, filter empty strings
    return [item.strip() for item in str(value).split("|") if item.strip()]


def normalize_service_code(service_text: str) -> Optional[str]:
    """
    Normalize service code from CSV to standard MiCA code (a-j).
    CSV contains various formats like "a. providing custody..." or just "a."
    Extract the letter (a-j) from the beginning of the text.
    """
    if not service_text:
        return None
    
    service_text = service_text.strip()
    if not service_text:
        return None
    
    # Look for letter a-j at the start (with optional period and space)
    import re
    match = re.match(r'^([a-j])\.?\s*', service_text, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    
    # If it's already just a single letter a-j, return it
    if len(service_text) == 1 and service_text.lower() in 'abcdefghij':
        return service_text.lower()
    
    return None


# MiCA standard service descriptions
MICA_SERVICE_DESCRIPTIONS = {
    "a": "providing custody and administration of crypto-assets on behalf of clients",
    "b": "operation of a trading platform for crypto-assets",
    "c": "exchange of crypto-assets for funds",
    "d": "exchange of crypto-assets for other crypto-assets",
    "e": "execution of orders for crypto-assets on behalf of clients",
    "f": "placing of crypto-assets",
    "g": "reception and transmission of orders for crypto-assets on behalf of clients",
    "h": "providing advice on crypto-assets",
    "i": "providing portfolio management on crypto-assets",
    "j": "providing transfer services for crypto-assets on behalf of clients"
}


def get_or_create_service(db: Session, service_code: str, service_cache: dict) -> Service:
    """Get existing service or create new one"""
    # Check cache first (for objects in current session)
    if service_code in service_cache:
        return service_cache[service_code]
    
    # Check database
    service = db.query(Service).filter(Service.code == service_code).first()
    if not service:
        description = MICA_SERVICE_DESCRIPTIONS.get(service_code, service_code)
        service = Service(code=service_code, description=description)
        db.add(service)
    # Cache it
    service_cache[service_code] = service
    return service


def get_or_create_country(db: Session, country_code: str, country_cache: dict) -> PassportCountry:
    """Get existing country or create new one"""
    # Check cache first (for objects in current session)
    if country_code in country_cache:
        return country_cache[country_code]
    
    # Check database
    country = db.query(PassportCountry).filter(PassportCountry.country_code == country_code).first()
    if not country:
        country = PassportCountry(country_code=country_code)
        db.add(country)
    # Cache it
    country_cache[country_code] = country
    return country


def fix_encoding_issues(text):
    """Fix common encoding issues in text data"""
    if not isinstance(text, str) or pd.isna(text):
        return text
    
    # Fix replacement character (U+FFFD = \ufffd) in context of German words
    # The replacement character can appear as different representations
    replacement_chars = ['\ufffd', '\xef\xbf\xbd', '']
    
    for rep_char in replacement_chars:
        # Fix "Stra" + replacement + "e" -> "Straße"
        if 'Stra' + rep_char + 'e' in text:
            text = text.replace('Stra' + rep_char + 'e', 'Straße')
        # Also handle case variations
        if 'stra' + rep_char + 'e' in text:
            text = text.replace('stra' + rep_char + 'e', 'straße')
        
        # Fix "L" + replacement + "w" -> "Löw" (common in German names/addresses)
        if 'L' + rep_char + 'w' in text:
            text = text.replace('L' + rep_char + 'w', 'Löw')
        if 'l' + rep_char + 'w' in text:
            text = text.replace('l' + rep_char + 'w', 'löw')
        
        # Fix other common patterns with replacement character
        # "M" + replacement + "n" -> "Mün" (München, etc.)
        if 'M' + rep_char + 'n' in text and ('chen' in text or 'ster' in text):
            text = text.replace('M' + rep_char + 'n', 'Mün')
    
    # Fix "Strae" (without replacement char, just missing ß)
    text = text.replace('Strae', 'Straße')
    text = text.replace('strae', 'straße')
    
    # Fix "Lw" -> "Löw" (without replacement char)
    text = text.replace('Lw', 'Löw')
    text = text.replace('lw', 'löw')
    
    # Fix other common patterns where ß was lost
    text = text.replace('Strasse', 'Straße')  # Alternative spelling
    
    # Fix common German umlauts (only fix broken encodings, not already correct ones)
    # These are common mis-encodings from UTF-8 read as Latin-1
    text = text.replace('Ã¤', 'ä')
    text = text.replace('Ã¶', 'ö')
    text = text.replace('Ã¼', 'ü')
    text = text.replace('Ã„', 'Ä')
    text = text.replace('Ã–', 'Ö')
    text = text.replace('Ãœ', 'Ü')
    text = text.replace('ÃŸ', 'ß')
    
    # Fix broken quotation marks (replacement character in quotes context)
    # Pattern: (replacement char)Text(replacement char) -> "Text"
    import re
    for rep_char in replacement_chars:
        if rep_char:  # Only process if replacement char is not empty
            # Fix pattern like (Kraken) -> ("Kraken")
            # Match: (replacement char)(word)(replacement char) inside parentheses
            pattern = r'\(' + re.escape(rep_char) + r'([A-Za-z][A-Za-z0-9\s]+?)' + re.escape(rep_char) + r'\)'
            text = re.sub(pattern, r'("\1")', text)
            # Also handle case where replacement char is at start/end of word in parentheses
            # (Kraken) -> ("Kraken")
            if rep_char in text and '(' in text and ')' in text:
                # More general pattern: find (replacement char)(text)(replacement char) and replace with ("text")
                text = re.sub(r'\(' + re.escape(rep_char) + r'([^)]+?)' + re.escape(rep_char) + r'\)', r'("\1")', text)
    
    # Fix common quotation mark encoding issues (Windows-1252 misread as UTF-8)
    text = text.replace('â€œ', '"')  # Left double quotation mark
    text = text.replace('â€', '"')   # Right double quotation mark
    text = text.replace('â€™', "'")   # Right single quotation mark
    text = text.replace('â€˜', "'")   # Left single quotation mark
    
    return text


def import_csv_to_db(db: Session, csv_path: str):
    """Import CSV data into database"""
    # Read CSV with proper encoding handling
    # Try multiple encodings to handle special characters (German umlauts, etc.)
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'windows-1252']
    df = None
    
    for encoding in encodings:
        try:
            # Use errors='replace' to handle any problematic characters
            df = pd.read_csv(csv_path, encoding=encoding, encoding_errors='replace')
            print(f"Successfully read CSV with encoding: {encoding}")
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if df is None:
        # Last resort: try with errors='replace' on utf-8
        try:
            df = pd.read_csv(csv_path, encoding='utf-8', encoding_errors='replace')
            print("Successfully read CSV with encoding: utf-8 (with error replacement)")
        except Exception as e:
            raise ValueError(f"Could not read CSV file. Error: {e}")
    
    # Fix encoding issues in text columns
    text_columns = ['ae_address', 'ae_commercial_name', 'ae_lei_name', 'ac_competentAuthority', 'ac_comments']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(fix_encoding_issues)
    
    # Clear existing data - delete in correct order to handle foreign keys
    from sqlalchemy import text
    db.execute(text("DELETE FROM entity_service"))
    db.execute(text("DELETE FROM entity_passport_country"))
    db.execute(text("DELETE FROM entity_tags"))
    db.query(Entity).delete()
    db.query(Service).delete()
    db.query(PassportCountry).delete()
    db.commit()
    
    # Caches to avoid duplicate objects in same session
    service_cache = {}
    country_cache = {}
    
    for index, row in df.iterrows():
        # Skip empty rows
        if pd.isna(row.get('ae_lei')) or str(row.get('ae_lei')).strip() == "":
            continue
        
        # Parse dates
        auth_date = parse_date(row.get('ac_authorisationNotificationDate'))
        end_date = parse_date(row.get('ac_authorisationEndDate'))
        last_update = parse_date(row.get('ac_lastupdate'))
        
        # Parse services and countries first (remove duplicates)
        service_texts = parse_pipe_separated(row.get('ac_serviceCode'))
        # Normalize service codes to standard MiCA codes (a-j)
        normalized_codes = []
        for service_text in service_texts:
            normalized = normalize_service_code(service_text)
            if normalized:
                normalized_codes.append(normalized)
        service_codes = list(set(normalized_codes))  # Remove duplicates
        
        passport_codes = list(set([c.strip().upper() for c in parse_pipe_separated(row.get('ac_serviceCode_cou')) if c.strip()]))
        
        # Get or create services and countries (deduplicate by object reference)
        services = []
        seen_services = set()
        for service_code in service_codes:
            service = get_or_create_service(db, service_code, service_cache)
            # Use id() for comparison since objects might not have .id yet
            service_key = id(service)
            if service_key not in seen_services:
                seen_services.add(service_key)
                services.append(service)
        
        countries = []
        seen_countries = set()
        for country_code in passport_codes:
            country = get_or_create_country(db, country_code, country_cache)
            # Use id() for comparison since objects might not have .id yet
            country_key = id(country)
            if country_key not in seen_countries:
                seen_countries.add(country_key)
                countries.append(country)
        
        # Create entity with relationships
        entity = Entity(
            competent_authority=str(row.get('ae_competentAuthority', '')).strip() if not pd.isna(row.get('ae_competentAuthority')) else None,
            home_member_state=str(row.get('ae_homeMemberState', '')).strip() if not pd.isna(row.get('ae_homeMemberState')) else None,
            lei_name=str(row.get('ae_lei_name', '')).strip() if not pd.isna(row.get('ae_lei_name')) else None,
            lei=str(row.get('ae_lei', '')).strip() if not pd.isna(row.get('ae_lei')) else None,
            lei_cou_code=str(row.get('ae_lei_cou_code', '')).strip() if not pd.isna(row.get('ae_lei_cou_code')) else None,
            commercial_name=str(row.get('ae_commercial_name', '')).strip() if not pd.isna(row.get('ae_commercial_name')) else None,
            address=str(row.get('ae_address', '')).strip() if not pd.isna(row.get('ae_address')) else None,
            website=str(row.get('ae_website', '')).strip() if not pd.isna(row.get('ae_website')) else None,
            website_platform=str(row.get('ae_website_platform', '')).strip() if not pd.isna(row.get('ae_website_platform')) else None,
            authorisation_notification_date=auth_date,
            authorisation_end_date=end_date,
            comments=str(row.get('ac_comments', '')).strip() if not pd.isna(row.get('ac_comments')) else None,
            last_update=last_update,
            services=services,
            passport_countries=countries
        )
        
        db.add(entity)
    
    # Commit everything at once to avoid duplicate relationship issues
    db.commit()
    print(f"Imported {len(df)} rows from CSV")


