// hoffman-browser/src/bmid-context.js
// Hoffman Browser -- BMID context enrichment for the analysis pipeline.
//
// Exported function: getBmidEnrichment(domain)
//
// Queries the BMID API for a known fisherman record before the LLM analysis
// runs. If intelligence exists, it returns a structured enrichment object
// that main.js passes to buildSystemPrompt() and to the novel-technique check.
//
// Contract:
//   - Never throws. Always returns an enrichment object (possibly empty).
//   - If BMID is down, unreachable, or times out: returns empty enrichment.
//   - Timeout: 2 seconds. Analysis must not be blocked on BMID availability.
//   - This is enrichment, not a gate. The model analyzes independently.

'use strict';

var http = require('http');

var BMID_HOST    = 'localhost';
var BMID_PORT    = 5000;
var BMID_TIMEOUT = 2000;  // ms

// Empty enrichment returned when BMID has nothing useful.
var EMPTY_ENRICHMENT = {
  domain:         '',
  owner:          '',
  businessModel:  '',
  primaryMotive:  '',
  documentedHarms: 0,
  knownTechniques: [],
  context:        null   // null signals: no context to prepend
};

/**
 * Query BMID for intelligence on a domain and return a structured enrichment
 * object. Resolves with EMPTY_ENRICHMENT on any failure.
 *
 * @param {string|null} domain  e.g. "foxnews.com", "facebook.com"
 * @returns {Promise<object>}
 */
function getBmidEnrichment(domain) {
  if (!domain || domain.trim() === '') {
    return Promise.resolve(Object.assign({}, EMPTY_ENRICHMENT));
  }

  var clean = domain.trim().toLowerCase();

  return new Promise(function(resolve) {
    var resolved = false;

    function finish(enrichment) {
      if (resolved) return;
      resolved = true;
      resolve(enrichment);
    }

    var timer = setTimeout(function() {
      finish(Object.assign({}, EMPTY_ENRICHMENT, { domain: clean }));
    }, BMID_TIMEOUT);

    var path = '/api/v1/explain?domain=' + encodeURIComponent(clean);

    var options = {
      hostname: BMID_HOST,
      port:     BMID_PORT,
      path:     path,
      method:   'GET',
      timeout:  BMID_TIMEOUT
    };

    var req = http.request(options, function(res) {
      var body = '';

      res.on('data', function(chunk) {
        body += chunk;
      });

      res.on('end', function() {
        clearTimeout(timer);

        try {
          var data = JSON.parse(body);
          finish(buildEnrichment(clean, data));
        } catch (parseErr) {
          finish(Object.assign({}, EMPTY_ENRICHMENT, { domain: clean }));
        }
      });
    });

    req.on('timeout', function() {
      req.destroy();
      clearTimeout(timer);
      finish(Object.assign({}, EMPTY_ENRICHMENT, { domain: clean }));
    });

    req.on('error', function() {
      clearTimeout(timer);
      finish(Object.assign({}, EMPTY_ENRICHMENT, { domain: clean }));
    });

    req.end();
  });
}

/**
 * Parse a BMID /explain response into a structured enrichment object.
 * Handles missing or partial data gracefully.
 *
 * @param {string} domain
 * @param {object} data  parsed JSON from BMID
 * @returns {object}
 */
function buildEnrichment(domain, data) {
  // intelligence_level === 'none' means BMID has no record for this domain.
  if (!data || data.intelligence_level === 'none') {
    return Object.assign({}, EMPTY_ENRICHMENT, { domain: domain });
  }

  var fisherman   = data.fisherman     || {};
  var motives     = data.motives       || [];
  var catchSummary = data.catch_summary || {};

  var owner         = fisherman.owner         || fisherman.display_name || '';
  var businessModel = fisherman.business_model || '';
  var primaryMotive = motives.length > 0
    ? (motives[0].description || motives[0].motive_type || '')
    : '';
  var documentedHarms = catchSummary.total_documented || 0;

  // Extract known technique identifiers from motive types and top_patterns.
  // Both are used so we catch whatever the BMID version returns.
  var knownTechniques = [];

  if (Array.isArray(data.top_patterns)) {
    data.top_patterns.forEach(function(p) {
      var key = (typeof p === 'string') ? p : (p.technique || p.pattern || '');
      if (key && knownTechniques.indexOf(key.toLowerCase()) === -1) {
        knownTechniques.push(key.toLowerCase());
      }
    });
  }

  motives.forEach(function(m) {
    var key = m.motive_type || '';
    if (key && knownTechniques.indexOf(key.toLowerCase()) === -1) {
      knownTechniques.push(key.toLowerCase());
    }
  });

  // Build the preformatted context string for the system prompt.
  var contextLines = [
    'KNOWN INTELLIGENCE ON THIS DOMAIN:'
  ];

  if (owner) {
    contextLines.push('Owner: ' + owner);
  }
  if (businessModel) {
    contextLines.push('Business model: ' + businessModel.replace(/_/g, ' '));
  }
  if (primaryMotive) {
    contextLines.push('Documented motive: ' + primaryMotive);
  }
  if (documentedHarms > 0) {
    contextLines.push(
      'Documented harms: ' + documentedHarms + ' case' +
      (documentedHarms !== 1 ? 's' : '') + ' on record'
    );
  }
  if (knownTechniques.length > 0) {
    contextLines.push('Known techniques: ' + knownTechniques.join(', '));
  }

  // Only return a context string if we actually have content beyond the header.
  var hasContent = owner || businessModel || primaryMotive ||
                   documentedHarms > 0 || knownTechniques.length > 0;

  return {
    domain:          domain,
    owner:           owner,
    businessModel:   businessModel,
    primaryMotive:   primaryMotive,
    documentedHarms: documentedHarms,
    knownTechniques: knownTechniques,
    context:         hasContent ? contextLines.join('\n') : null
  };
}

module.exports = {
  getBmidEnrichment: getBmidEnrichment
};
