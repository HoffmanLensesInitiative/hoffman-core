# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Hoffman Browser is an Electron desktop application that wraps a Chromium browser with a local AI analysis panel. Users can navigate to any webpage and click "Analyze" to detect media manipulation techniques — all processing happens on-device using a CPU-based LLM (Llama 3.2 3B Instruct Q4_K_M). The analyzed page is never aware of the analysis.

## Commands

```bash
npm install                                          # Install dependencies
npx --no node-llama-cpp download --electron         # Download Electron-specific native binaries (required after npm install)
npm start                                           # Run in development mode
npm run build                                       # Build platform-specific installer
```

The `--electron` flag on the `node-llama-cpp download` step is mandatory — standard Node binaries will not work inside Electron's runtime.

## Architecture

The app has three visual layers stacked in a single `BrowserWindow`:

1. **Toolbar** (`panel/toolbar.html`) — 70px strip at top; URL bar and navigation controls
2. **Browser View** — actual web content in a `BrowserView` with an isolated `persist:hoffman` session
3. **Panel View** (`panel/panel.html`) — analysis results rendered in native Electron window chrome (unreachable by page scripts)

All IPC flows through `src/main.js`. Preload scripts (`src/toolbar-preload.js`, `src/panel-preload.js`) expose limited safe methods via `contextBridge` — `contextIsolation: true` and `nodeIntegration: false` everywhere.

### Analysis pipeline

```
User clicks Analyze
  → panel sends 'analyze-page' IPC to main
  → main extracts page text via browserView.webContents.executeJavaScript('document.body.innerText')
  → analyzer.js cleans text, trims to 1200 chars (fits 2048-token context with system prompt)
  → model-manager.js calls getLlama({gpu: false}) + recreates context per call (avoids "no sequences left" error)
  → model returns JSON or prose
  → analyzer.js tries extractJson(), falls back to parseNaturalResponse()
  → structured flags returned to panel via 'analysis-complete' IPC
```

### Key source files

- `src/main.js` — window creation, IPC routing, model download progress
- `src/analyzer.js` — text cleaning, prompt construction, JSON parsing, natural-language fallback
- `src/model-manager.js` — LLM lifecycle: download from HuggingFace, load via node-llama-cpp, complete()
- `panel/panel.html` — full panel UI and rendering logic (self-contained, no build step)
- `panel/toolbar.html` — toolbar UI (self-contained)

### Model

Llama 3.2 3B Instruct (Q4_K_M, ~2.2GB) stored at `~/.config/Hoffman/models/` (or Electron `userData` path). Downloaded once on first use; never transmitted anywhere. The `models/` directory is gitignored.

### Manipulation techniques the system detects

`outrage_engineering`, `false_authority`, `tribal_activation`, `false_urgency`, `incomplete_hook`, `dehumanization`, `war_framing`, `enemy_framing`, `complicity_framing`

## Important constraints

- **Context recreation**: `model-manager.js` recreates the llama context on every `complete()` call. This is intentional to prevent the "no sequences left" error — do not refactor to reuse a single context.
- **1200-char text limit**: The analyzer truncates page text to fit within the 2048-token context window alongside the system prompt. Increasing this requires also increasing the context size in model-manager.js.
- **CPU-only inference**: `getLlama({gpu: false})` is intentional for universal hardware compatibility.
- **No build step for UI**: `panel/toolbar.html` and `panel/panel.html` are standalone files with inline CSS/JS — there is no bundler or transpiler.
