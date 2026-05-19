"""Best-effort Hermes ingestion."""

from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Any

from aeonik_ingrain.db import IngrainStore

IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
TEXT_COLUMNS = ("content", "text", "message", "prompt", "response", "user_content", "assistant_content", "summary")
ROLE_COLUMNS = ("role", "actor", "sender", "author")
SESSION_COLUMNS = ("session_id", "conversation_id", "thread_id", "id")
CREATED_COLUMNS = ("created_at", "timestamp", "ts", "updated_at")


def hermes_home(path: str | Path | None = None) -> Path:
    if path:
        return Path(path).expanduser()
    if os.environ.get("HERMES_HOME"):
        return Path(os.environ["HERMES_HOME"]).expanduser()
    return Path.home() / ".hermes"


def ingest_hermes(store: IngrainStore, *, hermes_home_path: str | Path | None = None, limit: int = 250) -> dict[str, Any]:
    home = hermes_home(hermes_home_path)
    store.initialize()
    result: dict[str, Any] = {"home": str(home), "inserted": 0, "seen": 0, "warnings": []}

    for name in ("MEMORY.md", "USER.md"):
        path = home / name
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            ref = store.add_event(
                source="hermes_builtin_memory",
                runner="hermes",
                event_type="reflection",
                actor="system",
                text=f"{name}:\n{text}",
                meta={"path": str(path), "kind": name},
            )
            result["seen"] += 1
            result["inserted"] += int(ref.inserted)

    state_db = home / "state.db"
    if not state_db.exists():
        result["warnings"].append(f"Hermes state.db not found at {state_db}")
        return result

    try:
        conn = sqlite3.connect(f"file:{state_db}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as exc:
        result["warnings"].append(f"Could not open Hermes state.db: {exc}")
        return result

    try:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        for table in _prioritize_tables(tables):
            if not IDENT_RE.match(table):
                continue
            columns = _columns(conn, table)
            imported = _import_table(conn, store, table, columns, limit=limit)
            result["seen"] += imported["seen"]
            result["inserted"] += imported["inserted"]
            if imported["seen"]:
                result.setdefault("tables", {})[table] = imported
    finally:
        conn.close()

    return result


def _prioritize_tables(tables: list[str]) -> list[str]:
    preferred = [t for t in tables if any(key in t.lower() for key in ("message", "turn", "session", "conversation"))]
    rest = [t for t in tables if t not in preferred]
    return preferred + rest


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [row[1] for row in rows]


def _import_table(conn: sqlite3.Connection, store: IngrainStore, table: str, columns: list[str], *, limit: int) -> dict[str, int]:
    text_col = _first(columns, TEXT_COLUMNS)
    if not text_col:
        return {"seen": 0, "inserted": 0}
    role_col = _first(columns, ROLE_COLUMNS)
    session_col = _first(columns, SESSION_COLUMNS)
    created_col = _first(columns, CREATED_COLUMNS)
    order = f" ORDER BY {created_col} DESC" if created_col and IDENT_RE.match(created_col) else ""
    sql = f"SELECT * FROM {table}{order} LIMIT ?"
    seen = 0
    inserted = 0
    for row in conn.execute(sql, (limit,)).fetchall():
        text = str(row[text_col] or "").strip()
        if not text:
            continue
        seen += 1
        role = str(row[role_col]) if role_col and row[role_col] is not None else "unknown"
        session_id = str(row[session_col]) if session_col and row[session_col] is not None else None
        created_at = str(row[created_col]) if created_col and row[created_col] is not None else None
        ref = store.add_event(
            source=f"hermes_state:{table}",
            runner="hermes",
            event_type="interaction",
            actor=role,
            text=text,
            session_id=session_id,
            meta={"table": table},
            created_at=created_at,
        )
        inserted += int(ref.inserted)
    return {"seen": seen, "inserted": inserted}


def _first(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    lower = {c.lower(): c for c in columns}
    for candidate in candidates:
        if candidate in lower:
            return lower[candidate]
    for column in columns:
        if any(candidate in column.lower() for candidate in candidates):
            return column
    return None
