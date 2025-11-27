/**
 * MiCA standard service codes with full descriptions
 * Maps service codes (a-j) to their full descriptions
 */
export const micaServiceDescriptions = {
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
};

/**
 * Short, user-friendly service names for display in tables
 */
export const micaServiceShortNames = {
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
};

/**
 * Medium-length service names for modal display
 * More descriptive than short names, less formal than full MiCA descriptions
 */
export const micaServiceMediumNames = {
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
};

/**
 * Get full service description from code
 * @param {string} code - Service code (a-j)
 * @returns {string} Full service description or code if not found
 */
export function getServiceDescription(code) {
  return micaServiceDescriptions[code] || code;
}

/**
 * Get short service name from code (for table display)
 * @param {string} code - Service code (a-j)
 * @returns {string} Short service name or full description if not found
 */
export function getServiceShortName(code) {
  return micaServiceShortNames[code] || getServiceDescription(code);
}

/**
 * Get medium-length service name from code (for modal display)
 * @param {string} code - Service code (a-j)
 * @returns {string} Medium service name or short name if not found
 */
export function getServiceMediumName(code) {
  return micaServiceMediumNames[code] || getServiceShortName(code);
}

/**
 * Get full service description with capitalized first letter (for modal and filters)
 * @param {string} code - Service code (a-j)
 * @returns {string} Full service description with first letter capitalized
 */
export function getServiceDescriptionCapitalized(code) {
  const description = getServiceDescription(code);
  if (!description) return code;
  return description.charAt(0).toUpperCase() + description.slice(1);
}

/**
 * Get service code order for sorting (a=0, b=1, ..., j=9)
 * @param {string} code - Service code (a-j)
 * @returns {number} Order index or 999 if not found
 */
export function getServiceCodeOrder(code) {
  const order = { 'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7, 'i': 8, 'j': 9 };
  return order[code] !== undefined ? order[code] : 999;
}

