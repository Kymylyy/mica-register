/**
 * Country code to full English name mapping
 * ISO 3166-1 alpha-2 country codes
 */
export const COUNTRY_NAMES = {
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
  'EL': 'Greece', // Alternative code for Greece
};

function normalizeCountryCode(countryCode) {
  if (typeof countryCode !== 'string') return '';
  return countryCode.trim().toUpperCase();
}

/**
 * Select primary country code for display.
 * Prefer home member state, fallback to LEI country code.
 *
 * @param {string | null | undefined} homeMemberState
 * @param {string | null | undefined} leiCountryCode
 * @returns {string | null}
 */
export function getPrimaryCountryCode(homeMemberState, leiCountryCode) {
  const normalizedHome = normalizeCountryCode(homeMemberState);
  if (normalizedHome) return normalizedHome;

  const normalizedLei = normalizeCountryCode(leiCountryCode);
  return normalizedLei || null;
}

/**
 * Get country name from country code
 * @param {string} countryCode - Two-letter country code
 * @returns {string} Country name or the code if not found
 */
export function getCountryName(countryCode) {
  return COUNTRY_NAMES[countryCode?.toUpperCase()] || countryCode;
}
