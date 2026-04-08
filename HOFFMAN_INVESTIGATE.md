# HOFFMAN_INVESTIGATE.md
# Hoffman Lenses -- Investigation Supervisor Document
# Supervisor agent: manages deep research and rabbit hole teams
# Reports to: Director (HOFFMAN.md)
# Last updated: March 2026

---

## MISSION

Go deep. Follow threads. Find what is documented but not yet compiled.

Investigation agents do not write code and do not maintain databases.
They research. They find primary sources. They map ownership structures.
They read court filings, academic papers, Senate testimony, and corporate
disclosures. They hand structured intelligence files to the Intel team.

The standard: find things that are true, documented, and not yet in the BMID.

---

## CURRENT STATE

### Active investigations
- None yet initiated

### Completed investigations
- None

### Standing research mandates
Every investigation team always maintains awareness of:
- New academic papers on algorithmic harm (weekly scan)
- New legal filings against Meta, TikTok, Alphabet, Twitter/X (weekly scan)
- New legislative activity on platform regulation (weekly scan)
- New documented child harm cases attributed to platforms (ongoing)

---

## SUBMISSIONS QUEUE (PRIORITY 0)

Every investigation cycle begins by calling `fetch_submissions` to retrieve pending
user-submitted domains from the BMID cloud. Users who analyze pages with the Hoffman
Browser and flag them as manipulative can contribute those findings for agent review.

For each submission: research the domain, then call `update_submission` with:
- `"accepted"` + `seed_cloud_bmid` call if the domain is a verified manipulation actor
- `"rejected"` + notes if the submission appears incorrect or the domain is benign
- `"investigating"` + current notes if more cycles are needed

---

## INVESTIGATION QUEUE

### Priority 1: Meta Platforms deep file
Goal: Complete evidence package for BMID Fisherman record
Sources to mine:
- Molly Russell inquest findings (Sept 2022) -- full PDF
- Frances Haugen Senate testimony (Oct 2021) -- full transcript
- WSJ Facebook Files series (Sept-Oct 2021) -- all articles
- FTC v. Meta complaint (2023) -- full filing
- Meta's own internal research documents (disclosed in litigation)
- Academic: Braghieri, Levy, Makarin (2022) -- Social Media and Mental Health
- Academic: Haidt & Allen (2020) -- Scrutinizing the effects of digital technology

Deliverable: structured BMID records for
  - 1 Fisherman record (Meta Platforms)
  - 3+ Motive records
  - 5+ Catch records with evidence
  - 10+ Evidence records

### Priority 2: Corporate ownership mapping
Goal: Map who owns the top 20 most manipulative domains
      (identified from extension session data as they accumulate)
Sources: SEC filings, Companies House, OpenCorporates, MediaBias/FactCheck
Deliverable: ownership tree for each domain, confidence-scored

### Priority 3: Ad network mapping
Goal: Document which advertising networks serve ads on
      high-manipulation-score domains
Sources: ads.txt files, DoubleVerify reports, GARM brand safety lists
Deliverable: net records linking fishermen to their advertising infrastructure

---

## AGENT INSTRUCTIONS

### For any investigation agent reading this document:

You follow threads. One finding leads to the next.
Document the chain, not just the conclusion.

Before investigating:
1. Read this document and BMID_SCHEMA.md
2. Check the investigation queue
3. Search existing BMID records -- do not duplicate work

While investigating:
1. Primary sources only -- court filings, official transcripts,
   published academic papers, corporate disclosures, government reports
2. For each finding, record: what it proves, where you found it, URL,
   archive URL (archive.org), date accessed
3. When a thread leads somewhere unexpected -- follow it and flag it
4. Never fabricate citations -- if you cannot find a primary source,
   say so and note it as an open question
5. Sensitive findings (active cases, potential defamation risk) --
   flag immediately for director review before writing to BMID

After investigating:
1. Write a structured intelligence file matching BMID schema
2. Hand off to Intel supervisor for database entry
3. Update Investigation Log below
4. List unresolved threads for the next investigation cycle

### The rabbit hole protocol:
When an investigation reveals an unexpected connection --
  a corporate ownership link, a shared ad network, a coordinated
  language pattern across supposedly independent sites --
flag it as a RABBIT HOLE FINDING and dedicate a full cycle to it.
These unexpected connections are often the most valuable discoveries.

---

## INVESTIGATION LOG

### Session 0 (March 2026)
No investigations yet initiated.
Priority queue established.
Standing mandates active.

---

## RABBIT HOLE FINDINGS

None yet. This section grows as investigation agents discover
unexpected connections.


---

<!-- AUTO CYCLE 2026-04-08 05:35 UTC -->

I'll investigate Rabbit Hole 21 — The MSI Mitigation Decision Chain — the critical gap in the Meta accountability record: who specifically made the decision to deprioritize the mitigation of the Meaningful Social Interactions algorithm harm.## CYCLE RESULT — INVESTIGATE — 2026-04-08 05:30 UTC

---

### Investigation target

**Rabbit Hole 21 — The MSI Mitigation Decision Chain**
Meta Platforms: Who specifically received the 2019 internal harm research findings on the Meaningful Social Interactions algorithm, who made the call to deprioritize the mitigation proposals, and whether that decision is documented anywhere in the primary source record.

---

### Key findings

**1. The public announcement vs. the internal reality — precisely dated.**
Zuckerberg's January 11, 2018 Facebook post characterizing MSI as a "wellbeing" initiative is primary-sourced and archived. The internal research documenting harms is dated to *2019* — one full year after the public announcement. This timing matters: the deception case rests not on the 2018 announcement itself (made before the findings existed) but on continued positive public characterization *after* 2019, which is an open investigation target (SEC 8-K earnings call transcripts, 2020–2021).

**2. The decision chain gap is real and precisely defined.**
The WSJ Facebook Files (named reporters Horwitz, Hagey, Seetharaman — high weight) documents that:
- Internal researchers wrote "our algorithms exploit the human brain's attraction to negativity" (2019 internal presentation, researcher unnamed)
- Specific mitigation proposals were developed and documented in writing
- The proposals were not implemented, "partly out of fear it would reduce engagement"

The gap: "presented to Facebook's most senior executives, including Zuckerberg" is sourced in the WSJ to **unnamed persons familiar with the matter** — which does not meet BMID's evidence standard for recording as fact. Confidence ceiling: 0.75 until a primary source is located.

**3. Haugen's sworn testimony on Zuckerberg's knowledge is a belief statement.**
Her exact testimony was "I believe he was aware of the research" — sworn, high weight, but not direct personal knowledge. It is recorded at 0.75 with this characterization.

**4. Three named actors are now open investigation targets.**
- **Sheryl Sandberg** (COO, 2008–2022): Organizational responsibility for the revenue side — the "fear of reduced engagement" motivation — but no primary source document places her in receipt of the 2019 MSI harm findings. Unknown. Not yet sufficient for actor record.
- **Guy Rosen** (VP Integrity): The integrity team is the organizational home of the researchers who generated the findings. His name does not appear in the MSI decision chain documents. Investigation target: Facebook Papers deep read, 2023 Senate testimony transcript.
- **Chris Cox** (Chief Product Officer, left March 2019): Had organizational authority over News Feed as a product decision. A critical variable: if the 2019 internal presentation was Q1 before March, Cox may have been in the decision chain. The precise month of the presentation is not in the public record. This is an open investigation target.

**5. Two independent paths to close the gap — one faster than the other.**
- **Path A (slower):** Facebook Papers or FTC v. Meta discovery document naming a specific executive as having received and decided against the 2019 proposals.
- **Path B (faster):** SEC EDGAR 8-K filings contain Meta earnings call transcripts. If a named executive made specific positive public claims about MSI *after* the 2019 internal findings, that independently establishes the deception claim without requiring the internal decision document. These filings are public, searchable, and do not require litigation discovery.

**6. The existing documented accountability chain is already substantial.**
Even with the named-individual gap, the chain holds: harm documented → internal knowledge documented (2019) → mitigation proposals documented → non-implementation documented → business model motive documented → public/private gap documented. What is missing is the named person in the room. Everything around that person is documented.

---

### Rabbit hole findings

**New rabbit hole — The Chris Cox departure timing.**
Cox left as CPO in March 2019. The internal harm presentation is dated "2019." If it was February or March 2019 and Cox received it before leaving, he is potentially in the decision chain. If it was April or later, the decision fell to whoever held product authority in his absence. Meta did not immediately name a CPO replacement — Zuckerberg reportedly assumed more direct product oversight during this period. This timing gap may actually strengthen the Zuckerberg accountability case: if there was no CPO in the organizational chart between Cox's departure and a replacement, product decisions including algorithm changes would have escalated directly to Zuckerberg. This is inference without documentation — recorded as open investigation target, not fact.

**New rabbit hole — The Sandberg departure timing.**
Sandberg left Meta in July 2022, eight months after the Haugen disclosures (October 2021). Her departure announcement cited a desire to focus on philanthropy and her foundation. The proximity to the Haugen disclosures is notable. BMID standard: notable but not evidence of anything without documentation. Investigation target: did Sandberg make any statement about the MSI algorithm or internal harm research at any point between October 2021 and her departure? Any such statement would add to the actor knowledge record.

**Confirmed rabbit hole — Path B (SEC 8-K earnings calls).**
This is not speculative. The filings are public. Q1 2020 through Q4 2021 earnings calls are in the SEC record. If any named executive made a specific positive characterization of MSI in those calls after the 2019 internal findings, that is a documented primary source that strengthens the accountability case significantly — and it requires no litigation, no disclosure, and no unnamed sources. This is the priority next investigation step.

---

### Files written

`reports/investigate-meta-msi-decision-chain.md` — 43,825 characters

**Contents:**
- Part 1: Full MSI announcement documentation and technical implementation
- Part 2: Three major internal findings (outrage amplification, mitigation proposals, teen body image) — primary-sourced
- Part 3: The decision chain — what is documented, what is alleged, what is unknown (table format, confidence-scored)
- Part 4: The public statement vs. internal reality gap — precisely dated
- Part 5: Academic corroboration (Braghieri et al. AER 2022; Huszár et al. PNAS 2022; Rathje et al. PNAS 2021)
- Part 6: The decision chain current documented state — structured truth table with confidence scores
- Part 7: The Sheryl Sandberg thread
- Part 8: The Guy Rosen / Integrity Team thread
- Part 9: The Chris Cox thread
- Part 10: What the known record establishes — seven-element accountability chain
- Part 11: BMID records ready for Intel team — actor record targets, evidence targets
- Part 12: Investigation summary and confidence assessment
- Part 13: Investigator notes on evidence quality, political balance, JackLynn Blackwell
- Appendix A: Full primary sources index

---

### Next cycle recommendation

**Immediate priority: Evidence Target 1 — SEC EDGAR 8-K earnings call review.**

This is Path B to closing the accountability gap. Meta's quarterly earnings call transcripts for Q1 2020 through Q4 2021 are publicly filed with the SEC as 8-K attachments at `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001326801&type=8-K`. If any named executive made a specific positive characterization of MSI in these calls — characterizing it as a wellbeing initiative or denying harm — *after* the 2019 internal findings, that closes the deception claim from the outside without requiring the internal decision document.

This is faster than waiting for litigation discovery and requires only reading public filings. A single cycle dedicated to this review would either close this thread definitively or confirm that the earnings calls do not address MSI specifically — both of which are useful findings.

**After Path B:** Rabbit Hole 22 — Haugen SEC filing deep read. The eight SEC complaints filed September 13, 2021 are the highest-weight legal documents in the Haugen disclosure. A systematic comparison of their content against Senate testimony and Facebook Papers journalism would identify any claims documented under oath that have not yet made it into the BMID evidence record.

---

*Evidence integrity: Every material claim traces to a named primary source. The accountability gap is documented precisely — not papered over. Unknown is recorded as unknown. Three investigation paths are identified and prioritized. The JackLynn Blackwell record remains at 0.30. Build accordingly.*

---

<!-- AUTO CYCLE 2026-04-08 15:18 UTC -->

I'll start by fetching pending submissions and then proceed to the investigation queue.Submissions queue unavailable (API key not set in this environment). Proceeding to the investigation queue.

The priority investigation from the last cycle was **Evidence Target 1 — SEC EDGAR 8-K earnings call review** (Path B): systematically reading Meta's public quarterly earnings call transcripts (Q1 2020 – Q4 2021) to determine whether any named executive made positive public characterizations of the Meaningful Social Interactions algorithm *after* the 2019 internal harm findings — closing the deception claim from the outside without requiring litigation discovery.

Let me compile the full intelligence file now.Now let me fetch the submissions queue before finalizing the cycle result.No API key configured — proceeding to the investigation queue. The investigation target for this cycle is **Evidence Target 1 / Path B: Meta SEC EDGAR 8-K earnings call review** — the fastest documented path to closing the MSI accountability gap identified in the previous cycle.Now seed the new actor records and evidence into the BMID: