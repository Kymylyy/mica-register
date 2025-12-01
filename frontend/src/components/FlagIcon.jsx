// Import flag-icons CSS
import 'flag-icons/css/flag-icons.min.css';

/**
 * Country code mappings for alternative codes to ISO 3166-1 alpha-2
 * Some systems use alternative codes that need to be mapped to standard ISO codes
 */
const COUNTRY_CODE_MAP = {
  'EL': 'GR', // Greece - EL is used in some systems, but GR is the ISO code
};

/**
 * Get country code for flag-icons (lowercase ISO code)
 * @param {string} countryCode - Two-letter country code (e.g., 'AT', 'DE', 'EL')
 * @returns {string|null} Lowercase ISO code or null if invalid
 */
function getFlagCode(countryCode) {
  if (!countryCode || countryCode.length !== 2) return null;
  const isoCode = COUNTRY_CODE_MAP[countryCode.toUpperCase()] || countryCode.toUpperCase();
  return isoCode.toLowerCase();
}

/**
 * Converts country code to emoji flag (kept for backward compatibility)
 * @param {string} countryCode - Two-letter country code (e.g., 'AT', 'DE', 'EL')
 * @returns {string} Emoji flag
 * @deprecated Use FlagIcon component instead for better compatibility
 */
export function getCountryFlag(countryCode) {
  const flagCode = getFlagCode(countryCode);
  if (!flagCode) return '';
  
  const codePoints = flagCode.toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt(0));
  
  return String.fromCodePoint(...codePoints);
}

/**
 * FlagIcon component - uses flag-icons library (SVG flags that work everywhere)
 * @param {string} countryCode - Two-letter country code (e.g., 'AT', 'DE', 'EL')
 * @param {string} className - Additional CSS classes
 * @param {string} size - Flag size: 'xs' (12px), 'sm' (16px), 'md' (20px), 'lg' (24px)
 * @returns {JSX.Element|null} Flag icon component
 */
export function FlagIcon({ countryCode, className = '', size = 'sm' }) {
  const flagCode = getFlagCode(countryCode);
  if (!flagCode) return null;
  
  // Size mapping: flag-icons uses font-size to control flag size
  // The flag width is 1.333em (4:3 ratio), so we set font-size accordingly
  const sizeStyles = {
    xs: { fontSize: '10px' },  // ~13px wide
    sm: { fontSize: '12px' },  // ~16px wide
    md: { fontSize: '16px' },  // ~21px wide
    lg: { fontSize: '20px' }   // ~27px wide
  };
  
  const style = sizeStyles[size] || sizeStyles.sm;
  
  return (
    <span 
      className={`fi fi-${flagCode} ${className}`.trim()}
      style={style}
      title={countryCode}
      role="img"
      aria-label={`Flag of ${countryCode}`}
    />
  );
}


