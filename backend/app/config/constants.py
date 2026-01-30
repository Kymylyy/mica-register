"""
Centralized constants for MiCA registers
Shared across import, validation, cleaning, and API modules

IMPORTANT: This file should NOT import from any other app modules
to avoid circular dependencies. It contains only data constants.
"""

# MiCA standard service descriptions (a-j)
# Used for parsing service codes from ESMA CSV files
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

# Short service names for compact display (UI chips, filters)
MICA_SERVICE_SHORT_NAMES = {
    "a": "Custody",
    "b": "Trading platform",
    "c": "Crypto-to-funds",
    "d": "Crypto-to-crypto",
    "e": "Order execution",
    "f": "Placement",
    "g": "Order routing",
    "h": "Advisory",
    "i": "Portfolio management",
    "j": "Transfer"
}

# Medium-length service names for table columns
MICA_SERVICE_MEDIUM_NAMES = {
    "a": "Custody and administration",
    "b": "Trading platform operation",
    "c": "Crypto-to-funds exchange",
    "d": "Crypto-to-crypto exchange",
    "e": "Order execution",
    "f": "Placing of crypto-assets",
    "g": "Reception and transmission of orders",
    "h": "Crypto-asset advisory",
    "i": "Portfolio management",
    "j": "Transfer services"
}

# Country code to full English name mapping (ISO 3166-1 alpha-2)
# Covers all EEA countries + common extensions
COUNTRY_NAMES = {
    'AT': 'Austria',
    'BE': 'Belgium',
    'BG': 'Bulgaria',
    'CY': 'Cyprus',
    'CZ': 'Czech Republic',
    'DE': 'Germany',
    'DK': 'Denmark',
    'EE': 'Estonia',
    'ES': 'Spain',
    'FI': 'Finland',
    'FR': 'France',
    'GR': 'Greece',
    'HR': 'Croatia',
    'HU': 'Hungary',
    'IE': 'Ireland',
    'IS': 'Iceland',
    'IT': 'Italy',
    'LI': 'Liechtenstein',
    'LT': 'Lithuania',
    'LU': 'Luxembourg',
    'LV': 'Latvia',
    'MT': 'Malta',
    'NL': 'Netherlands',
    'NO': 'Norway',
    'PL': 'Poland',
    'PT': 'Portugal',
    'RO': 'Romania',
    'SE': 'Sweden',
    'SI': 'Slovenia',
    'SK': 'Slovakia',
    'EL': 'Greece',  # Alternative code for Greece
}
