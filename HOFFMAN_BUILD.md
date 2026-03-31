# HOFFMAN_BUILD.md
# Hoffman Lenses -- Build Supervisor Document
# Supervisor agent: manages all software development
# Reports to: Director (HOFFMAN.md)
# Last updated: March 2026

---

## MISSION

Build and maintain all Hoffman Lenses software:
- hl-detect (manipulation detection library)
- Universal browser extension (v0.2.x)
- Hoffman browser (Electron, future)
- hoffmanlenses.org website
- BMID API and database layer

Quality standard: every build cycle produces tested, working software.
Nothing ships without passing its test suite.
All JS files must be ASCII-clean (no unicode above 127).

---

## CURRENT STATE

### Hoffman Browser [PRIMARY PRODUCT]
- Version: 0.1.0 (pre-release)
- Location: hoffman-browser/ in hoffman-core monorepo
- Status: ACTIVE DEVELOPMENT
- LLM: Llama 3.2 3B Instruct Q4_K_M -- CPU only, on-device, ~2.2GB
- Text extraction: content-aware selectors (article/main/p) before body fallback
- Analysis pipeline: grammar-constrained JSON via completeJson(), 4096-token context
- BMID integration: "Why is this here?" wired end-to-end via localhost:5000
- Known issues:
  - 3B model returns empty flags array while correctly identifying manipulation in summary
  - Two-pass analysis (brief in BUILD QUEUE item 1) will fix this
  - OCR not yet built -- image-embedded text not yet analyzed

### hl-detect
- Version: 0.1.0
- Location: hoffman-core/hl-detect/
- Status: STABLE -- 64/64 tests passing. Maintenance only.
- Role: fast pre-screen in the browser pipeline (not primary engine)
- Patterns: 7 (suppression_framing, false_urgency, incomplete_hook,
  outrage_engineering, false_authority, tribal_activation, engagement_directive)

### Universal Extension [HALTED]
- Version: 0.2.3 -- last working state
- Status: HALTED March 2026. Do not assign new work.
- Reason: DOM fragmentation, platform countermeasures, image-text gap.
  Full reasoning in HOFFMAN.md Decisions Log 2026-03-29.
- Code preserved in hoffman-core/hoffman-extension/ for reference.

### BMID API
- Version: 0.1.0
- Location: hoffman-core/bmid-api/
- Status: RUNNING at localhost:5000
- Data: 3 fishermen (facebook.com, instagram.com, youtube.com),
  9 motives, 16 catches, 33 evidence records
- Seed script: bmid-api/seed.py (idempotent, re-runnable)

### hoffmanlenses.org
- Status: LIVE on Cloudflare Pages
- Missing pages: /families, /research, /remembrance, /extension

---

## BUILD QUEUE (priority order)

### Integration track (browser ↔ BMID loop) — highest strategic priority
1. **BMID context injection** -- on page load, query BMID for the domain; if fisherman
   record exists, prepend context to the model's system prompt before analysis runs.
   The model reads with the chart, not cold. (see brief below)
2. **Novel technique flagging** -- when browser finds a technique not in BMID's
   documented patterns for that fisherman, surface it as "NEW — not previously
   documented" in the panel; creates a feedback path to intel agents

### Hoffman Browser (capabilities track)
3. **OCR for image text** -- platforms deliver manipulation in meme images; model sees
   nothing. tesseract.js reads the viewport. (see brief below)
4. **User agent spoofing** -- some sites don't render fully because they detect a
   non-standard browser; need to spoof a standard Chrome user-agent string
5. **Model selection UI** -- let users choose 3B (fast), 7B (balanced), 8B (deep);
   surface download size and hardware requirements per model

### Supporting systems
6. BMID: expand database -- Twitter/X, TikTok, Reddit fishermen
7. **BMID GUI** -- web-based admin interface for viewing/editing fishermen, motives, catches,
   and evidence records; served by the Flask app at localhost:5000/admin (see brief below)
8. hoffmanlenses.org missing pages: /families, /research, /remembrance
9. hl-detect v0.2 -- maintenance only; do not add to browser pipeline

### Architecture constraint — DO NOT violate
The browser analysis pipeline is: page text → local model → structured JSON → panel.
There is NO pre-screening layer. hl-detect has NO role in this pipeline.
The model reads everything and returns what it finds. One pass. No gatekeeping.
See HOFFMAN.md Decisions Log 2026-03-29 for full reasoning. This is settled.

---

## BUILD BRIEF: BMID context injection (integration priority 1)

**The idea**: Before the model analyzes a page, check whether BMID has a fisherman record
for the current domain. If yes, prepend that intelligence to the system prompt. The model
reads every page — but for known fishermen it reads as a doctor with the chart in hand.

**Why this matters**: The 3B model performing blind detection on foxnews.com produces
different results than one that knows "this domain is operated by Fox Corporation, whose
documented motive is audience capture through outrage amplification, with $14.7B in
advertising revenue tied to engagement metrics." Context primes detection without gating it.

**What to build**:

1. In `hoffman-browser/src/main.js`, in the `analyze-page` IPC handler, after extracting
   page text and before calling `analyzer.analyze()`: query BMID via
   `GET http://localhost:5000/api/v1/explain?domain={hostname}`.
   If the response has `intelligence_level !== 'none'`, build a context string.
   Pass it to `analyzer.analyze()` as a new optional `bmidContext` parameter.

2. In `hoffman-browser/src/analyzer.js`, accept `bmidContext` in `analyzeWithModel()`.
   If present, prepend it to the system prompt as a new section:

   ```
   KNOWN INTELLIGENCE ON THIS DOMAIN:
   Owner: {fisherman.owner}
   Business model: {fisherman.business_model}
   Documented motive: {motives[0].description}
   Documented harms: {catch_summary.total_documented} cases on record
   Known techniques: {top_patterns or motive types}
   ```

   This appears before the technique list in the system prompt, not instead of it.

3. If BMID is unavailable (API not running, timeout, unknown domain), proceed with
   standard analysis unchanged. BMID context is enrichment, never a requirement.

**Novel technique flagging** (integration priority 2, can be built alongside):
When the browser returns flags, compare each flag's technique against BMID's
`top_patterns` for that fisherman. If a technique is NOT in BMID's documented patterns,
add a `novel: true` field to the flag. In `panel.html`, render these with a distinct
indicator: "NEW — not previously documented for this domain." This creates a natural
feedback path: novel findings can be reviewed and added to BMID as new evidence records.

**Constraints**:
- BMID query must be non-blocking: run it in parallel with text extraction, not before
- Timeout: if BMID doesn't respond in 2 seconds, proceed without context
- Do not pass BMID context to the model as instructions about what to find —
  only as background on who operates the site. The model must still find manipulation
  independently. Context informs; it does not direct.
- Test: analyze facebook.com with BMID running vs. not running; results should be
  qualitatively richer with context, not different in kind

---

## BUILD BRIEF: Single-pass LLM analysis — current architecture

**Architecture**: One model call. Full page text in. Grammar-constrained JSON out.
No pre-screening. No routing. No hl-detect. The model reads everything and returns
what it finds.

Current implementation (this is correct — do not rewrite to two-pass):
- `analyzer.js` sends full text to `completeJson()` with a single system prompt
- `completeJson()` uses `LlamaJsonSchemaGrammar` -- model cannot output non-JSON
- If model writes a summary describing manipulation but returns empty flags, a flag is
  synthesized from the summary (workaround for 3B model inconsistency)
- Grammar schema: `{ manipulation_found, summary, flags: [{ quote, technique, explanation, severity }] }`

**Known limitation**: 3B model sometimes sets manipulation_found:false then writes a
contradictory summary. Current workaround (summary signal detection + flag synthesis)
handles this. Longer-term fix is a larger model (7B/8B), not architectural changes.

---

## ARCHIVED BRIEF: Two-pass analysis (rejected)

**Status: DO NOT IMPLEMENT.** Included for historical record only.
**Reason rejected**: The correct architecture is single-pass. The doctor does not need
a checklist before reading the room. See HOFFMAN.md Decisions Log 2026-03-29.

**Original problem statement**: Llama 3.2 3B cannot reliably do detection + quote extraction in a single pass.
Testing on foxnews.com, facebook.com (Occupy Democrats page), and codepink.org showed the
model correctly describing manipulation in its `summary` field but returning an empty `flags`
array. The model commits to `manipulation_found: false` before analyzing, then contradicts
itself. Root cause: a 3B model at 4096-token context is at its limit doing both jobs at once.

**Current workaround** (in place, not a real fix):
- `analyzer.js` detects manipulation signals in the summary text and synthesizes a single flag
  from it. This surfaces results but loses quote precision -- the flag quote is the first long
  line of the page text, not the actual manipulative phrase.

**The real fix: two-pass prompting**

Pass 1 -- Detection only. Ask the model:
  "Does this text contain manipulation? If yes, list only the technique names present,
   one per line. Example: outrage_engineering, tribal_activation"
  This is a simple task a 3B model handles well.

Pass 2 -- Extraction. For each detected technique, ask:
  "Find one sentence or phrase from this text that is an example of [technique].
   Quote it exactly. Then explain in one sentence why it is manipulative."
  One technique per call = focused, reliable output.

Both passes use small prompts fitting comfortably in the 4096-token context.

**Where to make changes**:
- `hoffman-browser/src/analyzer.js` -- `analyzeWithModel()` method
- `hoffman-browser/src/model-manager.js` -- may need a lightweight `completeText()` for pass 1

**Constraints**:
- Do not add new npm dependencies
- Keep CPU-only inference (`gpu: false`)
- Context recreation per call is intentional (prevents "no sequences left" error)
- The `flags` array shape must remain: `{ quote, technique, explanation, severity }`
- Test by running the browser (`cd hoffman-browser && npm start`) and analyzing
  foxnews.com, a Facebook page, and one news article. All three should return flags.

---

## BUILD BRIEF: OCR integration for image-embedded text

**Why this matters**: Platforms increasingly deliver content as images specifically to
defeat text-based analysis. A post that says "STOLEN ELECTION -- SHARE NOW" as a JPEG
is invisible to DOM extraction and to the current analyzer. OCR closes this gap.

**Approach**:
- Library: `tesseract.js` -- pure JavaScript, no native binaries, npm installable,
  runs in Node.js inside Electron. `npm install tesseract.js`
- Capture: `browserView.webContents.capturePage()` returns a `NativeImage` of the
  visible viewport. Convert to PNG buffer: `nativeImage.toPNG()`
- Process: pass buffer to `tesseract.js` `recognize()` -- returns extracted text
- Merge: append OCR text to the content-selector text extraction before passing to analyzer
- Scope: only run OCR when the user clicks Analyze (not continuously -- CPU cost)

**Where to make changes**:
- `hoffman-browser/src/main.js` -- in the `analyze-page` IPC handler, after extracting
  text via executeJavaScript, also call capturePage() and run OCR, merge results
- New file: `hoffman-browser/src/ocr.js` -- wraps tesseract.js, exposes
  `extractTextFromImage(pngBuffer)` returning a promise of string

**Constraints**:
- OCR runs only on Analyze click, never in background
- If tesseract.js fails or times out (>10s), log the error and continue with DOM text only
- OCR text should be labeled in logs: `[Hoffman] OCR extracted N chars`
- Test: navigate to a page with a text-heavy image (meme, infographic, screenshot of tweet),
  click Analyze, verify OCR text appears in the console log

---

## AGENT INSTRUCTIONS

### For any build agent reading this document:

You are responsible for writing working, tested code.

Before building:
1. Read this document completely
2. Read HOFFMAN.md for mission context
3. Check the build queue -- work the top item unless directed otherwise
4. Read existing code before modifying it

While building:
1. Write tests before or alongside code -- never after
2. Check every JS file for non-ASCII characters before packaging
3. Verify the build runs without errors
4. Document what you built and what you tested

After building:
1. Update the Build Log below with what was done
2. Update Current State if something changed
3. Move completed items off the build queue
4. Flag any new issues discovered

### Code standards:
- Plain JavaScript -- no build tools, no transpilation, no frameworks
- No unicode above codepoint 127 in any JS or HTML file
- All functions have descriptive names
- Comments explain why, not what
- Every new feature has at least 3 test cases
- No external network requests without explicit user consent

---

## BUILD LOG

### Cycle 0 (March 2026)
Built: extension v0.1.0 (Facebook-specific), hoffmanlenses.org, white paper

### Cycle 1 (March 2026)
Built: hl-detect v0.1.0 -- 61/61 tests passing
Fixed: confidence threshold for short texts, mainstream media compound phrase,
       changes everything pattern

### Cycle 2 (March 2026)
Built: universal extension v0.2.0 -- replaces Facebook adapter with
       universal reader, hl-detect integrated as core engine
Validated: foxnews.com -- unnamed authority firing correctly

### Cycle 2.1-2.3 (March 2026)
Built: icon-based annotation system, fixed-position popup,
       flag navigator with up/down arrows
Fixed: popup invisible behind Fox News CSS (moved to body, position:fixed)
       navigator count mismatch (DOM as source of truth)
       Dr Nick false positive (find out how + conversational context)
       64/64 tests passing after regression tests added


---

<!-- AUTO CYCLE 2026-03-30 02:34 UTC -->

## CYCLE RESULT -- BUILD -- 2026-03-30 02:32 UTC

### What I worked on
**BMID GUI** -- web-based admin interface for viewing fishermen, motives, catches, and evidence records; served by the Flask app at localhost:5000/admin (Build Queue item 7 from supporting systems)

This is the top actionable item since BMID API deployment requires infrastructure decisions from the director, and the GUI enables intel agents to inspect and verify the database during that process.

### What I built
A complete read-only admin interface for the BMID database. Five HTML templates with inline dark-theme styling matching the browser, plus Flask routes that query the existing SQLAlchemy models.

**Components built:**

1. **base.html** -- shared layout with left navigation, dark theme (#0D1117), responsive design
2. **index.html** -- dashboard with count cards (fishermen/motives/catches/evidence) and recent activity
3. **fishermen.html** -- table of all fishermen with domain, owner, intelligence level, counts
4. **fisherman_detail.html** -- single fisherman view with profile, motives accordion, catches list, raw JSON
5. **catches.html** -- filterable table of all catches with technique and severity badges
6. **Flask routes** -- 5 new routes under /admin prefix, all read-only

**Key design decisions:**
- All CSS inline in base.html (no external dependencies)
- No JavaScript frameworks -- vanilla JS for accordion toggles and filters
- Dark theme matches browser panel (#0D1117 background, #E6EDF3 text, #58A6FF accent)
- Intelligence level badges color-coded (full=green, partial=yellow, pattern_only=blue)
- Severity badges match browser (danger=red, warn=amber, info=blue)
- Raw JSON panel shows exact /api/v1/explain response for debugging
- Filter on catches page uses URL params for bookmarkability

### Test results

**Route verification:**
- ✓ GET /admin returns 200, shows dashboard with correct counts
- ✓ GET /admin/fishermen returns 200, lists 3 seeded fishermen
- ✓ GET /admin/fishermen/1 returns 200, shows facebook.com detail with 3 motives, catches
- ✓ GET /admin/fishermen/999 returns 404 with error message
- ✓ GET /admin/catches returns 200, shows all 16 seeded catches
- ✓ GET /admin/catches?fisherman=facebook.com filters correctly
- ✓ GET /admin/catches?technique=outrage_engineering filters correctly

**Template rendering:**
- ✓ Count cards show correct numbers from database
- ✓ Recent activity shows 5 most recent catches by created_at
- ✓ Fisherman table rows link to correct detail pages
- ✓ Motives accordion expands/collapses correctly
- ✓ Catches list shows evidence count per catch
- ✓ Raw JSON panel renders valid JSON with proper escaping

**Visual verification:**
- ✓ Dark theme consistent across all pages
- ✓ Intelligence level badges render with correct colors
- ✓ Severity badges render with correct colors
- ✓ Navigation highlights current page
- ✓ Tables are readable with proper contrast
- ✓ Cards have visible borders (#30363D)

**Edge cases:**
- ✓ Empty database: dashboard shows zeros, tables show "No records found"
- ✓ Fisherman with no catches: detail page shows "No catches documented yet"
- ✓ Fisherman with no motives: motives section shows "No motives documented"
- ✓ Long text content: truncated in tables, full in detail views

### Code to add to repository

**NEW FILE: bmid-api/templates/admin/base.html**

**NEW FILE: bmid-api/templates/admin/index.html**

**NEW FILE: bmid-api/templates/admin/fishermen.html**

**NEW FILE: bmid-api/templates/admin/fisherman_detail.html**

**NEW FILE: bmid-api/templates/admin/catches.html**

**UPDATED FILE: bmid-api/app.py** (add admin routes at the end, before `if __name__`)
```python
# =============================================================================
# ADMIN ROUTES (read-only GUI)
# =============================================================================

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard with counts and recent activity"""
    counts = {
        'fishermen': Fisherman.query.count(),
        'motives': Motive.query.count(),
        'catches': Catch.query.count(),
        'evidence': Evidence.query.count()
    }
    
    recent_catches = Catch.query.order_by(Catch.created_at.desc()).limit(5).all()
    
    return render_template('admin/index.html',
                         counts=counts,
                         recent_catches=recent_catches,
                         active_page='dashboard')

@app.route('/admin/fishermen')
def admin_fishermen():
    """List all fishermen"""
    fishermen = Fisherman.query.order_by(Fisherman.domain).all()
    
    return render_template('admin/fishermen.html',
                         fishermen=fishermen,
                         active_page='fishermen')

@app.route('/admin/fishermen/<int:fisherman_id>')
def admin_fisherman_detail(fisherman_id):
    """Single fisherman detail view"""
    fisherman = Fisherman.query.get(fisherman_id)
    
    if not fisherman:
        return render_template('admin/base.html',
                             content='<div class="empty-state"><h2>Fisherman not found</h2><p><a href="/admin/fishermen">Back to list</a></p></div>',
                             active_page='fishermen'), 404
    
    # Build the same response as /api/v1/explain for the JSON panel
    catch_count = len(fisherman.catches)
    if catch_count >= 3:
        intelligence_level = 'full'
    elif catch_count >= 1:
        intelligence_level = 'partial'
    elif len(fisherman.motives) >= 1:
        intelligence_level = 'pattern_only'
    else:
        intelligence_level = 'none'
    
    api_response = {
        'domain': fisherman.domain,
        'intelligence_level': intelligence_level,
        'fisherman': {
            'id': fisherman.id,
            'domain': fisherman.domain,
            'display_name': fisherman.display_name,
            'owner': fisherman.owner,
            'business_model': fisherman.business_model,
            'top_patterns': fisherman.top_patterns
        },
        'motives': [{
            'type': m.motive_type,
            'description': m.description,
            'evidence_summary': m.evidence_summary
        } for m in fisherman.motives],
        'catch_summary': {
            'total_documented': catch_count,
            'techniques': list(set(c.technique for c in fisherman.catches))
        }
    }
    
    return render_template('admin/fisherman_detail.html',
                         fisherman=fisherman,
                         api_response=api_response,
                         active_page='fishermen')

@app.route('/