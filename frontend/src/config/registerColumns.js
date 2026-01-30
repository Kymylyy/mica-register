/**
 * Column configuration for each register type
 * Defines which columns to display in the data table per register
 */

/**
 * Common columns present in all registers
 */
const COMMON_COLUMNS = [
  {
    id: 'commercial_name',
    label: 'Commercial Name',
    description: 'Trading name or brand name',
    visible: true,
  },
  {
    id: 'lei_name',
    label: 'LEI Name',
    description: 'Legal Entity Identifier name',
    visible: false,
    size: 250,
  },
  {
    id: 'lei',
    label: 'LEI',
    description: 'Legal Entity Identifier code',
    visible: false,
  },
  {
    id: 'home_member_state',
    label: 'Country',
    description: 'Home member state',
    visible: true,
  },
  {
    id: 'competent_authority',
    label: 'Authority',
    description: 'Competent authority',
    visible: false,
  },
  {
    id: 'authorisation_notification_date',
    label: 'Auth. Date',
    description: 'Authorization/notification date',
    visible: true,
  },
  {
    id: 'address',
    label: 'Address',
    description: 'Registered address',
    visible: false,
    size: 300,
  },
  {
    id: 'website',
    label: 'Website',
    description: 'Company website',
    visible: false,
    size: 250,
  },
  {
    id: 'comments',
    label: 'Comments',
    description: 'Additional comments',
    visible: false,
    size: 320,
  },
  {
    id: 'last_update',
    label: 'Last Update',
    description: 'Last update date',
    visible: false,
    size: 120,
  },
];

/**
 * CASP-specific columns
 */
const CASP_SPECIFIC_COLUMNS = [
  {
    id: 'services',
    label: 'Services',
    description: 'Crypto-asset services provided (a-j)',
    visible: true,
    size: 500,
  },
  {
    id: 'passport_countries',
    label: 'Passport',
    description: 'Passport countries',
    visible: false,
    size: 400,
  },
  {
    id: 'authorisation_end_date',
    label: 'End Date',
    description: 'Authorization end date',
    visible: false,
  },
];

/**
 * OTHER-specific columns (White Papers)
 */
const OTHER_SPECIFIC_COLUMNS = [
  {
    id: 'white_paper_url',
    label: 'White Paper',
    description: 'White paper URL',
    visible: true,
    size: 300,
  },
  {
    id: 'lei_casp',
    label: 'Linked CASP',
    description: 'LEI of linked CASP',
    visible: false,  // Hide LEI code, show readable name instead
  },
  {
    id: 'lei_name_casp',
    label: 'Linked CASP Name',
    description: 'Name of linked CASP',
    visible: false,  // Hidden by default
  },
  {
    id: 'offer_countries',
    label: 'Offer Countries',
    description: 'Countries where crypto-asset is offered',
    visible: false,
  },
  {
    id: 'dti_ffg',
    label: 'DTI FFG',
    description: 'Digital token identifier - First-in-First-out Group',
    visible: false,
  },
  {
    id: 'dti_codes',
    label: 'DTI Codes',
    description: 'Digital token identifier codes',
    visible: false,
  },
  {
    id: 'white_paper_comments',
    label: 'WP Comments',
    description: 'White paper comments',
    visible: false,
    size: 280,
  },
];

/**
 * ART-specific columns (Asset-Referenced Tokens)
 */
const ART_SPECIFIC_COLUMNS = [
  {
    id: 'credit_institution',
    label: 'Credit Institution',
    description: 'Whether issuer is a credit institution',
    visible: true,
  },
  {
    id: 'white_paper_url',
    label: 'White Paper',
    description: 'White paper URL',
    visible: true,
    size: 250,
  },
  {
    id: 'white_paper_offer_countries',
    label: 'Offer Countries',
    description: 'White paper offer countries',
    visible: false,
  },
  {
    id: 'authorisation_end_date',
    label: 'End Date',
    description: 'Authorization end date',
    visible: false,
  },
  {
    id: 'white_paper_comments',
    label: 'WP Comments',
    description: 'White paper comments',
    visible: false,
    size: 280,
  },
];

/**
 * EMT-specific columns (E-Money Tokens)
 */
const EMT_SPECIFIC_COLUMNS = [
  {
    id: 'authorisation_other_emt',
    label: 'Institution Type',
    description: 'Type of authorisation (credit institution, etc.)',
    visible: true,
  },
  {
    id: 'white_paper_notification_date',
    label: 'WP #1',
    description: 'White paper authorization/notification date',
    visible: true,  // Visible by default
    size: 130,
  },
  {
    id: 'white_paper_url',
    label: 'WP #2',
    description: 'White paper URL',
    visible: true,  // Changed from false
    size: 250,
  },
  {
    id: 'dti_ffg',
    label: 'DTI FFG',
    description: 'Digital token identifier - First-in-First-out Group',
    visible: false,
  },
  {
    id: 'dti_codes',
    label: 'DTI Codes',
    description: 'Digital token identifier codes',
    visible: false,
  },
  {
    id: 'authorisation_end_date',
    label: 'End Date',
    description: 'Authorization end date',
    visible: false,
  },
  {
    id: 'white_paper_comments',
    label: 'WP #3',
    description: 'White paper comments',
    visible: false,
    size: 280,
  },
];

/**
 * NCASP-specific columns (Non-Compliant Entities)
 */
const NCASP_SPECIFIC_COLUMNS = [
  {
    id: 'infringement',
    label: 'Infringement',
    description: 'Type of infringement',
    visible: true,
  },
  {
    id: 'reason',
    label: 'Reason',
    description: 'Reason for non-compliance',
    visible: false,  // Keep hidden (detailed, long text)
  },
  {
    id: 'decision_date',
    label: 'Decision Date',
    description: 'Date of decision',
    visible: true,
  },
  {
    id: 'websites',
    label: 'Websites',
    description: 'Multiple websites',
    visible: true,
  },
];

/**
 * Get column configuration for a specific register type
 * Handles register-specific column filtering
 * @param {string} registerType - Register type (casp, other, art, emt, ncasp)
 * @returns {Array} Array of column configurations
 */
export function getRegisterColumns(registerType) {
  const baseColumns = [...COMMON_COLUMNS];

  switch (registerType.toLowerCase()) {
    case 'casp':
      return [...baseColumns, ...CASP_SPECIFIC_COLUMNS];

    case 'other':
      // OTHER doesn't have commercial_name in CSV, so filter it out
      // Custom column order: WHITE PAPER / LEI NAME / COUNTRY / LAST UPDATE
      const otherCommon = baseColumns
        .filter(col => col.id !== 'commercial_name')
        .map(col => {
          if (col.id === 'lei_name') return {...col, visible: true};
          if (col.id === 'last_update') return {...col, visible: true};
          if (col.id === 'authorisation_notification_date') return {...col, visible: false};
          return col;
        });

      // Build columns in specific order: white_paper_url, lei_name, home_member_state, last_update, then rest
      const orderedColumns = [];

      // 1. White Paper (from OTHER_SPECIFIC_COLUMNS)
      const whitePaperCol = OTHER_SPECIFIC_COLUMNS.find(col => col.id === 'white_paper_url');
      if (whitePaperCol) orderedColumns.push(whitePaperCol);

      // 2. LEI Name (from otherCommon) - shorter for OTHER register
      const leiNameCol = otherCommon.find(col => col.id === 'lei_name');
      if (leiNameCol) orderedColumns.push({...leiNameCol, size: 300});

      // 3. Country (from otherCommon)
      const countryCol = otherCommon.find(col => col.id === 'home_member_state');
      if (countryCol) orderedColumns.push(countryCol);

      // 4. Last Update (from otherCommon)
      const lastUpdateCol = otherCommon.find(col => col.id === 'last_update');
      if (lastUpdateCol) orderedColumns.push(lastUpdateCol);

      // 5. Add remaining columns (not already added)
      const usedIds = new Set(['white_paper_url', 'lei_name', 'home_member_state', 'last_update']);
      otherCommon.forEach(col => {
        if (!usedIds.has(col.id)) orderedColumns.push(col);
      });
      OTHER_SPECIFIC_COLUMNS.forEach(col => {
        if (!usedIds.has(col.id)) orderedColumns.push(col);
      });

      return orderedColumns;

    case 'art':
      return [...baseColumns, ...ART_SPECIFIC_COLUMNS];

    case 'emt':
      // CRITICAL: Hide entity auth date, otherwise it remains visible from COMMON_COLUMNS
      // Also change "Commercial Name" to "Issuer" for EMT
      const emtCommon = baseColumns.map(col => {
        if (col.id === 'authorisation_notification_date') {
          return {...col, visible: false};  // Hide entity auth date (ac_authorisationNotificationDate)
        }
        if (col.id === 'commercial_name') {
          return {...col, label: 'Issuer'};  // Change label to "Issuer" for EMT
        }
        return col;
      });
      return [...emtCommon, ...EMT_SPECIFIC_COLUMNS];

    case 'ncasp':
      return [...baseColumns, ...NCASP_SPECIFIC_COLUMNS];

    default:
      console.warn(`Unknown register type: ${registerType}, defaulting to CASP`);
      return [...baseColumns, ...CASP_SPECIFIC_COLUMNS];
  }
}

/**
 * Get default column visibility for a register type
 * @param {string} registerType - Register type
 * @returns {Object} Object with column_id: boolean
 */
export function getDefaultColumnVisibility(registerType) {
  const columns = getRegisterColumns(registerType);
  return columns.reduce((acc, col) => {
    acc[col.id] = col.visible;
    return acc;
  }, {});
}

/**
 * Get register display name
 * @param {string} registerType - Register type
 * @returns {string} Display name
 */
export function getRegisterDisplayName(registerType) {
  const names = {
    casp: 'Crypto-Asset Service Providers',
    other: 'White Papers (Other Crypto-Assets)',
    art: 'Asset-Referenced Tokens',
    emt: 'E-Money Tokens',
    ncasp: 'Non-Compliant Entities',
  };

  return names[registerType.toLowerCase()] || registerType;
}

/**
 * Get register short name
 * @param {string} registerType - Register type
 * @returns {string} Short name
 */
export function getRegisterShortName(registerType) {
  const names = {
    casp: 'CASPs',
    other: 'White Papers',
    art: 'ART',
    emt: 'EMT',
    ncasp: 'Non-Compliant',
  };

  return names[registerType.toLowerCase()] || registerType.toUpperCase();
}

/**
 * Get register-specific label for the counter display
 * @param {string} registerType - Register type (casp, other, art, emt, ncasp)
 * @returns {string} Counter label (e.g., "Whitepapers", "Entities")
 */
export function getRegisterCounterLabel(registerType) {
  const labels = {
    casp: 'Entities',       // CASPs are entities
    other: 'WHITE PAPERS',   // OTHER register = whitepapers
    art: 'Whitepapers',     // ART register = whitepapers for asset-referenced tokens
    emt: 'Whitepapers',     // EMT register = whitepapers for e-money tokens
    ncasp: 'Entities',      // Non-compliant entities
  };
  return labels[registerType?.toLowerCase()] || 'Entities';
}

export default {
  getRegisterColumns,
  getRegisterDisplayName,
  getRegisterShortName,
  getRegisterCounterLabel,
};
