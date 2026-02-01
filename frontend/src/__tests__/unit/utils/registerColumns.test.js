/**
 * Unit tests for register column configuration
 *
 * Verifies that ALL fields from API are configured in registerColumns.js
 */

import { describe, test, expect } from 'vitest';
import { getRegisterColumns } from '../../../config/registerColumns';

describe('CASP Column Configuration', () => {
  test('all CASP fields are in registerColumns config', () => {
    const columns = getRegisterColumns('casp');
    const columnIds = columns.map(c => c.id);

    // Common fields
    expect(columnIds).toContain('commercial_name');
    expect(columnIds).toContain('lei');
    expect(columnIds).toContain('lei_name');
    expect(columnIds).toContain('home_member_state');
    expect(columnIds).toContain('competent_authority');
    expect(columnIds).toContain('authorisation_notification_date');

    // CASP-specific fields
    expect(columnIds).toContain('services');
    expect(columnIds).toContain('passport_countries');
    expect(columnIds).toContain('authorisation_end_date');
    // Note: website is in COMMON_COLUMNS, not CASP-specific
    expect(columnIds).toContain('website');
  });

  test('CASP columns have required properties', () => {
    const columns = getRegisterColumns('casp');

    columns.forEach(column => {
      expect(column).toHaveProperty('id');
      expect(column).toHaveProperty('label');
      expect(column).toHaveProperty('description');
      expect(column).toHaveProperty('visible');

      // Check types
      expect(typeof column.id).toBe('string');
      expect(typeof column.label).toBe('string');
      expect(typeof column.description).toBe('string');
      expect(typeof column.visible).toBe('boolean');
    });
  });

  test('CASP commercial_name is visible by default', () => {
    const columns = getRegisterColumns('casp');
    const commercialName = columns.find(c => c.id === 'commercial_name');

    expect(commercialName).toBeDefined();
    expect(commercialName.visible).toBe(true);
  });

  test('CASP lei is hidden by default', () => {
    const columns = getRegisterColumns('casp');
    const lei = columns.find(c => c.id === 'lei');

    expect(lei).toBeDefined();
    expect(lei.visible).toBe(false);
  });
});

describe('OTHER Column Configuration', () => {
  test('all OTHER fields are in registerColumns config', () => {
    const columns = getRegisterColumns('other');
    const columnIds = columns.map(c => c.id);

    // Common fields (note: OTHER doesn't have commercial_name)
    expect(columnIds).toContain('lei_name');
    expect(columnIds).toContain('home_member_state');
    expect(columnIds).toContain('competent_authority');

    // OTHER-specific fields
    expect(columnIds).toContain('lei_casp');
    expect(columnIds).toContain('lei_name_casp');
    expect(columnIds).toContain('offer_countries');
    expect(columnIds).toContain('white_paper_url');
    expect(columnIds).toContain('dti_ffg');
    expect(columnIds).toContain('dti_codes');
    expect(columnIds).toContain('white_paper_comments');
  });

  test('OTHER does not have commercial_name column', () => {
    const columns = getRegisterColumns('other');
    const columnIds = columns.map(c => c.id);

    expect(columnIds).not.toContain('commercial_name');
  });

  test('OTHER lei_name is visible by default', () => {
    const columns = getRegisterColumns('other');
    const leiName = columns.find(c => c.id === 'lei_name');

    expect(leiName).toBeDefined();
    expect(leiName.visible).toBe(true);
  });
});

describe('ART Column Configuration', () => {
  test('all ART fields are in registerColumns config', () => {
    const columns = getRegisterColumns('art');
    const columnIds = columns.map(c => c.id);

    // Common fields
    expect(columnIds).toContain('commercial_name');
    expect(columnIds).toContain('lei');
    expect(columnIds).toContain('home_member_state');
    expect(columnIds).toContain('competent_authority');
    expect(columnIds).toContain('authorisation_notification_date');

    // ART-specific fields
    expect(columnIds).toContain('credit_institution');
    expect(columnIds).toContain('white_paper_url');
    expect(columnIds).toContain('white_paper_offer_countries');
    expect(columnIds).toContain('authorisation_end_date');
    expect(columnIds).toContain('white_paper_comments');
  });

  test('ART credit_institution field exists', () => {
    const columns = getRegisterColumns('art');
    const creditInstitution = columns.find(c => c.id === 'credit_institution');

    expect(creditInstitution).toBeDefined();
    expect(creditInstitution.label).toBeTruthy();
  });
});

describe('EMT Column Configuration', () => {
  test('all EMT fields are in registerColumns config', () => {
    const columns = getRegisterColumns('emt');
    const columnIds = columns.map(c => c.id);

    // Common fields
    expect(columnIds).toContain('commercial_name');
    expect(columnIds).toContain('lei');
    expect(columnIds).toContain('home_member_state');
    expect(columnIds).toContain('competent_authority');
    expect(columnIds).toContain('authorisation_notification_date');

    // EMT-specific fields
    expect(columnIds).toContain('exemption_48_4');
    expect(columnIds).toContain('exemption_48_5');
    expect(columnIds).toContain('authorisation_other_emt');
    expect(columnIds).toContain('white_paper_notification_date');
    expect(columnIds).toContain('white_paper_url');
    expect(columnIds).toContain('dti_ffg');
    expect(columnIds).toContain('dti_codes');
    expect(columnIds).toContain('authorisation_end_date');
    expect(columnIds).toContain('white_paper_comments');
  });

  test('EMT exemption fields exist', () => {
    const columns = getRegisterColumns('emt');

    const exemption484 = columns.find(c => c.id === 'exemption_48_4');
    const exemption485 = columns.find(c => c.id === 'exemption_48_5');

    expect(exemption484).toBeDefined();
    expect(exemption485).toBeDefined();
  });
});

describe('NCASP Column Configuration', () => {
  test('all NCASP fields are in registerColumns config', () => {
    const columns = getRegisterColumns('ncasp');
    const columnIds = columns.map(c => c.id);

    // Common fields
    expect(columnIds).toContain('commercial_name');
    expect(columnIds).toContain('home_member_state');
    expect(columnIds).toContain('competent_authority');

    // NCASP-specific fields
    expect(columnIds).toContain('websites');
    expect(columnIds).toContain('infringement');
    expect(columnIds).toContain('reason');
    expect(columnIds).toContain('decision_date');
  });

  test('NCASP infringement field exists', () => {
    const columns = getRegisterColumns('ncasp');
    const infringement = columns.find(c => c.id === 'infringement');

    expect(infringement).toBeDefined();
    expect(infringement.label).toBeTruthy();
  });

  test('NCASP websites field exists for multiple URLs', () => {
    const columns = getRegisterColumns('ncasp');
    const websites = columns.find(c => c.id === 'websites');

    expect(websites).toBeDefined();
    expect(websites.label).toBeTruthy();
  });
});

describe('Column Configuration General', () => {
  test('getRegisterColumns defaults to CASP for invalid register type', () => {
    const columns = getRegisterColumns('invalid');
    const columnIds = columns.map(c => c.id);

    // Should default to CASP columns
    expect(columnIds).toContain('services');
    expect(columnIds).toContain('passport_countries');
  });

  test('all registers return non-empty column array', () => {
    const registers = ['casp', 'other', 'art', 'emt', 'ncasp'];

    registers.forEach(register => {
      const columns = getRegisterColumns(register);
      expect(Array.isArray(columns)).toBe(true);
      expect(columns.length).toBeGreaterThan(0);
    });
  });

  test('no duplicate column IDs within a register', () => {
    const registers = ['casp', 'other', 'art', 'emt', 'ncasp'];

    registers.forEach(register => {
      const columns = getRegisterColumns(register);
      const ids = columns.map(c => c.id);
      const uniqueIds = [...new Set(ids)];

      expect(ids.length).toBe(uniqueIds.length);
    });
  });
});
