/**
 * hoffman-browser/src/bmid-client.js
 * Hoffman Browser -- BMID API client
 *
 * Queries the BMID API for domain intelligence before page analysis runs.
 * All queries are non-blocking with a hard timeout so BMID unavailability
 * never delays or breaks the analysis pipeline.
 *
 * ASCII-clean: no unicode above codepoint 127.
 */

'use strict';

var http = require('http');
var url  = require('url');

var DEFAULT_BASE_URL = 'http://localhost:5000';
var DEFAULT_TIMEOUT_MS = 2000;

// ---------------------------------------------------------------------------
// Internal HTTP GET helper
// ---------------------------------------------------------------------------

/**
 * Perform a GET request and resolve with parsed JSON.
 * Rejects on timeout, network error, non-200 status, or parse failure.
 *
 * @param {string} requestUrl
 * @param {number} timeoutMs
 * @returns {Promise<object>}
 */
function getJson(requestUrl, timeoutMs) {
  return new Promise(function(resolve, reject) {
    var parsed = url.parse(requestUrl);
    var options = {
      hostname: parsed.hostname,
      port:     parsed.port ? parseInt(parsed.port, 10) : 80,
      path:     parsed.path || '/',
      method:   'GET',
      headers:  { 'Accept': 'application/json' }
    };

    var timedOut = false;

    var req = http.request(options, function(res) {
      var body = '';
      res.setEncoding('utf8');
      res.on('data', function(chunk) { body += chunk; });
      res.on('end', function() {
        if (timedOut) return;
        if (res.statusCode !== 200) {
          reject(new Error('BMID HTTP ' + res.statusCode));
          return;
        }
        try {
          resolve(JSON.parse(body));
        } catch (e) {
          reject(new Error('BMID JSON parse error: ' + e.message));
        }
      });
    });

    var timer = setTimeout(function() {
      timedOut = true;
      req.abort();
      reject(new Error('BMID timeout after ' + timeoutMs + 'ms'));
    }, timeoutMs);

    req.on('error', function(err) {
      if (timedOut) return;
      clearTimeout(timer);
      reject(err);
    });

    req.on('response', function() {
      clearTimeout(timer);
    });

    req.end();
  });
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Query BMID for domain intelligence.
 * Returns a structured result object in all cases -- never throws.
 *
 * Result shape on success:
 * {
 *   available: true,
 *   intelligence_level: 'full'|'partial'|'minimal'|'none',
 *   fisherman: { name, owner, business_model, ... } | null,
 *   motives: [...],
 *   catch_summary: { total_documented, ... },
 *   top_patterns: [...]
 * }
 *
 * Result shape when BMID is unavailable or domain unknown:
 * { available: false, reason: string }
 *
 * @param {string} domain      Hostname, e.g. 'foxnews.com'
 * @param {string} [baseUrl]   Override API base URL (default localhost:5000)
 * @param {number} [timeoutMs] Override timeout (default 2000ms)
 * @returns {Promise<object>}  Always resolves, never rejects
 */
function queryDomain(domain, baseUrl, timeoutMs) {
  baseUrl    = baseUrl    || DEFAULT_BASE_URL;
  timeoutMs  = timeoutMs  || DEFAULT_TIMEOUT_MS;

  if (!domain) {
    return Promise.resolve({ available: false, reason: 'no domain provided' });
  }

  // Normalise: strip www. prefix for lookup, lowercase
  var lookupDomain = domain.toLowerCase().replace(/^www\./, '');
  var endpoint = baseUrl + '/api/v1/explain?domain=' + encodeURIComponent(lookupDomain);

  return getJson(endpoint, timeoutMs).then(function(data) {
    // Attach flag indicating BMID responded
    data.available = true;
    return data;
  }).catch(function(err) {
    console.log('[Hoffman] BMID query failed for ' + domain + ': ' + err.message);
    return { available: false, reason: err.message };
  });
}

/**
 * Query the BMID /explain endpoint and return top_patterns list.
 * Returns empty array if BMID unavailable or domain unknown.
 *
 * @param {string} domain
 * @param {string} [baseUrl]
 * @param {number} [timeoutMs]
 * @returns {Promise<string[]>}
 */
function getTopPatterns(domain, baseUrl, timeoutMs) {
  return queryDomain(domain, baseUrl, timeoutMs).then(function(data) {
    if (!data.available) return [];
    return (data.top_patterns && Array.isArray(data.top_patterns))
      ? data.top_patterns
      : [];
  });
}

/**
 * Check whether BMID is running and healthy.
 * Resolves true if healthy, false otherwise.
 *
 * @param {string} [baseUrl]
 * @param {number} [timeoutMs]
 * @returns {Promise<boolean>}
 */
function healthCheck(baseUrl, timeoutMs) {
  baseUrl   = baseUrl   || DEFAULT_BASE_URL;
  timeoutMs = timeoutMs || DEFAULT_TIMEOUT_MS;
  return getJson(baseUrl + '/api/v1/health', timeoutMs)
    .then(function(data) { return data.status === 'ok'; })
    .catch(function()    { return false; });
}

// ---------------------------------------------------------------------------

module.exports = {
  queryDomain:    queryDomain,
  getTopPatterns: getTopPatterns,
  healthCheck:    healthCheck
};
