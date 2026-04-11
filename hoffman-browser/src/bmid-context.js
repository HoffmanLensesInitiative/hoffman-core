/**
 * bmid-context.js
 * Hoffman Browser -- BMID enrichment provider
 *
 * Before the model analyzes a page, this module queries the BMID API for
 * any fisherman record associated with that domain. If one exists, it
 * returns a structured enrichment object that the analyzer converts into
 * a context string prepended to the model system prompt.
 *
 * The model then reads the page knowing:
 *   - Who owns this platform
 *   - How they monetize attention
 *   - Their documented motive structure
 *   - How many harms are on record
 *   - Which techniques are already known for this domain
 *
 * Contract:
 *
 *   getBmidEnrichment(hostname) -> Promise<EnrichmentResult>
 *
 *   EnrichmentResult shape:
 *   {
 *     available: boolean,          // false if BMID down, domain unknown, or timeout
 *     owner: string|null,
 *     businessModel: string|null,
 *     primaryMotive: string|null,
 *     documentedHarms: number,     // total catch records on file
 *     knownTechniques: string[],   // normalised technique/motive type strings
 *     contextString: string        // pre-built prompt prefix, '' if not available
 *   }
 *
 * If BMID is unreachable, times out (2s), or returns no record for the domain,
 * available is false and contextString is ''. The caller proceeds unchanged.
 *
 * Architecture constraint (HOFFMAN.md 2026-03-29):
 *   BMID context enriches the model prompt -- it does not gate or pre-screen.
 *   The model must still find manipulation independently. Do not use knownTechniques
 *   as a whitelist that suppresses model findings.
 */

'use strict';

var http = require('http');

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

var BMID_HOST = '127.0.0.1';
var BMID_PORT = 5000;
var BMID_PATH_PREFIX = '/api/v1/explain';
var TIMEOUT_MS = 2000;

// ---------------------------------------------------------------------------
// Internal: HTTP GET with timeout
// ---------------------------------------------------------------------------

/**
 * Perform a lightweight HTTP GET against the BMID API running on localhost.
 * Resolves with parsed JSON body, or rejects on timeout / HTTP error / parse error.
 *
 * @param {string} path  e.g. '/api/v1/explain?domain=facebook.com'
 * @returns {Promise<object>}
 */
function httpGet(path) {
  return new Promise(function(resolve, reject) {
    var options = {
      hostname: BMID_HOST,
      port: BMID_PORT,
      path: path,
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    };

    var req = http.request(options, function(res) {
      var chunks = [];
      res.on('data', function(chunk) { chunks.push(chunk); });
      res.on('end', function() {
        try {
          var body = Buffer.concat(chunks).toString('utf8');
          var parsed = JSON.parse(body);
          resolve(parsed);
        } catch (e) {
          reject(new Error('BMID JSON parse error: ' + e.message));
        }
      });
    });

    // Abort after timeout
    var timer = setTimeout(function() {
      req.destroy();
      reject(new Error('BMID request timed out after ' + TIMEOUT_MS + 'ms'));
    }, TIMEOUT_MS);

    // Clear timer if request ends cleanly
    req.on('close', function() { clearTimeout(timer); });

    req.on('error', function(err) {
      clearTimeout(timer);
      reject(err);
    });

    req.end();
  });
}

// ---------------------------------------------------------------------------
// Internal: build empty (unavailable) result
// ---------------------------------------------------------------------------

function emptyResult() {
  return {
    available: false,
    owner: null,
    businessModel: null,
    primaryMotive: null,
    documentedHarms: 0,
    knownTechniques: [],
    contextString: ''
  };
}

// ---------------------------------------------------------------------------
// Internal: extract known techniques from BMID explain response
// ---------------------------------------------------------------------------

/**
 * The BMID /explain endpoint returns a structure that includes:
 *   fisherman.{owner, business_model, ...}
 *   motives: [{type, description, ...}]
 *   catch_summary: {total_documented, ...}
 *   top_patterns: [string] (may or may not be present)
 *   intelligence_level: 'high'|'medium'|'low'|'none'
 *
 * We collect technique labels from motives[].type and top_patterns (if present).
 *
 * @param {object} data  Parsed API response
 * @returns {string[]}
 */
function extractKnownTechniques(data) {
  var techniques = [];

  // Motive types (e.g. 'outrage_amplification', 'false_urgency')
  if (Array.isArray(data.motives)) {
    data.motives.forEach(function(motive) {
      if (motive && motive.type && typeof motive.type === 'string') {
        techniques.push(motive.type);
      }
      // Some BMID records store pattern names separately
      if (motive && motive.pattern && typeof motive.pattern === 'string') {
        techniques.push(motive.pattern);
      }
    });
  }

  // top_patterns field (may be an array of strings)
  if (Array.isArray(data.top_patterns)) {
    data.top_patterns.forEach(function(p) {
      if (p && typeof p === 'string') techniques.push(p);
    });
  }

  // Deduplicate (preserve order, case-insensitive)
  var seen = {};
  var deduped = [];
  techniques.forEach(function(t) {
    var key = t.toLowerCase().trim();
    if (!seen[key]) {
      seen[key] = true;
      deduped.push(t);
    }
  });

  return deduped;
}

// ---------------------------------------------------------------------------
// Internal: build the context string for the model system prompt
// ---------------------------------------------------------------------------

/**
 * Produce the text block that gets prepended to the model's system prompt.
 * Deliberately terse -- the model context window is limited (4096 tokens for 3B).
 *
 * @param {object} data        Parsed BMID API response
 * @param {string[]} techniques
 * @returns {string}
 */
function buildContextString(data, techniques) {
  var lines = [];
  lines.push('KNOWN INTELLIGENCE ON THIS DOMAIN:');

  var fisherman = data.fisherman || {};

  if (fisherman.owner) {
    lines.push('Owner: ' + fisherman.owner);
  }

  if (fisherman.business_model) {
    lines.push('Business model: ' + fisherman.business_model);
  }

  // Primary motive -- first entry
  if (Array.isArray(data.motives) && data.motives.length > 0) {
    var m = data.motives[0];
    if (m && m.description) {
      lines.push('Primary documented motive: ' + m.description);
    }
  }

  // Documented harms
  var harmCount = 0;
  if (data.catch_summary && typeof data.catch_summary.total_documented === 'number') {
    harmCount = data.catch_summary.total_documented;
  }
  lines.push('Documented harms on record: ' + harmCount);

  // Known techniques
  if (techniques.length > 0) {
    lines.push('Known techniques for this domain: ' + techniques.slice(0, 8).join(', '));
  }

  lines.push('');  // blank line before model instructions
  return lines.join('\n');
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Query BMID for enrichment data about the given hostname.
 * Always resolves (never rejects) -- failures return emptyResult().
 *
 * @param {string} hostname  e.g. 'www.facebook.com' or 'facebook.com'
 * @returns {Promise<EnrichmentResult>}
 */
function getBmidEnrichment(hostname) {
  if (!hostname || typeof hostname !== 'string') {
    return Promise.resolve(emptyResult());
  }

  // Strip 'www.' prefix for consistent BMID lookup
  var domain = hostname.replace(/^www\./, '');

  var path = BMID_PATH_PREFIX + '?domain=' + encodeURIComponent(domain);

  return httpGet(path).then(function(data) {
    // BMID returns intelligence_level 'none' when it has no record for domain
    if (!data || data.intelligence_level === 'none') {
      console.log('[Hoffman] BMID: no record for ' + domain);
      return emptyResult();
    }

    var techniques = extractKnownTechniques(data);
    var contextString = buildContextString(data, techniques);

    var fisherman = data.fisherman || {};
    var primaryMotive = null;
    if (Array.isArray(data.motives) && data.motives.length > 0) {
      primaryMotive = (data.motives[0] && data.motives[0].description) || null;
    }

    var documentedHarms = 0;
    if (data.catch_summary && typeof data.catch_summary.total_documented === 'number') {
      documentedHarms = data.catch_summary.total_documented;
    }

    console.log('[Hoffman] BMID: enrichment loaded for ' + domain +
      ' -- ' + techniques.length + ' known techniques, ' +
      documentedHarms + ' documented harms');

    return {
      available: true,
      owner: fisherman.owner || null,
      businessModel: fisherman.business_model || null,
      primaryMotive: primaryMotive,
      documentedHarms: documentedHarms,
      knownTechniques: techniques,
      contextString: contextString
    };

  }).catch(function(err) {
    // BMID is down, unreachable, timed out, or returned invalid JSON.
    // This is expected when BMID is not running locally.
    // Log briefly and continue without context.
    console.log('[Hoffman] BMID unavailable for ' + domain + ': ' + err.message);
    return emptyResult();
  });
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

module.exports = {
  getBmidEnrichment: getBmidEnrichment
};
