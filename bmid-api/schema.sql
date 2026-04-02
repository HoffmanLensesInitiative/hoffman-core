-- BMID Database Schema
-- Behavioral Manipulation Intelligence Database
-- Version: 0.2.0 (extended with network and actor tables March 30, 2026)

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
