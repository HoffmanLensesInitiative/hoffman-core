/**
 * bmid-context-builder.js
 * Hoffman Browser -- novel technique detection
 *
 * After the model returns analysis flags, this module compares each detected
 * technique against the set of techniques already documented in the BMID
 * for that domain. If a flag's technique is NOT in the BMID record, it is
 * marked as novel: true -- meaning the browser has found something the
 * intelligence database has not yet catalogued for this domain.
 *
 * Novel flags surface in the panel with a "NEW -- not previously documented
 * for this domain" indicator. Over time these feed back to intel agents who
 * update the BMID record.
 *
 * Public API:
 *
 *   isTechniqueNovel(technique, enrichment) -> boolean
 *
 *     technique  {string}  -- technique string from analyzer output, e.g. 'outrage_engineering'
 *     enrichment {object}  -- EnrichmentResult from getBmidEnrichment() in bmid-context.js
 *
 *     Returns true  if BMID is available for this domain AND technique is not in knownTechniques
 *     Returns false if BMID is unavailable (enrichment.available === false) OR technique is known
 *
 *   annotateFlags(flags, enrichment) -> flags[]
 *
 *     flags      {object[]}  -- array of flag objects from analyzer output
 *     enrichment {object}    -- EnrichmentResult from getBmidEnrichment()
 *
 *     Returns a new array of flag objects with novel:true added where appropriate.
 *     Does not mutate the input array.
 *
 * Design note:
 *   Novel detection only fires when BMID has a record (enrichment.available === true).
 *   If BMID has no record for the domain, we cannot say what is "known" vs. "novel" --
 *   it is all unknown. Novel is not the same as unknown.
 *   If BMID is unreachable, enrichment.available is false and no flags are marked novel.
 */

'use strict';

// ---------------------------------------------------------------------------
// Normalization
// ---------------------------------------------------------------------------

/**
 * Normalize a technique string for comparison.
 * Lower-case, trim whitespace, collapse whitespace/hyphens to underscores.
 *
 * Examples:
 *   'Outrage Engineering'  -> 'outrage_engineering'
 *   'false-urgency'        -> 'false_urgency'
 *   '  WAR_FRAMING '       -> 'war_framing'
 *
 * @param {string} s
 * @returns {string}
 */
function normalize(s) {
  if (!s || typeof s !== 'string') return '';
  return s
    .toLowerCase()
    .trim()
    .replace(/[\s\-]+/g, '_');
}

// ---------------------------------------------------------------------------
// Build known-technique lookup set from enrichment
// ---------------------------------------------------------------------------

/**
 * Convert the enrichment's knownTechniques array into a Set of normalised strings
 * for O(1) membership testing.
 *
 * @param {object} enrichment  EnrichmentResult from bmid-context.js
 * @returns {Set<string>}
 */
function buildKnownSet(enrichment) {
  var set = new Set();
  if (!enrichment || !enrichment.available) return set;
  if (!Array.isArray(enrichment.knownTechniques)) return set;
  enrichment.knownTechniques.forEach(function(t) {
    var n = normalize(t);
    if (n) set.add(n);
  });
  return set;
}

// ---------------------------------------------------------------------------
// Public: isTechniqueNovel
// ---------------------------------------------------------------------------

/**
 * Determine whether a technique is novel for this domain given current BMID state.
 *
 * @param {string} technique
 * @param {object} enrichment  EnrichmentResult
 * @returns {boolean}
 */
function isTechniqueNovel(technique, enrichment) {
  // If BMID has no record for this domain, we cannot make a novelty call.
  if (!enrichment || !enrichment.available) return false;

  var normalised = normalize(technique);
  if (!normalised) return false;

  var knownSet = buildKnownSet(enrichment);
  return !knownSet.has(normalised);
}

// ---------------------------------------------------------------------------
// Public: annotateFlags
// ---------------------------------------------------------------------------

/**
 * Add novel:true to any flag whose technique is not in the BMID record.
 * Returns a new array; does not mutate input.
 *
 * @param {object[]} flags      Array of flag objects from analyzer
 * @param {object}   enrichment EnrichmentResult from bmid-context.js
 * @returns {object[]}
 */
function annotateFlags(flags, enrichment) {
  if (!Array.isArray(flags)) return [];
  if (!enrichment || !enrichment.available) {
    // BMID unavailable: return flags unchanged, no novel annotations
    return flags.map(function(flag) {
      return Object.assign({}, flag, { novel: false });
    });
  }

  var knownSet = buildKnownSet(enrichment);

  return flags.map(function(flag) {
    var technique = (flag && flag.technique) ? flag.technique : '';
    var normalised = normalize(technique);
    var novel = (normalised !== '') && !knownSet.has(normalised);

    return Object.assign({}, flag, { novel: novel });
  });
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

module.exports = {
  isTechniqueNovel: isTechniqueNovel,
  annotateFlags: annotateFlags
};
