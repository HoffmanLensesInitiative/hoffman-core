/**
 * Hoffman Browser - BMID Client
 * Queries the Behavioral Manipulation Intelligence Database for publisher context.
 * Called before analysis runs so the model reads with the chart, not cold.
 */

'use strict';

const http = require('http');

const BMID_API = 'http://localhost:5000/api/v1';
const TIMEOUT_MS = 2000;

function extractDomain(url) {
  try {
    const hostname = new URL(url).hostname;
    return hostname.replace(/^www\./, '').replace(/^m\./, '');
  } catch (e) {
    return null;
  }
}

// Query BMID for domain intelligence.
// Returns a Promise that resolves to the response object or null.
// Never rejects -- failure always resolves to null so analysis proceeds normally.
function queryDomain(url) {
  const domain = extractDomain(url);
  if (!domain) return Promise.resolve(null);

  const apiUrl = BMID_API + '/explain?domain=' + encodeURIComponent(domain);

  return new Promise((resolve) => {
    const req = http.get(apiUrl, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          console.log('[BMID] Intelligence level for', domain + ':', parsed.intelligence_level);
          resolve(parsed);
        } catch (e) {
          console.log('[BMID] Invalid JSON response');
          resolve(null);
        }
      });
    });

    req.on('error', (err) => {
      console.log('[BMID] Query failed:', err.message);
      resolve(null);
    });

    req.setTimeout(TIMEOUT_MS, () => {
      console.log('[BMID] Query timed out after', TIMEOUT_MS, 'ms');
      req.destroy();
      resolve(null);
    });
  });
}

// Check whether a technique is already documented for this fisherman.
// Returns false if no BMID data -- novelty cannot be determined without intelligence.
function isTechniqueKnown(bmidResponse, technique) {
  if (!bmidResponse || bmidResponse.intelligence_level === 'none') return false;

  if (bmidResponse.top_patterns && Array.isArray(bmidResponse.top_patterns)) {
    return bmidResponse.top_patterns.includes(technique);
  }

  // Infer from motive types when top_patterns not populated
  if (bmidResponse.motives && Array.isArray(bmidResponse.motives)) {
    const motiveToTechnique = {
      'audience_capture':         ['outrage_engineering', 'tribal_activation'],
      'advertising_revenue':      ['false_urgency', 'engagement_directive'],
      'engagement_maximization':  ['engagement_directive', 'incomplete_hook'],
      'vulnerability_exploitation':['outrage_engineering', 'tribal_activation'],
    };
    for (const motive of bmidResponse.motives) {
      const techniques = motiveToTechnique[motive.motive_type] || [];
      if (techniques.includes(technique)) return true;
    }
  }

  return false;
}

module.exports = { queryDomain, isTechniqueKnown };
