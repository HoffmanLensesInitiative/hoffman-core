/**
 * bmid-submit.js
 * Hoffman Browser -- submit analysis results to the cloud BMID.
 *
 * Privacy model:
 *   - contributor_token = SHA-256(provider + ':' + apiKey), truncated to 32 hex chars
 *   - The raw API key never leaves the device
 *   - The token is a consistent anonymous identity used only for rate limiting
 *   - Rate limit is enforced server-side: 50 submissions per token per 24 hours
 *
 * Target: https://bmid.hoffmanlenses.org/api/v1/submit
 */

'use strict';

const https  = require('https');
const crypto = require('crypto');

var BMID_CLOUD_HOST = 'bmid.hoffmanlenses.org';
var BMID_CLOUD_PATH = '/api/v1/submit';

/**
 * Derive an anonymous contributor token from the user's API key.
 * One-way hash -- server cannot recover the key from the token.
 *
 * @param {string} provider  - 'anthropic' | 'openai' | 'google'
 * @param {string} apiKey
 * @returns {string}  32-char hex string
 */
function contributorToken(provider, apiKey) {
  return crypto
    .createHash('sha256')
    .update(provider + ':' + apiKey)
    .digest('hex')
    .slice(0, 32);
}

/**
 * Submit an analysis result to the cloud BMID.
 * Only called when flags.length > 0.
 *
 * @param {object} opts
 * @param {string}   opts.domain
 * @param {string}   opts.url
 * @param {Array}    opts.flags
 * @param {string}   opts.summary
 * @param {string}   opts.provider
 * @param {string}   opts.apiKey
 * @returns {Promise<{success, submission_id}>}
 */
function submitAnalysis(opts) {
  var token = contributorToken(opts.provider, opts.apiKey);

  var body = JSON.stringify({
    domain:            opts.domain,
    url:               opts.url   || '',
    flags:             opts.flags,
    summary:           opts.summary || '',
    contributor_token: token
  });

  return new Promise(function(resolve, reject) {
    var req = https.request({
      hostname: BMID_CLOUD_HOST,
      path:     BMID_CLOUD_PATH,
      method:   'POST',
      headers: {
        'Content-Type':   'application/json',
        'Content-Length': Buffer.byteLength(body)
      }
    }, function(res) {
      var raw = '';
      res.setEncoding('utf8');
      res.on('data',  function(chunk) { raw += chunk; });
      res.on('end',   function() {
        var data;
        try { data = JSON.parse(raw); } catch(e) {
          return reject(new Error('BMID response parse error'));
        }
        if (res.statusCode === 429) {
          return reject(new Error('Daily submission limit reached'));
        }
        if (res.statusCode >= 400) {
          return reject(new Error(data.error || data.message || 'HTTP ' + res.statusCode));
        }
        resolve(data);
      });
    });

    req.on('error', reject);

    req.setTimeout(10000, function() {
      req.destroy();
      reject(new Error('Submission timed out'));
    });

    req.write(body);
    req.end();
  });
}

module.exports = { submitAnalysis };
