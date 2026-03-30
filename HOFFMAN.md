# HOFFMAN.md
# The Hoffman Lenses Initiative — Master Build Document
# Version: 0.2.0
# Last updated: March 30, 2026
# THIS DOCUMENT IS THE SINGLE SOURCE OF TRUTH FOR THE HOFFMAN PROJECT.
# It is read by AI agents at the start of every build cycle.
# It is updated by AI agents after every build cycle.
# It is updated by the project director (Norm Robichaud) with decisions and redirections.
# Every action taken, every result observed, every decision made is recorded here.
# Nothing is lost between cycles. Every cycle builds on everything before it.

-----

## PART 1 — MISSION

### What Hoffman Is

Hoffman is a browser built on Chromium that makes behavioral manipulation visible to the people it operates on. It reads language the way an expert reads manipulation — recognizing not just what text says but what it is designed to do to the reader. It works on every website, every platform, every page — because manipulation is a property of language, not of any specific platform’s DOM structure.

The name comes from the Hoffman Lenses — the glasses in John Carpenter’s 1988 film They Live — which allowed the wearer to see hidden messages embedded in ordinary reality. Once you put them on, you cannot unsee what they reveal.

### What Hoffman Is Not

Hoffman is not a privacy browser. Brave does that.
Hoffman is not an ad blocker. That is a feature, not an identity.
Hoffman is not a platform-specific tool. It does not target Facebook or TikTok specifically. It reads language everywhere.
Hoffman is not a censorship tool. It blocks nothing. It hides nothing. It makes visible. The user decides what to do with what they see.

### Why This Exists

Behavioral Manipulation Systems — the algorithmic engines that power social media platforms — are injuring and killing human beings as a direct and foreseeable consequence of how they are designed to operate. Children have died. Adults have been radicalized. Relationships have been destroyed. Democracies have been destabilized.

The harm is not incidental. It is architectural. These systems optimize for engagement without obligation to human wellbeing. They exploit psychological vulnerabilities for profit. They operate invisibly.

Hoffman makes them visible. That is the mission.

The full human rights case is documented in the white paper:
“The Algorithm and the Child: A Human Rights Case for Abolishing Behavioral Manipulation Systems” — published at hoffmanlenses.org

### The People This Is For

Primary: Researchers, journalists, lawyers, parents, advocates —
people who actively want to understand what is being done to them and to others. People who will use Hoffman as a research instrument.

Secondary: General users who want to browse with awareness —
who want a knowledgeable presence reading alongside them.

Not trying to reach everyone. Trying to reach people who are ready to see. The glasses only work if you’re willing to put them on.

-----

## PART 2 — ARCHITECTURE

### The Three-Stage Build Plan

#### Stage 1 — hl-detect (COMPLETE)

A standalone JavaScript library that takes text as input and returns structured analysis of manipulation patterns present in that text.
Platform-agnostic. DOM-agnostic. No dependencies.
Status: v0.1.0 shipped, 64/64 tests passing.
Role going forward: standalone npm library for developers. Has NO role in the Hoffman Browser detection pipeline (see Decisions Log 2026-03-29).

#### Stage 2 — Universal Extension (HALTED)

A browser extension (Chrome + Firefox) that injects hl-detect into every page the user visits.
Status: v0.2.3 built and functional. Development halted March 2026.

Why halted:

- Fragmentation: Chrome, Firefox, Safari, and Edge all have different extension models and requirements, creating permanent maintenance burden
- DOM inconsistency: platforms use inconsistent and deliberately obfuscated DOM structure, making reliable text extraction impossible across sites
- Active countermeasures: platforms intentionally change their DOM syntax specifically to prevent tools like ours from reading page text
- Manifest V3: Chrome’s extension architecture further limits what content scripts can do, with a trajectory toward more restriction, not less
- Image text: extensions cannot read text embedded in images — a tactic platforms increasingly use to deliver content that bypasses text-based detection

The extension work is not wasted. Detection algorithms, BMID wiring, and UI patterns all inform browser development.

#### Stage 3 — Hoffman Browser (CURRENT STAGE)

A Chromium-based desktop browser with manipulation detection built in.
Built on Electron (JavaScript, no C++ required).
Platforms: Windows, Mac, Linux.

Why the browser wins where the extension loses:

- Text extraction reads what the user actually sees (rendered output), not DOM markup. Platforms cannot obfuscate rendered text without breaking their own product.
- OCR capability: the browser can screenshot its own viewport and run on-device OCR, reading text embedded in images — a detection surface extensions cannot reach
- No per-browser fragmentation: one Electron codebase runs identically everywhere
- The page is never aware it is being analyzed
- Local LLM runs on-device: no data leaves the machine, no network dependency, no platform can block it

Current capabilities: text extraction, LLM analysis via Llama 3.2 3B Instruct, BMID “Why is this here?” integration.
Next capability: OCR via tesseract.js for image-embedded text.

### Supporting Systems (parallel to all stages)

- Research database — anonymized session data from users who opt in
- Retrospective analysis tool — Facebook data archive analyzer for families, lawyers, law enforcement
- hoffmanlenses.org — website, white paper, remembrance list, research dashboard, family resources
- Agent loop infrastructure — this document + GitHub + Claude

-----

## PART 3 — HL-DETECT SPECIFICATION

### Purpose

hl-detect is a JavaScript library that analyzes text and identifies linguistic patterns associated with behavioral manipulation.

It does not care about HTML. It does not care about DOM structure.
It does not care about which platform the text came from.
It takes a string. It returns findings.

### Input

```
hlDetect(text, options)
```

- text: string — any text to analyze
- options: object (optional)
  - minConfidence: number 0-1 (default 0.6)
  - maxPatterns: number (default all)
  - explain: boolean (default true)
  - context: string — optional context hint

### Output

```
{
  text: string,
  flagged: boolean,
  patternCount: number,
  dominantPattern: string,
  escalationScore: number,
  patterns: [
    {
      type: string,
      confidence: number,
      label: string,
      explanation: string,
      evidence: string[],
      severity: string
    }
  ],
  metadata: {
    processingTimeMs: number,
    textLength: number,
    version: string
  }
}
```

### Pattern Library — Version 0.1

Seven core patterns implemented: suppression_framing, false_urgency, incomplete_hook, outrage_engineering, false_authority, tribal_activation, engagement_directive. Full pattern specifications in hl-detect source.

### Calibration Requirements

The library MUST:

- Return zero false positives on straightforward factual news reporting
- Return zero false positives on personal social media posts about daily life
- Return zero false positives on academic or scientific writing
- Correctly identify at least 80% of patterns in documented examples
- Process 1000 words in under 100ms on a standard laptop

The library MUST NOT:

- Flag political content solely because of its political position
- Flag emotional language in appropriate contexts (grief, celebration)
- Flag urgent language when urgency is genuine (emergency alerts)
- Flag authority claims when authority is properly cited

-----

## PART 4 — CURRENT STATE

### What Exists

- hoffmanlenses.org — live on Cloudflare, deployed
- White paper v2 — complete, cited, 25 references
- hl-detect v0.1.0 — standalone manipulation detection library, 64/64 tests passing
- Browser extension v0.2.3 — HALTED. Functional but no longer the primary product.
- Hoffman Browser v0.1.0 (Electron) — PRIMARY PRODUCT, active development
  - Location: hoffman-browser/ in hoffman-core repo
  - LLM: Llama 3.2 3B Instruct Q4_K_M, runs on CPU, on-device only
  - Text extraction: document.body.innerText via webContents.executeJavaScript
  - Analysis: JSON output, natural language fallback parsing
  - First successful analysis: Fox News — outrage_engineering + war_framing flagged
  - BMID: “Why is this here?” wired end-to-end, localhost:5000
  - Status: running, needs OCR for image text
- BMID API v0.1 — Python/Flask/SQLite, running at localhost:5000
  - 3 fishermen: facebook.com, instagram.com, youtube.com
  - 9 motives, 16 catches, 33 evidence records
  - Sourced from March 2026 intel/investigate agent cycles
- GitHub: HoffmanLensesInitiative/hoffman-core (monorepo)
- Claude Code v2.1.87 — connected, authenticated, operational

### What Needs to Be Built Next

1. OCR integration — tesseract.js reads text from images in the viewport
1. BMID network/actor schema — new tables for corporate mapping
1. Top 25 BMS operators research — Intel team standing mandate
1. hoffmanlenses.org missing pages: /extension, /families, /research, /remembrance

-----

## PART 5 — DECISIONS LOG

All significant decisions recorded here so agents do not revisit settled questions.

**2026-03-25: Browser over extension as primary product**
Decision: The primary Hoffman product is a browser, not a platform-specific extension.
Director: Norm Robichaud

**2026-03-25: Language as the detection surface**
Decision: hl-detect reads rendered text, not DOM structure. Manipulation is a property of language, not platform structure.
Director: Norm Robichaud

**2026-03-25: No mobile iOS pursuit**
Decision: Do not pursue iOS App Store distribution. Apple’s gatekeeper restrictions make iOS an unreliable distribution channel.
Director: Norm Robichaud

**2026-03-25: Electron for Stage 3 browser**
Decision: Build Hoffman browser on Electron first, not native Chromium fork.
Director: Norm Robichaud

**2026-03-25: Agent loop architecture**
Decision: Use agentic loop with this document as the central memory store.
Director: Norm Robichaud

**2026-03-25: Research tool framing for Phase 1**
Decision: Position Hoffman as a research instrument first, consumer product second.
Director: Norm Robichaud

**2026-03-25: Zero data retention**
Decision: Hoffman retains zero user data after session ends. All processing local. Non-negotiable. Never changes.
Director: Norm Robichaud

**2026-03-29: Browser and BMID are a loop, not two separate tools**
Decision: The Hoffman Browser and BMID must be developed as an integrated system. BMID informs the browser before analysis runs. The browser feeds BMID over time.
Director: Norm Robichaud

**2026-03-29: Extension development halted — browser is the primary product**
Decision: Stop all extension development. The Hoffman Browser (Electron) is now the sole primary build target. Intel, investigation, BMID, and advocacy work continue unchanged.
Director: Norm Robichaud

**2026-03-29: OCR as next major browser capability**
Decision: Integrate tesseract.js for on-device OCR of viewport screenshots. browserView.webContents.capturePage() captures the visible area; tesseract.js reads it without native binaries or network calls.
Director: Norm Robichaud

**2026-03-29: hl-detect has NO role in the browser detection pipeline**
Decision: hl-detect is explicitly NOT used as a pre-screen, triage layer, or hint generator in the Hoffman Browser analysis pipeline. The local model reads the full page text directly and is the sole detector.
Reason: hl-detect is a regex library with 67 rules. It only catches what someone remembered to write a rule for. During development it missed 14 of 15 real-world manipulation examples. The correct analogy: hl-detect is a corpsman with a checklist. The local model is the doctor who reads the whole room. The doctor does not need the corpsman to pre-screen. hl-detect’s legitimate roles: (1) standalone npm library for developers; (2) potentially a fast pre-screen for very high volume batch processing in future — not current architecture. The 67 patterns inform the model’s system prompt as vocabulary, not as code. Do not add hl-detect to the browser pipeline. This decision is settled.
Director: Norm Robichaud

**2026-03-30: Evidence integrity standard — non-negotiable**
Decision: Every claim in the BMID must meet a documented evidence standard. Hearsay, unnamed sources, unverified social media posts, speculation, and inference without documentation are not acceptable as evidence at any confidence level. Unknown is a valid answer. Evidence gaps are investigation targets, not reasons to infer.
Director: Norm Robichaud

**2026-03-30: Network and actor mapping added to BMID scope**
Decision: The BMID is extended to document corporate networks and individual actors, not just individual platforms. This includes ownership chains, investment relationships, board overlaps, personnel movement between platforms, political relationships, and documented moments of knowing conduct. Corporations do not make decisions. People do. Accountability requires identifying the humans in the chain.
Director: Norm Robichaud

**2026-03-30: Top 25 BMS operators — standing research mandate**
Decision: Intel team is tasked with building and maintaining a ranked list of the top 25 global BMS operators. The list is evidence-based, politically balanced, and updated as new evidence emerges. Every entry requires primary source documentation.
Director: Norm Robichaud

**2026-03-30: Political balance is mandatory in all research**
Decision: The BMID and all agent research must document BMS operators across the full political spectrum. A list that only flags one political side is advocacy, not research. The evidence standard — not political alignment — determines inclusion.
Director: Norm Robichaud

-----

## PART 6 — AGENT INSTRUCTIONS

### For any AI agent reading this document:

You are a contributor to the Hoffman project. Your role is to implement what is specified here, test what you build, and record what you learn.

**Before acting:**

1. Read this entire document
1. Read the Current State section — know what exists
1. Read the Decisions Log — do not revisit settled decisions
1. Identify the current build target (marked CURRENT STAGE)

**While acting:**

1. Build what is specified
1. Test against the examples provided
1. Note anything unclear or contradictory
1. Note any decisions you needed to make that aren’t covered

**After acting:**

1. Record what you built in the Build Log (Part 7)
1. Record test results
1. Record open questions for the next cycle
1. Flag any decisions made for director review
1. Update the Current State section

**What you must never do:**

- Deviate from the zero data retention principle
- Build anything that sends user data to external servers without explicit opt-in and anonymization
- Introduce dependencies on specific platform DOM structures into hl-detect
- Make architectural decisions that contradict the Decisions Log without flagging for director review
- Record claims in the BMID without primary source documentation
- Speculate or infer when evidence is absent — record as unknown

**The mission:**
Every line of code you write serves the families named in the white paper dedication. JackLynn Blackwell was nine years old. She loved karaoke. She wanted to be a star. Build accordingly.

-----

## PART 7 — BUILD LOG

### Cycle 0 — Foundation (March 2026)

**Agent:** Claude (Anthropic)
**Director:** Norm Robichaud
**Actions taken:**

- Built browser extension v0.1.0 (Facebook-specific)
- Built hoffmanlenses.org website
- Wrote white paper v2 with 25 citations
- Established GitHub organization HoffmanLensesInitiative
- Created two repositories
- Documented 7-workstream project plan
- Established agentic loop architecture

**What worked:**

- Extension successfully detects manipulation on Facebook
- Session bar running correctly
- Annotation panel appearing on flagged posts

**Next cycle target:** Build hl-detect v0.1

-----

### Cycle 1 — hl-detect v0.1.0 (March 2026)

**Agent:** Claude (Anthropic)
**Director:** Norm Robichaud
**Actions taken:**

- Built hl-detect v0.1.0 — standalone manipulation detection library
- 7 patterns implemented
- 64/64 tests passing

**What worked:**

- All 7 patterns detecting correctly on target examples
- Zero false positives on factual news, academic writing, personal posts
- Processes 1000 words in under 100ms

**Next cycle target:** Universal extension

-----

### Cycle 2 — Universal Extension v0.2.0 (March 2026)

**Agent:** Claude (Anthropic)
**Director:** Norm Robichaud
**Actions taken:**

- Built universal extension v0.2.0
- Replaced platform-specific adapters with universal reader.js
- Integrated hl-detect v0.1.0
- Validated on foxnews.com — 416 blocks scanned, 5 flagged

**What worked:**

- Extension running on foxnews.com
- False authority pattern firing correctly on health headlines
- Universal text-based detection validated

**Next cycle target:** Extension refinements, then browser pivot

-----

### Cycle 3 — Agent Organization + BMID (March 2026)

**Agent:** Claude (Anthropic)
**Director:** Norm Robichaud
**Actions taken:**

- Built four supervisor documents: BUILD, INTEL, INVESTIGATE, ADVOCATE
- Built BMID API v0.1 (Python/Flask/SQLite)
  - 7 endpoints: health, fisherman, bait, explain, pattern, search, session
  - Seeded first fisherman record: Meta Platforms
  - Seeded first catch record: Molly Russell (UK Coroner 2022)
- Updated HOFFMAN.md with agent organization and BMID architecture

**What works:**

- BMID API starts, initializes database, seeds records
- All endpoints tested and passing

**Next cycle targets:**

- Deploy BMID API
- Wire “Why is this here?” button
- Intelligence agents begin populating Meta record

-----

### Cycle 4 — Hoffman Browser v0.1.0 (March 2026)

**Agent:** Claude (Anthropic) + Director sessions
**Director:** Norm Robichaud
**Actions taken:**

- Built Hoffman Browser on Electron
- Integrated Llama 3.2 3B Instruct Q4_K_M — runs on CPU, on-device only
- Text extraction via webContents.executeJavaScript(‘document.body.innerText’)
- First successful analysis: Fox News flagged outrage_engineering + war_framing on “WAR WITH IRAN”
- Wired “Why is this here?” button to BMID localhost:5000
- Extension development formally halted
- hl-detect formally removed from browser detection pipeline
- Decision recorded: model is the sole detector, hl-detect has no role in browser pipeline
- Claude Code v2.1.87 installed and connected to GitHub

**What works:**

- Browser launches and renders pages
- Llama 3.2 3B loads on CPU
- JSON analysis pipeline: page text → model → structured flags → panel
- Fox News: 2 flags returned (outrage_engineering HIGH, war_framing HIGH)
- “Why is this here?” button wired to BMID

**Known limitations:**

- Image text not analyzed — manipulation in memes not detected
- Occupy Democrats returned clean because manipulation is in images, not text
- Analysis takes 5-15 minutes on CPU — GPU support future work
- Context window (2048) limits page text to ~1200 chars per analysis
- CodePink did not render fully — user agent spoofing needed

**Next cycle targets:**

1. OCR integration (tesseract.js) for image text
1. BMID network/actor schema implementation
1. Top 25 BMS operators research begins

-----

### Cycle 5 — Architecture Expansion (March 30, 2026)

**Director:** Norm Robichaud
**Actions directed:**

- Added Evidence Integrity Standard (Part 12)
- Added Network and Actor Architecture (Part 13)
- Added Top 25 BMS Operators mandate (Part 14)
- Updated Investigate team mandate to include network mapping
- Updated Intel team mandate to include Top 25 research
- Extended BMID schema with 6 new tables: network, actor, actor_role, actor_investment, actor_political, actor_knowledge
- Added 5 new BMID API endpoints for network and actor data
- Identified priority actor records to open: Zuckerberg, R. Murdoch

**Rationale:**
Individual platform documentation is necessary but insufficient. Accountability requires mapping the humans in the chain. The Top 25 list gives the project a research roadmap and gives Hoffman Browser a pre-analysis intelligence layer. Political balance is non-negotiable — BMS is not partisan.

-----

## PART 8 — OPEN QUESTIONS

1. What confidence threshold should trigger annotation display? Current thinking: 0.7 default, user-adjustable
1. How should hl-detect handle multilingual text? Current thinking: English only for v0.1
1. Should hl-detect be synchronous or async? Current thinking: synchronous for v0.1
1. How do we prevent the coordinated_language pattern from requiring multiple API calls? Current thinking: session-level memory
1. What is the right visual language for ambient annotation in a full browser?
1. How do we handle paywalled content?
1. What local AI model is the right fit for future versions? Current: Llama 3.2 3B
1. What is the legal threshold for conspiracy liability between connected BMS operators? Refer to legal counsel when available.
1. Which academic institutions are currently researching BMS networks and could be natural partners?
1. At what point does the BMID network map have sufficient data to be useful as a public-facing visualization?
1. Should actor records be public or restricted? Privacy interests vs. public accountability. Director decision required.
1. How do we handle actors who leave a platform and then take steps to address harm? The record should reflect the full arc.

-----

## PART 9 — RESOURCES

### Key documents

- White paper: hoffmanlenses.org/whitepaper
- Extension code: github.com/HoffmanLensesInitiative/hoffman-lenses-extension
- Website code: github.com/HoffmanLensesInitiative/hoffman-lenses-website

### Key contacts

- Project director: Norm Robichaud
- Contact: contact@hoffmanlenses.org (not yet active — Proton Mail pending)
- Press: press@hoffmanlenses.org (not yet active)
- Families: families@hoffmanlenses.org (not yet active)

### Relevant prior art

- Shoshana Zuboff, “The Age of Surveillance Capitalism” (2019)
- Jonathan Haidt, “The Anxious Generation” (2024)
- Frances Haugen Senate testimony (October 2021)
- Molly Russell inquest findings (September 2022)
- UN Guiding Principles on Business and Human Rights (2011)

-----

## PART 10 — AGENT ORGANIZATION

### Structure

```
DIRECTOR (Norm Robichaud)
    |
    |-- SUPERVISOR: BUILD         (HOFFMAN_BUILD.md)
    |       |-- Hoffman Browser agent  [PRIMARY -- Electron, LLM, OCR]
    |       |-- BMID API agent
    |       |-- Website agent
    |       |-- hl-detect agent        [maintenance only]
    |       |-- Extension agent        [HALTED -- do not assign work]
    |
    |-- SUPERVISOR: INTELLIGENCE  (HOFFMAN_INTEL.md)
    |       |-- Database agent
    |       |-- Publisher research agent
    |       |-- Pattern documentation agent
    |       |-- Top 25 BMS research agent [NEW]
    |
    |-- SUPERVISOR: INVESTIGATION (HOFFMAN_INVESTIGATE.md)
    |       |-- Deep research agents (rabbit holes)
    |       |-- Legal/court record agent
    |       |-- Academic literature agent
    |       |-- Corporate ownership agent [NEW]
    |       |-- Actor accountability agent [NEW]
    |
    |-- SUPERVISOR: ADVOCACY      (HOFFMAN_ADVOCATE.md)
            |-- White paper agent
            |-- Family outreach agent
            |-- Press agent
            |-- Legislative monitoring agent
```

### Updated Investigate Team Mandate

The Investigate team’s scope explicitly includes:

**Corporate network mapping:**
For every active fisherman file, map the complete corporate structure with evidence:

- Parent company and ownership chain
- Subsidiary platforms and properties
- Known corporate relationships with other fishermen
- Investment relationships and board compositions

**Actor accountability chains:**
For every active fisherman file, identify and document:

- The top 5 individual actors with documented decision-making roles
- When each actor first had documented knowledge of harm
- What action each actor took in response (or did not take)
- Connections to actors at other fisherman organizations

**Coordination evidence:**

- Shared technology, shared algorithms, shared data agreements
- Personnel movement between fisherman organizations
- Documented communications between fisherman organizations
- Shared political relationships or coordinated lobbying

**The “Meaningful Social Interactions” thread (Meta — active):**
Continue following this thread. If internal documents show Meta knew the 2018 algorithm change made harm worse while publicly claiming it was a fix, that is documented knowing deception. Establish: who received the internal findings, what they said in public after receiving them, and what the precise dates are.

### Updated Intel Team Mandate

The Intel team’s scope explicitly includes:

**Top 25 BMS operator research (standing mandate):**
Research and document candidates for the Top 25 list. One to two fully evidenced entries per cycle. See Part 14 for full specification.

**Network awareness:**
When researching any fisherman, flag all known connections to other fishermen. These connections feed the network tables.

**Actor identification:**
When researching any fisherman, identify named individuals with documented roles and flag them for actor record creation. Do not create actor records without primary source documentation.

### Supervisor documents

- HOFFMAN_BUILD.md — build queue, current state, build log
- HOFFMAN_INTEL.md — intelligence queue, BMID status, research targets
- HOFFMAN_INVESTIGATE.md — investigation queue, rabbit hole findings
- HOFFMAN_ADVOCATE.md — outreach queue, family contacts, press contacts

-----

## PART 11 — BMID ARCHITECTURE

### What it is

The Behavioral Manipulation Intelligence Database. An open intelligence repository documenting the supply chain of online manipulation: who does it, how they do it, where they lead people, and what harm has resulted.

### Schema location

hoffman-core/BMID_SCHEMA.md

### API location

hoffman-core/bmid-api/

### Status (March 2026)

- Schema: COMPLETE (extended March 30, 2026 — see Part 13)
- API: v0.1 BUILT AND TESTED, running at localhost:5000
- Database: 3 fishermen (facebook.com, instagram.com, youtube.com), 9 motives, 16 catches, 33 evidence records

### The integration vision — Browser and BMID as a loop

The browser and BMID are not two separate tools. They are two faces of the same system. BMID is institutional knowledge. The browser is the field instrument.

**Direction 1 — BMID informs the browser before analysis runs:**
When the user navigates to a page, query BMID for the domain. If a fisherman record exists, prepend that intelligence to the model’s system prompt as context. The model reads a Fox News page differently knowing Fox Corp’s documented motive structure.

**Direction 2 — Browser findings feed BMID:**
Every analysis the browser completes is potential intelligence. User session data (opt-in, anonymized) builds a picture of which sites use which techniques in the wild.

**Direction 3 — Cross-reference strengthens confidence:**
When the browser returns a flag, check whether BMID lists that technique as a known pattern for that fisherman. If so, display higher confidence.

### The “Why is this here?” pipeline (current)

Browser detects technique → user clicks button on flag card → panel-preload.js calls ipcRenderer.invoke(‘query-bmid’, domain, technique) → main.js calls GET localhost:5000/api/v1/explain → API returns fisherman record + motives + catch_summary → Panel renders: owner, business model, first motive, documented harm count, confidence

-----

## PART 12 — EVIDENCE INTEGRITY STANDARD

### The Standard

Every claim in the BMID must meet this standard before being recorded. This applies to all agents, all cycles, all research.

**Acceptable evidence (in order of preference):**

1. Court filings, judicial rulings, coroner findings — highest weight
1. Sworn congressional or parliamentary testimony — high weight
1. Internal documents disclosed through legal proceedings or whistleblower disclosure — high weight (verify chain of custody)
1. Regulatory filings (FTC, FCC, SEC, equivalent international bodies) — high weight
1. Named journalist + named publication + verifiable reporting — medium weight
1. Peer-reviewed academic research with named authors and institutions — medium weight
1. Official organizational statements and press releases — medium weight (documents what was said, not necessarily what is true)

**Not acceptable as evidence:**

- Anonymous sources (“sources say”, “insiders report”)
- Unnamed experts (“experts believe”, “researchers suggest” without citation)
- Unverified social media posts
- Speculation or inference without documented basis
- Hearsay — what someone heard someone else say
- Secondary reporting without traceable primary source
- Anything that cannot be independently verified

**Unknown is a valid and required answer:**

If a fact is not documented, record it as unknown. Do not infer. Do not fill gaps with assumptions. Do not extrapolate from adjacent facts. An evidence gap is an investigation target. Record it as such.

**Confidence scoring:**

All BMID records include a confidence score (0.0 to 1.0).

- 0.90-1.00: Primary source documentation, multiple independent sources
- 0.70-0.89: Strong secondary sources, single strong primary source
- 0.50-0.69: Credible reporting, limited primary source documentation
- 0.30-0.49: Early investigation, evidence collection in progress
- 0.00-0.29: Candidate only, insufficient evidence to characterize

**The test:**

Before recording any claim, ask: “Could this withstand scrutiny in a court proceeding or academic peer review?” If no — it does not belong in the BMID as fact. It may belong as an open investigation question.

-----

## PART 13 — NETWORK AND ACTOR ARCHITECTURE

### Why This Matters

Documenting individual platforms is necessary but insufficient. The manipulation ecosystem is a network — platforms owned by the same entities, funded by the same investors, run by executives who move between them carrying the same practices, coordinated in ways that may constitute conspiracy under existing law.

Corporations do not make decisions. People do.

The accountability chain that matters in law and in history is: Which person knew? When did they know it? What did they choose to do? Who profited from that choice? Who else was connected to that choice?

The BMID’s network and actor layers answer these questions with evidence.

### BMID Schema Extension — Network Tables

```sql
-- Corporate and ownership relationships between fishermen
CREATE TABLE IF NOT EXISTS network (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  parent_fisherman_id INTEGER REFERENCES fisherman(id),
  child_fisherman_id INTEGER REFERENCES fisherman(id),
  relationship_type TEXT NOT NULL,
  -- owns | funds | coordinates | shares_technology |
  -- amplifies | board_overlap | investment | regulatory_capture
  description TEXT,
  evidence TEXT NOT NULL,
  source_url TEXT,
  date_established TEXT,
  date_ended TEXT,
  confidence REAL DEFAULT 0.5,
  verified INTEGER DEFAULT 0,
  notes TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Individual actors with documented roles and knowledge
CREATE TABLE IF NOT EXISTS actor (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  name_aliases TEXT,
  current_role TEXT,
  current_fisherman_id INTEGER REFERENCES fisherman(id),
  documented_knowledge_of_harm INTEGER DEFAULT 0,
  knowledge_source TEXT,
  knowledge_date TEXT,
  notes TEXT,
  confidence REAL DEFAULT 0.5,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Actor roles across platforms over time
CREATE TABLE IF NOT EXISTS actor_role (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor_id INTEGER REFERENCES actor(id),
  fisherman_id INTEGER REFERENCES fisherman(id),
  role TEXT NOT NULL,
  date_start TEXT,
  date_end TEXT,
  evidence TEXT NOT NULL,
  source_url TEXT,
  notes TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Actor investment positions
CREATE TABLE IF NOT EXISTS actor_investment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor_id INTEGER REFERENCES actor(id),
  fisherman_id INTEGER REFERENCES fisherman(id),
  position_type TEXT NOT NULL,
  -- board | investor | major_shareholder | advisor | creditor
  stake_description TEXT,
  date_start TEXT,
  date_end TEXT,
  evidence TEXT NOT NULL,
  source_url TEXT,
  notes TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Actor political relationships
CREATE TABLE IF NOT EXISTS actor_political (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor_id INTEGER REFERENCES actor(id),
  relationship_type TEXT NOT NULL,
  -- donation | lobbying | regulatory_capture | testimony |
  -- government_appointment | revolving_door
  recipient TEXT,
  amount TEXT,
  date TEXT,
  jurisdiction TEXT,
  evidence TEXT NOT NULL,
  source_url TEXT,
  notes TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Known moments of documented awareness of harm
CREATE TABLE IF NOT EXISTS actor_knowledge (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor_id INTEGER REFERENCES actor(id),
  fisherman_id INTEGER REFERENCES fisherman(id),
  knowledge_type TEXT NOT NULL,
  -- internal_research | whistleblower_report | external_study |
  -- regulatory_finding | court_proceeding | media_coverage
  description TEXT NOT NULL,
  date TEXT NOT NULL,
  action_taken TEXT,
  evidence TEXT NOT NULL,
  source_url TEXT,
  confidence REAL DEFAULT 0.5,
  notes TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
```

### New BMID API Endpoints

```
GET /api/v1/network/{domain}
  Returns all documented relationships for a fisherman domain.
  Includes parent companies, subsidiaries, investment relationships,
  board overlaps, and coordination with other fishermen.

GET /api/v1/actor/{actor_id}
  Returns full profile for a documented actor.
  All roles across all platforms, investment positions,
  political relationships, and documented knowledge of harm.

GET /api/v1/actor/search?name={name}
  Search actors by name.

GET /api/v1/network/map
  Returns the full network graph as JSON suitable for visualization.
  Nodes: fishermen and actors.
  Edges: all documented relationships.

GET /api/v1/accountability/{domain}
  Returns the full accountability chain for a domain.
  Parent companies → key actors → documented knowledge moments →
  political relationships → documented harm.

GET /api/v1/conspiracy/{fisherman_id_1}/{fisherman_id_2}
  Returns documented connections between two fishermen.
  Shared ownership, shared investors, shared board members,
  documented coordination, shared personnel.
```

### Priority Actor Records to Open

The following actors have sufficient primary source documentation to open records immediately. Intel team to begin with these.

**Mark Zuckerberg**

- Founder and CEO, Meta Platforms
- Congressional testimony: April 2018, October 2021
- Frances Haugen documents: received by his team, documented
- Internal research on teen harm: documented in WSJ Facebook Files
- Confidence basis: sworn testimony, court filings, internal documents

**Rupert Murdoch / Lachlan Murdoch**

- Fox Corporation, News Corp
- Dominion Voting Systems lawsuit: internal communications disclosed
- UK Leveson Inquiry: documented testimony
- Confidence basis: court filings, sworn testimony, public record

Additional candidates requiring research before opening records:
Sundar Pichai (Google/YouTube), Shou Zi Chew (TikTok), Linda Yaccarino (X/Twitter), Bill Ackman (investor), Peter Thiel (investor).

-----

## PART 14 — TOP 25 BMS OPERATORS

### Standing Research Mandate — Intel Team

Build and maintain a ranked list of the top 25 global BMS operators. This is a living document, updated as evidence emerges. File location: hoffman-core/BMID_TOP25.md

### Ranking Criteria (in order of weight)

1. **Documented harm** — legal findings, coroner rulings, academic studies, whistleblower testimony, regulatory action. Most important criterion.
1. **Reach** — monthly active users, content impressions, audience size.
1. **Revenue model** — percentage of revenue dependent on engagement maximization.
1. **Algorithmic amplification** — documented evidence the platform’s algorithm amplifies outrage, fear, or tribal content.
1. **Awareness and intent** — internal documents or legal findings showing the operator knew about harm and continued the practice.

### Evidence Sources

- Pew Research Center media and platform studies
- Reuters Institute Digital News Report (annual)
- Knight Foundation research
- MIT Media Lab, Oxford Internet Institute, Stanford Internet Observatory
- Congressional and parliamentary testimony transcripts
- FTC, FCC, Ofcom, and equivalent international regulatory filings
- Coroner rulings and court findings
- Whistleblower disclosures (Frances Haugen, Sophie Zhang, others)
- State and federal attorney general filings
- Peer-reviewed journals: Journal of Communication, New Media & Society, Social Media + Society

### Mandatory Constraints

**Political balance is non-negotiable.**
BMS operators exist across the full political spectrum. The list must reflect that. The evidence standard — not political alignment — determines inclusion.

**Every entry requires primary source documentation.**
Opinion is not evidence. Reporting without a named primary source is not sufficient for top-tier ranking.

**Unknown is recorded as unknown.**
If reach, revenue model, or harm documentation is unavailable, record as not yet documented. Do not estimate or infer.

**Foreign state operators belong alongside domestic ones.**
Manipulation is manipulation regardless of national origin.

**The list is not permanent.**
Entries can be removed if evidence does not support inclusion. The Director reviews all additions to the top 10 before finalization.

### Output Format (for each entry in BMID_TOP25.md)

```
RANK: [1-25]
FISHERMAN: [operator name]
DOMAIN: [primary domain]
OWNER: [parent company / controlling entity]
REACH: [MAU or equivalent, with source and date]
REVENUE_MODEL: [how they monetize engagement, with source]
HARM_DOCUMENTED: [yes/no + brief description]
HARM_SOURCE: [primary source citation]
PRIMARY_SOURCES: [list with URLs]
ACTOR_RECORDS: [named actors with open BMID records]
NETWORK_CONNECTIONS: [known connections to other ranked operators]
BMID_STATUS: [file open / candidate / not yet opened]
CONFIDENCE: [0.0-1.0]
LAST_UPDATED: [date]
NOTES: [anything significant, open questions]
```

### Candidate List (unranked — research required before ranking)

Domestic platforms and networks:
Meta (Facebook/Instagram/WhatsApp/Threads), Google/YouTube, TikTok (US operations), Twitter/X, Fox News / Fox Corporation, Occupy Democrats, InfoWars / Alex Jones Network, Breitbart, The Daily Wire, Newsmax, One America News, MSNBC / NBCUniversal, The Daily Mail (US operations), Sinclair Broadcast Group, The New York Post, specific coordinated social media account networks

Foreign state operators:
RT (Russia Today), Sputnik, CGTN (China Global Television Network), Iran International, specific Telegram channel networks with documented state sponsorship

Emerging or specialized:
Specific podcast networks with documented radicalization pathways, specific Instagram/TikTok influencer networks functioning as coordinated amplification systems, foreign influence operation networks documented in Senate Intelligence Committee reports

### Intel Team Delivery Schedule

- Each cycle: research and fully document 1-2 candidates
- Quality over speed: a fully evidenced entry is worth more than 10 partially evidenced ones
- When a candidate has sufficient evidence, open a full BMID fisherman file and link from the Top 25 entry
- Director reviews Top 10 placements before finalizing

-----

*“They deserved better than to be engagement metrics.”*

*HOFFMAN.md is a living document.*
*It grows with every cycle.*
*It remembers everything.*

-----

**Dedicated to:**
JackLynn Blackwell (age 9, Texas, February 3, 2026)
Molly Russell (age 14, London, 2017)
Nylah Anderson (age 10, Philadelphia, 2021)
CJ Dawley (age 14, Wisconsin)
Amanda Todd (age 15, BC Canada, 2012)
Sadie Riggs (age 15, Pennsylvania, 2015)
Englyn Roberts
Frankie Thomas

*And to every child whose name we have not yet learned.*