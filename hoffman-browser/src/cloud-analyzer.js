/**
 * cloud-analyzer.js
 * Hoffman Browser -- cloud API analysis backend
 *
 * Supports Anthropic (Claude Haiku), OpenAI (GPT-4o Mini), Google (Gemini Flash).
 * All calls are plain HTTPS -- no SDK dependencies.
 * Returns the same shape as modelManager.completeJson():
 *   { manipulation_found, summary, flags[] }
 *
 * Privacy note: page text is sent to the selected provider.
 * The user configures and owns their own API key.
 */

'use strict';

const https = require('https');

// ---------------------------------------------------------------------------
// Provider definitions
// ---------------------------------------------------------------------------

var PROVIDERS = {

  anthropic: {
    hostname: 'api.anthropic.com',
    buildRequest: function(apiKey, systemPrompt, userMessage) {
      var body = JSON.stringify({
        model:      'claude-haiku-4-5-20251001',
        max_tokens: 1024,
        system:     systemPrompt,
        messages:   [{ role: 'user', content: userMessage }]
      });
      return {
        path: '/v1/messages',
        headers: {
          'Content-Type':      'application/json',
          'x-api-key':         apiKey,
          'anthropic-version': '2023-06-01',
          'Content-Length':    Buffer.byteLength(body)
        },
        body: body
      };
    },
    parseResponse: function(data) {
      // { content: [{ type: 'text', text: '{"manipulation_found":...}' }] }
      if (data.content && data.content[0] && data.content[0].text) {
        return parseJson(data.content[0].text);
      }
      throw new Error('Unexpected Anthropic response shape');
    }
  },

  openai: {
    hostname: 'api.openai.com',
    buildRequest: function(apiKey, systemPrompt, userMessage) {
      var body = JSON.stringify({
        model:           'gpt-4o-mini',
        messages:        [
          { role: 'system', content: systemPrompt },
          { role: 'user',   content: userMessage  }
        ],
        response_format: { type: 'json_object' },
        max_tokens:      1024,
        temperature:     0.1
      });
      return {
        path: '/v1/chat/completions',
        headers: {
          'Content-Type':   'application/json',
          'Authorization':  'Bearer ' + apiKey,
          'Content-Length': Buffer.byteLength(body)
        },
        body: body
      };
    },
    parseResponse: function(data) {
      // { choices: [{ message: { content: '{"manipulation_found":...}' } }] }
      if (data.choices && data.choices[0] && data.choices[0].message) {
        return parseJson(data.choices[0].message.content);
      }
      throw new Error('Unexpected OpenAI response shape');
    }
  },

  google: {
    hostname: 'generativelanguage.googleapis.com',
    buildRequest: function(apiKey, systemPrompt, userMessage) {
      var body = JSON.stringify({
        contents:           [{ parts: [{ text: userMessage }] }],
        systemInstruction:  { parts: [{ text: systemPrompt }] },
        generationConfig:   {
          responseMimeType: 'application/json',
          maxOutputTokens:  1024,
          temperature:      0.1
        }
      });
      return {
        path: '/v1beta/models/gemini-2.0-flash:generateContent?key=' + encodeURIComponent(apiKey),
        headers: {
          'Content-Type':   'application/json',
          'Content-Length': Buffer.byteLength(body)
        },
        body: body
      };
    },
    parseResponse: function(data) {
      // { candidates: [{ content: { parts: [{ text: '...' }] } }] }
      if (data.candidates && data.candidates[0] &&
          data.candidates[0].content && data.candidates[0].content.parts) {
        return parseJson(data.candidates[0].content.parts[0].text);
      }
      throw new Error('Unexpected Google response shape');
    }
  }

};

// ---------------------------------------------------------------------------
// JSON parser -- strips markdown code fences before parsing.
// Some models wrap their JSON response in ```json ... ``` even when
// instructed not to. This handles that gracefully.
// ---------------------------------------------------------------------------

function parseJson(text) {
  var s = text.trim();
  // Strip ```json ... ``` or ``` ... ```
  s = s.replace(/^```(?:json)?\s*/i, '').replace(/\s*```\s*$/, '');
  return JSON.parse(s);
}

// ---------------------------------------------------------------------------
// HTTP helper
// ---------------------------------------------------------------------------

function httpsPost(hostname, path, headers, body) {
  return new Promise(function(resolve, reject) {
    var req = https.request({
      hostname: hostname,
      path:     path,
      method:   'POST',
      headers:  headers
    }, function(res) {
      var raw = '';
      res.setEncoding('utf8');
      res.on('data',  function(chunk) { raw += chunk; });
      res.on('end',   function() {
        var data;
        try { data = JSON.parse(raw); } catch(e) {
          return reject(new Error('JSON parse error: ' + e.message));
        }
        if (res.statusCode >= 400) {
          var msg = (data.error && (data.error.message || data.error.code)) ||
                    ('HTTP ' + res.statusCode);
          return reject(new Error(msg));
        }
        resolve(data);
      });
    });

    req.on('error', function(e) { reject(e); });

    req.setTimeout(30000, function() {
      req.destroy();
      reject(new Error('Cloud analysis timed out after 30s'));
    });

    req.write(body);
    req.end();
  });
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Analyze page text using a cloud provider.
 * Returns the same shape as modelManager.completeJson().
 *
 * @param {string} provider     - 'anthropic' | 'openai' | 'google'
 * @param {string} apiKey
 * @param {string} systemPrompt - from analyzer.buildSystemPrompt()
 * @param {string} userMessage  - page text wrapped in instruction
 * @returns {Promise<{manipulation_found, summary, flags}>}
 */
async function analyzeWithCloud(provider, apiKey, systemPrompt, userMessage) {
  var config = PROVIDERS[provider];
  if (!config) throw new Error('Unknown provider: ' + provider);

  var req     = config.buildRequest(apiKey, systemPrompt, userMessage);
  var rawData = await httpsPost(config.hostname, req.path, req.headers, req.body);
  return config.parseResponse(rawData);
}

module.exports = {
  analyzeWithCloud: analyzeWithCloud,
  PROVIDER_NAMES: {
    anthropic: 'Anthropic (Claude Haiku)',
    openai:    'OpenAI (GPT-4o Mini)',
    google:    'Google (Gemini Flash)'
  }
};
