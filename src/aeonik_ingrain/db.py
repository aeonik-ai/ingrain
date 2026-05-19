"""SQLite store for Aeonik Ingrain."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any, Iterable

from .security import sanitize_for_storage

MIND_EVENT_TYPES = {
    "artifact",
    "interaction",
    "observation",
    "action",
    "decision",
    "plan",
    "goal",
    "reflection",
    "metric",
    "experiment",
    "chunk",
}

PROMOTION_TYPES = {
    "project_fact",
    "decision",
    "correction",
    "lesson",
    "artifact",
    "status",
    "risk",
    "track_record",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_home() -> Path:
    env = os.environ.get("INGRAIN_HOME")
    if env:
        return Path(env).expanduser()
    return Path.cwd() / ".ingrain"


def _hash(parts: Iterable[str]) -> str:
    h = hashlib.sha256()
    for part in parts:
        h.update((part or "").encode("utf-8", errors="replace"))
        h.update(b"\0")
    return h.hexdigest()


@dataclass(frozen=True)
class EventRef:
    id: str
    inserted: bool


class IngrainStore:
    def __init__(self, home: str | Path | None = None):
        self.home = Path(home).expanduser() if home else default_home()
        self.db_path = self.home / "mind.db"
        self.compiled_dir = self.home / "compiled"
        self.evals_dir = self.home / "evals"
        self.examples_dir = self.home / "examples"

    def initialize(self) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        self.compiled_dir.mkdir(parents=True, exist_ok=True)
        self.evals_dir.mkdir(parents=True, exist_ok=True)
        self.examples_dir.mkdir(parents=True, exist_ok=True)
        with self.session() as conn:
            conn.executescript(self._schema_sql())

    def connect(self) -> sqlite3.Connection:
        self.home.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def session(self):
        conn = self.connect()
        try:
            yield conn
        finally:
            conn.close()

    @staticmethod
    def _schema_sql() -> str:
        return resources.files("aeonik_ingrain").joinpath("schema.sql").read_text()

    def add_event(
        self,
        *,
        source: str,
        runner: str,
        event_type: str,
        text: str,
        actor: str = "user",
        session_id: str | None = None,
        project_id: str | None = None,
        thread_id: str | None = None,
        meta: dict[str, Any] | None = None,
        created_at: str | None = None,
    ) -> EventRef:
        self.initialize()
        if event_type not in MIND_EVENT_TYPES:
            raise ValueError(f"Invalid event_type {event_type!r}; use one of {sorted(MIND_EVENT_TYPES)}")
        clean_text = sanitize_for_storage(text)
        meta_obj = meta or {}
        meta_json = json.dumps(meta_obj, sort_keys=True, ensure_ascii=False)
        created = created_at or utc_now()
        fingerprint = _hash([source, runner, event_type, session_id or "", actor or "", clean_text])
        event_id = "evt_" + fingerprint[:24]
        with self.session() as conn:
            before = conn.total_changes
            conn.execute(
                """
                INSERT OR IGNORE INTO ledger_events
                (id, created_at, source, runner, event_type, session_id, project_id, thread_id, actor, text, meta_json, fingerprint)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, created, source, runner, event_type, session_id, project_id, thread_id, actor, clean_text, meta_json, fingerprint),
            )
            row = conn.execute("SELECT id FROM ledger_events WHERE fingerprint = ?", (fingerprint,)).fetchone()
            conn.commit()
            inserted = conn.total_changes > before
        return EventRef(id=row["id"], inserted=inserted)

    def list_events(self, *, limit: int | None = None) -> list[dict[str, Any]]:
        self.initialize()
        sql = "SELECT * FROM ledger_events ORDER BY rowid ASC"
        params: tuple[Any, ...] = ()
        if limit is not None:
            sql += " LIMIT ?"
            params = (limit,)
        with self.session() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def clear_promotions(self) -> None:
        self.initialize()
        with self.session() as conn:
            conn.execute("DELETE FROM promotions")
            conn.commit()

    def add_promotion(
        self,
        *,
        event_id: str,
        promoted_type: str,
        text: str,
        confidence: float,
        reason: str,
        current_state: str = "current",
        compiled_path: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> str:
        self.initialize()
        if promoted_type not in PROMOTION_TYPES:
            raise ValueError(f"Invalid promoted_type {promoted_type!r}; use one of {sorted(PROMOTION_TYPES)}")
        clean_text = sanitize_for_storage(text, limit=4000)
        key = _hash([event_id, promoted_type, clean_text, current_state])
        promotion_id = "prm_" + key[:24]
        meta_json = json.dumps(meta or {}, sort_keys=True, ensure_ascii=False)
        with self.session() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO promotions
                (id, event_id, promoted_type, text, confidence, reason, current_state, compiled_path, meta_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (promotion_id, event_id, promoted_type, clean_text, float(confidence), reason, current_state, compiled_path, meta_json, utc_now()),
            )
            conn.commit()
        return promotion_id

    def list_promotions(self, *, state: str | None = None) -> list[dict[str, Any]]:
        self.initialize()
        sql = "SELECT * FROM promotions"
        params: tuple[Any, ...] = ()
        if state:
            sql += " WHERE current_state = ?"
            params = (state,)
        sql += " ORDER BY rowid ASC"
        with self.session() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def write_compiled_page(
        self,
        *,
        path: str,
        title: str,
        page_type: str,
        content: str,
        source_event_ids: list[str],
    ) -> None:
        self.initialize()
        output_path = self.compiled_dir / path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        source_json = json.dumps(source_event_ids, sort_keys=True)
        updated_at = utc_now()
        with self.session() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO compiled_pages
                (path, title, page_type, content, source_event_ids_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (path, title, page_type, content, source_json, updated_at),
            )
            conn.commit()

    def list_compiled_pages(self) -> list[dict[str, Any]]:
        self.initialize()
        with self.session() as conn:
            rows = conn.execute("SELECT * FROM compiled_pages ORDER BY path ASC").fetchall()
        return [self._row_to_dict(row) for row in rows]

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        for key in ("meta_json", "source_event_ids_json"):
            if key in result:
                try:
                    result[key[:-5] if key.endswith("_json") else key] = json.loads(result[key] or "{}")
                except json.JSONDecodeError:
                    pass
        return result
