/**
 * Hoffman Browser - Analyzer
 * The doctor. Reads the room. Works with whatever the model says.
 */

'use strict';

const SYSTEM_PROMPT = `You are a media manipulation detection API. You respond only with a valid JSON object.

Analyze the provided webpage text for manipulation techniques. Return this JSON structure:

{
  "manipulation_found": true,
  "summary": "Brief description of what manipulation is present",
  "flags": [
    {
      "quote": "exact phrase from the text",
      "technique": "technique name",
      "explanation": "why this is manipulative",
      "severity": "high|medium|low"
    }
  ]
}

Techniques: outrage_engineering, false_authority, tribal_activation, false_urgency, incomplete_hook, dehumanization, war_framing, enemy_framing, complicity_framing.

If no manipulation is found return: {"manipulation_found": false, "summary": "No manipulation detected.", "flags": []}

Return only the JSON object. No explanation. No markdown. No text before or after the JSON.`;

class Analyzer {
  constructor(modelManager) {
    this.modelManager = modelManager;
  }

  setModel(model) {}

  async analyze(pageText, context) {
    const { url, hostname } = context;
    const cleaned = this.cleanText(pageText);

    if (!cleaned || cleaned.length < 50) {
      return { hostname, url, manipulation_found: false, summary: 'No readable text.', flags: [], method: 'empty' };
    }

    if (!this.modelManager.isReady()) {
      return { hostname, url, manipulation_found: null, summary: 'Load the Hoffman model to analyze this page.', flags: [], method: 'no-model' };
    }

    return await this.analyzeWithModel(cleaned, context);
  }

  async analyzeWithModel(text, context) {
    const { url, hostname } = context;
    const excerpt = text.length > 1200 ? text.substring(0, 1200) : text;

    try {
      const response = await this.modelManager.complete(
        SYSTEM_PROMPT,
        `Analyze this text from ${hostname}:\n\n${excerpt}`
      );

      console.log('[Hoffman] Raw length:', response.length);
      console.log('[Hoffman] Raw preview:', response.substring(0, 300));

      // Try JSON first, fall back to natural language parsing
      const jsonResult = this.extractJson(response);
      if (jsonResult && jsonResult.manipulation_found !== undefined) {
        console.log('[Hoffman] JSON parse succeeded');
        return { hostname, url, ...jsonResult, method: 'model', textLength: text.length };
      }
      console.log('[Hoffman] Falling back to natural language parse');
      return this.parseNaturalResponse(response, hostname, url, text.length);

    } catch (err) {
      console.log('[Hoffman] Error:', err.message);
      return { hostname, url, manipulation_found: null, summary: 'Error: ' + err.message, flags: [], method: 'error' };
    }
  }

  // Try to extract JSON from model response
  extractJson(text) {
    const start = text.indexOf('{');
    const end = text.lastIndexOf('}');
    if (start === -1 || end === -1 || end <= start) return null;
    try {
      return JSON.parse(text.substring(start, end + 1));
    } catch(e) {
      return null;
    }
  }

  // Parse natural language response -- no JSON required
  parseNaturalResponse(text, hostname, url, textLength) {
    const lower = text.toLowerCase();

    // Determine if manipulation was found
    const foundSignals = [
      'manipulation found', 'manipulative', 'outrage', 'tribal', 'dehumani',
      'false authority', 'false urgency', 'war framing', 'enemy framing',
      'incomplete hook', 'complicity', 'propaganda', 'inflammatory'
    ];
    const cleanSignals = [
      'no manipulation', 'does not contain', 'no manipulative',
      'not manipulative', 'straightforward', 'factual reporting'
    ];

    const foundScore  = foundSignals.filter(s => lower.includes(s)).length;
    const cleanScore  = cleanSignals.filter(s => lower.includes(s)).length;
    const manipulation_found = foundScore > cleanScore;

    // Extract flags from the text by looking for quoted content + technique mentions
    const flags = [];
    const techniqueMap = {
      'outrage engineering': 'outrage_engineering',
      'outrage':             'outrage_engineering',
      'false authority':     'false_authority',
      'tribal activation':   'tribal_activation',
      'tribal':              'tribal_activation',
      'false urgency':       'false_urgency',
      'incomplete hook':     'incomplete_hook',
      'dehumanization':      'dehumanization',
      'dehumanizing':        'dehumanization',
      'war framing':         'war_framing',
      'enemy framing':       'enemy_framing',
      'complicity framing':  'complicity_framing',
      'complicity':          'complicity_framing',
      'manipulative':        'outrage_engineering'
    };

    // Find quoted phrases in the response
    const quoteRegex = /"([^"]{10,200})"/g;
    let match;
    while ((match = quoteRegex.exec(text)) !== null) {
      const quote = match[1];
      const surroundingText = text.substring(Math.max(0, match.index - 200), match.index + 200).toLowerCase();

      // Find what technique is mentioned near this quote
      let technique = 'outrage_engineering';
      let severity = 'medium';
      for (const [keyword, tech] of Object.entries(techniqueMap)) {
        if (surroundingText.includes(keyword)) {
          technique = tech;
          break;
        }
      }
      if (surroundingText.includes('high') || surroundingText.includes('strong') || surroundingText.includes('extreme')) {
        severity = 'high';
      }

      // Get the explanation -- text after the quote
      const afterQuote = text.substring(match.index + match[0].length, match.index + match[0].length + 200).trim();

      if (flags.length < 10) {
        flags.push({
          quote,
          technique,
          explanation: afterQuote.substring(0, 200) || 'Identified as manipulative content.',
          severity
        });
      }
    }

    // If no quoted flags but manipulation found, create a summary flag
    if (manipulation_found && flags.length === 0) {
      flags.push({
        quote: 'See summary',
        technique: 'outrage_engineering',
        explanation: text.substring(0, 300),
        severity: 'medium'
      });
    }

    // Summary -- first 2 sentences of response
    const sentences = text.split(/[.!?]/).filter(s => s.trim().length > 20);
    const summary = sentences.slice(0, 2).join('. ').trim().substring(0, 300);

    return {
      hostname, url,
      manipulation_found,
      summary: summary || text.substring(0, 200),
      flags,
      method: 'model',
      textLength
    };
  }

  cleanText(text) {
    return text
      .replace(/\t/g, ' ')
      .replace(/ {3,}/g, '  ')
      .split('\n')
      .filter(line => {
        const l = line.trim();
        if (l.length < 3) return false;
        if (/^\d+(\.\d+)?[KM]?$/.test(l)) return false;
        return true;
      })
      .join('\n')
      .trim();
  }
}

module.exports = Analyzer;
