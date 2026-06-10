use std::fs;
use std::process::Command;

use rusqlite::{params, Connection};
use serde_json::Value;
use tempfile::TempDir;

const SCHEMA: &str = r#"
CREATE TABLE ledger_events (
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

CREATE TABLE promotions (
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

CREATE TABLE compiled_pages (
  path TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  page_type TEXT NOT NULL,
  content TEXT NOT NULL,
  source_event_ids_json TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"#;

fn bin() -> &'static str {
    env!("CARGO_BIN_EXE_ingrain-rs")
}

fn make_home() -> (TempDir, std::path::PathBuf) {
    let temp = TempDir::new().expect("tempdir");
    let home = temp.path().join(".ingrain");
    fs::create_dir(&home).expect("home");
    let conn = Connection::open(home.join("mind.db")).expect("open sqlite");
    conn.execute_batch(SCHEMA).expect("schema");
    conn.execute(
        "INSERT INTO ledger_events
         (id, created_at, source, runner, event_type, actor, text, meta_json, fingerprint)
         VALUES ('evt_push', '2026-06-10T10:00:00+00:00', 'test', 'codex', 'reflection', 'user', 'push rule', '{}', 'evt_push')",
        [],
    )
    .expect("event");
    conn.execute(
        "INSERT INTO promotions
         (id, event_id, promoted_type, text, confidence, reason, current_state, compiled_path, meta_json, created_at)
         VALUES ('prm_push', 'evt_push', 'correction', 'Do not push without running tests.', ?1, 'manual remember type', 'current', NULL, '{}', '2026-06-10T10:01:00+00:00')",
        params![0.96],
    )
    .expect("promotion");
    drop(conn);
    (temp, home)
}

#[test]
fn hydrate_command_outputs_evidence_context() {
    let (_temp, home) = make_home();

    let output = Command::new(bin())
        .args([
            "hydrate",
            "--home",
            home.to_str().expect("home str"),
            "--query",
            "push",
            "--level",
            "evidence",
        ])
        .output()
        .expect("run cli");

    assert!(
        output.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stdout = String::from_utf8(output.stdout).expect("stdout");
    assert!(stdout.contains("<aeonik_ingrain_context>"));
    assert!(stdout.contains("Do not push without running tests."));
    assert!(stdout.contains("confidence: 96%; reason: manual remember type"));
}

#[test]
fn report_command_outputs_json_for_readable_store() {
    let (_temp, home) = make_home();

    let output = Command::new(bin())
        .args([
            "report",
            "--home",
            home.to_str().expect("home str"),
            "--json",
        ])
        .output()
        .expect("run cli");

    assert!(
        output.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("json");
    assert_eq!(report["db_exists"], true);
    assert_eq!(report["db_readable"], true);
    assert_eq!(report["counts"]["ledger_events"], 1);
    assert_eq!(report["counts"]["promotions"], 1);
}

#[test]
fn verify_store_json_reports_missing_database_without_creating_it_and_exits_nonzero() {
    let temp = TempDir::new().expect("tempdir");
    let home = temp.path().join(".ingrain");

    let output = Command::new(bin())
        .args([
            "verify-store",
            "--home",
            home.to_str().expect("home str"),
            "--json",
        ])
        .output()
        .expect("run cli");

    assert!(!output.status.success());
    let report: Value = serde_json::from_slice(&output.stdout).expect("json");
    assert_eq!(report["db_exists"], false);
    assert_eq!(report["db_readable"], false);
    assert!(report["error"]
        .as_str()
        .unwrap_or_default()
        .contains("missing"));
    assert!(!home.exists());
}
