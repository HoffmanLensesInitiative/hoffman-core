/**
 * bmid-context.js
 * Hoffman Browser -- BMID context enrichment for the analysis pipeline
 *
 * Queries the local BMID API for a domain and returns:
 *   context        {string}   -- prompt-ready intelligence block, or '' if none
 *   knownTechniques {string[]} -- list of technique names documented for this fisherman
 *
 * This module is called in parallel with page text extraction in main.js.
 * If BMID is unavailable (not running, timeout, unknown domain) it returns
 * empty values and analysis proceeds unchanged.
 *
 * Architecture note:
 *   Context informs the model -- it does not direct it.
 *   The model must still find manipulation independently.
 *   See HOFFMAN.md Decisions Log 2026-03-29.
 */

'use strict';

var http = require('http');

var BMID_HOST    = 'localhost';
var BMID_PORT    = 5000;
var BMID_TIMEOUT = 2000; // ms -- if no response in 2s, proceed without context

/**
 * Fetch the BMID /explain endpoint for a domain.
 * Returns the raw parsed JSON or null on any error.
 *
 * @param {string} domain  e.g. "foxnews.com"
 * @returns {Promise<object|null>}
 */
function fetchBmidExplain(domain) {
  return new Promise(function(resolve) {
    if (!domain) {
      resolve(null);
      return;
    }

    var path = '/api/v1/explain?domain=' + encodeURIComponent(domain);
    var options = {
      hostname: BMID_HOST,
      port:     BMID_PORT,
      path:     path,
      method:   'GET',
      headers:  { 'Accept': 'application/json' }
    };

    var timedOut = false;

    var req = http.request(options, function(res) {
      var body = '';
      res.setEncoding('utf8');
      res.on('data', function(chunk) { body += chunk; });
      res.on('end', function() {
        try {
          resolve(JSON.parse(body));
        } catch (e) {
          resolve(null);
        }
      });
    });

    req.on('error', function() {
      if (!timedOut) resolve(null);
    });

    req.setTimeout(BMID_TIMEOUT, function() {
      timedOut = true;
      req.abort();
      resolve(null);
    });

    req.end();
  });
}

/**
 * Extract a list of technique/motive-type strings from BMID explain data.
 * Used for novel technique detection: any flag the model finds that is NOT
 * in this list gets flagged as novel in the panel.
 *
 * Sources mined (in order):
 *   1. data.top_patterns  -- explicit pattern list if API returns one
 *   2. data.motives[].motive_type  -- motive types as proxy for known techniques
 *
 * @param {object|null} data  -- raw BMID /explain response
 * @returns {string[]}
 */
function extractKnownTechniques(data) {
  if (!data) return [];

  var techniques = [];

  // Explicit pattern list (future BMID feature, guarded)
  if (Array.isArray(data.top_patterns)) {
    data.top_patterns.forEach(function(p) {
      if (typeof p === 'string' && p.length > 0) techniques.push(p.toLowerCase());
      else if (p && typeof p.technique === 'string') techniques.push(p.technique.toLowerCase());
    });
  }

  // Motive types as fallback (present in current BMID v0.1 schema)
  if (Array.isArray(data.motives)) {
    data.motives.forEach(function(m) {
      if (m && typeof m.motive_type === 'string' && m.motive_type.length > 0) {
        techniques.push(m.motive_type.toLowerCase());
      }
    });
  }

  // Deduplicate
  var seen = {};
  return techniques.filter(function(t) {
    if (seen[t]) return false;
    seen[t] = true;
    return true;
  });
}

/**
 * Build a prompt-ready intelligence block from BMID explain data.
 * Returns empty string if data is null, unavailable, or intelligence_level is 'none'.
 *
 * The block is prepended to the system prompt in buildSystemPrompt() (analyzer.js).
 * It is labelled clearly so the model treats it as background intelligence,
 * not as instructions.
 *
 * @param {object|null} data  -- raw BMID /explain response
 * @param {string}      domain
 * @returns {string}
 */
function buildContextString(data, domain) {
  if (!data) return '';
  if (data.intelligence_level === 'none' || data.intelligence_level === undefined) {
    // Check if there is still usable fisherman data despite missing intelligence_level
    if (!data.fisherman || !data.fisherman.domain) return '';
  }

  var f = data.fisherman || {};
  var lines = [];

  lines.push('--- KNOWN INTELLIGENCE ON THIS DOMAIN ---');

  if (domain) {
    lines.push('Domain: ' + domain);
  }

  if (f.display_name) {
    lines.push('Publisher: ' + f.display_name);
  }

  if (f.owner) {
    lines.push('Owner: ' + f.owner);
  }

  if (f.business_model) {
    lines.push('Business model: ' + f.business_model.replace(/_/g, ' '));
  }

  // First documented motive
  if (Array.isArray(data.motives) && data.motives.length > 0) {
    var firstMotive = data.motives[0];
    if (firstMotive && firstMotive.description) {
      lines.push('Primary documented motive: ' + firstMotive.description);
    } else if (firstMotive && firstMotive.motive_type) {
      lines.push('Primary documented motive: ' + firstMotive.motive_type.replace(/_/g, ' '));
    }
    if (data.motives.length > 1) {
      var additional = data.motives.slice(1).map(function(m) {
        return m.motive_type ? m.motive_type.replace(/_/g, ' ') : null;
      }).filter(Boolean);
      if (additional.length > 0) {
        lines.push('Additional motives: ' + additional.join(', '));
      }
    }
  }

  // Documented harm count
  if (data.catch_summary && typeof data.catch_summary.total_documented === 'number') {
    var n = data.catch_summary.total_documented;
    if (n > 0) {
      lines.push('Documented harm cases on record: ' + n);
    }
  }

  // Confidence
  if (typeof f.confidence_score === 'number') {
    lines.push('Intelligence confidence: ' + Math.round(f.confidence_score * 100) + '%');
  }

  lines.push('--- END INTELLIGENCE ---');

  // If all we have is the section header and footer, return empty
  if (lines.length <= 2) return '';

  return lines.join('\n');
}

/**
 * Main export: query BMID for a domain and return enrichment data
 * ready for use in the analysis pipeline.
 *
 * Returns:
 *   {
 *     context:         string    -- prompt block for buildSystemPrompt(), or ''
 *     knownTechniques: string[]  -- technique names for novel detection, or []
 *   }
 *
 * Never throws. On any BMID error, returns { context: '', knownTechniques: [] }.
 *
 * @param {string|null} domain
 * @returns {Promise<{ context: string, knownTechniques: string[] }>}
 */
function getBmidEnrichment(domain) {
  return fetchBmidExplain(domain).then(function(data) {
    try {
      var context         = buildContextString(data, domain);
      var knownTechniques = extractKnownTechniques(data);
      return { context: context, knownTechniques: knownTechniques };
    } catch (e) {
      console.warn('[Hoffman] bmid-context: error building context string:', e.message);
      return { context: '', knownTechniques: [] };
    }
  }).catch(function(e) {
    console.warn('[Hoffman] bmid-context: unexpected error:', e.message);
    return { context: '', knownTechniques: [] };
  });
}

module.exports = {
  getBmidEnrichment:    getBmidEnrichment,
  buildContextString:   buildContextString,
  extractKnownTechniques: extractKnownTechniques
};
