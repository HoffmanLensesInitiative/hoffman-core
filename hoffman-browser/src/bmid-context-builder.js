// hoffman-browser/src/bmid-context-builder.js
// Hoffman Browser -- novel technique detection helper.
//
// Exported function: isTechniqueNovel(technique, enrichment)
//
// After the LLM returns flags, each flag's technique is checked against the
// known techniques documented in the BMID for this domain. If the technique
// is NOT in the BMID record, it is marked novel: true in the panel so the
// user (and future intel agents) know this is new, undocumented behavior.
//
// This is a lightweight string-matching comparison. It does NOT call BMID --
// the enrichment object was already fetched before analysis ran.
//
// Contract:
//   - Never throws.
//   - If enrichment is null or has no knownTechniques, returns false.
//     (Absence of BMID data is not the same as a novel detection.)
//   - Matching is case-insensitive and trims whitespace.
//   - Partial match allowed: if any known technique is a substring of the
//     detected technique or vice versa, it is not novel. This prevents
//     false-novel labeling from minor naming variation (e.g. "outrage" vs
//     "outrage_engineering").

'use strict';

/**
 * Determine whether a detected technique is novel (not previously documented
 * in the BMID for this domain).
 *
 * @param {string} technique   Technique string from LLM flag, e.g. "outrage_engineering"
 * @param {object|null} enrichment   Enrichment object from getBmidEnrichment()
 * @returns {boolean}  true if novel (not in BMID), false if known or unknown
 */
function isTechniqueNovel(technique, enrichment) {
  // If no technique string, cannot be classified.
  if (!technique || typeof technique !== 'string') {
    return false;
  }

  // If we have no enrichment or no knownTechniques list, we cannot say it is
  // novel -- absence of BMID data is not evidence of novelty. Return false so
  // we do not label things novel when we simply have no reference data.
  if (!enrichment || !Array.isArray(enrichment.knownTechniques) ||
      enrichment.knownTechniques.length === 0) {
    return false;
  }

  var normalized = technique.trim().toLowerCase().replace(/\s+/g, '_');

  // Check each known technique for a match or partial overlap.
  var known = enrichment.knownTechniques;
  for (var i = 0; i < known.length; i++) {
    var k = known[i].trim().toLowerCase().replace(/\s+/g, '_');
    if (!k) continue;

    // Exact match.
    if (normalized === k) {
      return false;
    }

    // Substring match in either direction prevents false-novel labeling
    // from minor naming differences across BMID versions and model outputs.
    if (normalized.indexOf(k) !== -1 || k.indexOf(normalized) !== -1) {
      return false;
    }
  }

  // Not found in known techniques -- this is a novel detection.
  return true;
}

module.exports = {
  isTechniqueNovel: isTechniqueNovel
};
