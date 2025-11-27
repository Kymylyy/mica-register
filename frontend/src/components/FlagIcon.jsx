/**
 * Country code mappings for alternative codes to ISO 3166-1 alpha-2
 * Some systems use alternative codes that need to be mapped to standard ISO codes for flag emoji
 */
const COUNTRY_CODE_MAP = {
  'EL': 'GR', // Greece - EL is used in some systems, but GR is the ISO code for flag emoji
};

/**
 * Converts country code to emoji flag
 * @param {string} countryCode - Two-letter country code (e.g., 'AT', 'DE', 'EL')
 * @returns {string} Emoji flag
 */
export function getCountryFlag(countryCode) {
  if (!countryCode || countryCode.length !== 2) return '';
  
  // Map alternative codes to ISO 3166-1 alpha-2 codes
  const isoCode = COUNTRY_CODE_MAP[countryCode.toUpperCase()] || countryCode.toUpperCase();
  
  const codePoints = isoCode
    .split('')
    .map(char => 127397 + char.charCodeAt(0));
  
  return String.fromCodePoint(...codePoints);
}

export function FlagIcon({ countryCode, className = '' }) {
  const flag = getCountryFlag(countryCode);
  if (!flag) return null;
  
  return <span className={className} title={countryCode}>{flag}</span>;
}


