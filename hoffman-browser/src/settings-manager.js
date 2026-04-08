/**
 * settings-manager.js
 * Hoffman Browser -- user settings storage
 *
 * Stores provider selection and API key in userData/settings.json.
 * API key is encrypted with Electron's safeStorage (OS keychain-backed)
 * when available; falls back to plaintext if not.
 *
 * Never transmits settings anywhere. Key is only used during analyzeWithCloud().
 */

'use strict';

const fs   = require('fs');
const path = require('path');

class SettingsManager {
  constructor(userDataPath) {
    this._path      = path.join(userDataPath, 'settings.json');
    this._settings  = {};
    this._safe      = null; // set by init() after app is ready
  }

  /**
   * Call once after app is ready so safeStorage is available.
   * @param {object} safeStorage - Electron's safeStorage module
   */
  init(safeStorage) {
    this._safe = safeStorage;
    this._settings = this._load();
  }

  _load() {
    try {
      if (!fs.existsSync(this._path)) return {};
      var raw = JSON.parse(fs.readFileSync(this._path, 'utf8'));

      // Decrypt API key if stored encrypted
      if (raw.apiKeyEncrypted && this._safe && this._safe.isEncryptionAvailable()) {
        try {
          raw.apiKey = this._safe.decryptString(Buffer.from(raw.apiKeyEncrypted, 'base64'));
        } catch(e) {
          console.error('[Hoffman] Settings decrypt error:', e.message);
        }
        delete raw.apiKeyEncrypted;
      }

      return raw;
    } catch (e) {
      console.error('[Hoffman] Settings load error:', e.message);
      return {};
    }
  }

  _save() {
    try {
      var toSave = Object.assign({}, this._settings);

      // Encrypt API key before writing to disk
      if (toSave.apiKey && this._safe && this._safe.isEncryptionAvailable()) {
        toSave.apiKeyEncrypted = this._safe.encryptString(toSave.apiKey).toString('base64');
        delete toSave.apiKey;
      }

      fs.writeFileSync(this._path, JSON.stringify(toSave, null, 2), 'utf8');
    } catch (e) {
      console.error('[Hoffman] Settings save error:', e.message);
    }
  }

  /** Save provider and API key. Pass null/empty apiKey to leave key unchanged. */
  saveApiSettings(provider, apiKey) {
    this._settings.provider = provider || 'anthropic';
    if (apiKey && apiKey.trim()) {
      this._settings.apiKey = apiKey.trim();
    }
    this._save();
  }

  clearApiKey() {
    delete this._settings.apiKey;
    this._save();
  }

  hasApiKey()   { return !!(this._settings.apiKey && this._settings.apiKey.length > 0); }
  getApiKey()   { return this._settings.apiKey || null; }
  getProvider() { return this._settings.provider || 'anthropic'; }

  /**
   * Returns settings safe to send to the renderer process.
   * Never includes the raw API key.
   */
  getPublic() {
    var key = this._settings.apiKey || '';
    return {
      provider:     this._settings.provider || 'anthropic',
      hasApiKey:    key.length > 0,
      apiKeyPreview: key.length > 8 ? key.slice(0, 7) + '…' : (key.length > 0 ? '••••••••' : '')
    };
  }
}

module.exports = SettingsManager;
