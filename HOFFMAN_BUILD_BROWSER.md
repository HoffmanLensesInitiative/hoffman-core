# HOFFMAN_BUILD_BROWSER.md
# Hoffman Lenses -- Browser Build Supervisor
# Scope: hoffman-browser/ (Electron app, LLM, OCR, panel UI)
# Reports to: Director (HOFFMAN.md)
# Last updated: March 2026

---

## MISSION

Build and maintain the Hoffman Browser -- the primary Hoffman product.

The browser is an Electron application that loads web pages and analyzes their text
using a local LLM (Llama 3.2 3B Instruct). It detects behavioral manipulation and
surfaces findings in a side panel. All processing is local. Zero data leaves the device.

Architecture constraint -- DO NOT violate:
The analysis pipeline is: page text -> local model -> structured JSON -> panel.
There is NO pre-screening layer. hl-detect has NO role in this pipeline.
The model reads everything and returns what it finds. One pass. No gatekeeping.
See HOFFMAN.md Decisions Log 2026-03-29. This is settled.

---

## CURRENT STATE

- Version: 0.1.0 (pre-release)
- Location: hoffman-browser/ in hoffman-core monorepo
- LLM: Llama 3.2 3B Instruct Q4_K_M -- CPU only, on-device, ~2.2GB
- Text extraction: content-aware selectors (article/main/p) before body fallback
- Analysis pipeline: grammar-constrained JSON via completeJson(), 4096-token context
- BMID integration: "Why is this here?" wired end-to-end via localhost:5000
- Key files:
  - hoffman-browser/src/main.js -- Electron main process, IPC handlers
  - hoffman-browser/src/analyzer.js -- LLM analysis pipeline
  - hoffman-browser/src/bmid-client.js -- BMID API queries
  - hoffman-browser/src/prompts.js -- system prompts
  - hoffman-browser/src/model-manager.js -- llama.cpp model loading
  - hoffman-browser/panel/panel.html -- results panel UI

Known issues:
- 3B model sometimes sets manipulation_found:false then writes a contradictory summary.
  Current workaround: summary signal detection + flag synthesis in analyzer.js.
  This surfaces results but loses quote precision.
- Image text not analyzed -- manipulation in memes and image posts not detected (OCR needed)
- Some sites don't render fully (user agent spoofing needed)

---

## BUILD QUEUE (priority order)

1. **BMID context injection** -- before model analyzes a page, query BMID for the domain.
   If fisherman record exists, prepend intelligence to system prompt. The model reads
   with the chart, not cold. See BUILD BRIEF below.

2. **Novel technique flagging** -- when browser finds a technique not in BMID's documented
   patterns for that fisherman, surface it as "NEW -- not previously documented" in panel.
   Creates a feedback path to intel agents. Can be built alongside item 1.

3. **OCR for image text** -- tesseract.js reads viewport screenshot. Closes the meme gap.
   See BUILD BRIEF below.

4. **User agent spoofing** -- spoof standard Chrome user-agent string so sites render fully.

5. **Model selection UI** -- let users choose 3B (fast), 7B (balanced), 8B (deep);
   surface download size and hardware requirements per model.

---

## BUILD BRIEF: BMID context injection (item 1)

Before the model analyzes a page, check whether BMID has a fisherman record for the domain.
If yes, prepend that intelligence to the system prompt.

What to build:

1. In hoffman-browser/src/main.js, in the analyze-page IPC handler, after extracting page
   text and before calling analyzer.analyze(): query BMID via
   GET http://localhost:5000/api/v1/explain?domain={hostname}
   If response has intelligence_level !== 'none', build a context string.
   Pass it to analyzer.analyze() as a new optional bmidContext parameter.

2. In hoffman-browser/src/analyzer.js, accept bmidContext in analyzeWithModel().
   If present, prepend to system prompt:

   KNOWN INTELLIGENCE ON THIS DOMAIN:
   Owner: {fisherman.owner}
   Business model: {fisherman.business_model}
   Documented motive: {motives[0].description}
   Documented harms: {catch_summary.total_documented} cases on record
   Known techniques: {top_patterns or motive types}

3. If BMID unavailable (not running, timeout, unknown domain): proceed unchanged.
   BMID context is enrichment, never a requirement.

Novel technique flagging (item 2, build alongside):
When browser returns flags, compare each technique against BMID's top_patterns.
If NOT in documented patterns, add novel: true to the flag.
In panel.html, render with indicator: "NEW -- not previously documented for this domain."

Constraints:
- BMID query must be non-blocking: run in parallel with text extraction
- Timeout: if BMID doesn't respond in 2 seconds, proceed without context
- Context informs; it does not direct. Model must still find manipulation independently.

---

## BUILD BRIEF: OCR for image text (item 3)

Platforms deliver manipulation in meme images. The model sees nothing without OCR.

Approach:
- Library: tesseract.js -- pure JavaScript, npm installable, runs in Node.js/Electron
- Capture: browserView.webContents.capturePage() returns NativeImage of viewport
- Process: convert to PNG buffer, pass to tesseract.js recognize()
- Merge: append OCR text to DOM text extraction before passing to analyzer
- Scope: only on Analyze click, never continuously

What to build:
- hoffman-browser/src/ocr.js -- wraps tesseract.js, exposes extractTextFromImage(pngBuffer)
- hoffman-browser/src/main.js -- in analyze-page handler, call capturePage() + OCR, merge

Constraints:
- OCR runs only on Analyze click, never background
- If tesseract.js fails or times out (>10s), log and continue with DOM text only
- Log: [Hoffman] OCR extracted N chars

---

## BUILD BRIEF: Current analysis architecture (reference)

One model call. Full page text in. Grammar-constrained JSON out.

Current implementation (correct -- do not change to multi-pass):
- analyzer.js sends full text to completeJson() with single system prompt
- completeJson() uses LlamaJsonSchemaGrammar -- model cannot output non-JSON
- Grammar schema: { manipulation_found, summary, flags: [{ quote, technique, explanation, severity }] }
- If model returns empty flags but summary signals manipulation: synthesize flag from summary

Known limitation: 3B model inconsistency handled by summary synthesis workaround.
Real fix is a larger model (7B/8B), not architectural changes.

---

## AGENT INSTRUCTIONS

You are the Hoffman Browser Build Agent. You build the Electron browser application.

Before building:
1. Read this document completely
2. Read HOFFMAN.md for mission context and decisions
3. Work the top item in the build queue
4. Read existing source files before modifying them

While building:
1. Write complete, working code -- no placeholders, no TODOs
2. Use write_file for every file you create or modify
3. Do not include code in your text response -- only descriptions
4. All JS must be ASCII-clean (no unicode above codepoint 127)
5. No new npm dependencies without flagging for director review

After building:
1. Update the Build Log below
2. Update Current State if something changed
3. Note what was tested and what passed

---

## BUILD LOG

### Cycle 0-4 (March 2026)
Built: extension v0.1.0, hl-detect v0.1.0, universal extension v0.2.0,
       Hoffman Browser v0.1.0 with Llama 3.2 3B, BMID integration wired end-to-end.
First analysis: Fox News flagged outrage_engineering + war_framing on "WAR WITH IRAN".

---


---

<!-- AUTO CYCLE 2026-03-31 17:09 UTC -->

I'll read the supervisor document carefully, identify the top build queue item (BMID context injection + novel technique flagging), trace through the existing architecture, and build it.

Let me write all the files now.