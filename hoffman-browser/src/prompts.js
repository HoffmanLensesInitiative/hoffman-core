/**
 * hoffman-browser/src/prompts.js
 * System prompt builder for the Hoffman Browser analysis pipeline.
 *
 * The model is the sole detector. No pre-screening. No hl-detect.
 * BMID context enriches the prompt but does not direct findings.
 * The model reads independently and reports what it finds.
 *
 * ASCII-clean: no unicode above codepoint 127.
 */

'use strict';

// ---------------------------------------------------------------------------
// Core system prompt (no BMID context)
// ---------------------------------------------------------------------------

var BASE_SYSTEM_PROMPT = [
  'You are a behavioral manipulation analyst embedded in the Hoffman Browser.',
  'Your role is to read web page text and identify language patterns designed to',
  'manipulate reader psychology rather than inform.',
  '',
  'Manipulation techniques you should recognize:',
  '  outrage_engineering    -- language calibrated to provoke rage or moral disgust',
  '  false_urgency          -- artificial time pressure to bypass rational deliberation',
  '  fear_amplification     -- exaggerated or decontextualized threat framing',
  '  tribal_activation      -- us-vs-them framing to activate group loyalty over reason',
  '  suppression_framing    -- framing that delegitimizes questions or counter-evidence',
  '  false_authority        -- credibility claims that cannot be verified or are fabricated',
  '  incomplete_hook        -- information withheld to compel continued engagement',
  '  engagement_directive   -- explicit calls to react, share, or amplify emotionally',
  '  war_framing            -- conflict metaphors applied to domestic policy or discourse',
  '  scarcity_exploitation  -- manufactured scarcity to force immediate action',
  '  identity_threat        -- content framed as threatening who the reader IS',
  '  radicalization_pathway -- incremental escalation toward extreme positions',
  '',
  'IMPORTANT CALIBRATION RULES:',
  '  - Factual news reporting with named sources is NOT manipulation',
  '  - Personal posts about daily life are NOT manipulation',
  '  - Academic or scientific writing is NOT manipulation',
  '  - Emotional language in genuinely emotional contexts (grief, celebration) is NOT manipulation',
  '  - Urgent language when urgency is genuine (emergency alerts, breaking news with facts) is NOT manipulation',
  '  - Political positions you disagree with are NOT automatically manipulation',
  '  - Authority claims with proper citations are NOT false authority',
  '',
  'Your response must be valid JSON matching this exact schema:',
  '{',
  '  "manipulation_found": boolean,',
  '  "summary": "one sentence describing overall finding",',
  '  "flags": [',
  '    {',
  '      "quote": "exact phrase from the text",',
  '      "technique": "technique_name",',
  '      "explanation": "why this phrase uses this technique",',
  '      "severity": "LOW|MEDIUM|HIGH"',
  '    }',
  '  ]',
  '}',
  '',
  'If no manipulation is found, return manipulation_found:false, empty flags array.',
  'If manipulation is found, list each instance with an exact quote.'
].join('\n');

// ---------------------------------------------------------------------------
// BMID context block builder
// ---------------------------------------------------------------------------

/**
 * Build a context string from a BMID /explain response.
 * Appended to BASE_SYSTEM_PROMPT when BMID has a record for the domain.
 *
 * @param {object} bmidData   Parsed response from GET /api/v1/explain
 * @returns {string}          Formatted context block, or empty string
 */
function buildBmidContextBlock(bmidData) {
  if (!bmidData) return '';

  var level = bmidData.intelligence_level || 'none';
  if (level === 'none') return '';

  var lines = [
    '',
    '--- KNOWN INTELLIGENCE ON THIS DOMAIN ---',
    'The following is documented intelligence from the Hoffman BMID database.',
    'Use this as context. Do not let it substitute for reading the actual page.',
    'Your findings must be grounded in the text you are given, not in this briefing.'
  ];

  var fisherman = bmidData.fisherman;
  if (fisherman) {
    if (fisherman.name) {
      lines.push('Operator: ' + fisherman.name);
    }
    if (fisherman.owner) {
      lines.push('Owner: ' + fisherman.owner);
    }
    if (fisherman.business_model) {
      lines.push('Business model: ' + fisherman.business_model);
    }
  }

  var motives = bmidData.motives;
  if (motives && motives.length > 0) {
    var primaryMotive = motives[0];
    if (primaryMotive.description) {
      lines.push('Primary documented motive: ' + primaryMotive.description);
    }
  }

  var catchSummary = bmidData.catch_summary;
  if (catchSummary && typeof catchSummary.total_documented === 'number') {
    var n = catchSummary.total_documented;
    if (n > 0) {
      lines.push('Documented harm cases on record: ' + n);
    }
  }

  var topPatterns = bmidData.top_patterns;
  if (topPatterns && topPatterns.length > 0) {
    lines.push('Techniques previously documented for this operator: ' + topPatterns.join(', '));
  }

  lines.push('--- END INTELLIGENCE BRIEFING ---');
  lines.push('');

  return lines.join('\n');
}

// ---------------------------------------------------------------------------
// Top-level prompt builder
// ---------------------------------------------------------------------------

/**
 * Build the full system prompt for a page analysis call.
 *
 * @param {object|null} bmidData  BMID /explain response, or null if unavailable
 * @returns {string}              Complete system prompt string
 */
function buildSystemPrompt(bmidData) {
  var contextBlock = buildBmidContextBlock(bmidData);
  if (!contextBlock) {
    return BASE_SYSTEM_PROMPT;
  }
  // Inject context after the technique list and before the calibration rules.
  // We find the first calibration rule line and insert before it.
  var splitPoint = BASE_SYSTEM_PROMPT.indexOf('IMPORTANT CALIBRATION RULES:');
  if (splitPoint === -1) {
    // Fallback: append at end
    return BASE_SYSTEM_PROMPT + contextBlock;
  }
  var before = BASE_SYSTEM_PROMPT.slice(0, splitPoint);
  var after  = BASE_SYSTEM_PROMPT.slice(splitPoint);
  return before + contextBlock + after;
}

/**
 * Build the user-turn content for a page analysis call.
 *
 * @param {string} pageText     Extracted page text (DOM + OCR merged)
 * @param {string} [pageTitle]  Optional page title for context
 * @returns {string}
 */
function buildUserPrompt(pageText, pageTitle) {
  var lines = [];
  if (pageTitle) {
    lines.push('Page title: ' + pageTitle);
    lines.push('');
  }
  lines.push('Analyze the following page text for behavioral manipulation:');
  lines.push('');
  lines.push(pageText);
  return lines.join('\n');
}

// ---------------------------------------------------------------------------

module.exports = {
  BASE_SYSTEM_PROMPT:    BASE_SYSTEM_PROMPT,
  buildBmidContextBlock: buildBmidContextBlock,
  buildSystemPrompt:     buildSystemPrompt,
  buildUserPrompt:       buildUserPrompt
};
