/**
 * Mock Service Worker (MSW) setup for API mocking
 */

import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { beforeAll, afterEach, afterAll } from 'vitest';
import { createMockApiResponse, getMockEntities } from './fixtures';

const API_BASE = 'http://localhost:8000';

function normalizeSortValue(value) {
  if (value === null || value === undefined || value === '') {
    return { isMissing: true, value: '' };
  }

  if (Array.isArray(value)) {
    return {
      isMissing: false,
      value: value
        .map(item => normalizeSortValue(item).value)
        .join('|')
        .toLowerCase(),
    };
  }

  if (typeof value === 'object') {
    const preferredKeys = [
      'code',
      'country_code',
      'tag_name',
      'tag_value',
      'commercial_name',
      'lei_name',
      'website',
      'reason',
      'infringement',
      'authorisation_notification_date',
      'white_paper_notification_date',
      'authorisation_end_date',
      'decision_date',
      'last_update',
      'value',
    ];

    for (const key of preferredKeys) {
      if (value[key] !== undefined && value[key] !== null && value[key] !== '') {
        return normalizeSortValue(value[key]);
      }
    }

    return {
      isMissing: false,
      value: Object.values(value)
        .map(item => normalizeSortValue(item).value)
        .join('|')
        .toLowerCase(),
    };
  }

  if (typeof value === 'boolean') {
    return { isMissing: false, value: value ? 1 : 0 };
  }

  return { isMissing: false, value: String(value).toLowerCase() };
}

function sortMockEntities(entities, sortBy, sortDir = 'asc') {
  if (!sortBy) return [...entities];

  const direction = sortDir === 'desc' ? -1 : 1;

  return [...entities].sort((left, right) => {
    const leftValue = normalizeSortValue(left?.[sortBy]);
    const rightValue = normalizeSortValue(right?.[sortBy]);

    if (leftValue.isMissing && rightValue.isMissing) {
      return (left.id ?? 0) - (right.id ?? 0);
    }

    if (leftValue.isMissing) return 1;
    if (rightValue.isMissing) return -1;

    if (leftValue.value < rightValue.value) return -1 * direction;
    if (leftValue.value > rightValue.value) return 1 * direction;

    return (left.id ?? 0) - (right.id ?? 0);
  });
}

function paginateMockEntities(entities, skip, limit) {
  const start = Number.isFinite(skip) ? skip : 0;
  const end = Number.isFinite(limit) ? start + limit : undefined;
  return entities.slice(start, end);
}

/**
 * MSW handlers for API endpoints
 */
export const handlers = [
  // GET /api/entities - List entities with optional filtering
  http.get(`${API_BASE}/api/entities`, ({ request }) => {
    const url = new URL(request.url);
    const registerType = url.searchParams.get('register_type');
    const limit = parseInt(url.searchParams.get('limit') || '1000', 10);
    const skip = parseInt(url.searchParams.get('skip') || '0', 10);
    const sortBy = url.searchParams.get('sort_by');
    const sortDir = url.searchParams.get('sort_dir') || 'asc';

    if (registerType) {
      const entities = sortMockEntities(getMockEntities(registerType), sortBy, sortDir);
      const paginatedEntities = paginateMockEntities(entities, skip, limit);
      return HttpResponse.json(
        createMockApiResponse(paginatedEntities, entities.length, limit, skip)
      );
    }

    // Return empty list if no register type specified
    return HttpResponse.json(createMockApiResponse([]));
  }),

  // GET /api/casp/companies - CASP grouped list
  http.get(`${API_BASE}/api/casp/companies`, ({ request }) => {
    const url = new URL(request.url);
    const limit = parseInt(url.searchParams.get('limit') || '1000', 10);
    const skip = parseInt(url.searchParams.get('skip') || '0', 10);
    const sortBy = url.searchParams.get('sort_by');
    const sortDir = url.searchParams.get('sort_dir') || 'asc';

    const companies = sortMockEntities(getMockEntities('casp'), sortBy, sortDir);
    const paginatedCompanies = paginateMockEntities(companies, skip, limit);

    return HttpResponse.json(
      createMockApiResponse(paginatedCompanies, companies.length, limit, skip)
    );
  }),

  // GET /api/entities/:id - Get single entity
  http.get(`${API_BASE}/api/entities/:id`, ({ params }) => {
    const { id } = params;
    // For testing, just return CASP entity
    const entities = getMockEntities('casp');
    const entity = entities.find(e => e.id === parseInt(id, 10));

    if (entity) {
      return HttpResponse.json(entity);
    }

    return new HttpResponse(null, { status: 404 });
  }),

  // GET /api/casp/companies/:id - Get grouped CASP company
  http.get(`${API_BASE}/api/casp/companies/:id`, ({ params }) => {
    const { id } = params;
    const entities = getMockEntities('casp');
    const entity = entities.find(e => e.id === parseInt(id, 10));

    if (entity) {
      return HttpResponse.json(entity);
    }

    return new HttpResponse(null, { status: 404 });
  }),
];

/**
 * Setup MSW server
 */
export const server = setupServer(...handlers);

/**
 * Start server before tests
 */
export function setupMockServer() {
  beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());
}
