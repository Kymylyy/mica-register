import { describe, test, expect } from 'vitest';
import { getPrimaryCountryCode } from '../../../utils/countryNames';

describe('getPrimaryCountryCode', () => {
  test('prefers home member state when available', () => {
    expect(getPrimaryCountryCode('AT', 'DE')).toBe('AT');
  });

  test('falls back to LEI country code when home member state is missing', () => {
    expect(getPrimaryCountryCode('', 'AT')).toBe('AT');
  });

  test('normalizes whitespace and lowercase input', () => {
    expect(getPrimaryCountryCode('  ', ' at ')).toBe('AT');
  });

  test('returns null when both values are empty', () => {
    expect(getPrimaryCountryCode(null, '')).toBeNull();
  });
});
