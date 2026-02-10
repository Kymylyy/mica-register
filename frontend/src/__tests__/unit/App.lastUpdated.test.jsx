/** @vitest-environment jsdom */

import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const { mockGet } = vi.hoisted(() => ({
  mockGet: vi.fn(),
}));

vi.mock('@vercel/analytics/react', () => ({
  Analytics: () => null,
}));

vi.mock('../../utils/api', () => ({
  default: {
    get: mockGet,
  },
}));

vi.mock('../../components/RegisterSelector', () => ({
  RegisterSelector: () => <div data-testid="register-selector" />,
}));

import App from '../../App';

describe('App header last updated date', () => {
  beforeEach(() => {
    mockGet.mockReset();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders dynamic date from metadata endpoint', async () => {
    mockGet.mockImplementation((url) => {
      if (url.startsWith('/api/entities?')) {
        return Promise.resolve({ data: { items: [], total: 0 } });
      }
      if (url === '/api/metadata/last-updated') {
        return Promise.resolve({ data: { register_type: 'casp', last_updated: '2026-02-01' } });
      }
      return Promise.reject(new Error(`Unhandled URL in test: ${url}`));
    });

    render(<App registerType="casp" />);

    await waitFor(() => {
      expect(screen.getByText(/Last updated: 1 February 2026/i)).toBeTruthy();
    });
  });

  it('falls back to N/A when metadata is unavailable', async () => {
    mockGet.mockImplementation((url) => {
      if (url.startsWith('/api/entities?')) {
        return Promise.resolve({ data: { items: [], total: 0 } });
      }
      if (url === '/api/metadata/last-updated') {
        return Promise.reject(new Error('metadata unavailable'));
      }
      return Promise.reject(new Error(`Unhandled URL in test: ${url}`));
    });

    render(<App registerType="casp" />);

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/api/metadata/last-updated', {
        params: { register_type: 'casp' },
      });
    });

    expect(screen.getByText(/Last updated: N\/A/i)).toBeTruthy();
  });
});
