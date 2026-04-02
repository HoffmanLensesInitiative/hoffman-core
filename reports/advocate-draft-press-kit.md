# HOFFMAN LENSES — PRESS KIT
# Version: 0.1 DRAFT
# Prepared: 2026-04-02
# Status: READY FOR DIRECTOR REVIEW AND CONTENT APPROVAL
# Maintained by: Advocacy Agent

---

## EMBARGO NOTICE
This press kit is for background use only until Hoffman Lenses issues a public
launch announcement. Please do not publish without prior notification to
press@hoffmanlenses.org.

---

## THE ONE-PARAGRAPH SUMMARY

Hoffman Lenses is a research project building an open-source browser that makes
behavioral manipulation visible in real time. Named after the glasses in John
Carpenter's 1988 film *They Live* — which let the wearer see hidden messages
embedded in ordinary reality — the Hoffman Browser reads web pages the way an
expert reads manipulation: recognizing not just what text says, but what it is
designed to do to the reader. It works on any website, on any platform, because
manipulation is a property of language, not of any specific platform's structure.
It runs entirely on the user's device. No data leaves the machine. The project
is maintained by the Hoffman Lenses Initiative, an independent research effort
dedicated to making the machinery of online behavioral manipulation legible to
the people it operates on.

---

## THE PROBLEM IN THREE FACTS

1. **The harm is documented, not alleged.** In 2022, a UK coroner ruled that
   Instagram and Pinterest content contributed to the death of Molly Russell,
   age 14. It was the first time a legal body attributed an algorithmic death
   directly to platform design. She was not an isolated case.

2. **The harm is architectural, not accidental.** Internal Meta research,
   disclosed by whistleblower Frances Haugen in October 2021, showed that the
   company's own studies identified harm to teenage girls from Instagram use —
   and that this research was suppressed rather than acted upon.

3. **The harm is invisible to the people experiencing it.** Behavioral
   Manipulation Systems — the algorithmic engines that power social media
   platforms — are designed to maximize engagement without obligation to human
   wellbeing. They operate without disclosure, without consent, and without any
   mechanism that allows users to see what is being done to them. Hoffman Lenses
   exists to provide that mechanism.

---

## WHAT WE ARE BUILDING

### The Hoffman Browser (current primary product)
An Electron-based desktop browser with on-device manipulation detection built in.
When a user visits a page, the browser's local language model reads the rendered
text — what the user actually sees — and identifies patterns associated with
behavioral manipulation: outrage engineering, false urgency, suppression framing,
tribal activation, and others. Findings appear in a side panel. Nothing is sent
to any server. The model runs on the user's CPU.

Current status: functional prototype. First successful real-world detection:
Fox News page flagged for outrage engineering and war framing (March 2026).

### The Behavioral Manipulation Intelligence Database (BMID)
An evidence-based, open intelligence repository documenting the manipulation
ecosystem: which operators use which techniques, what harm has resulted, who
made the decisions, and when they knew about the consequences. Every claim
requires primary source documentation. Court filings. Sworn testimony. Internal
documents disclosed through legal proceedings. Unknown is a valid answer.

Current status: three operators documented (Facebook, Instagram, YouTube),
with a research mandate covering the top 25 global behavioral manipulation
operators across the full political spectrum.

### hl-detect (developer library)
A standalone JavaScript library that analyzes text and identifies linguistic
manipulation patterns. Available as an npm package for developers who want
to build manipulation detection into their own tools.

### The White Paper
*"The Algorithm and the Child: A Human Rights Case for Abolishing Behavioral
Manipulation Systems"* — available at hoffmanlenses.org. Full citations,
25 references, Creative Commons licensed.

---

## WHY THIS APPROACH

**Extensions fail.** Browser extensions can be blocked by platforms
(and increasingly are). Chrome's Manifest V3 restricts what extensions can do,
with a trajectory toward more restriction, not less. Platforms deliberately
obfuscate their DOM structure to prevent text extraction. A browser reads
rendered output — what the user actually sees — and platforms cannot obfuscate
that without breaking their own product.

**The model reads what rules miss.** Rule-based detection systems only catch
what someone remembered to write a rule for. A local language model reads the
full page, in context, and identifies manipulation patterns that no rule would
anticipate. It does not require a platform-specific adapter. It does not care
about DOM structure. It reads language.

**On-device is non-negotiable.** Sending page text to an external server for
analysis would itself be a form of surveillance. Every analysis runs on the
user's machine. No session data is retained after the session ends. This is
an architectural commitment, not a policy.

---

## THE RESEARCH USE CASE

Hoffman Browser is positioned first as a research instrument, not a consumer
product. Its primary users in this phase are:

- **Journalists** investigating platform manipulation practices
- **Researchers** studying algorithmic amplification and online harm
- **Lawyers and paralegals** working on social media harm litigation
- **Parents and advocates** who want to understand what their children are
  being exposed to
- **Legislative staff** developing platform regulation

The browser creates a documented record of manipulation patterns encountered
in a browsing session — a research instrument that currently does not exist.

---

## KEY FACTS

| Item | Detail |
|------|--------|
| Project name | Hoffman Lenses Initiative |
| Primary product | Hoffman Browser (Electron, desktop) |
| Platform | Windows, Mac, Linux |
| Data retention | Zero — no user data retained after session |
| Model | Llama 3.2 3B Instruct Q4_K_M — on-device, CPU |
| License | Open source (GitHub: HoffmanLensesInitiative/hoffman-core) |
| Founded | March 2026 |
| Director | Norm Robichaud |
| Location | British Columbia, Canada |
| Website | hoffmanlenses.org |
| Press contact | press@hoffmanlenses.org |

---

## THE WHITE PAPER — SUMMARY

*"The Algorithm and the Child: A Human Rights Case for Abolishing Behavioral
Manipulation Systems"* argues that Behavioral Manipulation Systems operated
by major social media platforms constitute a human rights violation under the
UN Guiding Principles on Business and Human Rights (Ruggie Framework, 2011).

The paper documents:
- The technical architecture of behavioral manipulation systems
- The documented harm, including legal findings and whistleblower disclosures
- The international human rights framework applicable to corporate actors
- The case for regulatory intervention and platform liability

Available for download at hoffmanlenses.org. Licensed CC BY 4.0.
25 cited sources. Appropriate for use as a research reference.

---

## THE DEDICATION

This project is dedicated to:

JackLynn Blackwell — age 9 — Texas — February 3, 2026
Molly Russell — age 14 — London — 2017
Nylah Anderson — age 10 — Philadelphia — 2021
CJ Dawley — age 14 — Wisconsin
Amanda Todd — age 15 — BC Canada — 2012
Sadie Riggs — age 15 — Pennsylvania — 2015
Englyn Roberts
Frankie Thomas

*And to every child whose name we have not yet learned.*

The project exists because these children deserved better than to be engagement
metrics.

---

## BACKGROUNDER: KEY LEGAL AND REGULATORY MILESTONES

**2022 — Molly Russell inquest (UK)**
Coroner Andrew Walker ruled that Molly Russell, 14, died partly as a result
of harmful content she was served on Instagram and Pinterest. First legal
attribution of a death to platform algorithm design. Primary source:
HM Senior Coroner, Area of North London, Prevention of Future Deaths Report, 2022.

**2021 — Frances Haugen disclosure**
Former Facebook product manager Frances Haugen disclosed thousands of internal
documents to the SEC and to journalists, showing Meta had internal research
demonstrating Instagram harm to teenage girls and had suppressed it. Testimony
to U.S. Senate Commerce Committee, October 2021.

**2021–present — Social media teen mental health MDL**
Multi-district litigation consolidated in the Northern District of California.
Hundreds of plaintiffs. Social Media Victims Law Center (lead: Matthew Bergman)
represents many families. Ongoing.

**2023 — UK Online Safety Act**
First major national legislation built on the premise that algorithmic
amplification itself — not just specific content — is a harm vector.
Implementation by Ofcom ongoing.

**2023 — U.S. Surgeon General Advisory**
Dr. Vivek Murthy issued a formal advisory on social media and youth mental
health, representing official U.S. government acknowledgment of the harm.

**2024 — Australia Social Media Age Verification Bill**
Mandates age verification for social media access under 16. Enforcement ongoing.

---

## FREQUENTLY ASKED QUESTIONS

**Is this affiliated with any political organization?**
No. Hoffman Lenses is an independent research project. The research mandate
explicitly requires political balance — behavioral manipulation systems exist
across the full political spectrum, and documentation follows the evidence,
not political alignment.

**Who funds this?**
The project is currently self-funded by the Director. No platform funding.
No advertising revenue. No data monetization.

**Is the browser available to download?**
The Hoffman Browser is in prototype development. A public release date has
not been set. Researchers interested in early access can contact
press@hoffmanlenses.org.

**Does the browser send data to Hoffman Lenses servers?**
No. All analysis is on-device. Nothing leaves the user's machine. This is
an architectural commitment built into the design and is non-negotiable.

**What is the BMID?**
The Behavioral Manipulation Intelligence Database. An evidence-based
intelligence repository documenting the manipulation ecosystem. Structured
like a research database: every claim requires a primary source. Open source.

**Can platforms block the Hoffman Browser?**
No. Because analysis happens on the user's device, using a local model,
after the page is rendered — platforms have no mechanism to detect or
interfere with the analysis. This is a core architectural advantage over
browser extensions.

---

## CONTACT

**General:** contact@hoffmanlenses.org
**Press:** press@hoffmanlenses.org
**Families:** families@hoffmanlenses.org
**Legal:** legal@hoffmanlenses.org

Website: hoffmanlenses.org
GitHub: github.com/HoffmanLensesInitiative

---

*REQUIRES DIRECTOR REVIEW*
*Specifically: founder bio (Section marked [BIO NEEDED] above — please provide
or approve draft text), timing for public release announcement, and approval
of the "current status" descriptions.*

*Note: "press@hoffmanlenses.org" must be active before this kit is distributed.*
