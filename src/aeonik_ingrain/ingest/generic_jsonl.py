"""Generic JSONL ingestion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aeonik_ingrain.db import IngrainStore, MIND_EVENT_TYPES


def ingest_jsonl(store: IngrainStore, path: str | Path, *, source: str = "generic_jsonl", runner: str = "generic") -> dict[str, int]:
    inserted = 0
    seen = 0
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            seen += 1
            item: dict[str, Any] = json.loads(line)
            event_type = item.get("event_type") or "interaction"
            if event_type not in MIND_EVENT_TYPES:
                event_type = "observation"
            ref = store.add_event(
                source=item.get("source") or source,
                runner=item.get("runner") or runner,
                event_type=event_type,
                text=item.get("text") or item.get("content") or "",
                actor=item.get("actor") or item.get("role") or "user",
                session_id=item.get("session_id"),
                project_id=item.get("project_id"),
                thread_id=item.get("thread_id"),
                meta=item.get("meta") or {},
                created_at=item.get("created_at"),
            )
            inserted += int(ref.inserted)
    return {"seen": seen, "inserted": inserted}
