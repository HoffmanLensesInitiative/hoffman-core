/**
 * bmid-context-builder.js
 * Hoffman Browser -- Novel technique detection helper
 *
 * Provides isTechniqueNovel(technique, knownTechniques):
 *   Returns true if the model-detected technique is NOT in BMID's documented
 *   pattern list for this fisherman.
 *
 *   "Novel" means: the browser has found something that BMID does not yet have
 *   on record for this domain. It does NOT mean the technique is rare or more
 *   serious -- it means BMID's intel on this domain is incomplete or this is
 *   a newly observed behaviour.
 *
 *   Novel flags are surfaced in the panel with a "NEW" badge and create a
 *   feedback signal for the intel team.
 *
 * Also exports normalizeTechnique(str) for consistent comparison.
 *
 * Architecture note:
 *   Novel detection is a labelling step that runs AFTER the model has already
 *   returned its findings. It does not modify or filter model output.
 *   See HOFFMAN.md Decisions Log 2026-03-29.
 */

'use strict';

/**
 * Normalize a technique string for comparison.
 * Lowercases, trims, and collapses whitespace/hyphens/underscores.
 *
 * Examples:
 *   "outrage_engineering" -> "outrage engineering"
 *   "Outrage-Engineering" -> "outrage engineering"
 *   "  war_framing  "     -> "war framing"
 *
 * @param {string} str
 * @returns {string}
 */
function normalizeTechnique(str) {
  if (typeof str !== 'string') return '';
  return str
    .toLowerCase()
    .trim()
    .replace(/[-_]+/g, ' ')
    .replace(/\s+/g, ' ');
}

/**
 * Return true if the technique is NOT in the list of BMID-documented techniques
 * for the current fisherman.
 *
 * Returns false (not novel -- do not badge) when:
 *   - knownTechniques is empty (BMID unavailable or domain unknown)
 *     Rationale: we cannot call something novel if we have no baseline.
 *     An empty list means "we don't know", not "nothing is known".
 *   - technique is null, undefined, or empty string
 *   - technique normalizes to a string present in knownTechniques
 *
 * Returns true (novel -- show badge) when:
 *   - knownTechniques is non-empty AND technique is non-empty AND
 *     technique does not match anything in knownTechniques
 *
 * @param {string}   technique        -- technique string from model output
 * @param {string[]} knownTechniques  -- from getBmidEnrichment().knownTechniques
 * @returns {boolean}
 */
function isTechniqueNovel(technique, knownTechniques) {
  // Guard: no baseline means we cannot determine novelty
  if (!Array.isArray(knownTechniques) || knownTechniques.length === 0) {
    return false;
  }

  // Guard: no technique to evaluate
  if (!technique || typeof technique !== 'string' || technique.trim().length === 0) {
    return false;
  }

  var normalized = normalizeTechnique(technique);
  if (normalized.length === 0) return false;

  // Check for substring match as well as exact match
  // Rationale: model may output "war framing" while BMID stores "outrage_war_framing"
  // A substring match in either direction is sufficient to consider it documented
  for (var i = 0; i < knownTechniques.length; i++) {
    var known = normalizeTechnique(knownTechniques[i]);
    if (!known) continue;

    // Exact normalized match
    if (known === normalized) return false;

    // Substring match (technique contains known, or known contains technique)
    if (known.length >= 4 && normalized.indexOf(known) !== -1) return false;
    if (normalized.length >= 4 && known.indexOf(normalized) !== -1) return false;
  }

  return true;
}

/**
 * Annotate an array of flag objects with { novel: true/false } based on
 * comparison against knownTechniques.
 *
 * Mutates a copy of each flag -- does not modify the originals.
 *
 * @param {object[]} flags            -- model output flags
 * @param {string[]} knownTechniques  -- from getBmidEnrichment().knownTechniques
 * @returns {object[]}                -- new array with novel property added to each flag
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
  isTechniqueNovel:     isTechniqueNovel,
  normalizeTechnique:   normalizeTechnique,
  annotateNovelFlags:   annotateNovelFlags
};
