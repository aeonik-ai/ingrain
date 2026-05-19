CREATE TABLE IF NOT EXISTS ledger_events (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  source TEXT NOT NULL,
  runner TEXT NOT NULL,
  event_type TEXT NOT NULL,
  session_id TEXT,
  project_id TEXT,
  thread_id TEXT,
  actor TEXT,
  text TEXT NOT NULL,
  meta_json TEXT NOT NULL,
  fingerprint TEXT UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_ledger_created_at ON ledger_events(created_at);
CREATE INDEX IF NOT EXISTS idx_ledger_source ON ledger_events(source);
CREATE INDEX IF NOT EXISTS idx_ledger_event_type ON ledger_events(event_type);

CREATE TABLE IF NOT EXISTS promotions (
  id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL,
  promoted_type TEXT NOT NULL,
  text TEXT NOT NULL,
  confidence REAL NOT NULL,
  reason TEXT NOT NULL,
  current_state TEXT NOT NULL,
  compiled_path TEXT,
  meta_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(event_id) REFERENCES ledger_events(id)
);

CREATE INDEX IF NOT EXISTS idx_promotions_type ON promotions(promoted_type);
CREATE INDEX IF NOT EXISTS idx_promotions_state ON promotions(current_state);

CREATE TABLE IF NOT EXISTS compiled_pages (
  path TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  page_type TEXT NOT NULL,
  content TEXT NOT NULL,
  source_event_ids_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
