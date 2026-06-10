use rusqlite::Connection;
use serde::{Deserialize, Serialize};

use crate::store::{IngrainStore, Result};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct StoreCounts {
    pub ledger_events: u64,
    pub promotions: u64,
    pub compiled_pages: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct EventSummary {
    pub id: String,
    pub created_at: String,
    pub source: String,
    pub runner: String,
    pub event_type: String,
    pub text_preview: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PromotionSummary {
    pub id: String,
    pub event_id: String,
    pub promoted_type: String,
    pub current_state: String,
    pub confidence: f64,
    pub text_preview: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct StoreReport {
    pub home: String,
    pub db_path: String,
    pub db_exists: bool,
    pub db_readable: bool,
    pub counts: StoreCounts,
    pub event_to_promotion_ratio: Option<f64>,
    pub latest_events: Vec<EventSummary>,
    pub latest_promotions: Vec<PromotionSummary>,
    pub error: Option<String>,
}

pub fn read_report(store: &IngrainStore) -> Result<StoreReport> {
    let conn = store.open_readonly()?;
    read_report_from_connection(store, &conn)
}

pub fn verify_store(store: &IngrainStore) -> StoreReport {
    match read_report(store) {
        Ok(report) => report,
        Err(error) => {
            let mut report = empty_report(store);
            report.db_exists = store.db_path().exists();
            report.db_readable = false;
            report.error = Some(error.to_string());
            report
        }
    }
}

fn read_report_from_connection(store: &IngrainStore, conn: &Connection) -> Result<StoreReport> {
    let ledger_events = count(conn, "ledger_events")?;
    let promotions = count(conn, "promotions")?;
    let compiled_pages = count(conn, "compiled_pages")?;
    let event_to_promotion_ratio = if ledger_events == 0 {
        None
    } else {
        Some(promotions as f64 / ledger_events as f64)
    };

    Ok(StoreReport {
        home: store.home().display().to_string(),
        db_path: store.db_path().display().to_string(),
        db_exists: true,
        db_readable: true,
        counts: StoreCounts {
            ledger_events,
            promotions,
            compiled_pages,
        },
        event_to_promotion_ratio,
        latest_events: latest_events(conn)?,
        latest_promotions: latest_promotions(conn)?,
        error: None,
    })
}

fn empty_report(store: &IngrainStore) -> StoreReport {
    StoreReport {
        home: store.home().display().to_string(),
        db_path: store.db_path().display().to_string(),
        db_exists: false,
        db_readable: false,
        counts: StoreCounts {
            ledger_events: 0,
            promotions: 0,
            compiled_pages: 0,
        },
        event_to_promotion_ratio: None,
        latest_events: Vec::new(),
        latest_promotions: Vec::new(),
        error: None,
    }
}

fn count(conn: &Connection, table: &str) -> Result<u64> {
    let sql = format!("SELECT COUNT(*) FROM {table}");
    let count: i64 = conn.query_row(&sql, [], |row| row.get(0))?;
    Ok(count.max(0) as u64)
}

fn latest_events(conn: &Connection) -> Result<Vec<EventSummary>> {
    let mut statement = conn.prepare(
        "SELECT id, created_at, source, runner, event_type, text
         FROM ledger_events
         ORDER BY created_at DESC, rowid DESC
         LIMIT 5",
    )?;
    let rows = statement.query_map([], |row| {
        let text: String = row.get("text")?;
        Ok(EventSummary {
            id: row.get("id")?,
            created_at: row.get("created_at")?,
            source: row.get("source")?,
            runner: row.get("runner")?,
            event_type: row.get("event_type")?,
            text_preview: preview(&text),
        })
    })?;
    rows.collect::<std::result::Result<Vec<_>, _>>()
        .map_err(Into::into)
}

fn latest_promotions(conn: &Connection) -> Result<Vec<PromotionSummary>> {
    let mut statement = conn.prepare(
        "SELECT id, event_id, promoted_type, current_state, confidence, text
         FROM promotions
         ORDER BY created_at DESC, rowid DESC
         LIMIT 5",
    )?;
    let rows = statement.query_map([], |row| {
        let text: String = row.get("text")?;
        Ok(PromotionSummary {
            id: row.get("id")?,
            event_id: row.get("event_id")?,
            promoted_type: row.get("promoted_type")?,
            current_state: row.get("current_state")?,
            confidence: row.get("confidence")?,
            text_preview: preview(&text),
        })
    })?;
    rows.collect::<std::result::Result<Vec<_>, _>>()
        .map_err(Into::into)
}

fn preview(text: &str) -> String {
    let normalized = text.split_whitespace().collect::<Vec<_>>().join(" ");
    let mut preview = normalized.chars().take(120).collect::<String>();
    if normalized.chars().count() > 120 {
        preview.push_str("...");
    }
    preview
}
