// hoffman-browser/src/main.js
// Hoffman Browser -- Electron main process
// Handles: browser window, BrowserView, IPC handlers, LLM analysis pipeline, BMID integration

'use strict';

const { app, BrowserWindow, BrowserView, ipcMain, shell } = require('electron');
const path = require('path');

const ModelManager = require('./model-manager');
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

let mainWindow   = null;
let browserView  = null;
let panelWindow  = null;
let modelManager = null;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getViewBounds(win) {
  const [width, height] = win.getContentSize();
  return {
    x: 0,
    y: TOOLBAR_HEIGHT,
    width: width - PANEL_WIDTH,
    height: height - TOOLBAR_HEIGHT
  };
}

function getPanelBounds(win) {
  const [width, height] = win.getContentSize();
  return {
    x: width - PANEL_WIDTH,
    y: TOOLBAR_HEIGHT,
    width: PANEL_WIDTH,
    height: height - TOOLBAR_HEIGHT
  };
}

// Extract hostname from a URL string, stripping www.
function hostnameFromUrl(urlString) {
  try {
    return new URL(urlString).hostname.replace(/^www\./, '');
  } catch (e) {
    return null;
  }
}

// ---------------------------------------------------------------------------
// App lifecycle
// ---------------------------------------------------------------------------

app.whenReady().then(async () => {
  console.log('[Hoffman] Starting up...');

  const modelsDir = path.join(app.getPath('userData'), 'models');
  modelManager = new ModelManager(modelsDir);

  await modelManager.load();
  console.log('[Hoffman] Model loaded.');

  // Main window (toolbar)
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, '../preload/toolbar-preload.js')
    },
    titleBarStyle: 'hiddenInset'
  });

  mainWindow.loadFile(path.join(__dirname, '../toolbar/toolbar.html'));

  // BrowserView for web content
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

  // Panel window (child)
  panelWindow = new BrowserWindow({
    parent: mainWindow,
    width: PANEL_WIDTH,
    height: 900,
    frame: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, '../panel/panel-preload.js')
    }
  });

  panelWindow.loadFile(path.join(__dirname, '../panel/panel.html'));

  mainWindow.on('resize', () => {
    browserView.setBounds(getViewBounds(mainWindow));
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
  panelWindow.webContents.send('panel-reset');
});

ipcMain.on('navigate-back', () => {
  if (browserView.webContents.canGoBack()) {
    browserView.webContents.goBack();
    panelWindow.webContents.send('panel-reset');
  }
});

ipcMain.on('navigate-forward', () => {
  if (browserView.webContents.canGoForward()) {
    browserView.webContents.goForward();
    panelWindow.webContents.send('panel-reset');
  }
});

ipcMain.on('navigate-reload', () => {
  browserView.webContents.reload();
  panelWindow.webContents.send('panel-reset');
});

ipcMain.handle('get-current-url', () => {
  return browserView.webContents.getURL();
});

// ---------------------------------------------------------------------------
// IPC: Analysis pipeline
// ---------------------------------------------------------------------------

ipcMain.handle('analyze-page', async () => {
  const currentUrl = browserView.webContents.getURL();
  const domain     = hostnameFromUrl(currentUrl);

  console.log('[Hoffman] Analysis requested for:', currentUrl);
  panelWindow.webContents.send('analysis-started');

  try {
    // Step 1: Extract page text and query BMID in parallel.
    // getBmidEnrichment makes one HTTP call and returns both the context string
    // and the list of known techniques -- no second BMID request needed.
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

    // Step 2: Build prompt and run model.
    // Text is truncated to 2400 chars to fit the 4096-token context window.
    // System prompt includes BMID context if available; model still detects independently.
    const truncated    = truncateText(pageText, 2400);
    const systemPrompt = buildSystemPrompt(enrichment.context);
    const userMessage  = 'Analyze this web page text for manipulation:\n\n' + truncated;

    console.log('[Hoffman] Starting analysis' +
      (enrichment.context ? ' (with BMID context)' : ' (no BMID context)') +
      ' | text: ' + truncated.length + ' chars');

    const startTime = Date.now();

    // completeJson returns a grammar-constrained parsed object -- never raw text.
    const parsed = await modelManager.completeJson(systemPrompt, userMessage);

    const elapsed = Date.now() - startTime;
    console.log('[Hoffman] Model returned in ' + elapsed + 'ms');

    // Step 3: Normalize result.
    const result = {
      manipulation_found: !!parsed.manipulation_found,
      summary:            parsed.summary || '',
      flags:              Array.isArray(parsed.flags) ? parsed.flags : [],
      processingTimeMs:   elapsed
    };

    // Workaround: 3B model sometimes sets manipulation_found:false but writes a
    // contradictory summary. Synthesize a flag from the summary signal.
    if (!result.manipulation_found && result.flags.length === 0) {
      var synthesized = synthesizeFlagsFromSummary(result.summary);
      if (synthesized.length > 0) {
        result.manipulation_found    = true;
        result.flags                 = synthesized;
        result.synthesizedFromSummary = true;
      }
    }

    // Step 4: Annotate novel techniques.
    // A flag is "novel" if its technique is not in BMID's documented patterns for this domain.
    if (enrichment.knownTechniques.length > 0 && result.flags.length > 0) {
      result.flags = result.flags.map(function(flag) {
        return Object.assign({}, flag, {
          novel: isTechniqueNovel(flag.technique, enrichment.knownTechniques)
        });
      });
    }

    console.log('[Hoffman] Analysis complete |',
      'manipulation_found:', result.manipulation_found,
      '| flags:', result.flags.length,
      result.synthesizedFromSummary ? '| (synthesized)' : '');

    panelWindow.webContents.send('analysis-complete', result);
    return result;

  } catch (err) {
    console.error('[Hoffman] Analysis error:', err);
    panelWindow.webContents.send('analysis-error', { message: err.message });
    throw err;
  }
});

// ---------------------------------------------------------------------------
// IPC: BMID "Why is this here?" query (panel button)
// ---------------------------------------------------------------------------

ipcMain.handle('query-bmid', async (event, domain, technique) => {
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
