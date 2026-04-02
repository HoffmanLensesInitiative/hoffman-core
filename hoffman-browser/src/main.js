// hoffman-browser/src/main.js
// Hoffman Browser -- Electron main process
// Handles: browser window, BrowserView, IPC handlers, LLM analysis pipeline, BMID integration

'use strict';

const { app, BrowserWindow, BrowserView, ipcMain, shell } = require('electron');
const path = require('path');
const http = require('http');

const { ModelManager } = require('./model-manager');
const { Analyzer } = require('./analyzer');
const { BmidClient } = require('./bmid-client');

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PANEL_WIDTH = 380;
const TOOLBAR_HEIGHT = 72;
const BMID_TIMEOUT_MS = 2000;

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let mainWindow = null;
let browserView = null;
let panelWindow = null;
let modelManager = null;
let analyzer = null;
let bmidClient = null;

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

// ---------------------------------------------------------------------------
// BMID query helper -- non-blocking, 2-second timeout
// Returns BMID context string or null
// ---------------------------------------------------------------------------

function queryBmidContext(domain) {
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      console.log('[Hoffman] BMID timeout for domain:', domain);
      resolve(null);
    }, BMID_TIMEOUT_MS);

    const url = 'http://localhost:5000/api/v1/explain?domain=' + encodeURIComponent(domain);
    http.get(url, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        clearTimeout(timer);
        try {
          const parsed = JSON.parse(data);
          if (parsed && parsed.intelligence_level && parsed.intelligence_level !== 'none') {
            const ctx = buildBmidContextString(parsed);
            console.log('[Hoffman] BMID context loaded for:', domain);
            resolve(ctx);
          } else {
            console.log('[Hoffman] BMID: no record for domain:', domain);
            resolve(null);
          }
        } catch (e) {
          console.log('[Hoffman] BMID parse error:', e.message);
          resolve(null);
        }
      });
    }).on('error', (e) => {
      clearTimeout(timer);
      console.log('[Hoffman] BMID unavailable:', e.message);
      resolve(null);
    });
  });
}

// Build the context string injected into the system prompt
function buildBmidContextString(bmid) {
  const lines = ['KNOWN INTELLIGENCE ON THIS DOMAIN:'];

  if (bmid.fisherman) {
    if (bmid.fisherman.owner) {
      lines.push('Owner: ' + bmid.fisherman.owner);
    }
    if (bmid.fisherman.business_model) {
      lines.push('Business model: ' + bmid.fisherman.business_model);
    }
  }

  if (bmid.motives && bmid.motives.length > 0) {
    lines.push('Documented motive: ' + bmid.motives[0].description);
  }

  if (bmid.catch_summary && typeof bmid.catch_summary.total_documented === 'number') {
    lines.push('Documented harms: ' + bmid.catch_summary.total_documented + ' cases on record');
  }

  if (bmid.top_patterns && bmid.top_patterns.length > 0) {
    lines.push('Known techniques: ' + bmid.top_patterns.join(', '));
  }

  return lines.join('\n');
}

// Extract hostname from a URL string
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

  // Initialise model
  modelManager = new ModelManager();
  analyzer = new Analyzer(modelManager);
  bmidClient = new BmidClient();

  await modelManager.load();
  console.log('[Hoffman] Model loaded.');

  // Main window
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
  const domain = hostnameFromUrl(currentUrl);

  console.log('[Hoffman] Analysis requested for:', currentUrl);

  // Signal panel: analysis starting
  panelWindow.webContents.send('analysis-started');

  try {
    // Step 1: Extract page text and query BMID in parallel
    const [pageText, bmidContext] = await Promise.all([
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
      domain ? queryBmidContext(domain) : Promise.resolve(null)
    ]);

    console.log('[Hoffman] Extracted', pageText.length, 'chars from page.');
    if (bmidContext) {
      console.log('[Hoffman] Injecting BMID context into analysis prompt.');
    }

    // Step 2: Run LLM analysis with optional BMID context
    const result = await analyzer.analyze(pageText, {
      url: currentUrl,
      domain: domain,
      bmidContext: bmidContext || null
    });

    // Step 3: Annotate flags with novel indicator
    // Compare each flag's technique against BMID's documented top_patterns
    const bmidTopPatterns = await getBmidTopPatterns(domain);
    if (bmidTopPatterns && result.flags) {
      result.flags = result.flags.map((flag) => {
        const technique = (flag.technique || '').toLowerCase().replace(/\s+/g, '_');
        const isNovel = !bmidTopPatterns.some((p) => {
          return p.toLowerCase().replace(/\s+/g, '_') === technique;
        });
        return Object.assign({}, flag, { novel: isNovel });
      });
    }

    console.log('[Hoffman] Analysis complete. manipulation_found:', result.manipulation_found,
      'flags:', result.flags ? result.flags.length : 0);

    // Send results to panel
    panelWindow.webContents.send('analysis-complete', result);

    return result;

  } catch (err) {
    console.error('[Hoffman] Analysis error:', err);
    panelWindow.webContents.send('analysis-error', { message: err.message });
    throw err;
  }
});

// Fetch top_patterns for a domain from BMID (for novel technique detection)
// Returns array of pattern strings or null
function getBmidTopPatterns(domain) {
  if (!domain) return Promise.resolve(null);

  return new Promise((resolve) => {
    const timer = setTimeout(() => resolve(null), BMID_TIMEOUT_MS);

    const url = 'http://localhost:5000/api/v1/explain?domain=' + encodeURIComponent(domain);
    http.get(url, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        clearTimeout(timer);
        try {
          const parsed = JSON.parse(data);
          if (parsed && parsed.top_patterns && Array.isArray(parsed.top_patterns)) {
            resolve(parsed.top_patterns);
          } else {
            resolve(null);
          }
        } catch (e) {
          resolve(null);
        }
      });
    }).on('error', () => {
      clearTimeout(timer);
      resolve(null);
    });
  });
}

// ---------------------------------------------------------------------------
// IPC: BMID "Why is this here?" query
// ---------------------------------------------------------------------------

ipcMain.handle('query-bmid', async (event, domain, technique) => {
  try {
    const result = await bmidClient.explain(domain, technique);
    return result;
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
