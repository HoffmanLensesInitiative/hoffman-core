/**
 * Hoffman Browser - Main Process
 *
 * Electron main process. Owns the browser window, the model,
 * and all analysis. The page sees nothing.
 */

const { app, BrowserWindow, BrowserView, ipcMain } = require('electron');
const path = require('path');
const http = require('http');
const Analyzer    = require('./analyzer');
const ModelManager = require('./model-manager');
const bmidClient  = require('./bmid-client');

let mainWindow = null;
let browserView = null;
let panelView  = null;
let analyzer   = null;
let modelManager = null;

const PANEL_WIDTH   = 380;
const TOOLBAR_HEIGHT = 72;
let _panelVisible = true;

// ── Window ────────────────────────────────────────────────

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: '#0D1117',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'toolbar-preload.js')
    }
  });

  mainWindow.loadFile(path.join(__dirname, '../panel/toolbar.html'));

  // Web content -- browses the actual web
  browserView = new BrowserView({
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      partition: 'persist:hoffman'
    }
  });
  mainWindow.addBrowserView(browserView);

  // Hoffman panel -- our analysis UI, native to window frame
  panelView = new BrowserView({
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'panel-preload.js')
    }
  });
  mainWindow.addBrowserView(panelView);
  panelView.webContents.loadFile(path.join(__dirname, '../panel/panel.html'));

  layoutViews();
  mainWindow.on('resize', layoutViews);

  // Navigation events -- keep toolbar URL in sync
  browserView.webContents.on('did-navigate', (event, url) => {
    mainWindow.webContents.send('url-changed', url);
    mainWindow.webContents.send('loading', false);
    panelView.webContents.send('page-changed', {
      url,
      hostname: safeHostname(url)
    });
  });

  browserView.webContents.on('did-start-loading', () => {
    mainWindow.webContents.send('loading', true);
  });

  browserView.webContents.on('page-title-updated', (e, title) => {
    mainWindow.webContents.send('title-changed', title);
  });

  browserView.webContents.loadURL('https://www.google.com');
}

function layoutViews() {
  if (!mainWindow) return;
  const [width, height] = mainWindow.getContentSize();
  const contentWidth = _panelVisible ? width - PANEL_WIDTH : width;

  browserView.setBounds({
    x: 0, y: TOOLBAR_HEIGHT,
    width: contentWidth,
    height: height - TOOLBAR_HEIGHT
  });

  panelView.setBounds({
    x: contentWidth, y: TOOLBAR_HEIGHT,
    width: _panelVisible ? PANEL_WIDTH : 0,
    height: height - TOOLBAR_HEIGHT
  });
}

function safeHostname(url) {
  try { return new URL(url).hostname; } catch(e) { return url; }
}

// ── IPC: toolbar ──────────────────────────────────────────

ipcMain.on('navigate', (event, input) => {
  let url = input.trim();
  if (!url.startsWith('http')) {
    url = url.includes('.') && !url.includes(' ')
      ? 'https://' + url
      : 'https://www.google.com/search?q=' + encodeURIComponent(url);
  }
  browserView.webContents.loadURL(url);
});

ipcMain.on('go-back',    () => browserView.webContents.canGoBack()    && browserView.webContents.goBack());
ipcMain.on('go-forward', () => browserView.webContents.canGoForward() && browserView.webContents.goForward());
ipcMain.on('reload',     () => browserView.webContents.reload());

ipcMain.on('toggle-panel', () => {
  _panelVisible = !_panelVisible;
  layoutViews();
  mainWindow.webContents.send('panel-state', _panelVisible);
});

// ── IPC: panel -- analysis ────────────────────────────────

ipcMain.on('analyze-page', async () => {
  panelView.webContents.send('analysis-started');
  try {
    const url      = browserView.webContents.getURL();
    const hostname = safeHostname(url);

    // Run text extraction and BMID query in parallel -- BMID must not block analysis
    const [text, bmidResponse] = await Promise.all([
      browserView.webContents.executeJavaScript(`(function() {
        // Priority 1: semantic content containers
        const selectors = [
          'article', 'main', '[role="main"]', '[role="article"]',
          '.post-content', '.article-body', '.story-body', '.entry-content',
          '#content', '#main-content', '.content'
        ];
        for (const sel of selectors) {
          const el = document.querySelector(sel);
          if (el && el.innerText && el.innerText.trim().length > 200) {
            return el.innerText;
          }
        }
        // Priority 2: collect all paragraphs, skip nav/header/footer
        const skip = new Set(['NAV','HEADER','FOOTER','ASIDE','SCRIPT','STYLE','NOSCRIPT']);
        const paras = Array.from(document.querySelectorAll('p, h1, h2, h3, blockquote'))
          .filter(el => {
            let p = el.parentElement;
            while (p) { if (skip.has(p.tagName)) return false; p = p.parentElement; }
            return el.innerText && el.innerText.trim().length > 30;
          })
          .map(el => el.innerText.trim());
        if (paras.length > 3) return paras.join('\\n');
        // Fallback: full body text
        return document.body.innerText;
      })()`),
      bmidClient.queryDomain(url)
    ]);

    // Give analyzer the BMID response so it can build context and flag novelty
    analyzer.setBmidResponse(bmidResponse);

    const results = await analyzer.analyze(text, { url, hostname });
    console.log('[Hoffman] Analysis complete, flags:', results.flags ? results.flags.length : 'none');
    console.log('[Hoffman] Summary:', results.summary ? results.summary.substring(0, 100) : 'none');
    // Trim results to avoid IPC size limits
    const safe = {
      hostname:          results.hostname || '',
      url:               results.url || '',
      manipulation_found: results.manipulation_found,
      summary:           (results.summary || '').substring(0, 500),
      method:            results.method || '',
      flags: (results.flags || []).slice(0, 20).map(function(f) {
        return {
          quote:       (f.quote || '').substring(0, 300),
          technique:   (f.technique || '').substring(0, 100),
          explanation: (f.explanation || '').substring(0, 500),
          severity:    f.severity || 'medium',
          novel:       f.novel || false
        };
      })
    };
    panelView.webContents.send('analysis-complete', safe);

  } catch (err) {
    panelView.webContents.send('analysis-error', err.message);
  }
});

ipcMain.on('get-model-status', () => {
  panelView.webContents.send('model-status', modelManager.getStatus());
});

ipcMain.on('load-model', async () => {
  try {
    await modelManager.load((progress) => {
      panelView.webContents.send('model-loading', progress);
    });
    panelView.webContents.send('model-ready');
  } catch (err) {
    panelView.webContents.send('model-error', err.message);
  }
});

// ── IPC: panel -- BMID ───────────────────────────────────

function bmidFetch(urlPath) {
  return new Promise((resolve, reject) => {
    const req = http.get('http://localhost:5000' + urlPath, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch (e) { reject(new Error('Invalid JSON from BMID')); }
      });
    });
    req.on('error', (err) => reject(new Error('BMID unavailable: ' + err.message)));
    req.setTimeout(5000, () => { req.destroy(); reject(new Error('BMID timeout')); });
  });
}

ipcMain.handle('query-bmid', async (event, domain, pattern) => {
  const clean = (domain || '').replace(/^www\./, '');
  const params = new URLSearchParams({ domain: clean });
  if (pattern) params.set('patterns', pattern);
  return bmidFetch('/api/v1/explain?' + params.toString());
});

// ── App lifecycle ─────────────────────────────────────────

app.whenReady().then(async () => {
  modelManager = new ModelManager(
    path.join(app.getPath('userData'), 'models')
  );
  analyzer = new Analyzer(modelManager);
  createWindow();

  // Tell panel what model state we're in after it loads
  setTimeout(() => {
    panelView.webContents.send('model-status', modelManager.getStatus());
  }, 1200);
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
