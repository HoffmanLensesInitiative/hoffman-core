/**
 * Hoffman Browser - Context Builder
 * Transforms a BMID intelligence response into system prompt context text.
 *
 * This is informational context only -- it tells the model who operates the site
 * and what has been documented about them. It does NOT tell the model what to find.
 * The model must detect manipulation independently. Context informs; it does not direct.
 */

'use strict';

// Rough token budget for context -- keeps room for page text within 4096-token window
const MAX_CONTEXT_CHARS = 800;

function buildContext(bmidResponse) {
  if (!bmidResponse || bmidResponse.intelligence_level === 'none' || !bmidResponse.fisherman) {
    return '';
  }

  const f = bmidResponse.fisherman;
  const lines = ['KNOWN INTELLIGENCE ON THIS DOMAIN:'];

  if (f.owner || f.display_name) {
    lines.push('Owner: ' + (f.owner || f.display_name));
  }

  if (f.business_model) {
    lines.push('Business model: ' + f.business_model);
  }

  if (bmidResponse.motives && bmidResponse.motives.length > 0) {
    // Include up to 2 motive descriptions -- enough context without dominating the prompt
    lines.push('Documented motives:');
    bmidResponse.motives.slice(0, 2).forEach(m => {
      if (m.description) {
        // Truncate long descriptions
        const desc = m.description.length > 200
          ? m.description.substring(0, 200) + '...'
          : m.description;
        lines.push('- ' + desc);
      }
    });
  }

  if (bmidResponse.catch_summary && bmidResponse.catch_summary.total_documented > 0) {
    const n = bmidResponse.catch_summary.total_documented;
    lines.push('Documented harms: ' + n + ' case' + (n !== 1 ? 's' : '') + ' on record');
  }

  if (bmidResponse.top_patterns && bmidResponse.top_patterns.length > 0) {
    const patterns = bmidResponse.top_patterns.filter(p => p && p.length > 0);
    if (patterns.length > 0) {
      lines.push('Known techniques: ' + patterns.join(', '));
    }
  }

  let context = lines.join('\n');

  if (context.length > MAX_CONTEXT_CHARS) {
    context = context.substring(0, MAX_CONTEXT_CHARS) + '...[truncated]';
  }

  return context + '\n\n';
}

module.exports = { buildContext };
