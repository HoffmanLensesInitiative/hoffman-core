/**
 * bmid-context-builder.js
 * Hoffman Browser -- Novel technique detection
 *
 * After the model returns its analysis flags, this module compares each flagged
 * technique against BMID's list of known techniques for that domain. If a
 * technique is NOT in BMID's documented patterns for this fisherman, it is marked
 * as novel: true. The panel renders novel flags with a "NEW -- not previously
 * documented for this domain" badge.
 *
 * This creates a feedback path: novel findings in the browser become candidates
 * for the Intel team to investigate and add to the BMID record.
 *
 * Rules:
 *   - Only marks novel if enrichment is non-null AND knownTechniques is populated
 *   - If BMID has no record for this domain, all techniques are unmarked (not novel)
 *     because we have no baseline to compare against
 *   - Comparison is case-insensitive and handles underscore/space variation
 *   - Never throws -- errors leave flags unchanged
 *
 * Exports:
 *   isTechniqueNovel(techniqueName, enrichment) -> boolean
 *   annotateFlags(flags, enrichment) -> flags[] with novel property set
 */

'use strict';

/**
 * Normalize a technique string for comparison.
 * Lowercases, replaces spaces with underscores, trims.
 *
 * @param {string} s
 * @returns {string}
 */
function normalizeTechnique(s) {
  if (!s || typeof s !== 'string') return '';
  return s.toLowerCase().trim().replace(/\s+/g, '_');
}

/**
 * Check whether a single technique name is novel for this domain.
 * Returns true if BMID has a record for the domain AND the technique
 * is NOT in that record's known techniques list.
 *
 * Returns false (not novel / unknown) if:
 *   - enrichment is null (BMID has no record -- no baseline)
 *   - enrichment.knownTechniques is empty (no documented techniques yet)
 *   - technique is present in knownTechniques
 *
 * @param {string} techniqueName
 * @param {object|null} enrichment  from bmid-context.js getBmidEnrichment()
 * @returns {boolean}
 */
function isTechniqueNovel(techniqueName, enrichment) {
  if (!enrichment) return false;
  if (!Array.isArray(enrichment.knownTechniques)) return false;
  if (enrichment.knownTechniques.length === 0) return false;

  var normalizedInput = normalizeTechnique(techniqueName);
  if (!normalizedInput) return false;

  var normalizedKnown = enrichment.knownTechniques.map(normalizeTechnique);

  // Not novel if it appears in known list
  for (var i = 0; i < normalizedKnown.length; i++) {
    if (normalizedKnown[i] === normalizedInput) return false;
    // Also check partial containment for compound names
    // e.g. "outrage_engineering" vs "outrage" -- if known list has the root, not novel
    if (normalizedInput.indexOf(normalizedKnown[i]) !== -1) return false;
    if (normalizedKnown[i].indexOf(normalizedInput) !== -1) return false;
  }

  return true;
}

/**
 * Annotate an array of analysis flags with the novel property.
 * Mutates a shallow copy of each flag -- does not modify originals.
 *
 * @param {Array<object>} flags  Each flag has at least { technique, ... }
 * @param {object|null} enrichment  from getBmidEnrichment()
 * @returns {Array<object>}  New array, each flag has novel: boolean
 */
function annotateFlags(flags, enrichment) {
  if (!Array.isArray(flags)) return [];

  return flags.map(function (flag) {
    if (!flag || typeof flag !== 'object') return flag;

    var technique = flag.technique || flag.type || '';
    var novel = isTechniqueNovel(technique, enrichment);

    // Shallow copy with novel added
    var annotated = {};
    var keys = Object.keys(flag);
    for (var i = 0; i < keys.length; i++) {
      annotated[keys[i]] = flag[keys[i]];
    }
    annotated.novel = novel;

    if (novel) {
      console.log('[Hoffman Novel] Technique not in BMID record: ' + technique);
    }

    return annotated;
  });
}

module.exports = {
  isTechniqueNovel: isTechniqueNovel,
  annotateFlags: annotateFlags
};
