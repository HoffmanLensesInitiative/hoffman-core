/**
 * bmid-prefetch.js
 * Hoffman Browser -- BMID domain intelligence prefetch
 *
 * Queries the BMID /explain endpoint for a given domain and returns
 * the raw response data. Designed to run in parallel with text extraction.
 *
 * Timeout: 2000ms. On timeout or any error, resolves with null.
 * BMID context is enrichment -- never a requirement.
 * If BMID is not running, the browser proceeds without context.
 */

'use strict';

var http = require('http');

var BMID_HOST    = 'localhost';
var BMID_PORT    = 5000;
var BMID_TIMEOUT = 2000; // ms -- if BMID doesn't respond, proceed without context

/**
 * Fetch BMID intelligence for the given domain.
 *
 * @param {string} domain  - hostname only, e.g. 'foxnews.com' (no protocol, no path)
 * @returns {Promise<object|null>}  resolves with response data or null on failure
 */
function fetchBmidContext(domain) {
  return new Promise(function(resolve) {
    if (!domain || typeof domain !== 'string') {
      resolve(null);
      return;
    }

    // Strip www. prefix so that www.foxnews.com and foxnews.com both match
    var cleanDomain = domain.replace(/^www\./, '');

    var path = '/api/v1/explain?domain=' + encodeURIComponent(cleanDomain);

    var options = {
      hostname: BMID_HOST,
      port:     BMID_PORT,
      path:     path,
      method:   'GET',
      headers:  { 'Accept': 'application/json' }
    };

    var timedOut = false;
    var responded = false;

    var req = http.request(options, function(res) {
      var chunks = [];

      res.on('data', function(chunk) {
        chunks.push(chunk);
      });

      res.on('end', function() {
        if (timedOut) return;
        responded = true;

        if (res.statusCode !== 200) {
          console.log('[Hoffman] BMID returned status ' + res.statusCode + ' for domain: ' + cleanDomain);
          resolve(null);
          return;
        }

        try {
          var body = Buffer.concat(chunks).toString('utf8');
          var data = JSON.parse(body);
          console.log('[Hoffman] BMID context fetched for domain: ' + cleanDomain +
            ' (intelligence_level: ' + (data.intelligence_level || 'unknown') + ')');
          resolve(data);
        } catch (parseErr) {
          console.log('[Hoffman] BMID response parse error for domain: ' + cleanDomain + ' -- ' + parseErr.message);
          resolve(null);
        }
      });

      res.on('error', function(err) {
        if (timedOut) return;
        console.log('[Hoffman] BMID response error for domain: ' + cleanDomain + ' -- ' + err.message);
        resolve(null);
      });
    });

    req.on('error', function(err) {
      if (timedOut) return;
      // ECONNREFUSED is normal when BMID is not running -- log quietly
      if (err.code === 'ECONNREFUSED') {
        console.log('[Hoffman] BMID not running -- proceeding without context');
      } else {
        console.log('[Hoffman] BMID request error: ' + err.message);
      }
      resolve(null);
    });

    // Set socket timeout
    req.setTimeout(BMID_TIMEOUT, function() {
      timedOut = true;
      req.destroy();
      if (!responded) {
        console.log('[Hoffman] BMID query timed out for domain: ' + cleanDomain + ' -- proceeding without context');
        resolve(null);
      }
    });

    req.end();
  });
}

module.exports = {
  fetchBmidContext: fetchBmidContext
};
