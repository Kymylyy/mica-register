"""
Central configuration for all ESMA MiCA registers

This module defines the structure, column mappings, and validation rules
for each register type (CASP, OTHER, ART, EMT, NCASP).
"""

from enum import Enum
from typing import Dict, List, Optional, Callable
from datetime import date


class RegisterType(str, Enum):
    """Enum for register types"""
    CASP = "casp"
    OTHER = "other"
    ART = "art"
    EMT = "emt"
    NCASP = "ncasp"


# CSV URLs for downloading registers from ESMA
# Note: These URLs are static for now (hardcoded date: 2024-12)
# TODO: Future enhancement - implement web scraping to get current URLs from ESMA website
# For now, scripts should update these URLs manually when ESMA changes them
REGISTER_CSV_URLS = {
    RegisterType.CASP: 'https://www.esma.europa.eu/sites/default/files/2024-12/CASPS.csv',
    RegisterType.OTHER: 'https://www.esma.europa.eu/sites/default/files/2024-12/OTHER.csv',
    RegisterType.ART: 'https://www.esma.europa.eu/sites/default/files/2024-12/ARTZZ.csv',
    RegisterType.EMT: 'https://www.esma.europa.eu/sites/default/files/2024-12/EMTWP.csv',
    RegisterType.NCASP: 'https://www.esma.europa.eu/sites/default/files/2024-12/NCASP.csv',
}


# Common columns present in all registers (base Entity model)
COMMON_COLUMNS = {
    'ae_competentAuthority': 'competent_authority',
    'ae_homeMemberState': 'home_member_state',
    'ae_lei_name': 'lei_name',
    'ae_lei': 'lei',
    'ae_lei_cou_code': 'lei_cou_code',
}


# Register-specific column mappings
# Maps CSV column name → database field name

CASP_COLUMNS = {
    **COMMON_COLUMNS,
    'ae_commercial_name': 'commercial_name',
    'ae_address': 'address',
    'ae_website': 'website',
    'ae_website_platform': 'website_platform',  # CASP-specific
    'ac_authorisationNotificationDate': 'authorisation_notification_date',
    'ac_authorisationEndDate': 'authorisation_end_date',  # CASP-specific
    'ac_serviceCode': 'services',  # Pipe-separated, special handling
    'ac_serviceCode_cou': 'passport_countries',  # Pipe-separated, special handling
    'ac_comments': 'comments',
    'ac_lastupdate': 'last_update',
}

OTHER_COLUMNS = {
    **COMMON_COLUMNS,
    # NOTE: OTHER register does NOT have commercial_name, address, website in base
    'ae_lei_name_casp': 'lei_name_casp',  # OTHER-specific: linked CASP name
    'ae_lei_casp': 'lei_casp',  # OTHER-specific: linked CASP LEI
    'ae_offerCode_cou': 'offer_countries',  # Pipe-separated
    'ae_DTI_FFG': 'dti_ffg',  # Boolean
    'ae_DTI': 'dti_codes',  # Pipe-separated
    'wp_url': 'white_paper_url',
    'wp_comments': 'white_paper_comments',
    'wp_lastupdate': 'white_paper_last_update',
}

ART_COLUMNS = {
    **COMMON_COLUMNS,
    'ae_commercial_name': 'commercial_name',
    'ae_address': 'address',
    'ae_website': 'website',
    'ac_authorisationNotificationDate': 'authorisation_notification_date',
    'ac_authorisationEndDate': 'authorisation_end_date',  # ART-specific
    'ae_credit_institution': 'credit_institution',  # ART-specific: boolean
    'wp_url': 'white_paper_url',
    'wp_authorisationNotificationDate': 'white_paper_notification_date',
    'wp_url_cou': 'white_paper_offer_countries',  # Pipe-separated
    'wp_comments': 'white_paper_comments',
    'wp_lastupdate': 'white_paper_last_update',
}

EMT_COLUMNS = {
    **COMMON_COLUMNS,
    'ae_commercial_name': 'commercial_name',
    'ae_address': 'address',
    'ae_website': 'website',
    'ac_authorisationNotificationDate': 'authorisation_notification_date',
    'ac_authorisationEndDate': 'authorisation_end_date',  # EMT-specific
    'ae_exemption48_4': 'exemption_48_4',  # EMT-specific: boolean (YES/NO)
    'ae_exemption48_5': 'exemption_48_5',  # EMT-specific: boolean
    'ae_authorisation_other_emt': 'authorisation_other_emt',  # EMT-specific: text
    'ae_DTI_FFG': 'dti_ffg',  # Boolean
    'ae_DTI': 'dti_codes',  # Pipe-separated
    'wp_url': 'white_paper_url',
    'wp_authorisationNotificationDate': 'white_paper_notification_date',
    'wp_comments': 'white_paper_comments',
    'wp_lastupdate': 'white_paper_last_update',
}

NCASP_COLUMNS = {
    **COMMON_COLUMNS,
    'ae_commercial_name': 'commercial_name',
    # NOTE: NCASP does NOT have ae_address
    'ae_website': 'websites',  # NCASP-specific: pipe-separated multiple websites
    'ae_infrigment': 'infringement',  # NCASP-specific
    'ae_reason': 'reason',  # NCASP-specific
    'ae_decision_date': 'decision_date',  # NCASP-specific
    'ae_comments': 'comments',  # Note: ae_ prefix (not ac_)
    'ae_lastupdate': 'last_update',  # Note: ae_ prefix (not ac_)
}


# Register configuration
class RegisterConfig:
    """Configuration for a single register"""

    def __init__(
        self,
        register_type: RegisterType,
        csv_url: str,
        csv_prefix: str,  # NEW: e.g., "CASP", "ART"
        column_mapping: Dict[str, str],
        csv_separator: str = ',',
        date_format: str = '%d/%m/%Y',  # Most registers use DD/MM/YYYY
        required_columns: Optional[List[str]] = None,
        multi_value_fields: Optional[Dict[str, str]] = None,  # field → separator
        boolean_fields: Optional[Dict[str, Callable]] = None,  # field → parser function
    ):
        self.register_type = register_type
        self.csv_url = csv_url
        self.csv_prefix = csv_prefix  # NEW
        self.column_mapping = column_mapping
        self.csv_separator = csv_separator
        self.date_format = date_format
        self.required_columns = required_columns or []
        self.multi_value_fields = multi_value_fields or {}
        self.boolean_fields = boolean_fields or {}

    def get_db_field(self, csv_column: str) -> Optional[str]:
        """Get database field name for CSV column"""
        return self.column_mapping.get(csv_column)

    def is_required(self, csv_column: str) -> bool:
        """Check if CSV column is required"""
        return csv_column in self.required_columns


# Boolean parsers for different formats
def parse_yes_no(value: str) -> Optional[bool]:
    """Parse YES/NO to boolean"""
    if not value or value.strip() == '':
        return None
    val = value.strip().upper()
    if val in ['YES', 'Y', '1', 'TRUE']:
        return True
    elif val in ['NO', 'N', '0', 'FALSE']:
        return False
    return None


def parse_true_false(value: str) -> Optional[bool]:
    """Parse true/false to boolean"""
    if not value or value.strip() == '':
        return None
    val = value.strip().lower()
    if val in ['true', '1', 'yes']:
        return True
    elif val in ['false', '0', 'no']:
        return False
    return None


# Register configurations
REGISTERS = {
    RegisterType.CASP: RegisterConfig(
        register_type=RegisterType.CASP,
        csv_url=REGISTER_CSV_URLS[RegisterType.CASP],
        csv_prefix="CASP",
        column_mapping=CASP_COLUMNS,
        csv_separator=',',
        date_format='%d/%m/%Y',  # CASP uses DD/MM/YYYY
        required_columns=['ae_lei', 'ae_lei_name', 'ae_homeMemberState'],
        multi_value_fields={
            'services': '|',  # Service codes separated by |
            'passport_countries': '|',  # Country codes separated by |
        },
    ),

    RegisterType.OTHER: RegisterConfig(
        register_type=RegisterType.OTHER,
        csv_url=REGISTER_CSV_URLS[RegisterType.OTHER],
        csv_prefix="OTHER",
        column_mapping=OTHER_COLUMNS,
        csv_separator=',',
        date_format='%d/%m/%Y',
        required_columns=['ae_lei', 'ae_lei_name', 'ae_homeMemberState'],
        multi_value_fields={
            'offer_countries': '|',
            'dti_codes': '|',
        },
        boolean_fields={
            'dti_ffg': parse_yes_no,
        },
    ),

    RegisterType.ART: RegisterConfig(
        register_type=RegisterType.ART,
        csv_url=REGISTER_CSV_URLS[RegisterType.ART],
        csv_prefix="ART",
        column_mapping=ART_COLUMNS,
        csv_separator=',',
        date_format='%d/%m/%Y',
        required_columns=['ae_lei', 'ae_lei_name', 'ae_homeMemberState'],
        multi_value_fields={
            'white_paper_offer_countries': '|',
        },
        boolean_fields={
            'credit_institution': parse_yes_no,
        },
    ),

    RegisterType.EMT: RegisterConfig(
        register_type=RegisterType.EMT,
        csv_url=REGISTER_CSV_URLS[RegisterType.EMT],
        csv_prefix="EMT",
        column_mapping=EMT_COLUMNS,
        csv_separator=',',
        date_format='%d/%m/%Y',
        required_columns=['ae_lei', 'ae_lei_name', 'ae_homeMemberState'],
        multi_value_fields={
            'dti_codes': '|',
        },
        boolean_fields={
            'exemption_48_4': parse_yes_no,
            'exemption_48_5': parse_yes_no,
            'dti_ffg': parse_yes_no,
        },
    ),

    RegisterType.NCASP: RegisterConfig(
        register_type=RegisterType.NCASP,
        csv_url=REGISTER_CSV_URLS[RegisterType.NCASP],
        csv_prefix="NCASP",
        column_mapping=NCASP_COLUMNS,
        csv_separator=',',
        date_format='%d/%m/%Y',
        required_columns=['ae_homeMemberState'],  # Note: LEI often missing in NCASP
        multi_value_fields={
            'websites': '|',  # Multiple websites separated by |
        },
        boolean_fields={
            'infringement': parse_yes_no,
        },
    ),
}


def get_register_config(register_type: RegisterType) -> RegisterConfig:
    """Get configuration for a specific register type"""
    config = REGISTERS.get(register_type)
    if not config:
        raise ValueError(f"Unknown register type: {register_type}")
    return config


def get_all_register_types() -> List[RegisterType]:
    """Get list of all register types"""
    return list(RegisterType)


# File naming patterns
def get_raw_csv_filename(register_type: RegisterType, date_str: str) -> str:
    """Get filename for raw CSV file

    Args:
        register_type: Register type
        date_str: Date string in YYYYMMDD format

    Returns:
        Filename like "CASP20260123.csv"
    """
    return f"{register_type.value.upper()}{date_str}.csv"


def get_cleaned_csv_filename(register_type: RegisterType, date_str: str) -> str:
    """Get filename for cleaned CSV file

    Args:
        register_type: Register type
        date_str: Date string in YYYYMMDD format

    Returns:
        Filename like "CASP20260123_clean.csv"
    """
    return f"{register_type.value.upper()}{date_str}_clean.csv"


# Validation helpers
def validate_lei(lei: str) -> bool:
    """Validate LEI format (20 alphanumeric characters)"""
    if not lei or not isinstance(lei, str):
        return False
    return len(lei) == 20 and lei.isalnum() and lei.isupper()


def validate_service_code(code: str) -> bool:
    """Validate MiCA service code (a-j)"""
    return code in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']


def validate_country_code(code: str) -> bool:
    """Validate ISO 2-letter country code"""
    # Basic validation - could use pycountry for more robust checking
    return len(code) == 2 and code.isalpha() and code.isupper()


# Export main objects
__all__ = [
    'RegisterType',
    'RegisterConfig',
    'REGISTERS',
    'get_register_config',
    'get_all_register_types',
    'get_raw_csv_filename',
    'get_cleaned_csv_filename',
    'validate_lei',
    'validate_service_code',
    'validate_country_code',
    'parse_yes_no',
    'parse_true_false',
]
