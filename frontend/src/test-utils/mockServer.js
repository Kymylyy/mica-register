/**
 * Mock Service Worker (MSW) setup for API mocking
 */

import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { beforeAll, afterEach, afterAll } from 'vitest';
import { createMockApiResponse, getMockEntities } from './fixtures';

const API_BASE = 'http://localhost:8000';

/**
 * MSW handlers for API endpoints
 */
export const handlers = [
  // GET /api/entities - List entities with optional filtering
  http.get(`${API_BASE}/api/entities`, ({ request }) => {
    const url = new URL(request.url);
    const registerType = url.searchParams.get('register_type');
    const limit = parseInt(url.searchParams.get('limit') || '1000', 10);

    if (registerType) {
      const entities = getMockEntities(registerType);
      return HttpResponse.json(createMockApiResponse(entities.slice(0, limit)));
    }

    // Return empty list if no register type specified
    return HttpResponse.json(createMockApiResponse([]));
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
