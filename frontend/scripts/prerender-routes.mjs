import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const baseUrl = 'https://www.micaregister.com';
const apiDocsUrl = 'https://mica-register-production.up.railway.app/docs';

const routes = [
  {
    path: '/',
    slug: '',
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

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const distDir = path.resolve(__dirname, '..', 'dist');
const indexPath = path.join(distDir, 'index.html');

function canonicalFor(routePath) {
  return routePath === '/' ? `${baseUrl}/` : `${baseUrl}${routePath}`;
}

function escapeHtml(value) {
  return value
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

function prerenderMarkup(route) {
  const quickLinks = routes
    .filter(({ path: routePath }) => routePath !== route.path)
    .map(
      ({ path: routePath, slug, heading }) =>
        `<li><a href="${routePath}" style="color:#0f4ecf;text-decoration:none;">${escapeHtml(heading)}</a> <span style="color:#64748b;">(${slug || 'home'})</span></li>`,
    )
    .join('');

  const highlights = route.highlights
    .map((item) => `<li style="margin:0 0 8px 0;">${escapeHtml(item)}</li>`)
    .join('');

  return `
      <main style="max-width:960px;margin:0 auto;padding:24px 16px 28px;font-family:Inter,Segoe UI,Arial,sans-serif;line-height:1.6;color:#0f172a;">
        <h1 style="font-size:32px;line-height:1.2;margin:0 0 12px 0;">${escapeHtml(route.heading)}</h1>
        <p style="font-size:18px;color:#334155;margin:0 0 16px 0;">${escapeHtml(route.summary)}</p>
        <p style="margin:0 0 16px 0;color:#334155;">This page is prerendered for search and indexing. The interactive app loads automatically in JavaScript-enabled browsers.</p>
        <ul style="padding-left:20px;margin:0 0 18px 0;">${highlights}</ul>
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

async function writeRouteFiles() {
  const templateHtml = await readFile(indexPath, 'utf8');

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
}

try {
  await writeRouteFiles();
  console.log(`Prerendered ${routes.length} route pages in ${distDir}`);
} catch (error) {
  console.error('Failed to prerender route pages:', error);
  process.exit(1);
}
