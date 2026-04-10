-- BMID Database Schema
-- Behavioral Manipulation Intelligence Database
-- Version: 0.2.1 (contributed_by added to amplifier table 2026-04-10)

-- Core fisherman record: a platform or operator that runs a BMS
CREATE TABLE IF NOT EXISTS fisherman (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fisherman_id TEXT UNIQUE NOT NULL,   -- e.g. "fisherman-facebook"
  domain TEXT UNIQUE NOT NULL,         -- e.g. "facebook.com"
  display_name TEXT NOT NULL,
  owner TEXT,
  parent_company TEXT,
  country TEXT,
  founded TEXT,
  business_model TEXT,
  revenue_sources TEXT,                -- JSON array
  confidence_score REAL DEFAULT 0.5,
  contributed_by TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

-- Documented motive: why a fisherman operates as it does
CREATE TABLE IF NOT EXISTS motive (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  motive_id TEXT UNIQUE NOT NULL,      -- e.g. "motive-facebook-ad-revenue"
  fisherman_id TEXT NOT NULL REFERENCES fisherman(fisherman_id),
  motive_type TEXT NOT NULL,           -- ad_revenue | data_harvesting | engagement_max | etc.
  description TEXT NOT NULL,
  revenue_model TEXT,
  beneficiary TEXT,
  documented_evidence TEXT,
  confidence_score REAL DEFAULT 0.5,
  contributed_by TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Documented catch: a harm outcome linked to a fisherman
CREATE TABLE IF NOT EXISTS catch (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  catch_id TEXT UNIQUE NOT NULL,       -- e.g. "catch-facebook-001"
  fisherman_id TEXT NOT NULL REFERENCES fisherman(fisherman_id),
  harm_type TEXT NOT NULL,
  victim_demographic TEXT,
  documented_outcome TEXT NOT NULL,
  scale TEXT,
  academic_citation TEXT,
  date_documented TEXT,
  severity_score INTEGER DEFAULT 5,    -- 1-10
  created_at TEXT DEFAULT (datetime('now'))
);

-- Evidence records: sources supporting fisherman, motive, or catch claims
CREATE TABLE IF NOT EXISTS evidence (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  evidence_id TEXT UNIQUE NOT NULL,    -- e.g. "ev-facebook-001"
  entity_id TEXT NOT NULL,             -- fisherman_id, motive_id, or catch_id
  entity_type TEXT NOT NULL,           -- "fisherman" | "motive" | "catch"
  source_type TEXT NOT NULL,           -- "primary" | "secondary" | "academic"
  url TEXT,
  title TEXT NOT NULL,
  author TEXT,
  publication TEXT,
  published_date TEXT,
  summary TEXT,
  confidence REAL DEFAULT 0.5,
  created_at TEXT DEFAULT (datetime('now'))
);

-- -------------------------------------------------------------------------
-- NETWORK AND ACTOR TABLES (added March 30, 2026 per HOFFMAN.md Part 13)
-- -------------------------------------------------------------------------

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

-- ---------------------------------------------------------------------------
-- CROWDSOURCED SUBMISSIONS (added 2026-04-08)
-- User-contributed catches from the Hoffman Browser.
-- Status: pending → investigating → accepted | rejected
-- contributor_token = SHA-256(provider:apikey) -- anonymous, rate-limited.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS submission (
  id                INTEGER PRIMARY KEY AUTOINCREMENT,
  submission_id     TEXT UNIQUE NOT NULL,
  domain            TEXT NOT NULL,
  url               TEXT,
  contributor_token TEXT NOT NULL,
  flags             TEXT NOT NULL,       -- JSON array of flag objects
  summary           TEXT,
  technique_count   INTEGER DEFAULT 0,
  submitted_at      TEXT DEFAULT (datetime('now')),
  status            TEXT DEFAULT 'pending',  -- pending|investigating|accepted|rejected
  agent_notes       TEXT
);

CREATE INDEX IF NOT EXISTS idx_submission_status ON submission(status);
CREATE INDEX IF NOT EXISTS idx_submission_domain  ON submission(domain);
CREATE INDEX IF NOT EXISTS idx_submission_token   ON submission(contributor_token, submitted_at);

-- ---------------------------------------------------------------------------
-- AMPLIFIER (added 2026-04-08, contributed_by added 2026-04-10)
-- Infrastructure platforms that systematically amplify manipulative content.
-- Distinct from fishermen: amplifiers do not create content.
-- They profit from routing users to manipulative content via algorithm design.
-- The co-evolutionary relationship: manipulative publishers adapt to amplifier
-- ranking signals; amplifiers optimize for the behavior those publishers perfected.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS amplifier (
  id                       INTEGER PRIMARY KEY AUTOINCREMENT,
  amplifier_id             TEXT UNIQUE NOT NULL,   -- e.g. "amplifier-google"
  name                     TEXT NOT NULL,           -- e.g. "Google Search / Google News"
  parent_entity            TEXT,                    -- e.g. "Alphabet Inc."
  domains                  TEXT,                    -- JSON array of domains
  optimization_target      TEXT NOT NULL,           -- what the algorithm optimizes for
  amplification_mechanism  TEXT NOT NULL,           -- how it amplifies manipulative content
  documented_motive        TEXT NOT NULL,           -- financial/strategic motive (documented)
  knowing_element          TEXT,                    -- what they knew, when, primary sources
  knowing_date             TEXT,                    -- earliest documented knowledge date
  co_evolutionary_note     TEXT,                    -- how manipulators adapted to this infrastructure
  regulatory_status        TEXT,                    -- antitrust/regulatory findings
  default_reach            TEXT,                    -- what % of population encounters this by default
  public_alternatives      TEXT,                    -- what responsible design would look like
  alternative_feasibility  TEXT,                    -- assessment of viability/cost
  confidence_score         REAL DEFAULT 0.5,
  contributed_by           TEXT,                    -- agent or researcher who created record
  sources                  TEXT,                    -- JSON array of source objects
  created_at               TEXT DEFAULT (datetime('now')),
  updated_at               TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_amplifier_id ON amplifier(amplifier_id);

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
