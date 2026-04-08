/**
 * bmid-context-builder.js
 * Hoffman Browser -- novel technique detection
 *
 * Compares techniques returned by the local model against techniques
 * already documented in the BMID for that fisherman. If a technique is
 * NOT in the known list, it is flagged as novel -- meaning the browser
 * has found something the database does not yet have on file.
 *
 * "Novel" does not mean certain -- it means "not previously documented
 * for this domain". It creates a feedback signal for intel agents.
 *
 * Usage:
 *   var { isTechniqueNovel } = require('./bmid-context-builder');
 *   var novel = isTechniqueNovel('outrage_engineering', knownTechniques);
 *
 * knownTechniques is the array returned by getBmidEnrichment().knownTechniques.
 * It may be empty if BMID has no record for the domain, in which case all
 * techniques are treated as novel (we have no baseline to compare against) --
 * UNLESS the fisherman file is simply new, in which case the first findings
 * are founding observations, not discoveries. To avoid false "novel" signals
 * on unknown domains, isTechniqueNovel returns false when knownTechniques is
 * empty (no baseline = no comparison = no novelty claim).
 */

'use strict';

/**
 * Normalize a technique string for comparison.
 * Lowercase, trim, replace hyphens with underscores.
 *
 * @param {string} t
 * @returns {string}
 */
function normalize(t) {
  if (!t) return '';
  return t.toLowerCase().trim().replace(/-/g, '_');
}

/**
 * Determine whether a model-returned technique is novel relative to
 * the fisherman's documented BMID pattern list.
 *
 * Returns false (not novel) if:
 *   - knownTechniques is empty (no baseline -- no comparison possible)
 *   - technique is blank or null
 *   - a normalized match is found in knownTechniques
 *
 * Returns true (novel) only if:
 *   - knownTechniques has at least one entry (baseline exists)
 *   - AND no normalized match is found
 *
 * @param {string}   technique       - technique string from model output
 * @param {string[]} knownTechniques - from getBmidEnrichment().knownTechniques
 * @returns {boolean}
 */
function isTechniqueNovel(technique, knownTechniques) {
  if (!technique) return false;
  if (!Array.isArray(knownTechniques) || knownTechniques.length === 0) return false;

  var normalized = normalize(technique);
  if (!normalized) return false;

  for (var i = 0; i < knownTechniques.length; i++) {
    var known = normalize(knownTechniques[i]);
    // Exact match
    if (known === normalized) return false;
    // Partial overlap: one contains the other (handles e.g. "outrage" vs "outrage_engineering")
    if (known.indexOf(normalized) !== -1) return false;
    if (normalized.indexOf(known) !== -1) return false;
  }

  return true;
}

/**
 * Annotate an array of flag objects with novel:true where appropriate.
 * Mutates nothing -- returns a new array with novel property added.
 *
 * @param {Array<object>} flags          - raw flags from analyzer
 * @param {string[]}      knownTechniques
 * @returns {Array<object>}
 */
function annotateNovelFlags(flags, knownTechniques) {
  if (!Array.isArray(flags)) return [];
  return flags.map(function(flag) {
    var copy = Object.assign({}, flag);
    copy.novel = isTechniqueNovel(flag.technique, knownTechniques);
    return copy;
  });
}

module.exports = {
  isTechniqueNovel:    isTechniqueNovel,
  annotateNovelFlags:  annotateNovelFlags
};
