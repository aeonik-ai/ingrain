use std::fmt;
use std::path::{Path, PathBuf};
use std::str::FromStr;

use rusqlite::{Connection, OpenFlags};
use serde_json::Value;

pub type Result<T> = std::result::Result<T, IngrainError>;

#[derive(Debug)]
pub enum IngrainError {
    Io(std::io::Error),
    Sqlite(rusqlite::Error),
    Json(serde_json::Error),
    InvalidLevel(String),
    MissingDatabase(PathBuf),
}

impl fmt::Display for IngrainError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Io(error) => write!(f, "I/O error: {error}"),
            Self::Sqlite(error) => write!(f, "SQLite error: {error}"),
            Self::Json(error) => write!(f, "JSON error: {error}"),
            Self::InvalidLevel(level) => {
                write!(
                    f,
                    "invalid hydration level {level:?}; use brief, cards, or evidence"
                )
            }
            Self::MissingDatabase(path) => {
                write!(f, "missing Ingrain database: {}", path.display())
            }
        }
    }
}

impl std::error::Error for IngrainError {}

impl From<std::io::Error> for IngrainError {
    fn from(error: std::io::Error) -> Self {
        Self::Io(error)
    }
}

impl From<rusqlite::Error> for IngrainError {
    fn from(error: rusqlite::Error) -> Self {
        Self::Sqlite(error)
    }
}

impl From<serde_json::Error> for IngrainError {
    fn from(error: serde_json::Error) -> Self {
        Self::Json(error)
    }
}

#[derive(Debug, Clone)]
pub struct IngrainStore {
    home: PathBuf,
    db_path: PathBuf,
}

impl IngrainStore {
    pub fn new(home: impl Into<PathBuf>) -> Self {
        let home = home.into();
        let db_path = home.join("mind.db");
        Self { home, db_path }
    }

    pub fn home(&self) -> &Path {
        &self.home
    }

    pub fn db_path(&self) -> &Path {
        &self.db_path
    }

    pub(crate) fn open_readonly(&self) -> Result<Connection> {
        if !self.db_path.exists() {
            return Err(IngrainError::MissingDatabase(self.db_path.clone()));
        }
        Connection::open_with_flags(
            &self.db_path,
            OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
        )
        .map_err(IngrainError::from)
    }

    pub fn current_promotions(&self) -> Result<Vec<Promotion>> {
        let conn = self.open_readonly()?;
        let mut statement = conn.prepare(
            "SELECT id, event_id, promoted_type, text, confidence, reason, current_state,
                    compiled_path, meta_json, created_at
             FROM promotions
             WHERE current_state = 'current'
             ORDER BY rowid ASC",
        )?;
        let rows = statement.query_map([], |row| {
            let meta_json: String = row.get("meta_json")?;
            let meta = serde_json::from_str(&meta_json).unwrap_or(Value::Null);
            Ok(Promotion {
                id: row.get("id")?,
                event_id: row.get("event_id")?,
                promoted_type: row.get("promoted_type")?,
                text: row.get("text")?,
                confidence: row.get("confidence")?,
                reason: row.get("reason")?,
                current_state: row.get("current_state")?,
                compiled_path: row.get("compiled_path")?,
                meta,
                created_at: row.get("created_at")?,
            })
        })?;
        rows.collect::<std::result::Result<Vec<_>, _>>()
            .map_err(IngrainError::from)
    }
}

impl FromStr for super::hydrate::HydrateLevel {
    type Err = IngrainError;

    fn from_str(value: &str) -> Result<Self> {
        match value {
            "brief" => Ok(Self::Brief),
            "cards" => Ok(Self::Cards),
            "evidence" => Ok(Self::Evidence),
            other => Err(IngrainError::InvalidLevel(other.to_string())),
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct Promotion {
    pub id: String,
    pub event_id: String,
    pub promoted_type: String,
    pub text: String,
    pub confidence: f64,
    pub reason: String,
    pub current_state: String,
    pub compiled_path: Option<String>,
    pub meta: Value,
    pub created_at: String,
}
