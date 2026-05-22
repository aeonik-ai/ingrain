"""Compile promoted learned experience into markdown pages."""

from __future__ import annotations

from collections import defaultdict
import re
from typing import Any

from aeonik_ingrain.db import IngrainStore, utc_now
from .rules import PromotionCandidate, extract_promotions

PAGE_BY_TYPE = {
    "project_fact": ("projects.md", "Projects", "project"),
    "decision": ("decisions.md", "Decisions", "decisions"),
    "correction": ("corrections.md", "Corrections", "corrections"),
    "lesson": ("lessons.md", "Lessons", "lessons"),
    "risk": ("lessons.md", "Lessons", "lessons"),
    "status": ("track-record.md", "Track Record", "track_record"),
    "track_record": ("track-record.md", "Track Record", "track_record"),
    "artifact": ("track-record.md", "Track Record", "track_record"),
}


def _dedupe_candidates(candidates: list[PromotionCandidate]) -> list[PromotionCandidate]:
    """Merge duplicate compiled facts while keeping source traceability."""
    merged: dict[tuple[str, str, str], PromotionCandidate] = {}
    event_ids_by_key: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    order: list[tuple[str, str, str]] = []

    for candidate in candidates:
        key = (candidate.promoted_type, _normalize_text(candidate.text), candidate.current_state)
        if key not in merged:
            merged[key] = candidate
            order.append(key)
        elif candidate.confidence > merged[key].confidence:
            replacement = candidate
            replacement.meta = {**merged[key].meta, **candidate.meta}
            merged[key] = replacement
        if candidate.event_id not in event_ids_by_key[key]:
            event_ids_by_key[key].append(candidate.event_id)

    deduped: list[PromotionCandidate] = []
    for key in order:
        candidate = merged[key]
        event_ids = event_ids_by_key[key]
        if len(event_ids) > 1:
            candidate.meta = {**candidate.meta, "duplicate_event_ids": event_ids}
        deduped.append(candidate)
    return deduped


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().rstrip(" .").casefold())


def compile_store(store: IngrainStore) -> dict[str, Any]:
    store.initialize()
    events = store.list_events()
    candidates = _dedupe_candidates(extract_promotions(events))
    store.clear_promotions()

    for candidate in candidates:
        path = PAGE_BY_TYPE.get(candidate.promoted_type, ("index.md", "Index", "index"))[0]
        store.add_promotion(
            event_id=candidate.event_id,
            promoted_type=candidate.promoted_type,
            text=candidate.text,
            confidence=candidate.confidence,
            reason=candidate.reason,
            current_state=candidate.current_state,
            compiled_path=path,
            meta=candidate.meta,
        )

    promotions = store.list_promotions()
    _write_pages(store, promotions)
    return {
        "events": len(events),
        "promotions": len(promotions),
        "compiled_pages": len(store.list_compiled_pages()),
        "home": str(store.home),
    }


def _write_pages(store: IngrainStore, promotions: list[dict[str, Any]]) -> None:
    by_path: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for promotion in promotions:
        path = promotion.get("compiled_path") or PAGE_BY_TYPE.get(promotion["promoted_type"], ("index.md", "Index", "index"))[0]
        by_path[path].append(promotion)

    for path, title, page_type in _all_pages():
        page_promotions = by_path.get(path, [])
        content = _render_page(title, page_promotions)
        source_ids = sorted({event_id for p in page_promotions for event_id in _promotion_source_ids(p)})
        store.write_compiled_page(path=path, title=title, page_type=page_type, content=content, source_event_ids=source_ids)

    index_content = _render_index(promotions)
    store.write_compiled_page(
        path="index.md",
        title="Aeonik Ingrain Index",
        page_type="index",
        content=index_content,
        source_event_ids=sorted({event_id for p in promotions for event_id in _promotion_source_ids(p)}),
    )


def _promotion_source_ids(promotion: dict[str, Any]) -> list[str]:
    source_ids = [promotion["event_id"]] if promotion.get("event_id") else []
    raw_meta = promotion.get("meta")
    meta = raw_meta if isinstance(raw_meta, dict) else {}
    for event_id in meta.get("duplicate_event_ids", []):
        if event_id and event_id not in source_ids:
            source_ids.append(event_id)
    return source_ids


def _all_pages() -> list[tuple[str, str, str]]:
    seen = []
    for item in PAGE_BY_TYPE.values():
        if item not in seen:
            seen.append(item)
    return seen


def _render_page(title: str, promotions: list[dict[str, Any]]) -> str:
    lines = [f"# {title}", "", f"Updated: {utc_now()}", ""]
    current = [p for p in promotions if p.get("current_state") == "current"]
    superseded = [p for p in promotions if p.get("current_state") != "current"]

    lines.append("## Current")
    lines.append("")
    if current:
        for item in current:
            lines.append(_format_item(item))
    else:
        lines.append("No current items.")

    if superseded:
        lines.extend(["", "## Superseded / Rejected", ""])
        for item in superseded:
            lines.append(_format_item(item))

    lines.append("")
    return "\n".join(lines)


def _render_index(promotions: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = defaultdict(int)
    for item in promotions:
        if item.get("current_state") == "current":
            counts[item["promoted_type"]] += 1
    lines = [
        "# Aeonik Ingrain Index",
        "",
        f"Updated: {utc_now()}",
        "",
        "Learned experience compiled from local agent runs.",
        "",
        "## Current Counts",
        "",
    ]
    if counts:
        for key in sorted(counts):
            lines.append(f"- {key}: {counts[key]}")
    else:
        lines.append("- No current learned experience yet.")
    lines.extend([
        "",
        "## Pages",
        "",
        "- [Projects](projects.md)",
        "- [Decisions](decisions.md)",
        "- [Corrections](corrections.md)",
        "- [Lessons](lessons.md)",
        "- [Track Record](track-record.md)",
        "",
    ])
    return "\n".join(lines)


def _format_item(item: dict[str, Any]) -> str:
    confidence = int(round(float(item.get("confidence") or 0) * 100))
    state = item.get("current_state", "current")
    text = item.get("text", "").strip()
    source = item.get("event_id", "")
    trace = _trace_suffix(item)
    suffix = f" source={source}{trace}, confidence={confidence}%"
    if state != "current":
        suffix += f", state={state}"
    return f"- {text} ({suffix})"


def _trace_suffix(item: dict[str, Any]) -> str:
    raw_meta = item.get("meta")
    meta = raw_meta if isinstance(raw_meta, dict) else {}
    source_id = meta.get("trace_source_id")
    thread = meta.get("trace_thread")
    parts = []
    if source_id:
        parts.append(f"source_id={source_id}")
    if thread:
        parts.append(f"thread={thread}")
    return "; " + "; ".join(parts) if parts else ""
