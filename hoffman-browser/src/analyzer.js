/**
 * analyzer.js
 * Hoffman Browser -- LLM analysis pipeline
 *
 * Sends page text to the local Llama model and returns structured flags.
 * One model call. Full page text in. Grammar-constrained JSON out.
 *
 * Updated: BMID context injection support.
 * analyzeWithModel() now accepts an optional bmidContext string.
 * If present, it is prepended to the system prompt before the model runs.
 *
 * Architecture note -- DO NOT CHANGE:
 * There is no pre-screening layer. hl-detect has no role here.
 * The model reads everything and returns what it finds.
 * See HOFFMAN.md Decisions Log 2026-03-29. This is settled.
 */

'use strict';

var modelManager = require('./model-manager');

// JSON schema for grammar-constrained output
// The model cannot output non-JSON when this grammar is active
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
          quote:        { type: 'string' },
          technique:    { type: 'string' },
          explanation:  { type: 'string' },
          severity:     { type: 'string' }
        },
        required: ['quote', 'technique', 'explanation', 'severity']
      }
    }
  },
  required: ['manipulation_found', 'summary', 'flags']
};

// Base system prompt -- no BMID context
// When bmidContext is provided it is prepended to this string
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
  '  engagement_directive  - explicit instructions to share, like, comment, or react',
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
  'Do not flag factual news reporting, academic writing, or personal posts',
  'that use emotional language in appropriate context.'
].join('\n');

/**
 * Truncate text to fit within a safe token budget.
 * Llama 3.2 3B has a 2048-token context; with prompt overhead ~1200 chars is safe.
 * Larger models can handle more -- this is conservative.
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
 *
 * @param {string} [bmidContext]  - optional context string from BMID
 * @returns {string}
 */
function buildSystemPrompt(bmidContext) {
  if (!bmidContext || bmidContext.trim() === '') {
    return BASE_SYSTEM_PROMPT;
  }

  return [
    bmidContext,
    '',
    'Use this intelligence as background context. The techniques above are documented',
    'for this domain -- but identify any manipulation present in the text independently.',
    'If you find techniques not listed above, flag them.',
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

  // Signal words that indicate the model found something despite the false flag
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

  // Attempt to extract a technique name from the summary
  var techniqueMap = {
    'outrage':        'outrage_engineering',
    'fear':           'fear_amplification',
    'tribal':         'tribal_activation',
    'urgency':        'false_urgency',
    'hook':           'incomplete_hook',
    'framing':        'suppression_framing',
    'authority':      'false_authority',
    'identity threat':'identity_threat',
    'war framing':    'war_framing',
    'partisan':       'outrage_engineering',
    'inflam':         'outrage_engineering',
    'mislead':        'suppression_framing',
    'clickbait':      'incomplete_hook',
    'manipul':        'outrage_engineering'
  };

  var technique = 'manipulation_detected';
  for (var i = 0; i < found.length; i++) {
    if (techniqueMap[found[i]]) {
      technique = techniqueMap[found[i]];
      break;
    }
  }

  return [{
    quote: '[extracted from model summary -- exact quote unavailable]',
    technique: technique,
    explanation: summary,
    severity: 'MEDIUM',
    synthesized: true
  }];
}

/**
 * Parse the model's JSON output into a normalized result object.
 * Handles both clean JSON output and text-wrapped JSON.
 *
 * @param {string} raw   - raw model output
 * @returns {object}     - normalized analysis result
 */
function parseModelOutput(raw) {
  if (!raw) {
    return { manipulation_found: false, summary: 'No output from model.', flags: [] };
  }

  var parsed;
  try {
    parsed = JSON.parse(raw.trim());
  } catch (e) {
    // Model may have wrapped JSON in prose -- try to extract
    var match = raw.match(/\{[\s\S]*\}/);
    if (match) {
      try {
        parsed = JSON.parse(match[0]);
      } catch (e2) {
        return {
          manipulation_found: false,
          summary: 'Model output could not be parsed.',
          flags: [],
          parseError: true
        };
      }
    } else {
      return {
        manipulation_found: false,
        summary: 'Model output was not valid JSON.',
        flags: [],
        parseError: true
      };
    }
  }

  // Normalize
  var result = {
    manipulation_found: !!parsed.manipulation_found,
    summary: parsed.summary || '',
    flags: Array.isArray(parsed.flags) ? parsed.flags : []
  };

  // Workaround: model says false but summary signals manipulation
  if (!result.manipulation_found && result.flags.length === 0) {
    var synthesized = synthesizeFlagsFromSummary(result.summary);
    if (synthesized.length > 0) {
      result.manipulation_found = true;
      result.flags = synthesized;
      result.synthesizedFromSummary = true;
    }
  }

  return result;
}

/**
 * Run the full analysis pipeline for a page.
 *
 * @param {string} pageText     - extracted text from the page
 * @param {string} [bmidContext] - optional context string from BMID
 * @returns {Promise<object>}   - analysis result
 */
async function analyzeWithModel(pageText, bmidContext) {
  var model = modelManager.getModel();
  if (!model) {
    throw new Error('Model not loaded. Call modelManager.loadModel() first.');
  }

  var maxChars = 1200;
  var truncated = truncateText(pageText, maxChars);

  var systemPrompt = buildSystemPrompt(bmidContext || '');

  var userMessage = 'Analyze this web page text for manipulation:\n\n' + truncated;

  console.log('[Hoffman] Starting analysis' +
    (bmidContext ? ' (with BMID context)' : ' (no BMID context)') +
    ', text length: ' + truncated.length + ' chars');

  var startTime = Date.now();

  var raw;
  try {
    raw = await model.completeJson(
      systemPrompt,
      userMessage,
      ANALYSIS_SCHEMA
    );
  } catch (e) {
    console.error('[Hoffman] Model error:', e.message);
    throw e;
  }

  var elapsed = Date.now() - startTime;
  console.log('[Hoffman] Analysis complete in ' + elapsed + 'ms');

  var result = parseModelOutput(raw);
  result.processingTimeMs = elapsed;

  console.log('[Hoffman] manipulation_found:', result.manipulation_found,
    '| flags:', result.flags.length,
    result.synthesizedFromSummary ? '| (synthesized from summary)' : '');

  return result;
}

/**
 * Convenience wrapper -- analyze a page given pre-extracted text and optional BMID data.
 *
 * @param {string}      pageText
 * @param {object|null} bmidData  - full BMID /explain response (or null)
 * @returns {Promise<object>}
 */
async function analyze(pageText, bmidData) {
  var bmidContextModule = require('./bmid-context');
  var contextStr = bmidData ? bmidContextModule.buildContextString(bmidData) : '';
  return analyzeWithModel(pageText, contextStr);
}

module.exports = {
  analyze: analyze,
  analyzeWithModel: analyzeWithModel,
  buildSystemPrompt: buildSystemPrompt,
  parseModelOutput: parseModelOutput,
  truncateText: truncateText
};
