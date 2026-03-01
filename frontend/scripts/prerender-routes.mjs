import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const baseUrl = 'https://www.micaregister.com';
const defaultApiBaseUrl = 'https://mica-register-production.up.railway.app';
const configuredApiBaseUrl =
  process.env.PRERENDER_API_URL || process.env.VITE_API_URL || defaultApiBaseUrl;
const apiBaseUrl = configuredApiBaseUrl.replace(/\/+$/, '');
const apiDocsUrl = `${apiBaseUrl}/docs`;

const parsedBatchSize = Number.parseInt(process.env.PRERENDER_DETAIL_BATCH_SIZE || '500', 10);
const detailBatchSize = Number.isInteger(parsedBatchSize) && parsedBatchSize > 0
  ? parsedBatchSize
  : 500;
const parsedMinDetailPages = Number.parseInt(process.env.PRERENDER_MIN_DETAIL_PAGES || '1', 10);
const minDetailPages = Number.isInteger(parsedMinDetailPages) && parsedMinDetailPages >= 0
  ? parsedMinDetailPages
  : 1;
const detailFailureModeRaw = process.env.PRERENDER_DETAIL_FAILURE_MODE;
const detailFailureModeDefault = process.env.CI === 'true' || process.env.VERCEL === '1'
  ? 'error'
  : 'warn';
const detailFailureMode = (detailFailureModeRaw || detailFailureModeDefault).toLowerCase();
const allowedDetailFailureModes = new Set(['error', 'warn', 'off']);

if (!allowedDetailFailureModes.has(detailFailureMode)) {
  throw new Error(
    `Invalid PRERENDER_DETAIL_FAILURE_MODE: "${detailFailureModeRaw}". Allowed values: error, warn, off.`,
  );
}

const staticRoutes = [
  {
    path: '/',
    slug: '',
    registerType: null,
    label: null,
    title: 'MiCA Register | ESMA MiCA Registers in One Place',
    description:
      'Browse all ESMA MiCA registers in one searchable interface: CASP, OTHER, ART, EMT, and NCASP.',
    heading: 'MiCA Register',
    summary:
      'Public register explorer for ESMA MiCA data across CASP, OTHER, ART, EMT, and NCASP registers.',
    highlights: [
      'Search by entity name, LEI, country, and register-specific fields.',
      'Filter by services, authorization dates, and member states.',
      'Data source: ESMA MiCA register publications.',
    ],
  },
  {
    path: '/casp',
    slug: 'casp',
    registerType: 'casp',
    label: 'CASP',
    title: 'MiCA CASP Register | EU Crypto-Asset Service Providers',
    description:
      'Search the MiCA CASP register of EU crypto-asset service providers by LEI, country, services, and authorization date.',
    heading: 'MiCA CASP Register',
    summary:
      'Registry view for Crypto-Asset Service Providers (CASP) under MiCA, including passport countries and service scope.',
    highlights: [
      'Provider identity fields including LEI and legal name.',
      'Service codes and passport countries.',
      'Authorization and last update dates.',
    ],
  },
  {
    path: '/other',
    slug: 'other',
    registerType: 'other',
    label: 'OTHER',
    title: 'MiCA OTHER Register | White Papers for Other Crypto-Assets',
    description:
      'Browse MiCA OTHER white paper notifications, including linked CASP entities, DTI fields, and offer countries.',
    heading: 'MiCA OTHER Register',
    summary:
      'Registry view for white papers related to other crypto-assets under MiCA.',
    highlights: [
      'White paper references and comments.',
      'Linked CASP LEI and legal name fields.',
      'Offer country and DTI metadata.',
    ],
  },
  {
    path: '/art',
    slug: 'art',
    registerType: 'art',
    label: 'ART',
    title: 'MiCA ART Register | Asset-Referenced Token Issuers',
    description:
      'Explore the MiCA ART register of asset-referenced token issuers with legal entity data and white paper references.',
    heading: 'MiCA ART Register',
    summary:
      'Registry view for Asset-Referenced Token (ART) issuers under MiCA.',
    highlights: [
      'Issuer legal entity and LEI data.',
      'Credit institution indicator where available.',
      'White paper references and related updates.',
    ],
  },
  {
    path: '/emt',
    slug: 'emt',
    registerType: 'emt',
    label: 'EMT',
    title: 'MiCA EMT Register | E-Money Token Issuers',
    description:
      'Explore the MiCA EMT register of e-money token issuers with exemption flags, institution type, and white paper fields.',
    heading: 'MiCA EMT Register',
    summary:
      'Registry view for E-Money Token (EMT) issuers under MiCA.',
    highlights: [
      'Institution type and exemption indicators.',
      'White paper, DTI, and related fields.',
      'Entity and jurisdiction metadata.',
    ],
  },
  {
    path: '/ncasp',
    slug: 'ncasp',
    registerType: 'ncasp',
    label: 'NCASP',
    title: 'MiCA NCASP Register | Non-Compliant Crypto Entities',
    description:
      'Review MiCA NCASP entries for non-compliant entities, including websites, infringement status, reasons, and decision dates.',
    heading: 'MiCA NCASP Register',
    summary:
      'Registry view for non-compliant crypto entities listed under MiCA NCASP publications.',
    highlights: [
      'Published website domains and identifiers.',
      'Infringement status and reason fields.',
      'Decision and publication date metadata.',
    ],
  },
];

const registerRoutes = staticRoutes.filter((route) => route.registerType);

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const distDir = path.resolve(__dirname, '..', 'dist');
const indexPath = path.join(distDir, 'index.html');

function canonicalFor(routePath) {
  return routePath === '/' ? `${baseUrl}/` : `${baseUrl}${routePath}`;
}

function escapeXml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;');
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function setMeta(html, pattern, replacement, label) {
  if (!pattern.test(html)) {
    throw new Error(`Missing expected ${label} tag in dist/index.html`);
  }
  return html.replace(pattern, replacement);
}

function normalizeEntityName(entity) {
  const commercialName = entity?.commercial_name;
  if (typeof commercialName === 'string' && commercialName.trim()) {
    return commercialName.trim();
  }

  const leiName = entity?.lei_name;
  if (typeof leiName === 'string' && leiName.trim()) {
    return leiName.trim();
  }

  return `Entity ${entity?.id ?? 'Unknown'}`;
}

function createDetailRoute(entity, registerRoute) {
  const entityId = Number.parseInt(String(entity?.id), 10);
  if (!Number.isInteger(entityId) || entityId <= 0) {
    return null;
  }

  const entityName = normalizeEntityName(entity);
  return {
    path: `${registerRoute.path}/${entityId}`,
    slug: `${registerRoute.slug}/${entityId}`,
    kind: 'detail',
    title: `${entityName} | MiCA ${registerRoute.label} Register`,
    description: `Entity details for ${entityName} in the MiCA ${registerRoute.label} register, including jurisdiction and register-specific fields.`,
    heading: entityName,
    summary: `Detailed profile for MiCA ${registerRoute.label} register entry ${entityId}.`,
    highlights: [
      `Register: ${registerRoute.heading}.`,
      `Entity ID: ${entityId}.`,
      'Open this URL to load the full interactive entity view.',
    ],
    registerPath: registerRoute.path,
    registerHeading: registerRoute.heading,
  };
}

async function fetchJsonWithTimeout(url, timeoutMs = 10000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status} for ${url}`);
    }

    return response.json();
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw new Error(`Request timed out for ${url}`);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

async function fetchRegisterEntities(registerType) {
  const entities = [];
  let skip = 0;

  while (true) {
    const url = `${apiBaseUrl}/api/entities?register_type=${encodeURIComponent(registerType)}&limit=${detailBatchSize}&skip=${skip}`;
    const payload = await fetchJsonWithTimeout(url);
    const items = Array.isArray(payload?.items) ? payload.items : [];

    if (items.length === 0) {
      break;
    }

    entities.push(...items);
    skip += items.length;

    const total = payload?.total;
    if (typeof total === 'number' && skip >= total) {
      break;
    }
  }

  return entities;
}

async function fetchDetailRoutes() {
  if (process.env.PRERENDER_ENTITY_DETAILS === '0') {
    console.log('Skipping entity detail prerender because PRERENDER_ENTITY_DETAILS=0');
    return {
      detailRoutes: [],
      registerSummaries: [],
      failures: [],
      skipped: true,
    };
  }

  const detailRoutes = [];
  const registerSummaries = [];
  const failures = [];

  for (const registerRoute of registerRoutes) {
    try {
      const entities = await fetchRegisterEntities(registerRoute.registerType);
      let detailCountForRegister = 0;

      for (const entity of entities) {
        const detailRoute = createDetailRoute(entity, registerRoute);
        if (detailRoute) {
          detailRoutes.push(detailRoute);
          detailCountForRegister += 1;
        }
      }

      registerSummaries.push({
        registerType: registerRoute.registerType,
        entityCount: entities.length,
        detailCount: detailCountForRegister,
        error: null,
      });
      console.log(
        `Prepared ${detailCountForRegister} detail pages for ${registerRoute.registerType.toUpperCase()} (entities fetched: ${entities.length})`,
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      failures.push({
        registerType: registerRoute.registerType,
        message,
      });
      registerSummaries.push({
        registerType: registerRoute.registerType,
        entityCount: 0,
        detailCount: 0,
        error: message,
      });
      console.warn(
        `Skipping detail prerender for ${registerRoute.registerType}: ${message}`,
      );
    }
  }

  return {
    detailRoutes,
    registerSummaries,
    failures,
    skipped: false,
  };
}

function reportDetailPrerenderSummary(detailResult) {
  if (detailResult.skipped) {
    console.log('Detail prerender summary: skipped by PRERENDER_ENTITY_DETAILS=0');
    return;
  }

  if (detailResult.registerSummaries.length === 0) {
    console.log('Detail prerender summary: no register summaries available');
    return;
  }

  const summary = detailResult.registerSummaries
    .map((item) => {
      const base = `${item.registerType}: entities=${item.entityCount}, details=${item.detailCount}`;
      if (item.error) {
        return `${base}, error=${item.error}`;
      }
      return base;
    })
    .join(' | ');

  console.log(`Detail prerender summary: ${summary}`);
}

function validateDetailPrerender(detailResult) {
  if (detailResult.skipped || detailFailureMode === 'off') {
    if (detailFailureMode === 'off' && !detailResult.skipped) {
      console.warn('Detail prerender validation is disabled (PRERENDER_DETAIL_FAILURE_MODE=off)');
    }
    return;
  }

  const detailCount = detailResult.detailRoutes.length;
  const issueLines = [];

  if (detailResult.failures.length > 0) {
    for (const failure of detailResult.failures) {
      issueLines.push(`${failure.registerType}: ${failure.message}`);
    }
  }

  if (detailCount < minDetailPages) {
    issueLines.push(
      `detail pages generated (${detailCount}) is below minimum PRERENDER_MIN_DETAIL_PAGES=${minDetailPages}`,
    );
  }

  if (issueLines.length === 0) {
    return;
  }

  const message = `Detail prerender validation issue(s): ${issueLines.join(' | ')}`;
  if (detailFailureMode === 'error') {
    throw new Error(message);
  }

  console.warn(message);
}

function prerenderMarkup(route) {
  const quickLinks = staticRoutes
    .filter(({ path: routePath }) => routePath !== route.path)
    .map(
      ({ path: routePath, slug, heading }) =>
        `<li><a href="${routePath}" style="color:#0f4ecf;text-decoration:none;">${escapeHtml(heading)}</a> <span style="color:#64748b;">(${slug || 'home'})</span></li>`,
    )
    .join('');

  const highlights = route.highlights
    .map((item) => `<li style="margin:0 0 8px 0;">${escapeHtml(item)}</li>`)
    .join('');

  const registerLink = route.kind === 'detail'
    ? `<p style="margin:0 0 10px 0;"><strong>Register page:</strong> <a href="${route.registerPath}" style="color:#0f4ecf;text-decoration:none;">${escapeHtml(route.registerHeading)}</a></p>`
    : '';

  return `
      <main style="max-width:960px;margin:0 auto;padding:24px 16px 28px;font-family:Inter,Segoe UI,Arial,sans-serif;line-height:1.6;color:#0f172a;">
        <h1 style="font-size:32px;line-height:1.2;margin:0 0 12px 0;">${escapeHtml(route.heading)}</h1>
        <p style="font-size:18px;color:#334155;margin:0 0 16px 0;">${escapeHtml(route.summary)}</p>
        <p style="margin:0 0 16px 0;color:#334155;">This page is prerendered for search and indexing. The interactive app loads automatically in JavaScript-enabled browsers.</p>
        <ul style="padding-left:20px;margin:0 0 18px 0;">${highlights}</ul>
        ${registerLink}
        <p style="margin:0 0 8px 0;"><strong>API documentation:</strong> <a href="${apiDocsUrl}" style="color:#0f4ecf;text-decoration:none;">${apiDocsUrl}</a></p>
        <p style="margin:0 0 8px 0;"><strong>Other register pages:</strong></p>
        <ul style="padding-left:20px;margin:0;">${quickLinks}</ul>
      </main>
  `;
}

function renderRouteHtml(templateHtml, route) {
  const url = canonicalFor(route.path);
  const title = escapeHtml(route.title);
  const description = escapeHtml(route.description);

  let html = templateHtml;
  html = setMeta(html, /<title>[\s\S]*?<\/title>/, `<title>${title}</title>`, 'title');
  html = setMeta(
    html,
    /<meta name="title" content="[^"]*"\s*\/?>/,
    `<meta name="title" content="${title}" />`,
    'meta title',
  );
  html = setMeta(
    html,
    /<meta name="description" content="[^"]*"\s*\/?>/,
    `<meta name="description" content="${description}" />`,
    'meta description',
  );
  html = setMeta(
    html,
    /<link rel="canonical" href="[^"]*"\s*\/?>/,
    `<link rel="canonical" href="${url}" />`,
    'canonical',
  );
  html = setMeta(
    html,
    /<meta property="og:title" content="[^"]*"\s*\/?>/,
    `<meta property="og:title" content="${title}" />`,
    'og:title',
  );
  html = setMeta(
    html,
    /<meta property="og:description" content="[^"]*"\s*\/?>/,
    `<meta property="og:description" content="${description}" />`,
    'og:description',
  );
  html = setMeta(
    html,
    /<meta property="og:url" content="[^"]*"\s*\/?>/,
    `<meta property="og:url" content="${url}" />`,
    'og:url',
  );
  html = setMeta(
    html,
    /<meta name="twitter:title" content="[^"]*"\s*\/?>/,
    `<meta name="twitter:title" content="${title}" />`,
    'twitter:title',
  );
  html = setMeta(
    html,
    /<meta name="twitter:description" content="[^"]*"\s*\/?>/,
    `<meta name="twitter:description" content="${description}" />`,
    'twitter:description',
  );
  html = setMeta(
    html,
    /"url":\s*"[^"]*"/,
    `"url": "${url}"`,
    'json-ld url',
  );
  html = setMeta(
    html,
    /<div id="root">[\s\S]*?<\/div>/,
    `<div id="root">${prerenderMarkup(route)}\n    </div>`,
    'root container',
  );

  return html;
}

function buildSitemapXml(routes) {
  const uniqueUrls = [...new Set(routes.map((route) => canonicalFor(route.path)))];
  const urlRows = uniqueUrls
    .map((url) => `  <url>\n    <loc>${escapeXml(url)}</loc>\n  </url>`)
    .join('\n');

  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urlRows}\n</urlset>\n`;
}

function buildRobotsTxt() {
  return `User-agent: *\nAllow: /\n\nSitemap: ${canonicalFor('/sitemap.xml')}\n`;
}

async function writeRouteFiles() {
  const templateHtml = await readFile(indexPath, 'utf8');
  const detailResult = await fetchDetailRoutes();
  reportDetailPrerenderSummary(detailResult);
  validateDetailPrerender(detailResult);
  const routes = [...staticRoutes, ...detailResult.detailRoutes];

  for (const route of routes) {
    const html = renderRouteHtml(templateHtml, route);
    if (route.path === '/') {
      await writeFile(indexPath, html, 'utf8');
      continue;
    }

    const outDir = path.join(distDir, route.slug);
    await mkdir(outDir, { recursive: true });
    await writeFile(path.join(outDir, 'index.html'), html, 'utf8');
  }

  await writeFile(path.join(distDir, 'sitemap.xml'), buildSitemapXml(routes), 'utf8');
  await writeFile(path.join(distDir, 'robots.txt'), buildRobotsTxt(), 'utf8');

  return {
    staticCount: staticRoutes.length,
    detailCount: detailResult.detailRoutes.length,
    detailFetchFailureCount: detailResult.failures.length,
    totalCount: routes.length,
    sitemapUrlCount: new Set(routes.map((route) => canonicalFor(route.path))).size,
  };
}

try {
  const {
    staticCount,
    detailCount,
    detailFetchFailureCount,
    totalCount,
    sitemapUrlCount,
  } = await writeRouteFiles();
  console.log(
    `Prerendered ${totalCount} route pages in ${distDir} (${staticCount} static + ${detailCount} detail, fetch failures: ${detailFetchFailureCount})`,
  );
  console.log(`Generated sitemap.xml with ${sitemapUrlCount} URLs and refreshed robots.txt`);
} catch (error) {
  console.error('Failed to prerender route pages:', error);
  process.exit(1);
}
