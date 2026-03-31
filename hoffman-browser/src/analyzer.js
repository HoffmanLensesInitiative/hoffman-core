/**
 * hoffman-browser/src/analyzer.js
 * LLM analysis pipeline for the Hoffman Browser.
 *
 * Pipeline:
 *   page text (+ optional BMID context) -> local Llama model -> structured JSON -> flags
 *
 * Architecture constraint (HOFFMAN.md 2026-03-29):
 *   ONE model call. Full page text in. Grammar-constrained JSON out.
 *   No pre-screening. No hl-detect. The model is the sole detector.
 *
 * BMID context (HOFFMAN_BUILD_BROWSER.md item 1):
 *   If bmidContext is supplied, it is prepended to the system prompt.
 *   It informs the model; it does not constrain what the model may find.
 *   Model must still find manipulation independently.
 *
 * Novel technique flagging (HOFFMAN_BUILD_BROWSER.md item 2):
 *   After analysis, each flag is compared against BMID's documented top_patterns.
 *   Flags not in that list receive novel:true.
 *
 * ASCII-clean: no unicode above codepoint 127.
 */

'use strict';

var { getLlamaInstance } = require('./model-manager');
var prompts              = require('./prompts');

// ---------------------------------------------------------------------------
// Grammar schema
// ---------------------------------------------------------------------------

// Grammar-constrained JSON schema. LlamaJsonSchemaGrammar forces the model
// to output only this shape -- no prose, no markdown, no escape hatches.
var ANALYSIS_SCHEMA = {
  type: 'object',
  properties: {
    manipulation_found: { type: 'boolean' },
    summary: { type: 'string' },
    flags: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          quote:       { type: 'string' },
          technique:   { type: 'string' },
          explanation: { type: 'string' },
          severity:    { type: 'string', enum: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'] }
        },
        required: ['quote', 'technique', 'explanation', 'severity']
      }
    }
  },
  required: ['manipulation_found', 'summary', 'flags']
};

// ---------------------------------------------------------------------------
// Text truncation
// ---------------------------------------------------------------------------

// 4096 token context window. Rough estimate: 1 token ~= 4 chars.
// Reserve ~800 tokens for system prompt + response headroom.
// Remaining: ~3296 tokens -> ~13184 chars for page text.
var MAX_TEXT_CHARS = 13000;

/**
 * Truncate text to fit within the model's context window.
 * Preserves the beginning and end of the document (titles and CTAs
 * often carry the most manipulation signal).
 *
 * @param {string} text
 * @returns {string}
 */
function truncateText(text) {
  if (!text || text.length <= MAX_TEXT_CHARS) return text || '';

  // Take first 75% from the front, last 25% from the back.
  var frontLen = Math.floor(MAX_TEXT_CHARS * 0.75);
  var backLen  = MAX_TEXT_CHARS - frontLen;
  var front    = text.slice(0, frontLen);
  var back     = text.slice(text.length - backLen);
  return front + '\n\n[... content truncated for analysis ...]\n\n' + back;
}

// ---------------------------------------------------------------------------
// Summary fallback -- handles 3B model inconsistency
// ---------------------------------------------------------------------------

// Phrases in the summary field that strongly signal manipulation even when
// manipulation_found is false (known 3B model inconsistency).
var SUMMARY_SIGNAL_PHRASES = [
  'outrage', 'fear', 'manipulat', 'tribal', 'us vs', 'us-vs', 'them',
  'emotionally charged', 'emotional language', 'designed to', 'intended to',
  'provoke', 'incite', 'inflame', 'sensational', 'war framing', 'urgency',
  'suppress', 'false authority', 'engagement bait', 'click', 'share this',
  'mislead', 'deceptive', 'radicali'
];

/**
 * Returns true if the summary text contains any manipulation signal phrases.
 *
 * @param {string} summary
 * @returns {boolean}
 */
function summarySignalsManipulation(summary) {
  if (!summary) return false;
  var lower = summary.toLowerCase();
  for (var i = 0; i < SUMMARY_SIGNAL_PHRASES.length; i++) {
    if (lower.indexOf(SUMMARY_SIGNAL_PHRASES[i]) !== -1) {
      return true;
    }
  }
  return false;
}

/**
 * Synthesize a flag from the summary when manipulation_found is false but
 * the summary text contradicts that assessment.
 *
 * @param {string} summary
 * @returns {object}  A flag object compatible with ANALYSIS_SCHEMA
 */
function synthesizeFlagFromSummary(summary) {
  return {
    quote:       summary.slice(0, 200),
    technique:   'unspecified_manipulation',
    explanation: summary,
    severity:    'MEDIUM',
    synthesized: true   // internal marker -- not in schema but harmless
  };
}

// ---------------------------------------------------------------------------
// Novel technique detection
// ---------------------------------------------------------------------------

/**
 * Mark flags that describe techniques not in BMID's documented top_patterns
 * for this domain. Adds novel:true to each such flag.
 *
 * @param {object[]} flags        Parsed flags from model output
 * @param {object|null} bmidData  Raw BMID intel response (may be null)
 * @returns {object[]}            Flags with novel property set
 */
function applyNovelFlags(flags, bmidData) {
  if (!flags || flags.length === 0) return flags;

  // Extract documented patterns from BMID intel response.
  // The /explain endpoint returns top_patterns in catch_summary or as a
  // top-level array. Try both locations.
  var documented = [];

  if (bmidData) {
    // Top-level top_patterns array
    if (Array.isArray(bmidData.top_patterns)) {
      documented = documented.concat(bmidData.top_patterns);
    }
    // catch_summary.top_patterns
    if (bmidData.catch_summary && Array.isArray(bmidData.catch_summary.top_patterns)) {
      documented = documented.concat(bmidData.catch_summary.top_patterns);
    }
    // motives[].type fields also carry technique vocabulary
    if (Array.isArray(bmidData.motives)) {
      bmidData.motives.forEach(function (m) {
        if (m.type) documented.push(m.type);
      });
    }
  }

  // Normalize to lowercase for comparison
  var docLower = documented.map(function (p) {
    return typeof p === 'string' ? p.toLowerCase().trim() : '';
  });

  return flags.map(function (flag) {
    var technique = (flag.technique || '').toLowerCase().trim();
    var isDocumented = docLower.some(function (d) {
      return d && (d === technique || technique.indexOf(d) !== -1 || d.indexOf(technique) !== -1);
    });
    return Object.assign({}, flag, { novel: !isDocumented && documented.length > 0 });
  });
}

// ---------------------------------------------------------------------------
// System prompt builder
// ---------------------------------------------------------------------------

/**
 * Build the system prompt, optionally prepending BMID intelligence context.
 *
 * @param {object|null} bmidContext  Formatted BMID intel (see buildBmidContextString)
 * @returns {string}
 */
function buildSystemPrompt(bmidContext) {
  var base = prompts.getAnalysisSystemPrompt();

  if (!bmidContext) return base;

  var intel = buildBmidContextString(bmidContext);
  if (!intel) return base;

  return intel + '\n\n' + base;
}

/**
 * Format BMID intel data into a system prompt prefix.
 * Returns empty string if data is insufficient to add value.
 *
 * @param {object} data  Raw BMID /explain response
 * @returns {string}
 */
function buildBmidContextString(data) {
  if (!data) return '';

  // Require at minimum a fisherman record and intelligence level
  if (!data.fisherman || data.intelligence_level === 'none') return '';

  var lines = [
    'KNOWN INTELLIGENCE ON THIS DOMAIN:',
    'Owner: '          + (data.fisherman.owner          || 'unknown'),
    'Business model: ' + (data.fisherman.business_model || 'unknown')
  ];

  // Primary motive
  if (Array.isArray(data.motives) && data.motives.length > 0) {
    lines.push('Documented primary motive: ' + data.motives[0].description);
  }

  // Documented harm count
  if (data.catch_summary && typeof data.catch_summary.total_documented === 'number') {
    lines.push('Documented harms on record: ' + data.catch_summary.total_documented + ' cases');
  }

  // Known techniques
  var patterns = [];
  if (Array.isArray(data.top_patterns) && data.top_patterns.length > 0) {
    patterns = data.top_patterns;
  } else if (data.catch_summary && Array.isArray(data.catch_summary.top_patterns)) {
    patterns = data.catch_summary.top_patterns;
  }
  if (patterns.length > 0) {
    lines.push('Known techniques: ' + patterns.slice(0, 5).join(', '));
  }

  lines.push('Use this intelligence as background context. Identify ALL manipulation present, whether or not it matches known patterns.');

  return lines.join('\n');
}

// ---------------------------------------------------------------------------
// Core analysis function
// ---------------------------------------------------------------------------

/**
 * Analyze page text using the local LLM.
 *
 * @param {string}      pageText    Extracted text from the page
 * @param {object|null} bmidData    Raw BMID intel response (may be null)
 * @returns {Promise<object>}       Structured analysis result
 *
 * Return shape:
 * {
 *   manipulation_found: boolean,
 *   summary: string,
 *   flags: [{ quote, technique, explanation, severity, novel, synthesized? }],
 *   bmid_context_used: boolean,
 *   processing_time_ms: number,
 *   text_length: number,
 *   model_version: string
 * }
 */
async function analyze(pageText, bmidData) {
  var startTime = Date.now();
  var bmidContextUsed = false;

  // --- Build input ----------------------------------------------------------
  var textToAnalyze = truncateText(pageText || '');

  if (!textToAnalyze || textToAnalyze.trim().length < 20) {
    return {
      manipulation_found: false,
      summary:            'Page contained insufficient text for analysis.',
      flags:              [],
      bmid_context_used:  false,
      processing_time_ms: Date.now() - startTime,
      text_length:        (pageText || '').length,
      model_version:      'Llama-3.2-3B-Instruct-Q4_K_M'
    };
  }

  // --- Build system prompt -------------------------------------------------
  var contextString = '';
  if (bmidData && bmidData.intelligence_level && bmidData.intelligence_level !== 'none') {
    contextString    = buildBmidContextString(bmidData);
    bmidContextUsed  = contextString.length > 0;
  }
  var systemPrompt = buildSystemPrompt(bmidContextUsed ? bmidData : null);

  // --- Model call ----------------------------------------------------------
  var result = null;
  try {
    var llama = getLlamaInstance();
    if (!llama) throw new Error('Model not loaded');

    result = await llama.completeJson(
      systemPrompt,
      'Analyze the following page text for behavioral manipulation:\n\n' + textToAnalyze,
      ANALYSIS_SCHEMA
    );
  } catch (e) {
    console.error('[Hoffman Analyzer] Model error:', e.message);
    return {
      manipulation_found: false,
      summary:            'Analysis failed: ' + e.message,
      flags:              [],
      bmid_context_used:  bmidContextUsed,
      processing_time_ms: Date.now() - startTime,
      text_length:        textToAnalyze.length,
      model_version:      'Llama-3.2-3B-Instruct-Q4_K_M',
      error:              true
    };
  }

  // --- Handle 3B model inconsistency (summary contradicts manipulation_found) --
  var flags = Array.isArray(result.flags) ? result.flags : [];

  if (!result.manipulation_found && flags.length === 0) {
    if (summarySignalsManipulation(result.summary)) {
      console.log('[Hoffman Analyzer] Summary-flag synthesis triggered');
      flags = [synthesizeFlagFromSummary(result.summary)];
      result.manipulation_found = true;
    }
  }

  // --- Novel technique flagging -------------------------------------------
  flags = applyNovelFlags(flags, bmidData);

  var processingTime = Date.now() - startTime;

  console.log('[Hoffman Analyzer] Done. manipulation_found=' + result.manipulation_found +
    ', flags=' + flags.length +
    ', novel=' + flags.filter(function (f) { return f.novel; }).length +
    ', bmid_context=' + bmidContextUsed +
    ', ms=' + processingTime);

  return {
    manipulation_found: result.manipulation_found || flags.length > 0,
    summary:            result.summary || '',
    flags:              flags,
    bmid_context_used:  bmidContextUsed,
    processing_time_ms: processingTime,
    text_length:        textToAnalyze.length,
    model_version:      'Llama-3.2-3B-Instruct-Q4_K_M'
  };
}

// ---------------------------------------------------------------------------

module.exports = {
  analyze:                    analyze,
  truncateText:               truncateText,
  summarySignalsManipulation: summarySignalsManipulation,
  synthesizeFlagFromSummary:  synthesizeFlagFromSummary,
  applyNovelFlags:            applyNovelFlags,
  buildBmidContextString:     buildBmidContextString,
  ANALYSIS_SCHEMA:            ANALYSIS_SCHEMA
};
