/**
 * bmid-context.js
 * Hoffman Browser -- builds the BMID context string injected into the model prompt
 *
 * Takes the raw response from /api/v1/explain and returns a plain-text block
 * suitable for prepending to the model system prompt.
 *
 * If the BMID has no record for this domain, returns an empty string.
 * The caller checks for empty string before modifying the prompt.
 *
 * Design rules:
 * - Context informs the model; it does not direct it.
 * - The model must still find manipulation independently.
 * - We do NOT tell the model "this site is bad" or "expect to find X".
 * - We tell the model what is known about the site's ownership and documented
 *   motives so it can read with full context, not cold.
 * - Output is ASCII-only -- no curly quotes, em-dashes, or unicode above 127.
 */

'use strict';

/**
 * Build a BMID context string from an /explain API response.
 *
 * @param {object|null} explainResponse - parsed JSON from /api/v1/explain, or null
 * @returns {string} - context block to prepend to system prompt, or '' if none
 */
function buildBmidContextString(explainResponse) {
  if (!explainResponse) return '';

  // The /explain endpoint sets intelligence_level to 'none' when domain is unknown
  var level = explainResponse.intelligence_level;
  if (!level || level === 'none') return '';

  // Extract what we need; guard every field access
  var fisherman    = explainResponse.fisherman    || {};
  var catchSummary = explainResponse.catch_summary || {};
  var motives      = explainResponse.motives       || [];
  var topPatterns  = explainResponse.top_patterns  || [];

  var name          = safeStr(fisherman.name          || fisherman.domain);
  var owner         = safeStr(fisherman.owner);
  var businessModel = safeStr(fisherman.business_model);
  var domain        = safeStr(fisherman.domain);

  var harmCount = (typeof catchSummary.total_documented === 'number')
    ? String(catchSummary.total_documented)
    : 'unknown';

  // Build motive lines -- up to 3 motives
  var motiveLines = [];
  for (var i = 0; i < Math.min(motives.length, 3); i++) {
    var m = motives[i];
    if (m && m.description) {
      motiveLines.push('  - ' + safeStr(m.description));
    }
  }

  // Build known technique lines -- up to 5
  var techLines = [];
  for (var j = 0; j < Math.min(topPatterns.length, 5); j++) {
    var t = topPatterns[j];
    if (typeof t === 'string' && t.length > 0) {
      techLines.push('  - ' + safeStr(t));
    } else if (t && t.pattern) {
      techLines.push('  - ' + safeStr(t.pattern));
    }
  }

  // Assemble the block
  var lines = [];
  lines.push('---');
  lines.push('INTELLIGENCE ON THIS DOMAIN (' + domain + ')');
  lines.push('');

  if (name)          lines.push('Operator: '       + name);
  if (owner)         lines.push('Owner: '          + owner);
  if (businessModel) lines.push('Business model: ' + businessModel);

  if (harmCount !== 'unknown') {
    lines.push('Documented harm cases on record: ' + harmCount);
  }

  if (motiveLines.length > 0) {
    lines.push('');
    lines.push('Documented engagement motives:');
    for (var k = 0; k < motiveLines.length; k++) {
      lines.push(motiveLines[k]);
    }
  }

  if (techLines.length > 0) {
    lines.push('');
    lines.push('Previously documented content techniques:');
    for (var l = 0; l < techLines.length; l++) {
      lines.push(techLines[l]);
    }
  }

  lines.push('');
  lines.push('Use this intelligence as background context only.');
  lines.push('Analyze the page text on its own merits. Report what you find.');
  lines.push('---');

  return lines.join('\n');
}

/**
 * Sanitize a value to a plain ASCII string.
 * Returns '' for null/undefined/non-string.
 *
 * @param {*} val
 * @returns {string}
 */
function safeStr(val) {
  if (!val) return '';
  var s = String(val);
  // Replace any character above ASCII 126 with a space
  s = s.replace(/[^\x00-\x7E]/g, ' ');
  // Collapse multiple spaces
  s = s.replace(/  +/g, ' ');
  return s.trim();
}

/**
 * Given the list of flag techniques returned by the model and the set of
 * known techniques from BMID, determine which flags are novel (not previously
 * documented for this domain).
 *
 * @param {string[]} flagTechniques  - technique strings from model output
 * @param {object|null} explainResponse - parsed /explain response
 * @returns {Set<string>} - set of technique strings that are novel for this domain
 */
function identifyNovelTechniques(flagTechniques, explainResponse) {
  var novel = new Set();
  if (!flagTechniques || flagTechniques.length === 0) return novel;

  // If there is no BMID record at all, everything is potentially novel --
  // but we only mark novel when we have a record to compare against.
  // With no record, we cannot say "not previously documented for this domain".
  if (!explainResponse || explainResponse.intelligence_level === 'none') {
    return novel;
  }

  // Build a set of normalised known techniques
  var known = new Set();
  var topPatterns = explainResponse.top_patterns || [];
  for (var i = 0; i < topPatterns.length; i++) {
    var t = topPatterns[i];
    var key = '';
    if (typeof t === 'string')  key = t.toLowerCase().trim();
    else if (t && t.pattern)   key = String(t.pattern).toLowerCase().trim();
    if (key) known.add(key);
  }

  // Also absorb motive type names as known
  var motives = explainResponse.motives || [];
  for (var j = 0; j < motives.length; j++) {
    var m = motives[j];
    if (m && m.type)  known.add(String(m.type).toLowerCase().trim());
    if (m && m.label) known.add(String(m.label).toLowerCase().trim());
  }

  // Compare each flag technique against the known set
  for (var k = 0; k < flagTechniques.length; k++) {
    var tech = flagTechniques[k];
    if (!tech) continue;
    var normTech = String(tech).toLowerCase().trim();
    if (!known.has(normTech)) {
      novel.add(tech); // keep original capitalisation for display
    }
  }

  return novel;
}

module.exports = {
  buildBmidContextString:   buildBmidContextString,
  identifyNovelTechniques:  identifyNovelTechniques
};
