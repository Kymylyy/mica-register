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
    visible: true,
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
    visible: true,
  },
  {
    id: 'authorisation_notification_date',
    label: 'Auth. Date',
    description: 'Authorization/notification date',
    visible: true,
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
  },
  {
    id: 'passport_countries',
    label: 'Passport',
    description: 'Passport countries',
    visible: true,
  },
  {
    id: 'website',
    label: 'Website',
    description: 'Company website',
    visible: false, // Hidden by default
  },
  {
    id: 'authorisation_end_date',
    label: 'End Date',
    description: 'Authorization end date',
    visible: false, // Hidden by default
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
  },
  {
    id: 'lei_casp',
    label: 'Linked CASP',
    description: 'LEI of linked CASP',
    visible: true,
  },
  {
    id: 'offer_countries',
    label: 'Offer Countries',
    description: 'Countries where crypto-asset is offered',
    visible: true,
  },
  {
    id: 'dti_ffg',
    label: 'DTI FFG',
    description: 'Digital token identifier - First-in-First-out Group',
    visible: false, // Hidden by default
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
  },
  {
    id: 'white_paper_offer_countries',
    label: 'Offer Countries',
    description: 'White paper offer countries',
    visible: true,
  },
  {
    id: 'authorisation_end_date',
    label: 'End Date',
    description: 'Authorization end date',
    visible: false, // Hidden by default
  },
];

/**
 * EMT-specific columns (E-Money Tokens)
 */
const EMT_SPECIFIC_COLUMNS = [
  {
    id: 'exemption_48_4',
    label: 'Exemption 48.4',
    description: 'Exemption under Article 48(4)',
    visible: true,
  },
  {
    id: 'exemption_48_5',
    label: 'Exemption 48.5',
    description: 'Exemption under Article 48(5)',
    visible: true,
  },
  {
    id: 'dti_ffg',
    label: 'DTI FFG',
    description: 'Digital token identifier - First-in-First-out Group',
    visible: false, // Hidden by default
  },
  {
    id: 'white_paper_url',
    label: 'White Paper',
    description: 'White paper URL',
    visible: false, // Hidden by default
  },
  {
    id: 'authorisation_end_date',
    label: 'End Date',
    description: 'Authorization end date',
    visible: false, // Hidden by default
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
    visible: true,
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
 * @param {string} registerType - Register type (casp, other, art, emt, ncasp)
 * @returns {Array} Array of column configurations
 */
export function getRegisterColumns(registerType) {
  const baseColumns = [...COMMON_COLUMNS];

  switch (registerType.toLowerCase()) {
    case 'casp':
      return [...baseColumns, ...CASP_SPECIFIC_COLUMNS];

    case 'other':
      return [...baseColumns, ...OTHER_SPECIFIC_COLUMNS];

    case 'art':
      return [...baseColumns, ...ART_SPECIFIC_COLUMNS];

    case 'emt':
      return [...baseColumns, ...EMT_SPECIFIC_COLUMNS];

    case 'ncasp':
      return [...baseColumns, ...NCASP_SPECIFIC_COLUMNS];

    default:
      console.warn(`Unknown register type: ${registerType}, defaulting to CASP`);
      return [...baseColumns, ...CASP_SPECIFIC_COLUMNS];
  }
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

export default {
  getRegisterColumns,
  getRegisterDisplayName,
  getRegisterShortName,
};
