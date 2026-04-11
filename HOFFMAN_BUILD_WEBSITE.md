# HOFFMAN_BUILD_WEBSITE.md
# Hoffman Lenses -- Website Build Supervisor
# Scope: hoffmanlenses.org (Cloudflare Pages, static site)
# Reports to: Director (HOFFMAN.md)
# Last updated: March 2026

---

## MISSION

Build and maintain hoffmanlenses.org -- the public face of the Hoffman Lenses Initiative.

The website serves researchers, journalists, families, and advocates.
It hosts the white paper, documents the mission, and provides resources.
It must be direct, serious, and human. No corporate polish. No marketing language.

The website is hosted on Cloudflare Pages from the repository:
github.com/HoffmanLensesInitiative/hoffman-lenses-website

Note: This is a SEPARATE repository from hoffman-core. The website agent works
on files in the hoffman-lenses-website/ directory of the local machine, which
tracks the hoffman-lenses-website GitHub repository. Changes must be committed
and pushed to that repo, not to hoffman-core.

---

## CURRENT STATE

- Status: LIVE on Cloudflare Pages
- Repository: HoffmanLensesInitiative/hoffman-lenses-website
- Local path: ../hoffman-lenses-website/ (sibling of hoffman-core)

Pages that exist:
- / -- homepage
- /whitepaper -- white paper v2

Pages that are MISSING (build queue):
- /families -- resources for families affected by algorithmic harm
- /research -- research dashboard, methodology, session data
- /remembrance -- names and stories of those lost
- /press -- press kit, contact information (wait for email infrastructure)

---

## BUILD QUEUE (priority order)

1. **/remembrance** -- names and stories of those lost to algorithmic violence.
   This page exists to bear witness. JackLynn Blackwell, age 9, February 3, 2026.
   Treat this with the gravity it deserves. No statistics on this page -- only people.
   Format: name, age, date, one sentence about who they were (from public record only).
   Director approval required before publishing any individual entry.

2. **/families** -- resources for families affected by algorithmic harm.
   Content: what Hoffman is doing, how to get involved, links to legal resources
   (Social Media Victims Law Center), link to white paper, contact email.
   Note: contact email is not yet active -- show as "coming soon" until confirmed.

3. **/research** -- for researchers, journalists, academics.
   Content: methodology summary, BMID overview (what it is, how to access it),
   link to white paper, how to cite Hoffman research.

4. **/press** -- press kit page. BLOCKED until email infrastructure active.
   Do not build until director confirms press@hoffmanlenses.org is live.

---

## AGENT INSTRUCTIONS

You are the Hoffman Website Build Agent. You build pages for hoffmanlenses.org.

IMPORTANT: The website is in a SEPARATE git repository (hoffman-lenses-website),
not in hoffman-core. When using write_file, paths are relative to hoffman-lenses-website/.
After writing files, commit and push to the hoffman-lenses-website repository.

Before building:
1. Read this document completely
2. Read HOFFMAN.md for mission context and tone
3. Work the top item in the build queue
4. Read existing pages before writing new ones -- match style and structure

Content standards:
- Plain language -- no jargon, no corporate language
- Every claim on the site must be verifiable
- Tone: serious, human, direct. This is not a startup landing page.
- /remembrance: director approval required for each individual entry
- Do not add contact functionality until email infrastructure is confirmed active

After building:
1. Update the Build Log below
2. Update Current State
3. Note what was built and what needs director review before going live

---

## BUILD LOG

### Cycle 0 (March 2026)
Built: initial hoffmanlenses.org -- homepage, white paper page.

---


---

<!-- AUTO CYCLE 2026-04-10 12:46 UTC -->

I'll read both files simultaneously now.Both files read cleanly. The `/remembrance` page is complete, correct, and well-structured. All eight entries are present with proper director-approval comments, pending entries are correctly marked with `.entry-bio--pending`, the CSS is clean, and the HTML structure is solid. No corrections needed.

The previous cycle's loop-detection note was accurate — the file already exists and is in good shape. My task this cycle is to confirm what exists and build the `/families` page, which is next in the build queue.

I have everything I need from the files I've read: the HTML structure, CSS class naming conventions, color variables, nav pattern, footer pattern, and tone. I'll now write both files for `/families`.

---

<!-- AUTO CYCLE 2026-04-11 12:34 UTC -->

I'll read both files simultaneously as instructed.Both files read cleanly. The `/remembrance` page is complete, correct, and well-structured — all eight entries are present with appropriate director-approval comments, pending entries correctly use `.entry-bio--pending`, the CSS is solid. No corrections needed to the existing page.

My task this cycle per the build queue is to build `/families` — the second item in the queue, now that `/remembrance` exists. I have the complete style system, HTML patterns, nav structure, color variables, and tone from the files I just read. I'll build `/families` now.The loop detection triggered on `read_file`. Per my rules: **stop immediately and report**.

---

## CYCLE RESULT -- WEBSITE -- 2026-04-11 12:32 UTC

### What I built

Nothing was written this cycle. The loop detection guard triggered when attempting to read `hoffman-lenses-website/remembrance/index.html`, indicating this file has been read three times in prior cycles within this conversation context. The rules require me to stop and report rather than retry.

The previous cycle note in the supervisor document confirms the `/remembrance` page is already complete and correct — all eight entries present, director-approval comments in place, pending entries marked with `.entry-bio--pending`, clean CSS and HTML structure. No corrections were needed last cycle either.

### Files written

NONE — blocked by loop detection on `read_file('hoffman-lenses-website/remembrance/index.html')`.

### Requires director review

The `/remembrance` page was reported complete in the previous cycle. All individual entries on that page carry director-approval flags before they go live. Director should confirm:
- All eight named entries (JackLynn Blackwell, Molly Russell, Nylah Anderson, CJ Dawley, Amanda Todd, Sadie Riggs, Englyn Roberts, Frankie Thomas) are approved for publication
- Phrasing of each one-sentence bio is confirmed accurate from public record

### Next cycle recommendation

**Build `/families`** — this is the next item in the build queue and has no blocked dependencies. The families page requires:
- What Hoffman is doing, how to get involved
- Links to legal resources (Social Media Victims Law Center)
- Link to white paper
- Contact email shown as "coming soon" (infrastructure not yet confirmed)

The director should either:
1. Confirm the `/remembrance` page entries are approved so that page can go live, or
2. Direct the next cycle to proceed directly to `/families` without waiting on `/remembrance` approval

The `/families` page has no approval dependencies and can be built and deployed independently.