/**
 * bmid-context.js
 * Hoffman Browser -- BMID enrichment query
 *
 * Before the model analyzes a page, this module queries the BMID API for
 * any known intelligence on the domain being visited. If a fisherman record
 * exists, that intelligence is returned as a structured object that analyzer.js
 * prepends to the model's system prompt.
 *
 * The model then reads the page knowing what BMID knows: who owns this domain,
 * what their documented business motive is, what harms have been recorded, and
 * what techniques have already been observed. The model reads with the chart,
 * not cold.
 *
 * Rules:
 *   - BMID must respond within 2000ms or the query is abandoned
 *   - If BMID is not running, or returns an error, or times out: resolve with null
 *   - BMID context is enrichment only -- the model must still find manipulation
 *     independently. The context informs; it does not direct.
 *   - Never throws -- all errors return null gracefully
 *
 * Returned enrichment object shape (non-null when record exists):
 * {
 *   owner: string,
 *   businessModel: string,
 *   primaryMotive: string,
 *   documentedHarms: number,
 *   knownTechniques: string[],
 *   contextString: string   -- formatted for system prompt injection
 * }
 */

'use strict';

var http = require('http');

var BMID_HOST = '127.0.0.1';
var BMID_PORT = 5000;
var BMID_TIMEOUT_MS = 2000;
var BMID_BASE = 'http://' + BMID_HOST + ':' + BMID_PORT;

/**
 * Query the BMID /api/v1/explain endpoint for a domain.
 * Returns structured enrichment or null.
 *
 * @param {string} domain  e.g. 'foxnews.com'
 * @returns {Promise<object|null>}
 */
function getBmidEnrichment(domain) {
  return new Promise(function (resolve) {
    if (!domain || typeof domain !== 'string') {
      resolve(null);
      return;
    }

    // Strip leading www. for cleaner matching
    var cleanDomain = domain.replace(/^www\./, '').toLowerCase();

    var path = '/api/v1/explain?domain=' + encodeURIComponent(cleanDomain);
    var options = {
      hostname: BMID_HOST,
      port: BMID_PORT,
      path: path,
      method: 'GET',
      timeout: BMID_TIMEOUT_MS
    };

    var req = http.request(options, function (res) {
      var body = '';
      res.setEncoding('utf8');

      res.on('data', function (chunk) {
        body += chunk;
      });

      res.on('end', function () {
        try {
          if (res.statusCode === 404) {
            // Domain not on file -- no enrichment available
            console.log('[Hoffman BMID] No record for domain: ' + cleanDomain);
            resolve(null);
            return;
          }

          if (res.statusCode !== 200) {
            console.log('[Hoffman BMID] Non-200 response (' + res.statusCode + ') for domain: ' + cleanDomain);
            resolve(null);
            return;
          }

          var data = JSON.parse(body);

          // Check intelligence_level -- if 'none', no useful data
          if (!data || data.intelligence_level === 'none' || data.intelligence_level === undefined) {
            resolve(null);
            return;
          }

          var enrichment = buildEnrichment(data, cleanDomain);
          if (enrichment) {
            console.log('[Hoffman BMID] Enrichment loaded for ' + cleanDomain + ': ' + enrichment.owner);
          }
          resolve(enrichment);

        } catch (parseErr) {
          console.log('[Hoffman BMID] Parse error for ' + cleanDomain + ': ' + parseErr.message);
          resolve(null);
        }
      });
    });

    req.on('timeout', function () {
      console.log('[Hoffman BMID] Timeout querying for domain: ' + cleanDomain);
      req.destroy();
      resolve(null);
    });

    req.on('error', function (err) {
      // BMID not running or connection refused -- not an error condition for the browser
      // Just log and continue without context
      if (err.code !== 'ECONNREFUSED') {
        console.log('[Hoffman BMID] Request error for ' + cleanDomain + ': ' + err.message);
      }
      resolve(null);
    });

    req.end();
  });
}

/**
 * Build the enrichment object from a successful BMID API response.
 * The /api/v1/explain endpoint returns a fisherman block, motives array,
 * and catch_summary object. We extract what the system prompt needs.
 *
 * @param {object} data  Parsed JSON response from /api/v1/explain
 * @param {string} domain
 * @returns {object|null}
 */
function buildEnrichment(data, domain) {
  try {
    var fisherman = data.fisherman || {};
    var motives = data.motives || [];
    var catchSummary = data.catch_summary || {};

    // Extract owner
    var owner = fisherman.owner || fisherman.name || domain;

    // Extract business model
    var businessModel = fisherman.business_model || 'engagement-based advertising';

    // Extract primary documented motive
    var primaryMotive = 'unknown';
    if (motives.length > 0 && motives[0].description) {
      primaryMotive = motives[0].description;
    } else if (motives.length > 0 && motives[0].motive_type) {
      primaryMotive = motives[0].motive_type;
    }

    // Extract documented harm count
    var documentedHarms = 0;
    if (catchSummary && typeof catchSummary.total_documented === 'number') {
      documentedHarms = catchSummary.total_documented;
    } else if (catchSummary && typeof catchSummary.count === 'number') {
      documentedHarms = catchSummary.count;
    }

    // Extract known techniques from motives and top patterns
    var knownTechniques = [];
    var topPatterns = data.top_patterns || [];
    if (Array.isArray(topPatterns)) {
      topPatterns.forEach(function (p) {
        if (p && typeof p === 'string') knownTechniques.push(p);
        else if (p && p.pattern) knownTechniques.push(p.pattern);
        else if (p && p.type) knownTechniques.push(p.type);
      });
    }
    // Also pull technique types out of motives if present
    motives.forEach(function (m) {
      if (m && m.motive_type && knownTechniques.indexOf(m.motive_type) === -1) {
        knownTechniques.push(m.motive_type);
      }
    });

    // Build the context string that will be prepended to the system prompt
    var lines = [
      'KNOWN INTELLIGENCE ON THIS DOMAIN:',
      'Owner: ' + owner,
      'Business model: ' + businessModel,
      'Documented motive: ' + primaryMotive,
      'Documented harms: ' + documentedHarms + ' cases on record'
    ];

    if (knownTechniques.length > 0) {
      lines.push('Known techniques: ' + knownTechniques.join(', '));
    }

    var contextString = lines.join('\n');

    return {
      owner: owner,
      businessModel: businessModel,
      primaryMotive: primaryMotive,
      documentedHarms: documentedHarms,
      knownTechniques: knownTechniques,
      contextString: contextString
    };

  } catch (err) {
    console.log('[Hoffman BMID] buildEnrichment error: ' + err.message);
    return null;
  }
}

module.exports = {
  getBmidEnrichment: getBmidEnrichment
};
