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

### hl-detect
- Version: 0.1.0
- Location: hoffman-core/hl-detect/
- Status: STABLE -- 64/64 tests passing
- Patterns: 7 (suppression_framing, false_urgency, incomplete_hook,
  outrage_engineering, false_authority, tribal_activation, engagement_directive)
- Known gaps: multilingual support (v0.2 target), coordinated_language
  requires session context (deferred)

### Universal Extension
- Version: 0.2.3
- Location: hoffman-lenses-extension/
- Status: WORKING -- validated on foxnews.com and facebook.com
- Features: icon-based annotations, fixed-position popup, flag navigator,
  session bar, background worker, popup panel
- Known issues:
  - Session export not yet built
  - "Why is this here?" button not yet built
  - Icon placeholder (not real Hoffman Lenses glasses icon)
  - Annotation icons sometimes appear below image elements not headlines

### hoffmanlenses.org
- Status: LIVE on Cloudflare Pages
- Missing pages: /whitepaper, /families, /research, /remembrance, /extension

### BMID API
- Status: NOT YET BUILT -- schema exists at hoffman-core/BMID_SCHEMA.md
- Next: build database layer and API endpoints

---

## BUILD QUEUE (priority order)

1. Session export -- download session as JSON/CSV from popup
2. "Why is this here?" button -- Claude API integration in popup
3. BMID API v0.1 -- basic read/write endpoints, SQLite initially
4. hl-detect v0.2 -- coordinated_language pattern, multilingual stub
5. hoffmanlenses.org missing pages
6. Hoffman Electron browser (Stage 3 -- deferred until extension stable)

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
