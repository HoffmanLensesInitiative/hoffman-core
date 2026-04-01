/**
 * bmid-context-builder.js
 * Hoffman Browser -- BMID intelligence -> system prompt context string
 *
 * Takes the raw BMID /explain response and produces two things:
 *   1. A formatted context string to prepend to the model system prompt
 *   2. A top_patterns array for novel technique detection
 *
 * Called only when intelligence_level !== 'none' and BMID data is available.
 * If data is malformed, returns null safely.
 */

'use strict';

/**
 * Build a prompt-ready context block from a BMID /explain response.
 *
 * @param {object|null} bmidData  - raw response from /api/v1/explain
 * @returns {{ contextBlock: string, topPatterns: string[] } | null}
 */
function buildBmidContext(bmidData) {
  if (!bmidData) return null;

  // If intelligence level is 'none' or missing, there is nothing useful to inject
  var level = bmidData.intelligence_level;
  if (!level || level === 'none') return null;

  var fisherman = bmidData.fisherman;
  if (!fisherman) return null;

  var lines = [];

  lines.push('KNOWN INTELLIGENCE ON THIS DOMAIN:');

  if (fisherman.owner) {
    lines.push('Owner: ' + fisherman.owner);
  }

  if (fisherman.business_model) {
    lines.push('Business model: ' + fisherman.business_model);
  }

  // First motive
  if (bmidData.motives && Array.isArray(bmidData.motives) && bmidData.motives.length > 0) {
    var motive = bmidData.motives[0];
    if (motive.description) {
      lines.push('Primary documented motive: ' + motive.description);
    }
    // Additional motives (brief)
    if (bmidData.motives.length > 1) {
      var additionalMotiveTypes = bmidData.motives.slice(1)
        .filter(function(m) { return m.motive_type; })
        .map(function(m) { return m.motive_type; })
        .join(', ');
      if (additionalMotiveTypes) {
        lines.push('Additional motive types: ' + additionalMotiveTypes);
      }
    }
  }

  // Documented harms
  if (bmidData.catch_summary) {
    var cs = bmidData.catch_summary;
    var harmCount = cs.total_documented;
    if (typeof harmCount === 'number') {
      lines.push('Documented harms on record: ' + harmCount);
    }
  }

  // Known techniques (from top_patterns or motive types)
  var topPatterns = [];

  if (bmidData.top_patterns && Array.isArray(bmidData.top_patterns) && bmidData.top_patterns.length > 0) {
    topPatterns = bmidData.top_patterns.map(function(p) {
      return typeof p === 'string' ? p : (p.pattern_type || p.name || String(p));
    });
    lines.push('Known manipulation techniques: ' + topPatterns.join(', '));
  } else if (bmidData.motives && Array.isArray(bmidData.motives)) {
    // Fallback: use motive types as pattern hints
    var motiveTypes = bmidData.motives
      .filter(function(m) { return m.motive_type; })
      .map(function(m) { return m.motive_type; });
    if (motiveTypes.length > 0) {
      topPatterns = motiveTypes;
      lines.push('Known motive types: ' + motiveTypes.join(', '));
    }
  }

  // Confidence
  if (typeof fisherman.confidence === 'number') {
    lines.push('Evidence confidence: ' + (fisherman.confidence * 100).toFixed(0) + '%');
  }

  var contextBlock = lines.join('\n');

  return {
    contextBlock: contextBlock,
    topPatterns:  topPatterns
  };
}

/**
 * Determine whether a technique returned by the model is novel --
 * i.e. not listed in BMID's documented patterns for this domain.
 *
 * @param {string}   technique   - technique string from model output
 * @param {string[]} topPatterns - known patterns from BMID context
 * @returns {boolean}
 */
function isTechniqueNovel(technique, topPatterns) {
  if (!technique || !topPatterns || topPatterns.length === 0) return false;

  var lowerTechnique = technique.toLowerCase().replace(/[_\s-]/g, '');

  for (var i = 0; i < topPatterns.length; i++) {
    var lowerPattern = topPatterns[i].toLowerCase().replace(/[_\s-]/g, '');
    if (lowerTechnique === lowerPattern) return false;
    // Substring match: 'outrage_engineering' contains 'outrage'
    if (lowerTechnique.indexOf(lowerPattern) !== -1) return false;
    if (lowerPattern.indexOf(lowerTechnique) !== -1) return false;
  }

  return true;
}

module.exports = {
  buildBmidContext:    buildBmidContext,
  isTechniqueNovel:    isTechniqueNovel
};
