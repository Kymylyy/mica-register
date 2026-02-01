import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
from .models import (
    Entity, Service, PassportCountry,
    CaspEntity, OtherEntity, ArtEntity, EmtEntity, NcaspEntity,
    RegisterType
)
from .config.registers import (
    get_register_config, RegisterConfig,
    parse_yes_no, parse_true_false
)
from .config.constants import MICA_SERVICE_DESCRIPTIONS
from typing import List, Optional

# Initialize logger
logger = logging.getLogger(__name__)


def parse_date(date_str: Optional[str], date_format: str = "%d/%m/%Y") -> Optional[datetime]:
    """
    Parse date from specified format (default: DD/MM/YYYY).

    Args:
        date_str: Date string to parse
        date_format: Expected date format (e.g., "%d/%m/%Y" or "%Y-%m-%d")

    Returns:
        datetime.date object or None if parsing fails
    """
    if not date_str or pd.isna(date_str) or date_str.strip() == "":
        return None

    # Clean up the date string - remove extra dots, spaces, etc.
    date_str = date_str.strip()

    # Fix common errors: "01/12/.2025" -> "01/12/2025"
    # Remove dots before year if they exist (handle various formats)
    import re
    # Handle "DD/MM/.YYYY" or "DD/MM/ .YYYY" (with slash and optional space before dot)
    date_str = re.sub(r'(\d{2}/\d{2})/\s*\.\s*(\d{4})', r'\1/\2', date_str)
    # Handle "DD/MM.YYYY" (without slash before dot)
    date_str = re.sub(r'(\d{2}/\d{2})\.(\d{4})', r'\1/\2', date_str)
    # Handle "DD/MM .YYYY" (space before dot, no slash)
    date_str = re.sub(r'(\d{2}/\d{2})\s+\.\s*(\d{4})', r'\1/\2', date_str)
    # Remove any trailing dots
    date_str = date_str.rstrip('.')

    try:
        return datetime.strptime(date_str, date_format).date()
    except (ValueError, AttributeError):
        # Try fallback formats if primary format fails
        fallback_formats = ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"]
        for fmt in fallback_formats:
            if fmt != date_format:  # Don't retry the same format
                try:
                    return datetime.strptime(date_str, fmt).date()
                except (ValueError, AttributeError):
                    continue
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


def normalize_commercial_name(name: Optional[str]) -> Optional[str]:
    """Normalize commercial name by fixing known errors"""
    if not name or pd.isna(name):
        return None
    
    name = str(name).strip()
    if not name:
        return None
    
    # Fix known errors in commercial names
    # "e Toro" -> "eToro"
    if name == "e Toro":
        return "eToro"
    
    return name


def is_url(value: Optional[str]) -> bool:
    """Check if a value looks like a URL"""
    if not value or pd.isna(value):
        return False
    
    value_str = str(value).strip()
    if not value_str:
        return False
    
    # Check if it starts with http://, https://, or www.
    if value_str.startswith(('http://', 'https://', 'www.')):
        return True
    
    # Check if it looks like a domain (contains a dot and looks like a domain)
    import re
    # Pattern: starts with alphanumeric, contains dot, ends with valid TLD-like pattern
    domain_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}'
    if re.match(domain_pattern, value_str):
        return True
    
    return False


def fix_address_website_parsing(row: pd.Series) -> tuple[Optional[str], Optional[str]]:
    """
    Fix cases where address with comma was incorrectly parsed by CSV reader,
    causing part of address to appear in website column.
    
    This happens when:
    1. Address contains comma (e.g., "61 rue de Lyon, 75012 Paris")
    2. CSV parser incorrectly splits it, putting "75012 Paris" in website column
    3. Website column doesn't look like a URL (no http://, https://, www., or domain pattern)
    
    If website doesn't look like URL and address exists, merge them back together.
    Returns (fixed_address, fixed_website)
    """
    address = str(row.get('ae_address', '')).strip() if not pd.isna(row.get('ae_address')) else ''
    website = str(row.get('ae_website', '')).strip() if not pd.isna(row.get('ae_website')) else ''
    
    # If website doesn't look like a URL and address exists, merge them
    # This handles cases where CSV parser incorrectly split address with comma
    if website and not is_url(website) and address:
        # Merge: address + ", " + website
        # This reconstructs the original address that was incorrectly split
        fixed_address = f"{address}, {website}"
        fixed_website = None  # No valid URL, so set to None (will display as "-" in UI)
        entity_name = str(row.get('ae_commercial_name', 'N/A')).strip() if not pd.isna(row.get('ae_commercial_name')) else 'N/A'
        print(f"  Fixed address parsing for {entity_name}: merged '{website}' back into address")
        return (fixed_address, None)
    
    # If website looks like URL but address seems incomplete (ends with comma or number),
    # check if next column might be part of address
    # This is a more advanced check for edge cases
    
    # Return None for empty strings, otherwise return as-is
    return (address if address else None, website if website else None)


def import_csv_to_db(db: Session, csv_path: str, register_type: RegisterType = RegisterType.CASP):
    """
    Import CSV data into database for a specific register type.

    Args:
        db: Database session
        csv_path: Path to cleaned CSV file
        register_type: Register type to import (CASP, OTHER, ART, EMT, NCASP)

    Expects a cleaned CSV file (from csv_clean.py) with:
    - UTF-8 encoding
    - Already fixed encoding issues
    - All rows preserved (no deduplication by LEI or other fields)
    - Already normalized service codes, commercial names, addresses, etc.

    Note: Duplicate LEI codes are allowed and preserved.
    Example: OTHER register may have multiple rows with same LEI (different white papers).

    This function handles:
    - Reading the cleaned CSV
    - Parsing dates, booleans, and pipe-separated values per register config
    - Creating database entities with correct extension tables
    """
    # Normalize register_type to enum (handles accidental string input like "CASP")
    if isinstance(register_type, str):
        try:
            register_type = RegisterType(register_type.lower())
        except ValueError as exc:
            raise ValueError(f"Unknown register_type: {register_type}") from exc

    # Normalize to lowercase string for DB comparisons (Postgres ENUM uses lowercase)
    register_type_value = register_type.value if isinstance(register_type, RegisterType) else str(register_type).lower()

    # Get register configuration
    config = get_register_config(register_type)
    print(f"Importing {register_type.value.upper()} register from: {csv_path}")

    # Read cleaned CSV (should be UTF-8, already cleaned)
    try:
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        logger.info(f"Successfully read cleaned CSV file: {csv_path} ({len(df)} rows)")
        print(f"Successfully read cleaned CSV file: {len(df)} rows")
    except pd.errors.EmptyDataError:
        print(f"⚠ CSV file is empty, skipping {register_type.value.upper()} import")
        return
    except UnicodeDecodeError as e:
        logger.warning(f"UTF-8-sig decode failed for {csv_path}: {e}")
        # Fallback for edge cases
        try:
            df = pd.read_csv(csv_path, encoding='utf-8', encoding_errors='replace')
            logger.info(f"Successfully read {csv_path} with UTF-8 fallback encoding")
            print("Read CSV with UTF-8 fallback encoding")
        except pd.errors.EmptyDataError:
            print(f"⚠ CSV file is empty, skipping {register_type.value.upper()} import")
            return
        except Exception as e:
            logger.error(f"Failed to read CSV file {csv_path}: {e}", exc_info=True)
            raise ValueError(f"Could not read CSV file. Expected cleaned UTF-8 file. Error: {e}")

    # Check if DataFrame is empty (no rows)
    if len(df) == 0:
        print(f"⚠ No data rows in CSV file, skipping {register_type.value.upper()} import")
        return

    # Clear existing data for this register type ONLY
    # Delete entities and their extensions for this register
    print(f"Clearing existing {register_type.value.upper()} data...")

    # Delete extension table data first (if applicable)
    if register_type == RegisterType.CASP:
        db.execute(text("DELETE FROM casp_entity_service WHERE casp_entity_id IN (SELECT id FROM entities WHERE register_type = 'casp')"))
        db.execute(text("DELETE FROM casp_entity_passport_country WHERE casp_entity_id IN (SELECT id FROM entities WHERE register_type = 'casp')"))
        db.execute(text("DELETE FROM casp_entities WHERE id IN (SELECT id FROM entities WHERE register_type = 'casp')"))
    elif register_type == RegisterType.OTHER:
        db.execute(text("DELETE FROM other_entities WHERE id IN (SELECT id FROM entities WHERE register_type = 'other')"))
    elif register_type == RegisterType.ART:
        db.execute(text("DELETE FROM art_entities WHERE id IN (SELECT id FROM entities WHERE register_type = 'art')"))
    elif register_type == RegisterType.EMT:
        db.execute(text("DELETE FROM emt_entities WHERE id IN (SELECT id FROM entities WHERE register_type = 'emt')"))
    elif register_type == RegisterType.NCASP:
        db.execute(text("DELETE FROM ncasp_entities WHERE id IN (SELECT id FROM entities WHERE register_type = 'ncasp')"))

    # Delete entity_tags for this register
    db.execute(text(f"DELETE FROM entity_tags WHERE entity_id IN (SELECT id FROM entities WHERE register_type = '{register_type.value}')"))

    # Delete entities for this register type
    db.query(Entity).filter(Entity.register_type == register_type_value).delete()
    db.commit()

    # Caches to avoid duplicate objects in same session (CASP only)
    service_cache = {}
    country_cache = {}

    # Import rows
    imported_count = 0
    for index, row in df.iterrows():
        # Check required fields based on register config
        # For NCASP and OTHER, LEI is often missing, so we check lei_name or home_member_state instead
        if register_type in [RegisterType.NCASP, RegisterType.OTHER]:
            # For NCASP and OTHER: require either lei_name or home_member_state
            has_lei_name = not pd.isna(row.get('ae_lei_name')) and str(row.get('ae_lei_name')).strip() != ""
            has_home_state = not pd.isna(row.get('ae_homeMemberState')) and str(row.get('ae_homeMemberState')).strip() != ""
            if not (has_lei_name or has_home_state):
                continue  # Skip rows without any identifier
        else:
            # For CASP, ART, EMT: LEI is required
            if pd.isna(row.get('ae_lei')) or str(row.get('ae_lei')).strip() == "":
                continue  # Skip rows without LEI

        # === Parse common fields (all registers) ===
        competent_authority = str(row.get('ae_competentAuthority', '')).strip() if not pd.isna(row.get('ae_competentAuthority')) else None
        home_member_state = str(row.get('ae_homeMemberState', '')).strip() if not pd.isna(row.get('ae_homeMemberState')) else None
        lei_name = str(row.get('ae_lei_name', '')).strip() if not pd.isna(row.get('ae_lei_name')) else None
        lei = str(row.get('ae_lei', '')).strip() if not pd.isna(row.get('ae_lei')) else None
        lei_cou_code = str(row.get('ae_lei_cou_code', '')).strip() if not pd.isna(row.get('ae_lei_cou_code')) else None

        # Commercial name (optional in some registers like OTHER)
        commercial_name = str(row.get('ae_commercial_name', '')).strip() if not pd.isna(row.get('ae_commercial_name')) else None

        # Address (optional in some registers like NCASP)
        address = str(row.get('ae_address', '')).strip() if not pd.isna(row.get('ae_address')) else None

        # Website (different column name in NCASP: ae_website vs websites)
        website_col = 'ae_website'
        if register_type == RegisterType.NCASP:
            website_col = 'ae_website'  # NCASP also uses ae_website but can have multiple (pipe-separated)
        website = str(row.get(website_col, '')).strip() if not pd.isna(row.get(website_col)) else None

        # Dates - use register-specific date format
        auth_date = parse_date(row.get('ac_authorisationNotificationDate'), config.date_format)
        last_update_col = 'ac_lastupdate' if register_type in [RegisterType.CASP] else 'ae_lastupdate' if register_type == RegisterType.NCASP else 'wp_lastupdate'
        last_update = parse_date(row.get(last_update_col), config.date_format)

        # Comments (different column names per register)
        comments_col = 'ac_comments' if register_type in [RegisterType.CASP] else 'ae_comments' if register_type == RegisterType.NCASP else 'wp_comments'
        comments = str(row.get(comments_col, '')).strip() if not pd.isna(row.get(comments_col)) else None

        # === Create base Entity ===
        entity = Entity(
            register_type=register_type,
            competent_authority=competent_authority,
            home_member_state=home_member_state,
            lei_name=lei_name,
            lei=lei,
            lei_cou_code=lei_cou_code,
            commercial_name=commercial_name,
            address=address,
            website=website,
            authorisation_notification_date=auth_date,
            last_update=last_update,
            comments=comments
        )
        db.add(entity)
        db.flush()  # Get entity.id for extension table

        # === Create register-specific extension ===
        if register_type == RegisterType.CASP:
            # CASP-specific fields
            website_platform = str(row.get('ae_website_platform', '')).strip() if not pd.isna(row.get('ae_website_platform')) else None
            end_date = parse_date(row.get('ac_authorisationEndDate'), config.date_format)

            # Parse services
            service_texts = parse_pipe_separated(row.get('ac_serviceCode'))
            service_codes = []
            for service_text in service_texts:
                normalized = normalize_service_code(service_text)
                if normalized:
                    service_codes.append(normalized)
            service_codes = list(set(service_codes))  # Remove duplicates

            # Parse passport countries
            passport_codes = list(set([c.strip().upper() for c in parse_pipe_separated(row.get('ac_serviceCode_cou')) if c.strip()]))

            # Get or create services
            services = []
            for service_code in service_codes:
                service = get_or_create_service(db, service_code, service_cache)
                services.append(service)

            # Get or create countries
            countries = []
            for country_code in passport_codes:
                country = get_or_create_country(db, country_code, country_cache)
                countries.append(country)

            # Assign to legacy relationships for backward compatibility
            # This ensures Entity.services and Entity.passport_countries work in API responses
            # until we fully migrate to using entity.casp_entity.services
            entity.services = services
            entity.passport_countries = countries

            # Create CaspEntity extension
            casp_entity = CaspEntity(
                id=entity.id,
                website_platform=website_platform,
                authorisation_end_date=end_date,
                services=services,
                passport_countries=countries
            )
            db.add(casp_entity)

        elif register_type == RegisterType.OTHER:
            # OTHER-specific fields
            white_paper_url = str(row.get('wp_url', '')).strip() if not pd.isna(row.get('wp_url')) else None
            white_paper_comments = str(row.get('wp_comments', '')).strip() if not pd.isna(row.get('wp_comments')) else None
            white_paper_last_update = parse_date(row.get('wp_lastupdate'), config.date_format)
            lei_casp = str(row.get('ae_lei_casp', '')).strip() if not pd.isna(row.get('ae_lei_casp')) else None
            lei_name_casp = str(row.get('ae_lei_name_casp', '')).strip() if not pd.isna(row.get('ae_lei_name_casp')) else None

            # Parse pipe-separated fields
            offer_countries = '|'.join(parse_pipe_separated(row.get('ae_offerCode_cou')))
            dti_codes = '|'.join(parse_pipe_separated(row.get('ae_DTI')))

            # DTI FFG is a string code (identifier), not a boolean
            dti_ffg = str(row.get('ae_DTI_FFG', '')).strip() if not pd.isna(row.get('ae_DTI_FFG')) else None

            # Create OtherEntity extension
            other_entity = OtherEntity(
                id=entity.id,
                white_paper_url=white_paper_url,
                white_paper_comments=white_paper_comments,
                white_paper_last_update=white_paper_last_update,
                offer_countries=offer_countries if offer_countries else None,
                dti_codes=dti_codes if dti_codes else None,
                dti_ffg=dti_ffg,
                lei_casp=lei_casp,
                lei_name_casp=lei_name_casp
            )
            db.add(other_entity)

        elif register_type == RegisterType.ART:
            # ART-specific fields
            end_date = parse_date(row.get('ac_authorisationEndDate'), config.date_format)
            credit_institution = parse_yes_no(row.get('ae_credit_institution')) if not pd.isna(row.get('ae_credit_institution')) else None
            white_paper_url = str(row.get('wp_url', '')).strip() if not pd.isna(row.get('wp_url')) else None
            white_paper_notification_date = parse_date(row.get('wp_authorisationNotificationDate'), config.date_format)
            white_paper_offer_countries = '|'.join(parse_pipe_separated(row.get('wp_url_cou')))
            white_paper_comments = str(row.get('wp_comments', '')).strip() if not pd.isna(row.get('wp_comments')) else None
            white_paper_last_update = parse_date(row.get('wp_lastupdate'), config.date_format)

            # Create ArtEntity extension
            art_entity = ArtEntity(
                id=entity.id,
                authorisation_end_date=end_date,
                credit_institution=credit_institution,
                white_paper_url=white_paper_url,
                white_paper_notification_date=white_paper_notification_date,
                white_paper_offer_countries=white_paper_offer_countries if white_paper_offer_countries else None,
                white_paper_comments=white_paper_comments,
                white_paper_last_update=white_paper_last_update
            )
            db.add(art_entity)

        elif register_type == RegisterType.EMT:
            # EMT-specific fields
            end_date = parse_date(row.get('ac_authorisationEndDate'), config.date_format)
            exemption_48_4 = parse_yes_no(row.get('ae_exemption48_4')) if not pd.isna(row.get('ae_exemption48_4')) else None
            exemption_48_5 = parse_yes_no(row.get('ae_exemption48_5')) if not pd.isna(row.get('ae_exemption48_5')) else None
            authorisation_other_emt = str(row.get('ae_authorisation_other_emt', '')).strip() if not pd.isna(row.get('ae_authorisation_other_emt')) else None
            # DTI FFG is a string code (identifier), not a boolean
            dti_ffg = str(row.get('ae_DTI_FFG', '')).strip() if not pd.isna(row.get('ae_DTI_FFG')) else None
            dti_codes = '|'.join(parse_pipe_separated(row.get('ae_DTI')))
            white_paper_url = str(row.get('wp_url', '')).strip() if not pd.isna(row.get('wp_url')) else None
            white_paper_notification_date = parse_date(row.get('wp_authorisationNotificationDate'), config.date_format)
            white_paper_comments = str(row.get('wp_comments', '')).strip() if not pd.isna(row.get('wp_comments')) else None
            white_paper_last_update = parse_date(row.get('wp_lastupdate'), config.date_format)

            # Create EmtEntity extension
            emt_entity = EmtEntity(
                id=entity.id,
                authorisation_end_date=end_date,
                exemption_48_4=exemption_48_4,
                exemption_48_5=exemption_48_5,
                authorisation_other_emt=authorisation_other_emt,
                dti_ffg=dti_ffg,
                dti_codes=dti_codes if dti_codes else None,
                white_paper_url=white_paper_url,
                white_paper_notification_date=white_paper_notification_date,
                white_paper_comments=white_paper_comments,
                white_paper_last_update=white_paper_last_update
            )
            db.add(emt_entity)

        elif register_type == RegisterType.NCASP:
            # NCASP-specific fields
            websites = '|'.join(parse_pipe_separated(row.get('ae_website')))  # Multiple websites
            infringement = str(row.get('ae_infrigment', '')).strip() if not pd.isna(row.get('ae_infrigment')) else None  # Note: typo in CSV column name
            reason = str(row.get('ae_reason', '')).strip() if not pd.isna(row.get('ae_reason')) else None
            decision_date = parse_date(row.get('ae_decision_date'), config.date_format)

            # Create NcaspEntity extension
            ncasp_entity = NcaspEntity(
                id=entity.id,
                websites=websites if websites else None,
                infringement=infringement,
                reason=reason,
                decision_date=decision_date
            )
            db.add(ncasp_entity)

        imported_count += 1

    # Commit everything at once
    db.commit()
    print(f"✓ Successfully imported {imported_count} {register_type.value.upper()} entities")
