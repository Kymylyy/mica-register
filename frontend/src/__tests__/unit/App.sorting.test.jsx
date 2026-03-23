/** @vitest-environment jsdom */

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
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

vi.mock('../../components/Filters', () => ({
  Filters: () => <div data-testid="filters" />,
}));

vi.mock('../../components/DataTable', () => ({
  DataTable: ({ onSortingChange, sorting }) => (
    <div>
      <button type="button" onClick={() => onSortingChange([{ id: 'last_update', desc: false }])}>
        Sort Last Update Asc
      </button>
      <button type="button" onClick={() => onSortingChange([])}>
        Clear Sort
      </button>
      <div data-testid="sorting-state">{JSON.stringify(sorting)}</div>
    </div>
  ),
}));

import App from '../../App';

function renderApp(path = '/other') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/other" element={<App registerType="other" />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('App sorting integration', () => {
  beforeEach(() => {
    mockGet.mockReset();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('sends sort params to the API and resets pagination to page 1', async () => {
    mockGet.mockImplementation((url) => {
      if (url.startsWith('/api/entities?')) {
        return Promise.resolve({
          data: {
            items: [
              {
                id: 1,
                register_type: 'other',
                lei_name: 'Circle Internet Financial',
                home_member_state: 'FR',
                lei_cou_code: 'FR',
                last_update: '2025-01-01',
              },
            ],
            total: 150,
            skip: 0,
            limit: 100,
            has_more: true,
          },
        });
      }

      if (url === '/api/metadata/last-updated') {
        return Promise.resolve({ data: { register_type: 'other', last_updated: '2026-02-01' } });
      }

      return Promise.reject(new Error(`Unhandled URL in test: ${url}`));
    });

    renderApp();

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/api/entities?register_type=other&limit=100&skip=0', {
        signal: expect.any(AbortSignal),
      });
    });

    fireEvent.click(screen.getByRole('button', { name: 'Next' }));

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/api/entities?register_type=other&limit=100&skip=100', {
        signal: expect.any(AbortSignal),
      });
    });

    fireEvent.click(screen.getByRole('button', { name: 'Sort Last Update Asc' }));

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith(
        '/api/entities?register_type=other&limit=100&skip=0&sort_by=last_update&sort_dir=asc',
        { signal: expect.any(AbortSignal) }
      );
    });
  });

  it('removes sort params when sorting is cleared', async () => {
    mockGet.mockImplementation((url) => {
      if (url.startsWith('/api/entities?')) {
        return Promise.resolve({
          data: {
            items: [
              {
                id: 1,
                register_type: 'other',
                lei_name: 'Circle Internet Financial',
                home_member_state: 'FR',
                lei_cou_code: 'FR',
                last_update: '2025-01-01',
              },
            ],
            total: 1,
            skip: 0,
            limit: 100,
            has_more: false,
          },
        });
      }

      if (url === '/api/metadata/last-updated') {
        return Promise.resolve({ data: { register_type: 'other', last_updated: '2026-02-01' } });
      }

      return Promise.reject(new Error(`Unhandled URL in test: ${url}`));
    });

    renderApp();

    await waitFor(() => {
      expect(screen.getByTestId('sorting-state').textContent).toBe('[]');
    });

    fireEvent.click(screen.getByRole('button', { name: 'Sort Last Update Asc' }));

    await waitFor(() => {
      expect(screen.getByTestId('sorting-state').textContent).toContain('"last_update"');
    });

    fireEvent.click(screen.getByRole('button', { name: 'Clear Sort' }));

    await waitFor(() => {
      expect(screen.getByTestId('sorting-state').textContent).toBe('[]');
    });

    const entityCalls = mockGet.mock.calls
      .filter(([url]) => typeof url === 'string' && url.startsWith('/api/entities?'))
      .map(([url]) => url);

    expect(entityCalls.at(-1)).toBe('/api/entities?register_type=other&limit=100&skip=0');
  });
});
