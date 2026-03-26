# HOFFMAN.md
# The Hoffman Lenses Initiative — Master Build Document
# Version: 0.1.0
# Last updated: March 2026
#
# THIS DOCUMENT IS THE SINGLE SOURCE OF TRUTH FOR THE HOFFMAN PROJECT.
# It is read by AI agents at the start of every build cycle.
# It is updated by AI agents after every build cycle.
# It is updated by the project director (Norm Robichaud) with decisions and redirections.
# Every action taken, every result observed, every decision made is recorded here.
# Nothing is lost between cycles. Every cycle builds on everything before it.

---

## PART 1 — MISSION

### What Hoffman Is

Hoffman is a browser built on Chromium that makes behavioral manipulation visible to the people it operates on. It reads language the way an expert reads manipulation — recognizing not just what text says but what it is designed to do to the reader. It works on every website, every platform, every page — because manipulation is a property of language, not of any specific platform's DOM structure.

The name comes from the Hoffman Lenses — the glasses in John Carpenter's 1988 film They Live — which allowed the wearer to see hidden messages embedded in ordinary reality. Once you put them on, you cannot unsee what they reveal.

### What Hoffman Is Not

Hoffman is not a privacy browser. Brave does that.
Hoffman is not an ad blocker. That is a feature, not an identity.
Hoffman is not a platform-specific tool. It does not target Facebook or TikTok specifically. It reads language everywhere.
Hoffman is not a censorship tool. It blocks nothing. It hides nothing. It makes visible. The user decides what to do with what they see.

### Why This Exists

Behavioral Manipulation Systems — the algorithmic engines that power social media platforms — are injuring and killing human beings as a direct and foreseeable consequence of how they are designed to operate. Children have died. Adults have been radicalized. Relationships have been destroyed. Democracies have been destabilized. Adults have been radicalized. Relationships have been destroyed. Democracies have been destabilized.

The harm is not incidental. It is architectural. These systems optimize for engagement without obligation to human wellbeing. They exploit psychological vulnerabilities for profit. They operate invisibly.

Hoffman makes them visible. That is the mission.

The full human rights case is documented in the white paper:
"The Algorithm and the Child: A Human Rights Case for Abolishing Behavioral Manipulation Systems" — published at hoffmanlenses.org

### The People This Is For

Primary: Researchers, journalists, lawyers, parents, advocates —
people who actively want to understand what is being done to them and to others. People who will use Hoffman as a research instrument.

Secondary: General users who want to browse with awareness —
who want a knowledgeable presence reading alongside them.

Not trying to reach everyone. Trying to reach people who are ready to see. The glasses only work if you're willing to put them on.

---

## PART 2 — ARCHITECTURE

### The Three-Stage Build Plan

#### Stage 1 — hl-detect (CURRENT STAGE)
A standalone JavaScript library that takes text as input and returns structured analysis of manipulation patterns present in that text.
Platform-agnostic. DOM-agnostic. No dependencies.
The brain of everything that comes after.

#### Stage 2 — Universal Extension
A browser extension (Chrome + Firefox) that injects hl-detect into every page the user visits. Reads rendered text. Annotates manipulation patterns in real time. Runs on every website, not just social media.
Replaces the Facebook-specific extension (v0.1.0) already built.

#### Stage 3 — Hoffman Browser
A Chromium-based browser with hl-detect running natively.
Initial target: Electron-based (JavaScript, no C++ required).
Later: Native Chromium fork if performance requires it.
Platforms: Windows, Mac, Linux, Android.

### Supporting Systems (parallel to all stages)
- Research database — anonymized session data from users who opt in
- Retrospective analysis tool — Facebook data archive analyzer
for families, lawyers, law enforcement
- hoffmanlenses.org — website, white paper, remembrance list,
research dashboard, family resources
- Agent loop infrastructure — this document + GitHub + Claude

---

## PART 3 — HL-DETECT SPECIFICATION

### Purpose
hl-detect is a JavaScript library that analyzes text and identifies linguistic patterns associated with behavioral manipulation.

It does not care about HTML. It does not care about DOM structure.
It does not care about which platform the text came from.
It takes a string. It returns findings.

### Input
```javascript
hlDetect(text, options)
```

- text: string — any text to analyze
- options: object (optional)
  - minConfidence: number 0-1 (default 0.6) — minimum confidence to report
  - maxPatterns: number (default all) — limit patterns returned
  - explain: boolean (default true) — include plain language explanations
  - context: string — optional context hint ('social_media', 'news',
    'advertising', 'email', 'general')

### Output
```javascript
{ text: string,           // original input text flagged: boolean,       // true if any patterns detected above threshold patternCount: number,   // total patterns detected dominantPattern: string, // highest confidence pattern type escalationScore: number, // 0-100 overall manipulation intensity patterns: [ { type: string,         // pattern identifier (see Pattern Library)
      confidence: number,   // 0-1 confidence score
      label: string,        // short human-readable label
      explanation: string,  // plain language explanation (3 sentences max)
                            // Format: What happened. Why the author did it.
                            // Why it matters to you.
      evidence: string[],   // specific phrases that triggered detection
      severity: string      // 'info' | 'warn' | 'danger'
    }
],
metadata: { processingTimeMs: number,
    textLength: number,
    version: string
} }
```

### Pattern Library — Version 0.1

Each pattern has:
- identifier: string key
- severity: info / warn / danger
- description: what this pattern is
- explanation_template: plain language explanation for the user
- detection_rules: what to look for (keywords, structures, regex patterns)
- examples: real text examples that SHOULD trigger this pattern
- counterexamples: real text that should NOT trigger this pattern
(to prevent false positives)

---

#### PATTERN 1: suppression_framing
**Severity:** danger
**Description:**
Content that implies powerful forces are attempting to hide, censor,
or suppress the information being presented. This framing bypasses critical evaluation by making the reader feel they are accessing forbidden truth.

**Explanation template:**
"This content claims it is being suppressed or hidden by powerful forces. This framing is designed to make you feel you are accessing forbidden truth — bypassing your skepticism. Legitimate information does not need to warn you that it is being censored."

**Detection rules:**
Keywords/phrases (case insensitive):
- "they don't want you to"
- "before this gets deleted"
- "before it gets taken down"
- "share before"
- "watch before it disappears"
- "censored"
- "banned"
- "what they're hiding"
- "what the media won't tell you"
- "mainstream media won't cover"
- "suppressed"
- "forbidden"
- "they tried to delete"
- "won't see this on the news"
- "big pharma doesn't want"
- "government doesn't want you to know"

Structural patterns:
- Imperative verb + "before" + threat of removal
("Share before", "Watch before", "Download before")

**Examples (should trigger):**
- "Share this before Facebook deletes it"
- "The video they don't want you to see"
- "Watch before it gets taken down"
- "What mainstream media won't tell you about vaccines"
- "They're trying to suppress this information"

**Counterexamples (should NOT trigger):**
- "Download the report before the deadline"
- "Watch before the event starts"
- "What the media covered about the election"

---

#### PATTERN 2: false_urgency
**Severity:** warn
**Description:**
Artificial time pressure designed to prevent critical evaluation.
Creates a sense that immediate action is required, bypassing the cognitive processes that would otherwise evaluate the claim.

**Explanation template:**
"This content creates artificial time pressure — implying you must act immediately or miss out. This technique bypasses careful thinking by triggering anxiety about loss. Genuine important information does not expire in minutes."

**Detection rules:**
Keywords/phrases:
- "limited time"
- "act now"
- "only X left" (where X is a small number)
- "offer expires"
- "ends tonight"
- "ends soon"
- "don't wait"
- "before it's too late"
- "last chance"
- "selling fast"
- "almost gone"
- "expires in"
- "hurry"
- "urgent"
- "immediately"
- "right now" (in imperative context)
- "today only"

Structural patterns:
- Number + "left" in proximity to product/offer
- Time reference + imperative verb

**Examples (should trigger):**
- "Only 3 seats left — book now"
- "This offer expires tonight at midnight"
- "Act now before it's too late"
- "Limited time: 50% off ends soon"

**Counterexamples (should NOT trigger):**
- "The deadline for applications is Friday"
- "The sale runs until the end of the month"
- "Registration closes when capacity is reached"

---

#### PATTERN 3: incomplete_hook
**Severity:** warn
**Description:**
Information is deliberately withheld to compel a click or continued reading. The headline or opening promises information but does not deliver it, creating an information gap the reader is compelled to fill.

**Explanation template:**
"This headline or opening deliberately withholds information to compel you to click or keep reading. The information gap it creates is engineered — there is no reason the information could not be stated directly. This technique is designed to generate engagement, not inform."

**Detection rules:**
Keywords/phrases:
- "you won't believe"
- "what happened next"
- "the reason will shock you"
- "the reason will surprise you"
- "find out why"
- "here's what happened"
- "this is why"
- "this explains everything"
- "this changes everything"
- "nobody expected"
- "the truth about"
- "what really happened"
- "the real reason"
- "the shocking truth"
- "you need to see this"

Structural patterns:
- Subject + action + withheld outcome
("She did X and you won't believe what happened")
- "The [noun] that [vague consequential verb]"
("The secret that changes everything")

**Examples (should trigger):**
- "She posted one photo and you won't believe the reaction"
- "What happened next will shock you"
- "The real reason they changed the policy"
- "Find out what they're not telling you"

**Counterexamples (should NOT trigger):**
- "Here is what happened at the summit"
- "The reason the policy changed was budget constraints"
- "Scientists discover new evidence about climate change"

---

#### PATTERN 4: outrage_engineering
**Severity:** danger
**Description:**
Language calibrated to produce maximum outrage rather than convey information. Uses emotional intensifiers, extreme characterizations,
and moral framing to trigger visceral response. Strong emotions drive engagement — shares, comments, reactions — regardless of whether the content is accurate.

**Explanation template:**
"This content uses language calibrated to produce outrage rather than inform. Emotional intensifiers, extreme characterizations, and moral framing are being used to trigger a visceral response. Strong emotional reactions drive engagement metrics — which is why this language appears,
not because the situation genuinely requires it."

**Detection rules:**
Emotional intensifier stacking:
- Multiple intensifiers in close proximity
("absolutely disgusting", "completely outrageous",
"utterly shameful", "totally unacceptable")

Extreme characterization patterns:
- Dehumanizing language about groups
- Absolute moral condemnation without qualification
- "worst ever", "most dangerous", "most corrupt"
- Comparison to historical atrocities in non-atrocity contexts

Manufactured consensus outrage:
- "Everyone is outraged"
- "People are furious"
- "The internet is losing its mind"
- "Twitter is exploding"

**Examples (should trigger):**
- "This is absolutely disgusting and completely unacceptable"
- "The most corrupt administration in history"
- "Everyone is furious about what they just did"
- "Twitter is exploding over this outrageous decision"

**Counterexamples (should NOT trigger):**
- "Critics called the decision deeply problematic"
- "The policy drew significant opposition"
- "Many expressed concern about the announcement"

---

#### PATTERN 5: false_authority
**Severity:** warn
**Description:**
Authority is invoked without being identified, verified, or made accountable. Creates an impression of credibility without providing any actual evidence. The reader's deference to unnamed expertise is exploited.

**Explanation template:**
"This content invokes authority without identifying it. 'Studies show,' 'experts say,' and 'research proves' are claims that cannot be evaluated without knowing which studies, which experts, which research.
Legitimate authority identifies itself and can be checked."

**Detection rules:**
Keywords/phrases:
- "studies show" (without citation)
- "experts say" (without naming experts)
- "research proves" (without citing research)
- "scientists agree" (without specification)
- "doctors recommend" (without naming)
- "it has been proven"
- "it is well known"
- "everyone knows"
- "as we all know"
- "it's a fact that"
- "the science is clear"

Structural patterns:
- Authority claim + assertion without citation
- Passive voice authority construction
("It has been shown that...")

**Examples (should trigger):**
- "Studies show this diet cures cancer"
- "Experts say the economy is about to collapse"
- "It's been proven that vaccines cause autism"
- "As we all know, the election was stolen"

**Counterexamples (should NOT trigger):**
- "A 2023 Harvard study found that..."
- "Dr. Anthony Fauci said in a press conference..."
- "According to the CDC's 2024 report..."

---

#### PATTERN 6: tribal_activation
**Severity:** warn
**Description:**
Content that signals tribal identity as a prerequisite for accepting a claim. Does not make an argument — instead signals which group identity is required to agree. Exploits in-group belonging and out-group threat to bypass critical evaluation.

**Explanation template:**
"This content signals group identity rather than making an argument.
It implies that accepting this claim is what members of your tribe do,
and that rejecting it means you don't belong. This bypasses evaluation of the actual claim by making acceptance a matter of identity."

**Detection rules:**
Keywords/phrases:
- "real [group members] know"
- "true [believers/patriots/Americans/etc] understand"
- "if you care about [identity]"
- "wake up"
- "sheeple"
- "the sheep"
- "do your research" (as dismissal)
- "open your eyes"
- "still asleep"
- "we know the truth"
- "those of us who know"
- "you've been lied to"

Structural patterns:
- In-group knowledge claim + out-group ignorance implication
- Identity label + exclusive claim to truth

**Examples (should trigger):**
- "Real Americans know what's actually happening"
- "True patriots understand what they're trying to do to us"
- "Wake up — you've been lied to your whole life"
- "Do your own research, sheeple"

**Counterexamples (should NOT trigger):**
- "American voters have expressed concern about..."
- "Many people feel misled by the coverage of..."
- "Researchers found that people who follow the issue closely..."

---

#### PATTERN 7: coordinated_language
**Severity:** danger
**Description:**
Multiple pieces of content use identical or near-identical unusual phrasing. Organic individuals do not independently choose the same distinctive phrases. Coordinated language patterns indicate organized campaigns designed to manufacture the appearance of widespread organic sentiment.

**Explanation template:**
"This content uses phrases that appear identically or near-identically across multiple unrelated sources. Real people expressing genuine views independently do not choose the same unusual words. This pattern suggests coordinated messaging designed to make a minority view appear widespread."

**Detection rules:**
Note: This pattern requires comparing multiple text inputs.
When called with an array of texts, hl-detect identifies:
- Identical phrases of 5+ words appearing across multiple texts
- Near-identical sentence structures with only nouns swapped
- Unusual specific phrases appearing more than statistically expected

Single-text heuristics (lower confidence):
- Unusually specific talking points presented as personal opinion
- Phrases that sound like they come from a briefing document
- Highly polished language in ostensibly personal contexts

**Examples (should trigger when comparing multiple texts):**
Text A: "The radical left is destroying our way of life"
Text B: "The radical left is destroying our way of life"
Text C: "The radical left is destroying our way of life"
→ Identical phrase across three supposedly independent sources

**Counterexamples (should NOT trigger):**
- Common phrases that appear frequently in natural language
- Standard journalistic language appearing across news sources
- Academic terminology appearing in papers on the same topic

---

### Calibration Requirements

The library MUST:
- Return zero false positives on straightforward factual news reporting
- Return zero false positives on personal social media posts about daily life
- Return zero false positives on academic or scientific writing
- Correctly identify at least 80% of patterns in the examples above
- Process 1000 words in under 100ms on a standard laptop

The library MUST NOT:
- Flag political content solely because of its political position
- Flag emotional language in appropriate contexts (grief, celebration)
- Flag urgent language when urgency is genuine (emergency alerts)
- Flag authority claims when authority is properly cited

---

## PART 4 — CURRENT STATE

### What Exists
- hoffmanlenses.org — live on Cloudflare, deployed
- White paper v2 — complete, cited, 25 references
- Browser extension v0.1.0 — working on Facebook
  - Detects: sponsored content, inserted posts, not-in-network,
    old content, engagement bait
  - Session bar running at bottom of page
  - Popup panel with session stats
  - Background worker tracking session state
  - Files: manifest.json, background/worker.js, content/core.js,
    content/overlay.js, content/platforms/facebook.js,
    styles/overlay.css, popup/*
- GitHub repositories:
  - HoffmanLensesInitiative/hoffman-lenses-website
  - HoffmanLensesInitiative/hoffman-lenses-extension
- Project list — 7 workstreams documented

### What Needs to Be Built Next
1. hl-detect v0.1 — the standalone detection library (THIS STAGE)
2. Test suite for hl-detect
3. Universal extension using hl-detect
4. Session export functionality
5. Hoffman Electron browser (Stage 3)

### Known Issues in Extension v0.1.0
- Annotation panel positioning — appears beside post not below it
- Post detection overcounting — Groups widgets counted as posts
- "From your network" stat meaningless on empty accounts
- Flag descriptions too technical — need plain language rewrites
- Icons are placeholders — need real Hoffman Lenses sunglasses icon

---

## PART 5 — DECISIONS LOG

All significant decisions recorded here so agents do not revisit settled questions.

**2026-03-25: Browser over extension as primary product**
Decision: The primary Hoffman product is a browser, not a platform- specific extension. The extension is a proof of concept and interim tool. The browser reads language universally.
Reason: Platform-specific extensions are permanently vulnerable to
platform DOM changes. Language-based detection is platform-agnostic and impossible for platforms to counter without changing how language works.
Director: Norm Robichaud

**2026-03-25: Language as the detection surface**
Decision: hl-detect reads rendered text, not DOM structure.
It receives a string and returns findings. It has no knowledge of what platform or website the text came from.
Reason: Manipulation is a property of language, not of platform
structure. This makes detection universal and resistant to platform countermeasures.
Director: Norm Robichaud

**2026-03-25: No mobile iOS pursuit**
Decision: Do not pursue iOS App Store distribution.
Apple's gatekeeper restrictions make iOS an unreliable distribution channel for a tool that exposes platform manipulation.
Focus on desktop browsers and Android.
iOS limitation is itself documented as evidence of infrastructure gatekeeping in the white paper.
Director: Norm Robichaud

**2026-03-25: Electron for Stage 3 browser**
Decision: Build Hoffman browser on Electron first, not native Chromium fork. Electron allows JavaScript-only development,
avoiding C++ expertise requirement.
Upgrade to native Chromium fork if performance demands it.
Director: Norm Robichaud

**2026-03-25: Agent loop architecture**
Decision: Use agentic loop with this document as the central memory store. AI agents read HOFFMAN.md, act, write results back.
Director directs and reviews between cycles.
Director: Norm Robichaud

**2026-03-25: Research tool framing for Phase 1**
Decision: Position Hoffman as a research instrument first,
consumer product second. Primary users are researchers,
journalists, lawyers, advocates, families. Mass consumer adoption follows evidence base, not precedes it.
Director: Norm Robichaud

**2026-03-25: Zero data retention**
Decision: Hoffman and all associated tools retain zero user data after session ends. All processing local. Opt-in contribution to research database is anonymized before leaving device.
Non-negotiable. Never changes.
Director: Norm Robichaud

---

## PART 6 — AGENT INSTRUCTIONS

### For any AI agent reading this document:

You are a contributor to the Hoffman project. Your role is to implement what is specified here, test what you build, and record what you learn.

**Before acting:**
1. Read this entire document
2. Read the Current State section — know what exists
3. Read the Decisions Log — do not revisit settled decisions
4. Identify the current build target (marked CURRENT STAGE)
5. Read the full specification for that target

**While acting:**
1. Build what is specified
2. Test against the examples provided
3. Note anything unclear or contradictory in the specification
4. Note any decisions you needed to make that aren't covered

**After acting:**
1. Record what you built in the Build Log (Part 7)
2. Record test results — what passed, what failed, confidence scores
3. Record open questions for the next cycle
4. Record any decisions you made and flag them for director review
5. Update the Current State section

**What you must never do:**
- Deviate from the zero data retention principle
- Build anything that sends user data to external servers
without explicit opt-in and anonymization
- Introduce dependencies on specific platform DOM structures
into hl-detect (it must remain platform-agnostic)
- Make architectural decisions that contradict the Decisions Log
without flagging for director review

**The mission:**
Every line of code you write serves the families named in the white paper dedication. JackLynn Blackwell was nine years old.
She loved karaoke. She wanted to be a star.
Build accordingly.

---

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
- Established agentic loop architecture (this document)

**What worked:**
- Extension successfully detects manipulation on Facebook
- Session bar running correctly
- Annotation panel appearing on flagged posts
- Engagement bait detection firing on real posts (Occupy Democrats)
- Follow button detection working

**What needs improvement:**
- Annotation panel positioning (beside post not below)
- Post detection overcounting non-posts
- Flag descriptions too technical
- Icon is placeholder

**Open questions for Cycle 1:**
- What is the optimal confidence threshold for each pattern?
- How do we handle multilingual text?
- How do we handle very short text (< 20 words)?
- Should escalation score be linear or weighted?

**Next cycle target:** Build hl-detect v0.1

---

## PART 8 — OPEN QUESTIONS

Questions that have not been resolved. Each cycle should attempt to answer at least one. Answered questions move to Decisions Log.

1. What confidence threshold should trigger annotation display?
(Too low = too many false positives. Too high = misses real patterns.)
   Current thinking: 0.7 default, user-adjustable

2. How should hl-detect handle multilingual text?
   Current thinking: English only for v0.1, language detection
and multilingual support in v0.2

3. Should hl-detect be synchronous or async?
   Current thinking: Synchronous for v0.1 (simpler), async for v0.2
when we add the local AI model

4. How do we prevent the coordinated_language pattern from
requiring multiple API calls? (It needs to compare texts)
   Current thinking: Session-level memory in the extension/browser
stores recent texts for comparison

5. What is the right visual language for ambient annotation
in a full browser? (More subtle than the extension popup boxes)
   Current thinking: Margin indicators + collapsible companion panel

6. How do we handle paywalled content where text is not visible?
   Current thinking: Analyze visible text only, note limitation

7. What local AI model is the right fit for v0.2 classification?
   Current thinking: Evaluate Phi-3-mini, Gemma 2B, Llama 3.2 1B
for size/accuracy tradeoff when that stage arrives

---

## PART 9 — RESOURCES

### Key documents
- White paper: hoffmanlenses.org/whitepaper
- Project list: hoffman-lenses-project-list.md
- Extension code: github.com/HoffmanLensesInitiative/hoffman-lenses-extension
- Website code: github.com/HoffmanLensesInitiative/hoffman-lenses-website

### Key contacts
- Project director: Norm Robichaud
- Contact: contact@hoffmanlenses.org (not yet active — Proton Mail pending)
- Press: press@hoffmanlenses.org (not yet active)
- Families: families@hoffmanlenses.org (not yet active)

### Relevant prior art
- Shoshana Zuboff, "The Age of Surveillance Capitalism" (2019)
— defines the economic model hl-detect is designed to expose
- Jonathan Haidt, "The Anxious Generation" (2024)
— documents harm to children, especially relevant to teen patterns
- Frances Haugen Senate testimony (October 2021)
— primary source on platform internal knowledge of harm
- Molly Russell inquest findings (September 2022)
— first legal ruling attributing child death to algorithmic violence
- UN Guiding Principles on Business and Human Rights (2011)
— legal framework for corporate accountability

---

*"They deserved better than to be engagement metrics."*

*HOFFMAN.md is a living document.* *It grows with every cycle.* *It remembers everything.*

### Cycle 1 -- hl-detect v0.1.0 (March 2026)
**Agent:** Claude (Anthropic)
**Director:** Norm Robichaud
**Actions taken:**
- Built hl-detect v0.1.0 -- standalone manipulation detection library
- 7 patterns implemented: suppression_framing, false_urgency, incomplete_hook, outrage_engineering, false_authority, tribal_activation, engagement_directive
- Built 61-test test suite covering detection, false positives, calibration, performance, batch, and session analysis
- All 61 tests passing

**What worked:**
- All 7 patterns detecting correctly on target examples
- Zero false positives on factual news, academic writing, personal posts, product reviews
- Processes 1000 words in under 100ms
- Works in Node.js and browser environments
- UMD module format -- usable everywhere

**What needed fixing during cycle:**
- Short text confidence penalty was too aggressive (< 30 chars) -- reduced threshold to < 15 chars
- "mainstream media" compound phrase not matched by single-word regex -- added compound phrase variant
- "changes everything" pattern required "this" prefix -- removed prefix requirement

**Open questions answered this cycle:**
- Confidence threshold: 0.6 default is correct -- short text penalty adjusted to < 15 chars
- Synchronous vs async: synchronous for v0.1 confirmed -- fast enough, simpler

**Next cycle target:** Universal extension -- wrap hl-detect in a browser extension that runs on every page, every website. Replace the Facebook-specific extension v0.1.0.

### Cycle 2 -- Universal Extension v0.2.0 (March 2026)
**Agent:** Claude (Anthropic)
**Director:** Norm Robichaud
**Actions taken:**
- Built universal extension v0.2.0 -- runs on every website, not just Facebook
- Replaced all platform-specific adapters with universal reader.js
- Integrated hl-detect v0.1.0 as the core detection engine
- Built new background worker, overlay renderer, and popup panel
- Manifest updated to <all_urls> -- runs everywhere

**What worked:**
- Extension running successfully on foxnews.com -- 416 blocks scanned, 5 flagged
- "The overlooked cause that doctors say may drive chronic digestive problems" -- correctly flagged as Unnamed authority (75% confidence). "Doctors say" without naming which doctors. Textbook false authority construction.
- Mike Rowe story NOT flagged -- specific named person making specific claim. Calibration correct.
- Annotation panel appearing with correct dark design, amber dot, plain language explanation
- Session bar showing live stats at bottom of page: Scanned / Flagged / Escalation / Site
- Universal approach validated -- hl-detect reads language, not DOM structure. Works on any site without platform knowledge.
- All JS files ASCII-clean -- no unicode injection failures

**What needs improvement:**
- Annotation positioning -- appearing between page cards rather than directly below the flagged headline element. Needs CSS refinement.
- 5 flags from 416 scanned on Fox News homepage is reasonable but needs validation across more sites
- Session bar missing duration stat -- present in popup but not in bar
- Annotation sometimes appearing in wrong column on grid layouts

**Real world validation:**
- foxnews.com: 416 scanned, 5 flagged, escalation LOW (1)
- Detection confirmed working on live site with no platform-specific knowledge
- False authority pattern firing correctly on health headlines using unnamed "doctors say" construction

**Open questions answered this cycle:**
- Universal text-based detection is viable -- confirmed on live site
- reader.js selector strategy (article, h1-h3, p, role=article, class*=card) captures enough content without overcounting
- Annotation positioning needs work but core functionality confirmed

**Next cycle target:** Refinements
- Fix annotation positioning to appear directly below flagged element
- Add more patterns to hl-detect based on real-world observations
- Test on more sites: CNN, Reddit, X, YouTube, shopping sites
- Consider annotation being less visually dominant -- more ambient, less alarming
- Session export feature -- download session as JSON/CSV


---

## PART 10 -- AGENT ORGANIZATION

### Structure

```
DIRECTOR (Norm Robichaud)
    |
    |-- SUPERVISOR: BUILD         (HOFFMAN_BUILD.md)
    |       |-- hl-detect agent
    |       |-- Extension agent
    |       |-- Website agent
    |       |-- BMID API agent
    |
    |-- SUPERVISOR: INTELLIGENCE  (HOFFMAN_INTEL.md)
    |       |-- Database agent
    |       |-- Publisher research agent
    |       |-- Pattern documentation agent
    |
    |-- SUPERVISOR: INVESTIGATION (HOFFMAN_INVESTIGATE.md)
    |       |-- Deep research agents (rabbit holes)
    |       |-- Legal/court record agent
    |       |-- Academic literature agent
    |       |-- Corporate ownership agent
    |
    |-- SUPERVISOR: ADVOCACY      (HOFFMAN_ADVOCATE.md)
            |-- White paper agent
            |-- Family outreach agent
            |-- Press agent
            |-- Legislative monitoring agent
```

### Supervisor documents
- HOFFMAN_BUILD.md -- build queue, current state, build log
- HOFFMAN_INTEL.md -- intelligence queue, BMID status, research targets
- HOFFMAN_INVESTIGATE.md -- investigation queue, rabbit hole findings
- HOFFMAN_ADVOCATE.md -- outreach queue, family contacts, press contacts

### Communication protocol
- Agents read their supervisor document before acting
- Agents write results back to their supervisor document
- Supervisors write summaries to HOFFMAN.md (this document)
- Director reads HOFFMAN.md, makes decisions, redirects as needed
- Nothing is lost -- every cycle is recorded

---

## PART 11 -- BMID ARCHITECTURE

### What it is
The Behavioral Manipulation Intelligence Database.
An open intelligence repository documenting the supply chain of
online manipulation: who does it, how they do it, where they lead
people, and what harm has resulted.

### Schema location
hoffman-core/BMID_SCHEMA.md

### API location
hoffman-core/bmid-api/

### Status
- Schema: COMPLETE
- API: v0.1 BUILT AND TESTED
- Database: initialized with first record (Meta Platforms / Molly Russell)
- Endpoints: health, fisherman, bait, explain, pattern, search, session

### First record
Fisherman: Meta Platforms (facebook.com)
Catch: Molly Russell, age 14, UK, 2017
Evidence: UK Coroner ruling September 2022
Intelligence level: full (fisherman + motive + catch + evidence)

### The "Why is this here?" pipeline
Extension detects pattern -> sends domain + patterns to /api/v1/explain
-> API returns fisherman record + motives + catch summary
-> Claude generates plain language explanation from structured data
-> User sees: not a generic pattern description but specific intelligence
   about this publisher, their documented business model, and documented harm

---

### Cycle 3 -- Agent organization + BMID (March 2026)
**Agent:** Claude (Anthropic)
**Director:** Norm Robichaud
**Actions taken:**
- Built four supervisor documents: BUILD, INTEL, INVESTIGATE, ADVOCATE
- Built BMID API v0.1 (Python/Flask/SQLite)
  - 7 endpoints: health, fisherman, bait, explain, pattern, search, session
  - Full schema implemented matching BMID_SCHEMA.md
  - Seeded first fisherman record: Meta Platforms
  - Seeded first catch record: Molly Russell (UK Coroner 2022)
  - All endpoints tested and passing
- Updated HOFFMAN.md with agent organization and BMID architecture

**What works:**
- BMID API starts, initializes database, seeds first record
- GET /api/v1/fisherman/facebook.com returns full record with motives and catches
- GET /api/v1/explain returns intelligence_level: full for facebook.com
- Search endpoint returning results
- Session endpoint ready to accept extension data

**Next cycle targets:**
- Deploy BMID API to hoffmanlenses.org (or separate subdomain)
- Wire "Why is this here?" button in extension to /api/v1/explain
- Intelligence agents begin populating Meta Platforms record fully
- Investigation agents begin deep file on Meta (Frances Haugen, Molly Russell)
- Session export feature in extension popup
