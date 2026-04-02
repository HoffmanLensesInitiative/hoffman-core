/**
 * bmid-context.js
 * Hoffman Browser -- BMID context enrichment helper
 *
 * Queries the local BMID API for intelligence on a domain before analysis runs.
 * Returns a context string to prepend to the model's system prompt.
 * If BMID is unavailable or the domain is unknown, returns null -- analysis proceeds unchanged.
 *
 * This module is non-blocking by design. Always resolves; never rejects.
 * Timeout: 2000ms. If BMID does not respond in time, returns null.
 */

'use strict';

const http = require('http');

const BMID_BASE = 'http://localhost:5000';
const TIMEOUT_MS = 2000;

/**
 * Query BMID for intelligence on a domain.
 * @param {string} domain - hostname, e.g. "foxnews.com"
 * @returns {Promise<string|null>} context string or null
 */
async function getBmidContext(domain) {
  if (!domain || typeof domain !== 'string') return null;

  const cleanDomain = domain.replace(/^www\./, '').toLowerCase();

  return new Promise((resolve) => {
    const url = `${BMID_BASE}/api/v1/explain?domain=${encodeURIComponent(cleanDomain)}`;
    const timer = setTimeout(() => {
      console.log('[Hoffman] BMID context query timed out for:', cleanDomain);
      resolve(null);
    }, TIMEOUT_MS);

    http.get(url, (res) => {
      let raw = '';
      res.on('data', (chunk) => { raw += chunk; });
      res.on('end', () => {
        clearTimeout(timer);
        try {
          const data = JSON.parse(raw);

          // If BMID has no record for this domain, skip context
          if (!data || data.intelligence_level === 'none' || !data.fisherman) {
            resolve(null);
            return;
          }

          const context = buildContextString(data);
          console.log('[Hoffman] BMID context loaded for:', cleanDomain,
            '| intelligence_level:', data.intelligence_level);
          resolve(context);
        } catch (e) {
          console.log('[Hoffman] BMID context parse error for:', cleanDomain, e.message);
          resolve(null);
        }
      });
      res.on('error', (e) => {
        clearTimeout(timer);
        console.log('[Hoffman] BMID context response error:', e.message);
        resolve(null);
      });
    }).on('error', (e) => {
      clearTimeout(timer);
      console.log('[Hoffman] BMID context connection error:', e.message);
      resolve(null);
    });
  });
}

/**
 * Build the context string to prepend to the system prompt.
 * @param {object} data - parsed BMID /explain response
 * @returns {string}
 */
function buildContextString(data) {
  const f = data.fisherman || {};
  const motives = Array.isArray(data.motives) ? data.motives : [];
  const catchSummary = data.catch_summary || {};
  const topPatterns = Array.isArray(data.top_patterns) ? data.top_patterns : [];

  const lines = [
    'KNOWN INTELLIGENCE ON THIS DOMAIN:',
    `Owner: ${f.owner || 'unknown'}`,
    `Business model: ${f.business_model || 'unknown'}`,
  ];

  if (motives.length > 0) {
    lines.push(`Documented primary motive: ${motives[0].description || motives[0].motive_type || 'unknown'}`);
  }

  const harmCount = catchSummary.total_documented;
  if (harmCount !== undefined && harmCount !== null) {
    lines.push(`Documented harms on record: ${harmCount}`);
  }

  if (topPatterns.length > 0) {
    lines.push(`Known manipulation techniques: ${topPatterns.join(', ')}`);
  } else if (motives.length > 0) {
    // Fall back to motive types if top_patterns not available
    const motiveTypes = motives
      .map((m) => m.motive_type)
      .filter(Boolean)
      .slice(0, 3);
    if (motiveTypes.length > 0) {
      lines.push(`Known motive types: ${motiveTypes.join(', ')}`);
    }
  }

  return lines.join('\n');
}

/**
 * Extract the known technique names from a BMID explain response.
 * Used for novel technique detection -- comparing model output against known patterns.
 * @param {object} data - parsed BMID /explain response
 * @returns {string[]} array of known technique strings (lowercase)
 */
function getKnownTechniques(data) {
  if (!data) return [];

  const techniques = [];

  if (Array.isArray(data.top_patterns)) {
    data.top_patterns.forEach((p) => {
      if (typeof p === 'string') techniques.push(p.toLowerCase());
    });
  }

  if (Array.isArray(data.motives)) {
    data.motives.forEach((m) => {
      if (m && typeof m.motive_type === 'string') {
        techniques.push(m.motive_type.toLowerCase());
      }
    });
  }

  return [...new Set(techniques)];
}

/**
 * Query BMID and return both context string and known techniques list.
 * Single HTTP call, two useful outputs.
 * @param {string} domain
 * @returns {Promise<{ context: string|null, knownTechniques: string[] }>}
 */
async function getBmidEnrichment(domain) {
  if (!domain || typeof domain !== 'string') {
    return { context: null, knownTechniques: [] };
  }

  const cleanDomain = domain.replace(/^www\./, '').toLowerCase();

  return new Promise((resolve) => {
    const url = `${BMID_BASE}/api/v1/explain?domain=${encodeURIComponent(cleanDomain)}`;
    const timer = setTimeout(() => {
      console.log('[Hoffman] BMID enrichment timed out for:', cleanDomain);
      resolve({ context: null, knownTechniques: [] });
    }, TIMEOUT_MS);

    http.get(url, (res) => {
      let raw = '';
      res.on('data', (chunk) => { raw += chunk; });
      res.on('end', () => {
        clearTimeout(timer);
        try {
          const data = JSON.parse(raw);

          if (!data || data.intelligence_level === 'none' || !data.fisherman) {
            resolve({ context: null, knownTechniques: [] });
            return;
          }

          const context = buildContextString(data);
          const knownTechniques = getKnownTechniques(data);

          console.log('[Hoffman] BMID enrichment loaded for:', cleanDomain,
            '| techniques known:', knownTechniques.length);

          resolve({ context, knownTechniques });
        } catch (e) {
          console.log('[Hoffman] BMID enrichment parse error for:', cleanDomain, e.message);
          resolve({ context: null, knownTechniques: [] });
        }
      });
      res.on('error', (e) => {
        clearTimeout(timer);
        resolve({ context: null, knownTechniques: [] });
      });
    }).on('error', (e) => {
      clearTimeout(timer);
      resolve({ context: null, knownTechniques: [] });
    });
  });
}

module.exports = { getBmidContext, getBmidEnrichment, getKnownTechniques };
