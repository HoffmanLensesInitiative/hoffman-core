# Hoffman Lenses -- Director Briefing
## 2026-03-30

### What got done today

**ADVOCATE** prepared four documents for email infrastructure and family outreach: a Proton Mail setup guide, a family outreach protocol with consent framework, a draft family letter template, and a press kit outline. No outreach will occur until you set up the email accounts and approve the materials.

**BUILD** completed a web-based admin interface for the BMID database at localhost:5000/admin. The GUI includes a dashboard with counts, a filterable fishermen list with detail pages, a catches table with filters, and raw JSON panels for debugging. All read-only, dark theme, no external dependencies.

**INTEL** added 10 new evidence records for existing fishermen (Meta and YouTube), primarily regulatory decisions and court filings. Key additions include the FTC $5B Meta consent decree, the EU DPC €1.2B fine, the 41-state AG complaint, Haugen's congressional testimony, and Guillaume Chaslot's Senate testimony on YouTube's algorithm.

**INVESTIGATE** completed the Break Glass investigation documenting eight specific algorithmic interventions Meta used during the 2020 election, their confirmed effectiveness, and their deliberate reversal afterward. The Civic Integrity team dissolution in December 2020 is flagged as significant—Meta dismantled the team that knew how to operate the safety measures.

### Files created or modified

- `reports/advocate-draft-protonmail-setup.md`
- `reports/advocate-draft-family-outreach-protocol.md`
- `reports/advocate-draft-family-letter-template.md`
- `reports/advocate-draft-press-kit-outline.md`
- `bmid-api/templates/admin/base.html`
- `bmid-api/templates/admin/index.html`
- `bmid-api/templates/admin/fishermen.html`
- `bmid-api/templates/admin/fisherman_detail.html`
- `bmid-api/templates/admin/catches.html`
- `bmid-api/app.py` (admin routes added)
- `reports/investigate-meta-break-glass-measures.md`

### Decisions needed from you

1. **Proton Mail setup** — You need to create the accounts in Proton Mail's web interface. The guide is ready at `reports/advocate-draft-protonmail-setup.md`.

2. **Family letter template approval** — Review `reports/advocate-draft-family-letter-template.md`. It mentions the project was "catalyzed" by JackLynn Blackwell's story—confirm this framing is accurate and appropriate.

3. **Blackwell family contact timing** — Protocol recommends 60-day minimum wait from date of death (February 3, 2026), meaning earliest contact April 4, 2026. Confirm this timing.

4. **Anderson family approach** — Given active litigation, protocol recommends contact through Social Media Victims Law Center rather than directly. Confirm this approach.

5. **Founder bio** — Press kit needs a Norm Robichaud bio. Provide or approve the text.

### Things to know

The INVESTIGATE finding on break glass measures is significant for litigation value: Meta had eight documented interventions that worked, they knew they worked, and they chose to turn them off and dissolve the team that operated them. Every algorithmic harm since January 2021 occurred while proven countermeasures sat unused. This is not negligence—it's documented choice.

INTEL flagged that YouTube lacks a whistleblower disclosure equivalent to Frances Haugen's. Evidence for YouTube motives relies more heavily on external research and Guillaume Chaslot's testimony rather than internal documents.

### What happens tomorrow

**ADVOCATE** waits for email infrastructure before any outreach work.

**BUILD** will build the /press and /remembrance pages on hoffmanlenses.org once email is active.

**INTEL** will complete Twitter/X evidence records (8 catches and 4 motives need primary source links).

**INVESTIGATE** will pursue Rabbit Hole 17: internal communications around the Civic Integrity team dissolution in December 2020.