/**
 * Mock data fixtures for testing
 *
 * These represent API responses with all fields populated
 */

export const mockCaspEntity = {
  id: 1,
  register_type: 'casp',
  competent_authority: 'BaFin',
  lei: '5299001HFNLCLQMF3X50',
  commercial_name: 'Binance Europe Services Ltd.',
  home_member_state: 'DE',
  authorisation_date: '2025-01-15',
  authorisation_end_date: null,
  services: [
    { code: 'a', description: 'Providing custody and administration of crypto-assets on behalf of clients' },
    { code: 'e', description: 'Placing of crypto-assets' }
  ],
  passport_countries: [
    { country_code: 'BE' },
    { country_code: 'FR' },
    { country_code: 'NL' }
  ],
  passporting: true,
  website_platform: 'https://www.binance.com',
  lei_name: 'Binance Europe Services Limited',
  lei_cou_code: 'DE',
  address: null,
  website: null,
  comments: null,
  last_update: '2025-01-15',
  authorisation_notification_date: '2025-01-15'
};

export const mockOtherEntity = {
  id: 2,
  register_type: 'other',
  competent_authority: 'BaFin',
  lei_name: 'Tether Operations Limited',
  lei: null,
  home_member_state: 'DE',
  lei_casp: '5299001HFNLCLQMF3X50',
  lei_name_casp: 'Binance Europe Services Ltd.',
  offer_countries: 'DE|FR|IT',
  white_paper_url: 'https://tether.to/whitepaper.pdf',
  dti_ffg: true,
  dti_codes: 'DTI-001|DTI-002',
  white_paper_comments: 'Approved with conditions',
  white_paper_last_update: '2025-01-15',
  lei_cou_code: null
};

export const mockArtEntity = {
  id: 3,
  register_type: 'art',
  competent_authority: 'BaFin',
  lei: '5299001HFNLCLQMF3X50',
  commercial_name: 'Binance EUR Stablecoin',
  home_member_state: 'DE',
  authorisation_date: '2025-01-15',
  credit_institution: true,
  white_paper_url: 'https://binance.com/eur-whitepaper.pdf',
  white_paper_offer_countries: 'DE|FR|IT|NL',
  authorisation_end_date: null,
  white_paper_comments: 'Approved for EU-wide distribution',
  lei_name: 'Binance EUR Stablecoin Ltd',
  lei_cou_code: 'DE',
  address: null,
  website: null,
  authorisation_notification_date: '2025-01-15',
  white_paper_notification_date: null,
  white_paper_last_update: '2025-01-15'
};

export const mockEmtEntity = {
  id: 4,
  register_type: 'emt',
  competent_authority: 'BaFin',
  lei: '5299001HFNLCLQMF3X50',
  commercial_name: 'German E-Money Token',
  home_member_state: 'DE',
  authorisation_date: '2025-01-15',
  exemption_48_4: true,
  exemption_48_5: false,
  authorisation_other_emt: 'Credit institution under CRD',
  white_paper_notification_date: '2024-12-15',
  white_paper_url: 'https://de-emoney.de/wp.pdf',
  dti_ffg: true,
  dti_codes: 'EMT-001|EMT-002',
  authorisation_end_date: null,
  white_paper_comments: 'Full compliance verified',
  lei_name: 'German E-Money Token GmbH',
  lei_cou_code: 'DE',
  address: null,
  website: null,
  authorisation_notification_date: '2025-01-15',
  white_paper_last_update: '2025-01-15'
};

export const mockNcaspEntity = {
  id: 5,
  register_type: 'ncasp',
  competent_authority: 'BaFin',
  commercial_name: 'Crypto Scam Platform GmbH',
  home_member_state: 'DE',
  lei: null,
  lei_name: null,
  websites: 'https://scam-crypto.de|https://scam-crypto.com',
  infringement: true,
  reason: 'Unauthorized crypto-asset services provision',
  decision_date: '2025-01-15',
  lei_cou_code: null,
  comments: null,
  last_update: '2025-01-15'
};

/**
 * Generate mock API response for entity list
 */
export function createMockApiResponse(entities, total = null) {
  return {
    items: entities,
    total: total !== null ? total : entities.length,
    limit: 1000,
    offset: 0
  };
}

/**
 * Mock entities by register type
 */
export const mockEntitiesByRegister = {
  casp: [mockCaspEntity],
  other: [mockOtherEntity],
  art: [mockArtEntity],
  emt: [mockEmtEntity],
  ncasp: [mockNcaspEntity]
};

/**
 * Get mock entities for a specific register type
 */
export function getMockEntities(registerType) {
  return mockEntitiesByRegister[registerType] || [];
}
