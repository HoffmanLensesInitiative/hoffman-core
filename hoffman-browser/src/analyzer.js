/**
 * analyzer.js
 * Hoffman Browser -- LLM analysis utilities
 *
 * Exports pure utility functions used by main.js in the analysis pipeline.
 * The model call itself (completeJson) lives in model-manager.js.
 * The BMID query lives in bmid-context.js.
 *
 * Architecture note -- DO NOT CHANGE:
 * There is no pre-screening layer. hl-detect has no role here.
 * The model reads everything and returns what it finds.
 * See HOFFMAN.md Decisions Log 2026-03-29. This is settled.
 */

'use strict';

// JSON schema for grammar-constrained output.
// Passed to ModelManager.completeJson() -- model cannot output non-JSON tokens.
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
          severity:    { type: 'string' }
        },
        required: ['quote', 'technique', 'explanation', 'severity']
      }
    }
  },
  required: ['manipulation_found', 'summary', 'flags']
};

// Base system prompt -- no BMID context.
// When bmidContext is provided it is prepended by buildSystemPrompt().
var BASE_SYSTEM_PROMPT = [
  'You are a manipulation detection expert. Your task is to read web page text',
  'and identify behavioral manipulation techniques.',
  '',
  'Manipulation techniques to look for:',
  '  outrage_engineering   - language designed to provoke anger and partisan identity',
  '  false_urgency         - artificial time pressure with no real deadline',
  '  incomplete_hook       - withheld information to force a click or action',
  '  suppression_framing   - framing that delegitimizes or suppresses opposing views',
  '  false_authority       - unverified or inflated authority claims',
  '  tribal_activation     - in-group/out-group identity pressure',
  '  engagement_directive  - instructions to sign, donate, share, call, or take action',
  '  war_framing           - conflict and battle framing applied to non-military topics',
  '  fear_amplification    - systematic inflation of threat magnitude',
  '  identity_threat       - framing that positions the reader\'s identity as under attack',
  '  social_proof_pressure - manufactured consensus to pressure conformity',
  '  scarcity_signal       - false or inflated scarcity claims',
  '',
  'Return only valid JSON matching the schema. For each flag, quote the exact text,',
  'name the technique, explain why it is manipulative, and rate severity as',
  'LOW, MEDIUM, HIGH, or CRITICAL.',
  '',
  'If no manipulation is found, return manipulation_found: false, empty flags array,',
  'and a brief summary explaining what the text does.',
  '',
  'Flag a technique whenever it is present. The legitimacy of the cause does not',
  'matter -- engagement_directive on an anti-war site is still engagement_directive.',
  'Only skip flagging if the text is purely factual with no persuasion tactics.'
].join('\n');

/**
 * Truncate text to fit within a safe token budget.
 * 2400 chars fits the 4096-token context alongside the system prompt.
 *
 * @param {string} text
 * @param {number} maxChars
 * @returns {string}
 */
function truncateText(text, maxChars) {
  if (!text) return '';
  text = text.trim();
  if (text.length <= maxChars) return text;
  return text.substring(0, maxChars) + '\n[... text truncated for analysis ...]';
}

/**
 * Build the full system prompt for a model call.
 * If bmidContext is provided, it is prepended as a clearly labelled section.
 * The model is instructed to use it as background, not as a directive.
 *
 * @param {string|null} bmidContext  - optional BMID context string
 * @returns {string}
 */
function buildSystemPrompt(bmidContext) {
  if (!bmidContext || bmidContext.trim() === '') {
    return BASE_SYSTEM_PROMPT;
  }

  return [
    bmidContext,
    '',
    'Use this intelligence as background context. Identify any manipulation present',
    'in the text independently. If you find techniques not listed above, flag them.',
    '',
    BASE_SYSTEM_PROMPT
  ].join('\n');
}

/**
 * Synthesize a flag from the summary text when the model sets manipulation_found:false
 * but the summary itself signals manipulation was detected.
 * This is a known 3B model inconsistency workaround.
 *
 * @param {string} summary
 * @returns {Array<object>} zero or one synthesized flags
 */
function synthesizeFlagsFromSummary(summary) {
  if (!summary) return [];

  var lower = summary.toLowerCase();

  var signals = [
    'outrage',   'manipul',  'mislead',  'inflam',
    'fear',      'tribal',   'urgency',  'hook',
    'framing',   'authority','partisan', 'identity threat',
    'clickbait', 'war framing'
  ];

  var found = signals.filter(function(sig) {
    return lower.indexOf(sig) !== -1;
  });

  if (found.length === 0) return [];

  var techniqueMap = {
    'outrage':         'outrage_engineering',
    'fear':            'fear_amplification',
    'tribal':          'tribal_activation',
    'urgency':         'false_urgency',
    'hook':            'incomplete_hook',
    'framing':         'suppression_framing',
    'authority':       'false_authority',
    'identity threat': 'identity_threat',
    'war framing':     'war_framing',
    'partisan':        'outrage_engineering',
    'inflam':          'outrage_engineering',
    'mislead':         'suppression_framing',
    'clickbait':       'incomplete_hook',
    'manipul':         'outrage_engineering'
  };

  var technique = 'manipulation_detected';
  for (var i = 0; i < found.length; i++) {
    if (techniqueMap[found[i]]) {
      technique = techniqueMap[found[i]];
      break;
    }
  }

  return [{
    quote:       '[extracted from model summary -- exact quote unavailable]',
    technique:   technique,
    explanation: summary,
    severity:    'MEDIUM',
    synthesized: true
  }];
}

module.exports = {
  ANALYSIS_SCHEMA:            ANALYSIS_SCHEMA,
  BASE_SYSTEM_PROMPT:         BASE_SYSTEM_PROMPT,
  buildSystemPrompt:          buildSystemPrompt,
  truncateText:               truncateText,
  synthesizeFlagsFromSummary: synthesizeFlagsFromSummary
};
