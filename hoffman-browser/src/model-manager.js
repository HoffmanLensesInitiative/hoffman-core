/**
 * Hoffman Browser - Model Manager
 *
 * Manages the local AI model lifecycle.
 * Downloads once, stays resident, runs locally.
 * No data ever leaves the device.
 *
 * Uses node-llama-cpp with Phi-3 Mini (Q4 quantized, ~2.2GB)
 * Runs on CPU -- works on any machine regardless of GPU/VRAM.
 */

'use strict';

const path  = require('path');
const fs    = require('fs');
const https = require('https');

const MODEL_CONFIG = {
  name:        'Llama-3.2-3B-Instruct-Q4_K_M',
  filename:    'Llama-3.2-3B-Instruct-Q4_K_M.gguf',
  url:         'https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf',
  sizeMB:      2200,
  description: 'Llama 3.2 3B Instruct -- better instruction following, same size'
};

class ModelManager {
  constructor(modelsDir) {
    this.modelsDir  = modelsDir;
    this.modelPath  = path.join(modelsDir, MODEL_CONFIG.filename);
    this._status      = 'not-loaded';
    this._llama       = null;
    this._llamaModule = null;  // cached ESM import -- avoids re-importing on every call
    this._model       = null;
    this._context     = null;
    this._Session     = null;

    if (!fs.existsSync(modelsDir)) {
      fs.mkdirSync(modelsDir, { recursive: true });
    }

    if (fs.existsSync(this.modelPath)) {
      this._status = 'downloaded';
    }
  }

  getStatus() {
    return {
      status:      this._status,
      modelName:   MODEL_CONFIG.name,
      modelSizeMB: MODEL_CONFIG.sizeMB,
      description: MODEL_CONFIG.description,
      downloaded:  fs.existsSync(this.modelPath),
      ready:       this._status === 'ready'
    };
  }

  isReady() {
    return this._status === 'ready' && this._model !== null;
  }

  async load(progressCallback) {
    if (!fs.existsSync(this.modelPath)) {
      this._status = 'downloading';
      await this.download(progressCallback);
    }

    this._status = 'loading';
    if (progressCallback) {
      progressCallback({ stage: 'loading', message: 'Loading model into memory...' });
    }

    try {
      // Use Function constructor to import ESM module from CommonJS.
      // Cache the result on this._llamaModule so completeJson doesn't re-import.
      const importFn = new Function('specifier', 'return import(specifier)');
      const llama = await importFn('node-llama-cpp');
      this._llamaModule = llama;

      const { getLlama, LlamaChatSession } = llama;
      this._Session = LlamaChatSession;

      // Try GPU first (Metal/CUDA/Vulkan). If the GPU lacks VRAM for a 2048-token
      // context, fall back to CPU automatically -- same behavior, just slower.
      let loadedOnGpu = false;
      try {
        this._llama = await getLlama();
        this._model = await this._llama.loadModel({ modelPath: this.modelPath });
        this._context = await this._model.createContext({ contextSize: 2048 });
        loadedOnGpu = !!this._llama.gpu;
      } catch (gpuErr) {
        console.log('[Hoffman] GPU load failed (' + gpuErr.message + ') -- falling back to CPU');
        // Clean up any partial GPU state before retrying on CPU
        if (this._context)  { try { await this._context.dispose();  } catch(e) {} this._context  = null; }
        if (this._model)    { try { await this._model.dispose();    } catch(e) {} this._model    = null; }
        if (this._llama)    { try { await this._llama.dispose();    } catch(e) {} this._llama    = null; }
        this._llama   = await getLlama({ gpu: false });
        this._model   = await this._llama.loadModel({ modelPath: this.modelPath });
        this._context = await this._model.createContext({ contextSize: 2048 });
      }

      this._status = 'ready';
      const backend = loadedOnGpu ? ('GPU (' + this._llama.gpu + ')') : 'CPU';
      console.log('[Hoffman] Model loaded on ' + backend + ', context 2048');

      if (progressCallback) {
        progressCallback({ stage: 'ready', message: 'Model ready' });
      }

    } catch (err) {
      this._status = 'error';
      throw new Error('Failed to load model: ' + err.message);
    }
  }

  async complete(systemPrompt, userMessage) {
    if (!this.isReady()) throw new Error('Model not ready');

    if (!this._context) {
      this._context = await this._model.createContext({ contextSize: 2048 });
    }

    const sequence = this._context.getSequence();
    const session = new this._Session({
      contextSequence: sequence,
      systemPrompt
    });

    let result;
    try {
      result = await session.prompt(userMessage, {
        maxTokens:   1024,
        temperature: 0.1
      });
    } finally {
      try { await sequence.dispose(); } catch(e) {}
    }
    return result;
  }

  // completeJson -- forces valid JSON output at the grammar level
  // The model physically cannot output non-JSON tokens
  async completeJson(systemPrompt, userMessage) {
    if (!this.isReady()) throw new Error('Model not ready');

    // Reuse the cached llama import -- importing on every call adds latency
    const { LlamaJsonSchemaGrammar } = this._llamaModule;

    // Define the exact JSON shape we want
    const grammar = new LlamaJsonSchemaGrammar(this._llama, {
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
            }
          }
        }
      }
    });

    // Reuse the persistent context -- only dispose the sequence after each call.
    // Avoids reallocating the KV cache (createContext) on every analysis.
    // If the context was somehow lost, recreate it once.
    if (!this._context) {
      this._context = await this._model.createContext({ contextSize: 2048 });
    }

    const sequence = this._context.getSequence();

    const session = new this._Session({
      contextSequence: sequence,
      systemPrompt
    });

    let raw;
    try {
      raw = await session.prompt(userMessage, {
        // A full analysis (summary + 3-4 flags) is ~200-400 tokens.
        // 600 gives headroom for verbose explanations.
        maxTokens:   600,
        temperature: 0.1,
        grammar
      });
    } finally {
      // Always free the sequence slot back to the context, even on error.
      try { await sequence.dispose(); } catch(e) {}
    }

    return grammar.parse(raw);
  }

  async download(progressCallback) {
    return new Promise((resolve, reject) => {
      const tmpPath  = this.modelPath + '.download';
      const file     = fs.createWriteStream(tmpPath);
      let downloaded = 0;

      const request = (url) => {
        https.get(url, (response) => {
          if (response.statusCode === 301 || response.statusCode === 302) {
            request(response.headers.location);
            return;
          }
          if (response.statusCode !== 200) {
            reject(new Error('Download failed: HTTP ' + response.statusCode));
            return;
          }

          const total = parseInt(response.headers['content-length']) ||
                        MODEL_CONFIG.sizeMB * 1024 * 1024;

          response.on('data', (chunk) => {
            downloaded += chunk.length;
            const pct = Math.round((downloaded / total) * 100);
            if (progressCallback) {
              progressCallback({
                stage:      'downloading',
                percent:    pct,
                downloaded: Math.round(downloaded / 1024 / 1024),
                total:      Math.round(total / 1024 / 1024),
                message:    'Downloading model: ' + pct + '%'
              });
            }
          });

          response.pipe(file);
          file.on('finish', () => {
            file.close();
            fs.renameSync(tmpPath, this.modelPath);
            this._status = 'downloaded';
            resolve();
          });
        }).on('error', (err) => {
          fs.unlink(tmpPath, () => {});
          reject(err);
        });
      };

      request(MODEL_CONFIG.url);
    });
  }
}

module.exports = ModelManager;
