/**
 * bmid-client.js
 * Hoffman Browser -- HTTP client for the BMID API
 *
 * All requests are fire-and-forget from the browser's perspective:
 * if BMID is not running, or times out, or returns an error, the caller
 * receives null and continues without BMID context.
 *
 * Base URL defaults to http://localhost:5000 but can be overridden via
 * the BMID_BASE_URL environment variable for testing.
 *
 * Timeout: 2 seconds for context queries (used in the analysis path).
 * Longer timeout (10s) is available for non-blocking UI queries.
 *
 * ASCII-only source -- no unicode above codepoint 127.
 */

'use strict';

var http = require('http');
var https = require('https');
var url  = require('url');

var DEFAULT_BASE_URL    = 'http://localhost:5000';
var CONTEXT_TIMEOUT_MS  = 2000;  // must not slow down analysis
var UI_TIMEOUT_MS       = 10000; // for panel "why is this here?" calls

/**
 * Return the configured base URL.
 * @returns {string}
 */
function baseUrl() {
  return (process.env.BMID_BASE_URL || DEFAULT_BASE_URL).replace(/\/$/, '');
}

/**
 * Generic HTTP GET with timeout.
 * Resolves with parsed JSON body, or null on any error/timeout.
 *
 * @param {string} path        - URL path including query string
 * @param {number} timeoutMs
 * @returns {Promise<object|null>}
 */
function get(path, timeoutMs) {
  return new Promise(function(resolve) {
    var fullUrl = baseUrl() + path;
    var parsed;

    try {
      parsed = url.parse(fullUrl);
    } catch (e) {
      console.error('[Hoffman] bmid-client: bad URL', fullUrl, e.message);
      return resolve(null);
    }

    var lib = (parsed.protocol === 'https:') ? https : http;

    var options = {
      hostname:  parsed.hostname,
      port:      parsed.port || (parsed.protocol === 'https:' ? 443 : 80),
      path:      parsed.path,
      method:    'GET',
      headers:   { 'Accept': 'application/json' }
    };

    var finished = false;

    function done(val) {
      if (finished) return;
      finished = true;
      resolve(val);
    }

    var req = lib.request(options, function(res) {
      var chunks = [];
      res.on('data', function(chunk) { chunks.push(chunk); });
      res.on('end', function() {
        try {
          var body = Buffer.concat(chunks).toString('utf8');
          var parsed = JSON.parse(body);
          done(parsed);
        } catch (e) {
          console.error('[Hoffman] bmid-client: JSON parse error', e.message);
          done(null);
        }
      });
      res.on('error', function(e) {
        console.error('[Hoffman] bmid-client: response error', e.message);
        done(null);
      });
    });

    req.on('error', function(e) {
      // ECONNREFUSED is normal when BMID is not running -- do not log as error
      if (e.code !== 'ECONNREFUSED') {
        console.error('[Hoffman] bmid-client: request error', e.message);
      }
      done(null);
    });

    req.setTimeout(timeoutMs, function() {
      console.warn('[Hoffman] bmid-client: timeout after', timeoutMs, 'ms for', path);
      req.destroy();
      done(null);
    });

    req.end();
  });
}

/**
 * Query /api/v1/explain for a domain.
 * Used in the analysis path -- 2-second timeout.
 *
 * Returns the parsed response object, or null.
 * When domain has no record, the API returns { intelligence_level: 'none' }.
 * buildBmidContextString() handles that gracefully.
 *
 * @param {string} domain  - hostname, e.g. 'foxnews.com'
 * @returns {Promise<object|null>}
 */
function queryExplain(domain) {
  if (!domain) return Promise.resolve(null);
  // Sanitise domain -- strip protocol and paths, keep hostname only
  var clean = domain.replace(/^https?:\/\//i, '').split('/')[0].toLowerCase().trim();
  if (!clean) return Promise.resolve(null);
  var path = '/api/v1/explain?domain=' + encodeURIComponent(clean);
  return get(path, CONTEXT_TIMEOUT_MS);
}

/**
 * Query /api/v1/explain for the panel "Why is this here?" display.
 * Uses the longer UI timeout so a slower BMID response is acceptable.
 *
 * @param {string} domain
 * @returns {Promise<object|null>}
 */
function queryExplainForPanel(domain) {
  if (!domain) return Promise.resolve(null);
  var clean = domain.replace(/^https?:\/\//i, '').split('/')[0].toLowerCase().trim();
  if (!clean) return Promise.resolve(null);
  var path = '/api/v1/explain?domain=' + encodeURIComponent(clean);
  return get(path, UI_TIMEOUT_MS);
}

/**
 * Health check -- resolves true if BMID is reachable, false otherwise.
 * Used at startup to log BMID status without blocking.
 *
 * @returns {Promise<boolean>}
 */
function healthCheck() {
  return get('/api/v1/health', CONTEXT_TIMEOUT_MS).then(function(res) {
    return !!(res && res.status === 'ok');
  });
}

module.exports = {
  queryExplain:        queryExplain,
  queryExplainForPanel: queryExplainForPanel,
  healthCheck:         healthCheck
};
