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

const TEST_COMPANY = {
  id: 123,
  slug: 'test-casp-entity',
  register_type: 'casp',
  commercial_name: 'Test CASP Entity',
  lei_name: 'Test CASP Entity',
  lei: '529900032TYR45XIEW79',
  services: [],
  passport_countries: [],
  record_count: 1,
  authorisation_records: [
    {
      entity_id: 123,
      authorisation_notification_date: '2025-11-21',
      services: [],
      passport_countries: [],
    },
  ],
};

function mockCommonEndpoints(url) {
  if (url.startsWith('/api/casp/companies?')) {
    return Promise.resolve({ data: { items: [], total: 0 } });
  }
  if (url === '/api/metadata/last-updated') {
    return Promise.resolve({ data: { register_type: 'casp', last_updated: '2026-02-01' } });
  }
  return null;
}

function renderApp(path) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/casp" element={<App registerType="casp" />} />
        <Route path="/casp/:entityId" element={<App registerType="casp" />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('App slug routing', () => {
  beforeEach(() => {
    mockGet.mockReset();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('loads entity details from a slug deep-link', async () => {
    mockGet.mockImplementation((url) => {
      if (url === '/api/casp/companies/by-slug/test-casp-entity') {
        return Promise.resolve({ data: TEST_COMPANY });
      }
      return mockCommonEndpoints(url) ?? Promise.reject(new Error(`Unhandled URL in test: ${url}`));
    });

    renderApp('/casp/test-casp-entity');

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/api/casp/companies/by-slug/test-casp-entity');
    });

    expect(screen.getByRole('heading', { level: 2, name: 'Test CASP Entity' })).toBeTruthy();
  });

  it('redirects a legacy numeric deep-link to the slug URL', async () => {
    mockGet.mockImplementation((url) => {
      if (url === '/api/casp/companies/123') {
        return Promise.resolve({ data: TEST_COMPANY });
      }
      if (url === '/api/casp/companies/by-slug/test-casp-entity') {
        return Promise.resolve({ data: TEST_COMPANY });
      }
      return mockCommonEndpoints(url) ?? Promise.reject(new Error(`Unhandled URL in test: ${url}`));
    });

    renderApp('/casp/123');

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/api/casp/companies/123');
    });

    // After the redirect the route param becomes the slug and the app refetches by slug
    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/api/casp/companies/by-slug/test-casp-entity');
    });

    expect(screen.getByRole('heading', { level: 2, name: 'Test CASP Entity' })).toBeTruthy();
  });

  it('loads non-CASP entity details by slug with register_type hint', async () => {
    mockGet.mockImplementation((url) => {
      if (url === '/api/entities/by-slug/scam-co?register_type=ncasp') {
        return Promise.resolve({
          data: {
            id: 7,
            slug: 'scam-co',
            register_type: 'ncasp',
            lei_name: 'Scam Co',
            services: [],
            passport_countries: [],
          },
        });
      }
      if (url.startsWith('/api/entities?')) {
        return Promise.resolve({ data: { items: [], total: 0 } });
      }
      if (url === '/api/metadata/last-updated') {
        return Promise.resolve({ data: { register_type: 'ncasp', last_updated: '2026-02-01' } });
      }
      return Promise.reject(new Error(`Unhandled URL in test: ${url}`));
    });

    render(
      <MemoryRouter initialEntries={['/ncasp/scam-co']}>
        <Routes>
          <Route path="/ncasp" element={<App registerType="ncasp" />} />
          <Route path="/ncasp/:entityId" element={<App registerType="ncasp" />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/api/entities/by-slug/scam-co?register_type=ncasp');
    });

    expect(screen.getByRole('heading', { level: 2, name: 'Scam Co' })).toBeTruthy();
  });
});
