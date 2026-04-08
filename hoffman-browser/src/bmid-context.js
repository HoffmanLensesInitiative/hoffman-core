/**
 * bmid-context.js
 * Hoffman Browser -- BMID context enrichment for the analysis pipeline
 *
 * Queries BMID before each analysis run. Returns:
 *   - context: a plain-text string prepended to the model's system prompt
 *   - knownTechniques: array of technique strings documented for this fisherman
 *
 * If BMID is unavailable, offline, or the domain is unknown, returns empty
 * values so the pipeline continues unchanged. BMID context is enrichment,
 * never a requirement.
 *
 * Architecture note:
 * This module is called once per analysis, in parallel with DOM text extraction.
 * It has a hard 2-second timeout. It never throws -- all errors return empty enrichment.
 */

'use strict';

var http = require('http');

var BMID_HOST    = '127.0.0.1';
var BMID_PORT    = 5000;
var BMID_TIMEOUT = 2000; // ms

// Empty enrichment returned on any failure or unknown domain.
var EMPTY_ENRICHMENT = {
  context:         null,
  knownTechniques: []
};

/**
 * Perform a GET request to the local BMID API.
 * Returns parsed JSON or rejects on timeout/error.
 *
 * @param {string} path  - e.g. '/api/v1/explain?domain=foxnews.com'
 * @returns {Promise<object>}
 */
function bmidGet(path) {
  return new Promise(function(resolve, reject) {
    var options = {
      hostname: BMID_HOST,
      port:     BMID_PORT,
      path:     path,
      method:   'GET',
      headers:  { 'Accept': 'application/json' }
    };

    var req = http.request(options, function(res) {
      var body = '';
      res.setEncoding('utf8');
      res.on('data', function(chunk) { body += chunk; });
      res.on('end', function() {
        try {
          resolve(JSON.parse(body));
        } catch (e) {
          reject(new Error('BMID JSON parse error: ' + e.message));
        }
      });
    });

    req.on('error', function(e) {
      reject(new Error('BMID request error: ' + e.message));
    });

    req.setTimeout(BMID_TIMEOUT, function() {
      req.destroy();
      reject(new Error('BMID request timed out after ' + BMID_TIMEOUT + 'ms'));
    });

    req.end();
  });
}

/**
 * Extract known technique strings from a BMID explain response.
 * Looks in motives for motive_type values, and in top_patterns if present.
 * Returns a lowercase array suitable for novelty comparison.
 *
 * @param {object} data  - BMID /explain API response
 * @returns {string[]}
 */
function extractKnownTechniques(data) {
  var techniques = [];

  // Motive types double as technique categories
  if (Array.isArray(data.motives)) {
    data.motives.forEach(function(m) {
      if (m.motive_type) {
        techniques.push(m.motive_type.toLowerCase());
      }
    });
  }

  // top_patterns is explicitly provided by some BMID responses
  if (Array.isArray(data.top_patterns)) {
    data.top_patterns.forEach(function(p) {
      var name = (typeof p === 'string') ? p : (p.pattern_type || p.technique || '');
      if (name) techniques.push(name.toLowerCase());
    });
  }

  // Deduplicate
  return techniques.filter(function(v, i, a) { return a.indexOf(v) === i; });
}

/**
 * Build the context string prepended to the model system prompt.
 * Written in plain, direct language the model can read as background.
 *
 * @param {object} data  - BMID /explain API response
 * @param {string} domain
 * @returns {string|null}  null if no useful intelligence available
 */
function buildContextString(data, domain) {
  if (!data || data.intelligence_level === 'none') return null;

  var f = data.fisherman || {};
  var lines = [];

  lines.push('KNOWN INTELLIGENCE ON THIS DOMAIN:');

  if (f.display_name || f.owner || domain) {
    var ownerLine = 'Publisher: ' + (f.display_name || domain);
    if (f.owner && f.owner !== f.display_name) {
      ownerLine += ' (owned by ' + f.owner + ')';
    }
    lines.push(ownerLine);
  }

  if (f.business_model) {
    lines.push('Business model: ' + f.business_model.replace(/_/g, ' '));
  }

  if (Array.isArray(data.motives) && data.motives.length > 0) {
    // Lead with the highest-confidence motive
    var motive = data.motives[0];
    if (motive.description || motive.motive_type) {
      lines.push('Primary documented motive: ' + (motive.description || motive.motive_type));
    }
    if (data.motives.length > 1) {
      var additionalTypes = data.motives.slice(1).map(function(m) {
        return m.motive_type || '';
      }).filter(Boolean).join(', ');
      if (additionalTypes) {
        lines.push('Additional motives: ' + additionalTypes);
      }
    }
  }

  if (data.catch_summary && data.catch_summary.total_documented > 0) {
    var n = data.catch_summary.total_documented;
    lines.push('Documented harms on record: ' + n + ' case' + (n !== 1 ? 's' : ''));
  }

  if (f.confidence_score != null) {
    var pct = Math.round(f.confidence_score * 100);
    lines.push('Intelligence confidence: ' + pct + '%');
  }

  if (lines.length <= 1) return null; // Only the header -- no useful data

  return lines.join('\n');
}

/**
 * Query BMID for domain enrichment. Returns enrichment object with context
 * string and known techniques. Never throws.
 *
 * @param {string|null} domain  - e.g. 'foxnews.com'
 * @returns {Promise<{context: string|null, knownTechniques: string[]}>}
 */
function getBmidEnrichment(domain) {
  if (!domain) {
    return Promise.resolve(EMPTY_ENRICHMENT);
  }

  var encodedDomain = encodeURIComponent(domain);
  var apiPath = '/api/v1/explain?domain=' + encodedDomain;

  return bmidGet(apiPath).then(function(data) {
    var context         = buildContextString(data, domain);
    var knownTechniques = extractKnownTechniques(data);

    if (context) {
      console.log('[Hoffman] BMID enrichment for ' + domain + ': ' +
        knownTechniques.length + ' known techniques, ' +
        (data.catch_summary ? data.catch_summary.total_documented : 0) + ' harm records');
    } else {
      console.log('[Hoffman] BMID: no intelligence on file for ' + domain);
    }

    return {
      context:         context,
      knownTechniques: knownTechniques
    };

  }).catch(function(err) {
    // BMID offline or timed out -- proceed without context, never block analysis
    console.log('[Hoffman] BMID unavailable (' + err.message + ') -- proceeding without context');
    return EMPTY_ENRICHMENT;
  });
}

module.exports = {
  getBmidEnrichment: getBmidEnrichment
};
