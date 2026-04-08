# BMID — Behavioral Manipulation Intelligence Database
# Schema v0.1
# Hoffman Lenses Initiative
# License: CC BY 4.0

---

## The analogy

Every piece of manipulation has a supply chain.
The database maps that supply chain completely.

  AMPLIFIER  -- infrastructure that routes users to manipulative content at scale
  FISHERMAN  -- who is doing this
  BAIT       -- what they use to attract attention
  HOOK       -- the specific manipulation technique embedded in the bait
  NET        -- the destination ecosystem that catches the clicked user
  CATCH      -- documented harm that resulted
  MOTIVE     -- the documented intent and business model behind it
  EVIDENCE   -- primary sources proving any of the above

---

## AMPLIFIER
Infrastructure platforms that systematically route users to manipulative content.
Distinct from fishermen: **amplifiers do not create content — they distribute it.**

The key distinction: a fisherman deceives. An amplifier routes.
The amplifier's algorithm selects what content reaches users at scale,
and that selection rewards the properties that make content manipulative.

The co-evolutionary relationship: manipulative publishers learn to optimize
for amplifier ranking signals. Amplifiers optimize for the behavior those
publishers perfected. Neither designed the relationship — it emerged from
each optimizing for their own metrics. The structural outcome is that
manipulation receives preferential distribution.

```
amplifier_id             string PRIMARY KEY        -- e.g. "amplifier-google"
name                     string                    -- e.g. "Google Search / Google News"
parent_entity            string                    -- e.g. "Alphabet Inc."
domains                  string[]                  -- domains operated
optimization_target      string                    -- what the algorithm optimizes for
                                                   -- e.g. "click-through rate (CTR)"
amplification_mechanism  text                      -- how it amplifies manipulative content
documented_motive        text                      -- financial/strategic motive (documented)
knowing_element          text                      -- what they knew, when, primary sources
knowing_date             date                      -- earliest documented knowledge
co_evolutionary_note     text                      -- how manipulators adapted to this infra
regulatory_status        text                      -- antitrust/regulatory findings
default_reach            text                      -- what % of population by default
public_alternatives      text                      -- what responsible design looks like
alternative_feasibility  text                      -- why alternatives are/aren't viable
confidence_score         float 0-1
sources                  object[]                  -- primary source references
```

### Documented amplifiers

| amplifier_id       | name                          | confidence |
|--------------------|-------------------------------|------------|
| amplifier-google   | Google Search / Google News   | 0.90       |

*YouTube, Facebook News Feed, Twitter/X "For You" are priority research targets.*

---

## FISHERMAN
The publisher, platform, page, or content source.
Every other record links back to a Fisherman.

```
fisherman_id        uuid PRIMARY KEY
domain              string UNIQUE          -- e.g. "foxnews.com"
display_name        string                 -- e.g. "Fox News"
owner               string                 -- e.g. "News Corp"
parent_company      string                 -- ultimate corporate parent
country             string ISO-3166        -- country of incorporation
founded             year
business_model      enum [
                      advertising,
                      subscription,
                      donation,
                      political_pac,
                      state_media,
                      influence_operation,
                      data_harvesting,
                      affiliate_marketing,
                      mixed
                    ]
revenue_sources     string[]               -- documented revenue streams
ad_networks         string[]               -- advertising platforms used
data_brokers        string[]               -- documented data sharing relationships
political_affiliation string               -- documented political alignment if any
documented_reach    integer                -- monthly unique visitors (documented)
legal_status        enum [
                      active,
                      under_investigation,
                      sanctioned,
                      defunct
                    ]
confidence_score    float 0-1              -- confidence in this record's accuracy
last_verified       timestamp
created_at          timestamp
updated_at          timestamp
contributed_by      string                 -- agent or researcher who created record
```

---

## BAIT
A specific piece of content observed using manipulation techniques.
One piece of content = one Bait record.

```
bait_id             uuid PRIMARY KEY
fisherman_id        uuid FOREIGN KEY -> fisherman.fisherman_id
headline_text       string                 -- exact observed headline or text
url                 string                 -- URL where observed (may be dead)
destination_url     string                 -- where clicking leads
pattern_types       string[]               -- hl-detect pattern IDs detected
escalation_score    integer 0-100          -- hl-detect escalation score
emotional_register  enum [
                      fear,
                      outrage,
                      urgency,
                      tribalism,
                      curiosity,
                      disgust,
                      hope,
                      mixed
                    ]
content_category    enum [
                      health,
                      politics,
                      finance,
                      entertainment,
                      crime,
                      religion,
                      science,
                      other
                    ]
observed_at         timestamp
reported_by         string                 -- extension session ID (anonymized) or researcher
verified            boolean
```

---

## HOOK
A specific manipulation pattern instance within a piece of Bait.
One bait can have multiple hooks.

```
hook_id             uuid PRIMARY KEY
bait_id             uuid FOREIGN KEY -> bait.bait_id
fisherman_id        uuid FOREIGN KEY -> fisherman.fisherman_id
pattern_type        string                 -- hl-detect pattern ID
                                           -- suppression_framing
                                           -- false_urgency
                                           -- incomplete_hook
                                           -- outrage_engineering
                                           -- false_authority
                                           -- tribal_activation
                                           -- engagement_directive
                                           -- coordinated_language (future)
trigger_phrase      string                 -- exact phrase that triggered detection
trigger_context     string                 -- surrounding sentence for context
confidence          float 0-1              -- hl-detect confidence score
severity            enum [danger, warn, info]
hl_detect_version   string                 -- version of hl-detect that flagged this
plain_explanation   string                 -- plain language explanation shown to user
created_at          timestamp
```

---

## NET
The destination ecosystem a user enters after taking the bait.
What catches them on the other side of the click.

```
net_id              uuid PRIMARY KEY
fisherman_id        uuid FOREIGN KEY -> fisherman.fisherman_id
destination_domain  string                 -- domain the click leads to
net_type            enum [
                      advertising_page,     -- page monetized by display ads
                      subscription_funnel,  -- designed to capture subscription
                      data_harvesting,      -- designed to harvest user data
                      donation_page,        -- political/advocacy donation
                      product_sale,         -- direct product sale
                      affiliate_redirect,   -- affiliate marketing chain
                      content_farm,         -- low quality content for ad revenue
                      influence_payload,    -- designed to deliver a political message
                      radicalization_path,  -- leads toward extreme content
                      mixed
                    ]
ad_network          string                 -- primary ad network on destination
tracking_pixels     string[]               -- documented tracking on destination
data_harvested      string[]               -- what user data is collected
                                           -- e.g. ["email", "location", "browsing_history"]
average_session_time integer               -- seconds (if documented)
documented_revenue  string                 -- what this net earns (if documented)
documented_at       timestamp
evidence_id         uuid FOREIGN KEY -> evidence.evidence_id
```

---

## CATCH
A documented instance of harm attributed to a fisherman's operations.
The fish that didn't get away.

```
catch_id            uuid PRIMARY KEY
fisherman_id        uuid FOREIGN KEY -> fisherman.fisherman_id
bait_id             uuid FOREIGN KEY -> bait.bait_id (nullable)
harm_type           enum [
                      self_harm,
                      radicalization,
                      financial_loss,
                      health_misinformation,
                      relationship_harm,
                      political_manipulation,
                      data_breach,
                      addiction_facilitation,
                      child_exploitation_adjacent,
                      death
                    ]
victim_demographic  string                 -- documented affected group
                                           -- e.g. "adolescent girls 13-17"
documented_outcome  text                   -- plain language description of harm
scale               enum [
                      individual,           -- single documented case
                      group,                -- documented group harm
                      population            -- population-level documented harm
                    ]
legal_case_id       string                 -- court case reference if applicable
academic_citation   string                 -- academic paper DOI if applicable
date_documented     date
severity_score      integer 1-10           -- 10 = death, 1 = minor measurable harm
evidence_ids        uuid[]                 -- links to evidence records
```

---

## MOTIVE
The documented intent and business model behind a fisherman's manipulation.
Why they fish.

```
motive_id           uuid PRIMARY KEY
fisherman_id        uuid FOREIGN KEY -> fisherman.fisherman_id
motive_type         enum [
                      advertising_revenue,  -- manipulation drives clicks = ad revenue
                      subscription_growth,  -- outrage/fear drives subscription sign-ups
                      political_influence,  -- content designed to shift political views
                      data_acquisition,     -- manipulation drives data consent
                      product_sales,        -- health/supplement/product sales
                      donation_solicitation,-- political/advocacy donations
                      foreign_influence,    -- documented foreign state operation
                      audience_capture,     -- building captive audience for later use
                      competitor_harm,      -- designed to damage a competitor
                      mixed
                    ]
description         text                   -- plain language description of motive
revenue_model       text                   -- how the manipulation converts to money
beneficiary         string                 -- who profits (may differ from fisherman)
documented_evidence text                   -- summary of evidence for this motive
confidence_score    float 0-1
evidence_ids        uuid[]
created_at          timestamp
```

---

## EVIDENCE
Primary source documentation for any record in the database.
The proof behind every claim.

```
evidence_id         uuid PRIMARY KEY
entity_id           uuid                   -- id of the record this supports
entity_type         enum [
                      fisherman,
                      bait,
                      hook,
                      net,
                      catch,
                      motive
                    ]
source_type         enum [
                      court_filing,
                      academic_paper,
                      senate_testimony,
                      fcc_filing,
                      corporate_filing,
                      news_investigation,
                      government_report,
                      ngo_report,
                      internal_document,    -- leaked/disclosed internal docs
                      foia_response,
                      extension_session     -- anonymized data from hl-detect
                    ]
url                 string                 -- primary URL
archive_url         string                 -- archive.org backup URL
title               string
author              string
publication         string
published_date      date
summary             text                   -- plain language summary of what this proves
direct_quote        string                 -- relevant excerpt (under 15 words)
verified_by         string                 -- researcher or agent that verified
verified_at         timestamp
confidence          float 0-1
```

---

## API ENDPOINTS (planned)

### Public read endpoints

GET /api/v1/fisherman/{domain}
  Returns: fisherman record + summary of baits, hooks, nets, motives

GET /api/v1/fisherman/{domain}/bait
  Returns: all documented bait for this fisherman

GET /api/v1/fisherman/{domain}/catch
  Returns: all documented harm attributed to this fisherman

GET /api/v1/pattern/{pattern_type}
  Returns: all hooks of this pattern type across all fishermen

GET /api/v1/search?domain=&pattern=&harm_type=
  Returns: filtered query across the database

GET /api/v1/explain?domain=&headline=&patterns=
  Returns: AI-generated plain language explanation of what this content
           is trying to do and why, powered by the fisherman's record
           This is the "Why is this here?" button endpoint

### Contribution endpoints (authenticated)

POST /api/v1/session
  Accepts: anonymized extension session report
  Creates: bait + hook records from observed content

POST /api/v1/evidence
  Accepts: evidence submission from researcher or agent
  Creates: evidence record pending verification

---

## CONFIDENCE SCORING

Every record has a confidence score 0-1.

1.0  -- proven in court, admitted by the entity, or in primary documents
0.9  -- documented by multiple independent credible sources
0.8  -- documented by one credible source (major outlet, academic paper)
0.7  -- documented by credible source with minor gaps
0.6  -- documented by extension data (observed pattern, not verified intent)
0.5  -- documented by single source with known bias
0.4  -- inferred from circumstantial evidence
0.3  -- community-submitted, not yet verified
0.0  -- disputed or pending removal

Records below 0.6 are flagged for verification before appearing in
user-facing explanations.

---

## AGENT INSTRUCTIONS

Intelligence agents writing to this database must:

1. Assign a confidence score honestly -- never inflate
2. Always link an evidence record to any factual claim
3. Never infer motive without documented evidence
4. Use the entity's own words where possible (within 15 words)
5. Mark all records with their source (agent ID or researcher name)
6. Flag for human review any record touching active legal cases
7. Never store personally identifiable information about victims
8. Victim records reference documented cases only -- no speculation

The standard for every record: could this stand up in court?
If not, lower the confidence score until it can.

---

## PRIORITY RESEARCH TARGETS

### Amplifiers (infrastructure enablers)
1. **Google / Alphabet** (google.com, news.google.com) -- SEEDED
   -- DOJ antitrust ruling, CTR optimization, ad network motive
2. **YouTube / Alphabet** (youtube.com) -- research target
   -- recommendation algorithm radicalization pathway (distinct from search)
3. **Facebook News Feed / Meta** (facebook.com) -- research target
   -- engagement optimization, filter bubble creation
4. **Twitter/X "For You"** (twitter.com, x.com) -- research target
   -- post-acquisition algorithm changes, documented political amplification

### Fishermen (content creators)

1. Meta Platforms (facebook.com, instagram.com)
   -- Molly Russell inquest, Frances Haugen testimony, internal research
2. TikTok / ByteDance (tiktok.com)
   -- Senate testimony, FTC investigation, teen mental health research
3. YouTube / Alphabet (youtube.com)
   -- radicalization pathway research, recommendation algorithm studies
4. Occupy Democrats (occupydemocrats.com)
   -- engagement bait patterns, political donation funnel
5. Health supplement content farms (multiple domains)
   -- false authority patterns, unnamed authority in health content
6. Fox News (foxnews.com)
   -- unnamed authority health content, outrage engineering patterns
7. State-sponsored influence operations (multiple domains)
   -- coordinated language patterns, suppression framing

---

*"The fisherman can change their bait. They cannot erase their record."*

*BMID is maintained by the Hoffman Lenses Initiative.*
*hoffmanlenses.org*
*License: CC BY 4.0*
