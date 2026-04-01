/**
 * prompts.js
 * Hoffman Browser -- LLM system prompt construction
 *
 * Builds the system prompt for each analysis call.
 * Optional BMID context is injected when available, prepended before
 * the core detection instructions.
 *
 * The BMID intelligence informs context -- it does NOT instruct the model
 * to find manipulation. The model must find it independently.
 */

'use strict';

/**
 * Core detection instruction.
 * This is always present, with or without BMID context.
 */
var CORE_INSTRUCTION = [
  'You are a behavioral manipulation analyst. Your task is to read the following',
  'web page text and identify any language techniques designed to manipulate the',
  'reader\'s emotions, beliefs, or behavior rather than inform them.',
  '',
  'Known manipulation techniques include but are not limited to:',
  '  suppression_framing   -- framing that hides key context to control the conclusion',
  '  false_urgency         -- artificial time pressure or manufactured urgency',
  '  incomplete_hook       -- withheld information to compel engagement or clicks',
  '  outrage_engineering   -- language calibrated to provoke anger or moral outrage',
  '  war_framing           -- conflict framing applied to non-conflict topics',
  '  fear_amplification    -- exaggerating threat to produce anxiety or compliance',
  '  tribal_activation     -- us-vs-them framing to activate group identity',
  '  false_authority       -- unverified or misleading authority claims',
  '  engagement_directive  -- explicit commands to share, react, or comment',
  '  manufactured_consensus -- false claims about what "everyone" thinks or does',
  '  identity_threat       -- framing that positions the reader\'s identity as under attack',
  '  moral_licensing       -- framing that makes harmful actions seem virtuous',
  '',
  'Be precise. Quote the specific text that demonstrates the technique.',
  'Do not flag straightforward factual reporting, academic writing, or',
  'personal posts about daily life.',
  'Do not flag emotional language in appropriate contexts (grief, celebration).',
  'Do not flag urgent language when urgency is genuine (emergency alerts).',
  'Do not flag political positions solely because of their political content.',
  'Do not flag authority claims when authority is properly cited.',
  '',
  'If you find manipulation, set manipulation_found to true and list each finding.',
  'If the text is clean, set manipulation_found to false and leave flags empty.',
  'Always write a brief summary of your overall finding in the summary field.'
].join('\n');

/**
 * Build the BMID intelligence context block.
 * Returns an empty string if the explainResponse is null or intelligence_level is none.
 *
 * @param {object|null} explainResponse  - from bmid-client.explain()
 * @returns {string}
 */
function buildBmidContext(explainResponse) {
  if (!explainResponse) return '';

  var level = explainResponse.intelligence_level;
  if (!level || level === 'none') return '';

  var fisherman = explainResponse.fisherman || {};
  var motives = explainResponse.motives || [];
  var catchSummary = explainResponse.catch_summary || {};
  var topPatterns = explainResponse.top_patterns || [];

  var lines = [
    'KNOWN INTELLIGENCE ON THIS DOMAIN:',
    'Owner: ' + (fisherman.owner || 'Unknown'),
    'Business model: ' + (fisherman.business_model || 'Unknown')
  ];

  if (motives.length > 0) {
    var primaryMotive = motives[0];
    lines.push('Primary documented motive: ' + (primaryMotive.description || primaryMotive.motive_type || 'Unknown'));
  }

  var harmCount = catchSummary.total_documented;
  if (typeof harmCount === 'number' && harmCount > 0) {
    lines.push('Documented harm cases on record: ' + harmCount);
  } else if (typeof harmCount === 'string') {
    lines.push('Documented harm cases on record: ' + harmCount);
  }

  if (Array.isArray(topPatterns) && topPatterns.length > 0) {
    lines.push('Documented techniques for this domain: ' + topPatterns.join(', '));
  } else if (motives.length > 1) {
    // Fall back: list motive types as documented techniques
    var techniqueList = motives.slice(0, 4).map(function(m) {
      return m.motive_type || '';
    }).filter(function(t) { return t.length > 0; });
    if (techniqueList.length > 0) {
      lines.push('Documented motive types for this domain: ' + techniqueList.join(', '));
    }
  }

  lines.push(
    '',
    'Use this intelligence as background context only. Analyze the page text',
    'independently. The intelligence does not determine your findings --',
    'the text does.'
  );

  return lines.join('\n');
}

/**
 * Build the complete system prompt for an analysis call.
 *
 * @param {object|null} explainResponse  - BMID context, or null if unavailable
 * @returns {string}
 */
function buildSystemPrompt(explainResponse) {
  var bmidBlock = buildBmidContext(explainResponse);

  if (bmidBlock.length > 0) {
    return bmidBlock + '\n\n' + CORE_INSTRUCTION;
  }

  return CORE_INSTRUCTION;
}

/**
 * Build the user message content for an analysis call.
 * Wraps the page text with a clear instruction.
 *
 * @param {string} pageText
 * @returns {string}
 */
function buildUserMessage(pageText) {
  return 'Analyze the following web page text for behavioral manipulation:\n\n' + pageText;
}

module.exports = {
  buildSystemPrompt: buildSystemPrompt,
  buildUserMessage: buildUserMessage,
  buildBmidContext: buildBmidContext,
  CORE_INSTRUCTION: CORE_INSTRUCTION
};
