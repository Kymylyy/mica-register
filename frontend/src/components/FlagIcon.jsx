/**
 * Converts country code to emoji flag
 * @param {string} countryCode - Two-letter country code (e.g., 'AT', 'DE')
 * @returns {string} Emoji flag
 */
export function getCountryFlag(countryCode) {
  if (!countryCode || countryCode.length !== 2) return '';
  
  const codePoints = countryCode
    .toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt(0));
  
  return String.fromCodePoint(...codePoints);
}

export function FlagIcon({ countryCode, className = '' }) {
  const flag = getCountryFlag(countryCode);
  if (!flag) return null;
  
  return <span className={className} title={countryCode}>{flag}</span>;
}


