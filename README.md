# Hoffman Browser

Research software for reading the web as it actually is.

Built on Electron/Chromium. Ships with a local AI model that reads
manipulation in real time. No data ever leaves your device.

---

## What it is

A browser with one added capability: it can read the room.

Navigate to any page. Click **Analyze**. The local AI model reads
the full page text -- exactly what you see -- and identifies
manipulation techniques: outrage engineering, false authority,
tribal activation, dehumanization, war framing, and more.

The page sees nothing. The analysis never leaves your machine.

---

## Architecture

```
Page loads in Chromium
        |
Electron main process extracts rendered text
(webContents.executeJavaScript -- above the page)
        |
Local AI model reads the full text
"What on this page is manipulative? Quote it. Explain it."
        |
Hoffman panel displays results
(native window chrome -- untouchable by any website)
        |
User sees flags. Page sees nothing.
```

The AI model (Phi-3 Mini, ~2.2GB) runs entirely on your machine.
Downloaded once, cached permanently, never phones home.

---

## Getting started

```bash
# Install dependencies
npm install

# Start in development mode
npm start
```

First launch: click **Download Hoffman model** in the panel.
One-time download of ~2.2GB. After that, works offline.

---

## Building for distribution

```bash
npm run build
```

Produces platform-specific installers in `dist/`.

---

## Project structure

```
src/
  main.js              -- Electron main process, window management
  analyzer.js          -- The doctor: AI-powered analysis
  model-manager.js     -- Local model download, load, inference
  toolbar-preload.js   -- Toolbar IPC bridge
  panel-preload.js     -- Panel IPC bridge
panel/
  toolbar.html         -- Browser toolbar UI
  panel.html           -- Hoffman analysis panel
models/                -- Local model stored here (gitignored)
```

---

## The model

Phi-3 Mini 4K Instruct (Q4_K_M quantization)
- Size: ~2.2GB
- Parameters: 3.8B
- Context: 4096 tokens
- Source: Microsoft / HuggingFace
- License: MIT

Runs on CPU or GPU. GPU recommended for faster analysis.
Typical analysis time: 2-5 seconds on modern hardware.

---

## What hl-detect does now

hl-detect is not in the analysis path for Hoffman Browser.
The local model does the full analysis.

hl-detect lives on as:
- A standalone library for developers (npm)
- A reference for what patterns the model should catch
- Potentially a fast pre-screen for very high volume use cases

---

## Hoffman Lenses Initiative

hoffmanlenses.org
github.com/HoffmanLensesInitiative

License: MIT (code) / CC BY 4.0 (written works)

"They deserved better than to be engagement metrics."

Dedicated to JackLynn Blackwell, Molly Russell, Nylah Anderson,
CJ Dawley, Amanda Todd, and Sadie Riggs.
