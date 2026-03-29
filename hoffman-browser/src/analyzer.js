/**
 * Hoffman Browser - Analyzer
 * The doctor. Reads the room. Works with whatever the model says.
 *
 * Architecture: single pass. Full page text in, grammar-constrained JSON out.
 * No pre-screening. No routing. The model reads everything and returns what it finds.
 * BMID context is prepended to the system prompt when available -- the doctor with the
 * chart -- but the model still detects independently.
 */

'use strict';

const { isTechniqueKnown } = require('./bmid-client.js');
const { buildContext }     = require('./context-builder.js');

const BASE_SYSTEM_PROMPT = `You are a media manipulation detection API. You respond only with a valid JSON object.

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
    this._lastBmidResponse = null;
  }

  setModel(model) {}

  // Called by main.js after BMID query completes (runs in parallel with text extraction)
  setBmidResponse(bmidResponse) {
    this._lastBmidResponse = bmidResponse;
  }

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
    const excerpt = text.length > 2400 ? text.substring(0, 2400) : text;

    // Build system prompt -- prepend BMID context if available
    const bmidContext = buildContext(this._lastBmidResponse);
    const systemPrompt = bmidContext
      ? bmidContext + BASE_SYSTEM_PROMPT
      : BASE_SYSTEM_PROMPT;

    if (bmidContext) {
      console.log('[Hoffman] Analyzing with BMID context (' + bmidContext.length + ' chars)');
    }

    try {
      // Single pass -- grammar-constrained JSON -- model physically cannot output non-JSON tokens
      const jsonResult = await this.modelManager.completeJson(
        systemPrompt,
        `Analyze this text from ${hostname}:\n\n${excerpt}`
      );

      // Normalize: don't trust the boolean the model committed to before analyzing.
      // A 3B model often writes manipulation_found:false then a summary describing manipulation.
      // Derive truth from the summary text and flags array.
      const flags = jsonResult.flags || [];
      const summarySignals = ['manipulat', 'outrage', 'tribal', 'dehumani', 'false authority',
        'false urgency', 'war framing', 'enemy framing', 'complicity', 'propaganda'];
      const summaryImpliesFound = summarySignals.some(s =>
        (jsonResult.summary || '').toLowerCase().includes(s)
      );
      const manipulation_found = flags.length > 0 || summaryImpliesFound;

      // If manipulation detected in summary but model returned no flags, synthesize one.
      if (manipulation_found && flags.length === 0 && jsonResult.summary) {
        const techniqueMap = {
          'outrage':         'outrage_engineering',
          'tribal':          'tribal_activation',
          'false urgency':   'false_urgency',
          'false authority': 'false_authority',
          'dehumani':        'dehumanization',
          'war framing':     'war_framing',
          'enemy framing':   'enemy_framing',
          'complicity':      'complicity_framing',
        };
        let technique = 'outrage_engineering';
        const lsummary = jsonResult.summary.toLowerCase();
        for (const [kw, tech] of Object.entries(techniqueMap)) {
          if (lsummary.includes(kw)) { technique = tech; break; }
        }
        flags.push({
          quote: excerpt.split('\n').find(l => l.trim().length > 40) || excerpt.substring(0, 100),
          technique,
          explanation: jsonResult.summary,
          severity: 'high'
        });
      }

      // Mark novel techniques -- ones not previously documented for this fisherman in BMID
      if (this._lastBmidResponse && this._lastBmidResponse.intelligence_level !== 'none') {
        flags.forEach(flag => {
          flag.novel = !isTechniqueKnown(this._lastBmidResponse, flag.technique);
        });
      }

      console.log('[Hoffman] flags:', flags.length, 'manipulation_found:', manipulation_found);
      return { hostname, url, ...jsonResult, flags, manipulation_found, method: 'model', textLength: text.length };

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
