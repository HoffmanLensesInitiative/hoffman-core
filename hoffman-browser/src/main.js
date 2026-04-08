// hoffman-browser/src/main.js
// Hoffman Browser -- Electron main process
// Handles: browser window, BrowserView, panel window, IPC, LLM pipeline, BMID

'use strict';

const { app, BrowserWindow, BrowserView, ipcMain, shell, safeStorage } = require('electron');
const path = require('path');

const ModelManager    = require('./model-manager');
const SettingsManager = require('./settings-manager');
const { analyzeWithCloud } = require('./cloud-analyzer');
const { buildSystemPrompt, truncateText, synthesizeFlagsFromSummary } = require('./analyzer');
const { getBmidEnrichment } = require('./bmid-context');
const { isTechniqueNovel } = require('./bmid-context-builder');
const bmidClient = require('./bmid-client');

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PANEL_WIDTH    = 380;
const TOOLBAR_HEIGHT = 72;

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let mainWindow    = null;
let browserView   = null;
let panelWindow   = null;
let modelManager  = null;
let settingsManager = null;

// ---------------------------------------------------------------------------
// Window bounds helpers
// ---------------------------------------------------------------------------

function getViewBounds(win) {
  const [w, h] = win.getContentSize();
  return { x: 0, y: TOOLBAR_HEIGHT, width: w - PANEL_WIDTH, height: h - TOOLBAR_HEIGHT };
}

// Position the panel flush against the right edge of the main window.
// Called on create, resize, and move.
function updatePanelBounds() {
  if (!mainWindow || !panelWindow) return;
  if (mainWindow.isDestroyed() || panelWindow.isDestroyed()) return;
  const b = mainWindow.getBounds();
  panelWindow.setBounds({
    x:      b.x + b.width - PANEL_WIDTH,
    y:      b.y + TOOLBAR_HEIGHT,
    width:  PANEL_WIDTH,
    height: b.height - TOOLBAR_HEIGHT
  });
}

// ---------------------------------------------------------------------------
// Utility
// ---------------------------------------------------------------------------

function hostnameFromUrl(urlString) {
  try { return new URL(urlString).hostname.replace(/^www\./, ''); }
  catch (e) { return null; }
}

// ---------------------------------------------------------------------------
// Model loading -- user-triggered, with progress events to panel
// ---------------------------------------------------------------------------

function sendToPanel(channel, payload) {
  if (panelWindow && !panelWindow.isDestroyed()) {
    panelWindow.webContents.send(channel, payload);
  }
}

async function loadModel() {
  sendToPanel('model-loading', { stage: 'loading', message: 'Loading model...' });

  try {
    await modelManager.load((progress) => {
      sendToPanel('model-loading', progress);
    });
    sendToPanel('model-ready');
    console.log('[Hoffman] Model ready.');
  } catch (err) {
    console.error('[Hoffman] Model load failed:', err.message);
    sendToPanel('model-error', err.message);
  }
}

// ---------------------------------------------------------------------------
// App lifecycle
// ---------------------------------------------------------------------------

app.whenReady().then(async () => {
  console.log('[Hoffman] Starting up...');

  const userData = app.getPath('userData');

  modelManager    = new ModelManager(path.join(userData, 'models'));
  settingsManager = new SettingsManager(userData);
  settingsManager.init(safeStorage);

  // Main window (toolbar)
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'toolbar-preload.js')
    },
    titleBarStyle: 'hiddenInset'
  });

  mainWindow.loadFile(path.join(__dirname, '../panel/toolbar.html'));

  // BrowserView for web content (left side)
  browserView = new BrowserView({
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  mainWindow.addBrowserView(browserView);
  browserView.setBounds(getViewBounds(mainWindow));
  browserView.setAutoResize({ width: true, height: true });
  browserView.webContents.loadURL('https://www.google.com');

  // Panel window -- positioned flush to the right edge of mainWindow
  panelWindow = new BrowserWindow({
    parent: mainWindow,
    width:  PANEL_WIDTH,
    height: 900,
    frame:  false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'panel-preload.js')
    }
  });

  panelWindow.loadFile(path.join(__dirname, '../panel/panel.html'));

  // Position panel once it has loaded (bounds are stable after load)
  panelWindow.webContents.once('did-finish-load', () => {
    updatePanelBounds();

    // Send initial model + settings status
    const status = modelManager.getStatus();
    sendToPanel('model-status', status);
    sendToPanel('settings-status', settingsManager.getPublic());

    // If no cloud key and model already downloaded, auto-load it
    if (!settingsManager.hasApiKey() && status.downloaded && !status.ready) {
      loadModel();
    }
  });

  // Keep panel anchored to the right edge on resize and move
  mainWindow.on('resize', () => {
    browserView.setBounds(getViewBounds(mainWindow));
    updatePanelBounds();
  });

  mainWindow.on('move', () => {
    updatePanelBounds();
  });

  mainWindow.on('closed', () => {
    app.quit();
  });

  console.log('[Hoffman] Browser ready.');
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// ---------------------------------------------------------------------------
// IPC: Navigation
// ---------------------------------------------------------------------------

ipcMain.on('navigate', (event, url) => {
  let target = url.trim();
  if (!target.startsWith('http://') && !target.startsWith('https://')) {
    target = 'https://' + target;
  }
  browserView.webContents.loadURL(target);
  sendToPanel('panel-reset');
});

ipcMain.on('navigate-back', () => {
  if (browserView.webContents.canGoBack()) {
    browserView.webContents.goBack();
    sendToPanel('panel-reset');
  }
});

ipcMain.on('navigate-forward', () => {
  if (browserView.webContents.canGoForward()) {
    browserView.webContents.goForward();
    sendToPanel('panel-reset');
  }
});

ipcMain.on('navigate-reload', () => {
  browserView.webContents.reload();
  sendToPanel('panel-reset');
});

ipcMain.handle('get-current-url', () => {
  return browserView.webContents.getURL();
});

// ---------------------------------------------------------------------------
// IPC: Model management
// ---------------------------------------------------------------------------

ipcMain.on('get-model-status', () => {
  sendToPanel('model-status', modelManager.getStatus());
});

ipcMain.on('load-model', () => {
  loadModel();
});

// ---------------------------------------------------------------------------
// IPC: Settings
// ---------------------------------------------------------------------------

ipcMain.handle('get-settings', () => {
  return settingsManager.getPublic();
});

ipcMain.handle('save-settings', (event, { provider, apiKey }) => {
  settingsManager.saveApiSettings(provider, apiKey);
  console.log('[Hoffman] Settings saved: provider=' + provider +
    ', hasKey=' + settingsManager.hasApiKey());
  return settingsManager.getPublic();
});

ipcMain.handle('clear-api-key', () => {
  settingsManager.clearApiKey();
  console.log('[Hoffman] API key cleared');
  return settingsManager.getPublic();
});

// ---------------------------------------------------------------------------
// IPC: Analysis pipeline
// ---------------------------------------------------------------------------

ipcMain.on('analyze-page', async () => {
  const useCloud = settingsManager.hasApiKey();

  if (!useCloud && !modelManager.isReady()) {
    sendToPanel('analysis-error', 'No API key configured and local model not loaded. ' +
      'Add an API key in Settings (⚙) or load the local model.');
    return;
  }

  const currentUrl = browserView.webContents.getURL();
  const domain     = hostnameFromUrl(currentUrl);

  console.log('[Hoffman] Analysis requested for:', currentUrl,
    '| mode:', useCloud ? settingsManager.getProvider() : 'local');
  sendToPanel('analysis-started');

  try {
    // Extract page text and query BMID in parallel.
    const [pageText, enrichment] = await Promise.all([
      browserView.webContents.executeJavaScript(`
        (function() {
          var selectors = ['article', 'main', '[role="main"]', '.content', '#content', 'body'];
          for (var i = 0; i < selectors.length; i++) {
            var el = document.querySelector(selectors[i]);
            if (el && el.innerText && el.innerText.trim().length > 200) {
              return el.innerText.trim();
            }
          }
          return document.body.innerText.trim();
        })()
      `),
      getBmidEnrichment(domain)
    ]);

    if (enrichment.context) {
      console.log('[Hoffman] BMID context injected for:', domain);
    }

    const truncated    = truncateText(pageText, 2400);
    const systemPrompt = buildSystemPrompt(enrichment.context);
    const userMessage  = 'Analyze this web page text for manipulation:\n\n' + truncated;

    console.log('[Hoffman] Starting analysis' +
      (enrichment.context ? ' (with BMID context)' : ' (no BMID context)') +
      ' | text: ' + truncated.length + ' chars');

    const startTime = Date.now();

    let parsed;
    if (useCloud) {
      // Cloud path: fast, no local CPU usage
      parsed = await analyzeWithCloud(
        settingsManager.getProvider(),
        settingsManager.getApiKey(),
        systemPrompt,
        userMessage
      );
    } else {
      // Local path: grammar-constrained JSON, runs on device
      parsed = await modelManager.completeJson(systemPrompt, userMessage);
    }

    const elapsed = Date.now() - startTime;
    console.log('[Hoffman] Analysis returned in ' + elapsed + 'ms via ' +
      (useCloud ? settingsManager.getProvider() : 'local model'));

    // Normalize result
    const result = {
      manipulation_found: !!parsed.manipulation_found,
      summary:            parsed.summary || '',
      flags:              Array.isArray(parsed.flags) ? parsed.flags : [],
      processingTimeMs:   elapsed,
      via:                useCloud ? settingsManager.getProvider() : 'local'
    };

    // Workaround: small models sometimes set manipulation_found:false but write
    // a contradictory summary. Synthesize a flag from the summary signal.
    if (!result.manipulation_found && result.flags.length === 0) {
      const synthesized = synthesizeFlagsFromSummary(result.summary);
      if (synthesized.length > 0) {
        result.manipulation_found     = true;
        result.flags                  = synthesized;
        result.synthesizedFromSummary = true;
      }
    }

    // Annotate novel techniques -- flags not in BMID's documented patterns.
    if (enrichment.knownTechniques.length > 0 && result.flags.length > 0) {
      result.flags = result.flags.map((flag) =>
        Object.assign({}, flag, {
          novel: isTechniqueNovel(flag.technique, enrichment.knownTechniques)
        })
      );
    }

    console.log('[Hoffman] Analysis complete |',
      'manipulation_found:', result.manipulation_found,
      '| flags:', result.flags.length,
      result.synthesizedFromSummary ? '| (synthesized)' : '');

    sendToPanel('analysis-complete', result);

  } catch (err) {
    console.error('[Hoffman] Analysis error:', err);
    sendToPanel('analysis-error', err.message);
  }
});

// ---------------------------------------------------------------------------
// IPC: BMID "Why is this here?" query (panel button)
// ---------------------------------------------------------------------------

ipcMain.handle('query-bmid', async (event, domain) => {
  try {
    return await bmidClient.queryExplain(domain);
  } catch (err) {
    console.error('[Hoffman] BMID query error:', err);
    return null;
  }
});

// ---------------------------------------------------------------------------
// IPC: Open external links
// ---------------------------------------------------------------------------

ipcMain.on('open-external', (event, url) => {
  shell.openExternal(url);
});
