-- BMID Schema v0.2.0
-- Behavioral Manipulation Intelligence Database
-- Every table uses CREATE TABLE IF NOT EXISTS for idempotent migrations.
-- Extended March 30, 2026: network, actor, and accountability tables added.

-- ─────────────────────────────────────────────
-- CORE TABLES (v0.1.0)
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fisherman (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  domain TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  owner TEXT,
  parent_company TEXT,
  business_model TEXT,
  headquarters TEXT,
  founded TEXT,
  monthly_active_users TEXT,
  revenue_model TEXT,
  primary_manipulation_vector TEXT,
  confidence REAL DEFAULT 0.5,
  verified INTEGER DEFAULT 0,
  notes TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS motive (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fisherman_id INTEGER REFERENCES fisherman(id),
  motive_type TEXT NOT NULL,
  description TEXT NOT NULL,
  evidence TEXT,
  source_url TEXT,
  confidence REAL DEFAULT 0.5,
  verified INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS catch (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fisherman_id INTEGER REFERENCES fisherman(id),
  name TEXT NOT NULL,
  age INTEGER,
  location TEXT,
  date TEXT,
  harm_type TEXT,
  description TEXT,
  source_type TEXT,
  source_url TEXT,
  confidence REAL DEFAULT 0.5,
  verified INTEGER DEFAULT 0,
  notes TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS evidence (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fisherman_id INTEGER REFERENCES fisherman(id),
  catch_id INTEGER REFERENCES catch(id),
  evidence_type TEXT NOT NULL,
  description TEXT NOT NULL,
  source TEXT NOT NULL,
  source_url TEXT,
  date TEXT,
  confidence REAL DEFAULT 0.5,
  verified INTEGER DEFAULT 0,
  notes TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────
-- NETWORK AND ACTOR TABLES (v0.2.0)
-- Extended per HOFFMAN.md Part 13
-- ─────────────────────────────────────────────

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
