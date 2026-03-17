/** @vitest-environment jsdom */

import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

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

function renderApp(path = '/casp') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/casp" element={<App registerType="casp" />} />
        <Route path="/casp/:entityId" element={<App registerType="casp" />} />
      </Routes>
    </MemoryRouter>
  );
}

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
      if (url.startsWith('/api/casp/companies?')) {
        return Promise.resolve({ data: { items: [], total: 0 } });
      }
      if (url === '/api/metadata/last-updated') {
        return Promise.resolve({ data: { register_type: 'casp', last_updated: '2026-02-01' } });
      }
      return Promise.reject(new Error(`Unhandled URL in test: ${url}`));
    });

    renderApp();

    await waitFor(() => {
      expect(screen.getByText(/Last updated: 1 February 2026/i)).toBeTruthy();
    });
  });

  it('falls back to N/A when metadata is unavailable', async () => {
    mockGet.mockImplementation((url) => {
      if (url.startsWith('/api/casp/companies?')) {
        return Promise.resolve({ data: { items: [], total: 0 } });
      }
      if (url === '/api/metadata/last-updated') {
        return Promise.reject(new Error('metadata unavailable'));
      }
      return Promise.reject(new Error(`Unhandled URL in test: ${url}`));
    });

    renderApp();

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/api/metadata/last-updated', {
        params: { register_type: 'casp' },
      });
    });

    expect(screen.getByText(/Last updated: N\/A/i)).toBeTruthy();
  });

  it('loads entity details when opening deep-link route', async () => {
    mockGet.mockImplementation((url) => {
      if (url.startsWith('/api/casp/companies?')) {
        return Promise.resolve({ data: { items: [], total: 0 } });
      }
      if (url === '/api/casp/companies/123') {
        return Promise.resolve({
          data: {
            id: 123,
            register_type: 'casp',
            commercial_name: 'Test CASP Entity',
            lei_name: 'Test CASP Entity',
            lei: '529900032TYR45XIEW79',
            services: [],
            passport_countries: [],
            record_count: 2,
            authorisation_records: [
              {
                entity_id: 123,
                authorisation_notification_date: '2025-11-21',
                services: [],
                passport_countries: [],
              },
              {
                entity_id: 45,
                authorisation_notification_date: '2025-04-01',
                services: [],
                passport_countries: [],
              },
            ],
          },
        });
      }
      if (url === '/api/metadata/last-updated') {
        return Promise.resolve({ data: { register_type: 'casp', last_updated: '2026-02-01' } });
      }
      return Promise.reject(new Error(`Unhandled URL in test: ${url}`));
    });

    renderApp('/casp/123');

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/api/casp/companies/123');
    });

    expect(screen.getByRole('heading', { level: 2, name: 'Test CASP Entity' })).toBeTruthy();
    expect(screen.getByText(/2 authorisation records/i)).toBeTruthy();
  });

  it('renders grouped CASP companies in the list', async () => {
    mockGet.mockImplementation((url) => {
      if (url.startsWith('/api/casp/companies?')) {
        return Promise.resolve({
          data: {
            items: [
              {
                id: 123,
                register_type: 'casp',
                commercial_name: 'EUWAX AG',
                lei_name: 'EUWAX AG',
                lei: '529900032TYR45XIEW79',
                home_member_state: 'DE',
                lei_cou_code: 'DE',
                authorisation_notification_date: '2025-11-21',
                services: [{ code: 'e', description: 'Execution of orders' }],
                passport_countries: [{ id: 1, country_code: 'DE' }],
                record_count: 2,
              },
            ],
            total: 1,
          },
        });
      }
      if (url === '/api/metadata/last-updated') {
        return Promise.resolve({ data: { register_type: 'casp', last_updated: '2026-02-01' } });
      }
      return Promise.reject(new Error(`Unhandled URL in test: ${url}`));
    });

    renderApp('/casp');

    await waitFor(() => {
      expect(screen.getAllByText('EUWAX AG').length).toBeGreaterThan(0);
    });

    expect(screen.queryByText(/2 records/i)).toBeNull();
    expect(
      screen.getAllByText((_, element) => element?.textContent?.includes('1 Companies') ?? false).length
    ).toBeGreaterThan(0);
  });
});
