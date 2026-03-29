-- BMID Schema v0.1
-- Behavioral Manipulation Intelligence Database
-- Hoffman Lenses Initiative

CREATE TABLE IF NOT EXISTS fisherman (
  fisherman_id        TEXT PRIMARY KEY,
  domain              TEXT UNIQUE NOT NULL,
  display_name        TEXT NOT NULL,
  owner               TEXT,
  parent_company      TEXT,
  country             TEXT,
  founded             INTEGER,
  business_model      TEXT,
  revenue_sources     TEXT,  -- JSON array
  ad_networks         TEXT,  -- JSON array
  data_brokers        TEXT,  -- JSON array
  political_affiliation TEXT,
  documented_reach    INTEGER,
  legal_status        TEXT DEFAULT 'active',
  confidence_score    REAL DEFAULT 0.5,
  last_verified       TEXT,
  created_at          TEXT DEFAULT (datetime('now')),
  updated_at          TEXT DEFAULT (datetime('now')),
  contributed_by      TEXT
);

CREATE TABLE IF NOT EXISTS bait (
  bait_id             TEXT PRIMARY KEY,
  fisherman_id        TEXT NOT NULL REFERENCES fisherman(fisherman_id),
  headline_text       TEXT NOT NULL,
  url                 TEXT,
  destination_url     TEXT,
  pattern_types       TEXT,  -- JSON array of hl-detect pattern IDs
  escalation_score    INTEGER,
  emotional_register  TEXT,
  content_category    TEXT,
  observed_at         TEXT DEFAULT (datetime('now')),
  reported_by         TEXT,
  verified            INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS hook (
  hook_id             TEXT PRIMARY KEY,
  bait_id             TEXT NOT NULL REFERENCES bait(bait_id),
  fisherman_id        TEXT NOT NULL REFERENCES fisherman(fisherman_id),
  pattern_type        TEXT NOT NULL,
  trigger_phrase      TEXT,
  trigger_context     TEXT,
  confidence          REAL,
  severity            TEXT,
  hl_detect_version   TEXT,
  plain_explanation   TEXT,
  created_at          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS net (
  net_id              TEXT PRIMARY KEY,
  fisherman_id        TEXT NOT NULL REFERENCES fisherman(fisherman_id),
  destination_domain  TEXT NOT NULL,
  net_type            TEXT,
  ad_network          TEXT,
  tracking_pixels     TEXT,  -- JSON array
  data_harvested      TEXT,  -- JSON array
  average_session_time INTEGER,
  documented_revenue  TEXT,
  documented_at       TEXT DEFAULT (datetime('now')),
  evidence_id         TEXT
);

CREATE TABLE IF NOT EXISTS catch (
  catch_id            TEXT PRIMARY KEY,
  fisherman_id        TEXT NOT NULL REFERENCES fisherman(fisherman_id),
  bait_id             TEXT REFERENCES bait(bait_id),
  harm_type           TEXT NOT NULL,
  victim_demographic  TEXT,
  documented_outcome  TEXT,
  scale               TEXT,
  legal_case_id       TEXT,
  academic_citation   TEXT,
  date_documented     TEXT,
  severity_score      INTEGER,
  evidence_ids        TEXT,  -- JSON array
  created_at          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS motive (
  motive_id           TEXT PRIMARY KEY,
  fisherman_id        TEXT NOT NULL REFERENCES fisherman(fisherman_id),
  motive_type         TEXT NOT NULL,
  description         TEXT,
  revenue_model       TEXT,
  beneficiary         TEXT,
  documented_evidence TEXT,
  confidence_score    REAL DEFAULT 0.5,
  contributed_by      TEXT,
  evidence_ids        TEXT,  -- JSON array
  created_at          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS evidence (
  evidence_id         TEXT PRIMARY KEY,
  entity_id           TEXT NOT NULL,
  entity_type         TEXT NOT NULL,
  source_type         TEXT NOT NULL,
  url                 TEXT,
  archive_url         TEXT,
  title               TEXT,
  author              TEXT,
  publication         TEXT,
  published_date      TEXT,
  summary             TEXT,
  direct_quote        TEXT,
  verified_by         TEXT,
  verified_at         TEXT,
  confidence          REAL DEFAULT 0.7,
  created_at          TEXT DEFAULT (datetime('now'))
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_bait_fisherman ON bait(fisherman_id);
CREATE INDEX IF NOT EXISTS idx_hook_fisherman ON hook(fisherman_id);
CREATE INDEX IF NOT EXISTS idx_hook_pattern ON hook(pattern_type);
CREATE INDEX IF NOT EXISTS idx_catch_fisherman ON catch(fisherman_id);
CREATE INDEX IF NOT EXISTS idx_catch_harm ON catch(harm_type);
CREATE INDEX IF NOT EXISTS idx_evidence_entity ON evidence(entity_id);
CREATE INDEX IF NOT EXISTS idx_net_fisherman ON net(fisherman_id);
