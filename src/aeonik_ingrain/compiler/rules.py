"""Deterministic promotion rules for v0."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PromotionCandidate:
    event_id: str
    promoted_type: str
    text: str
    confidence: float
    reason: str
    current_state: str = "current"
    meta: dict[str, Any] = field(default_factory=dict)


CORRECTION_PATTERNS = [
    re.compile(r"\bcorrection\b[:,]?\s*(.+)", re.I),
    re.compile(r"\bremember\b[:,]?\s*(.+)", re.I),
    re.compile(r"\bdo not\b\s+(.+)", re.I),
    re.compile(r"\bdon't\b\s+(.+)", re.I),
    re.compile(r"\bnever\b\s+(.+)", re.I),
    re.compile(r"\balways\b\s+(.+)", re.I),
    re.compile(r"\bfrom now on\b[:,]?\s*(.+)", re.I),
    re.compile(r"\bno[, ]+that's wrong[.:]?\s*(.+)", re.I),
    re.compile(r"\buse\b\s+(.+\binstead\b\.?)", re.I),
]

DECISION_PATTERNS = [
    re.compile(r"\bdecision\b[:,]?\s*(.+)", re.I),
    re.compile(r"\bwe decided\b\s*(?:that|to)?\s*(.+)", re.I),
    re.compile(r"\bthe decision is\b\s*(.+)", re.I),
]

PLAN_PATTERNS = [
    re.compile(r"^\s*plan\b[:,]?\s*(.+)", re.I),
    re.compile(r"\bthe plan is\b\s*(.+)", re.I),
]

LESSON_PATTERNS = [
    re.compile(r"^\s*lesson\b[:,]?\s*(.+)", re.I),
    re.compile(r"^\s*observation\b[:,]?\s*(.+)", re.I),
]

PROJECT_PATTERNS = [
    re.compile(r"^\s*project\b[:,]?\s*(.+)", re.I),
    re.compile(r"\bactive project\b[:,]?\s*(.+)", re.I),
]

TRACK_PATTERNS = [
    re.compile(r"^\s*completed\b[:,]?\s*(.+)", re.I),
    re.compile(r"^\s*shipped\b[:,]?\s*(.+)", re.I),
    re.compile(r"^\s*fixed\b[:,]?\s*(.+)", re.I),
    re.compile(r"^\s*(tests? passed\b[:,]?.*)", re.I),
]

RISK_PATTERNS = [
    re.compile(r"\bblocked\b[:,]?\s*(.+)", re.I),
    re.compile(r"\bfailed\b[:,]?\s*(.+)", re.I),
    re.compile(r"^\s*(.+\btimed out\b.+)", re.I),
    re.compile(r"\bavoid\b\s+(.+)", re.I),
]

STOPWORDS = {
    "the",
    "and",
    "for",
    "that",
    "this",
    "with",
    "from",
    "into",
    "because",
    "should",
    "would",
    "could",
    "after",
    "before",
    "decision",
    "project",
}

TRACE_KIND_PROMOTIONS = {
    "source_of_truth": ("project_fact", 0.94, "source-of-truth document"),
    "roadmap": ("project_fact", 0.82, "roadmap document"),
    "run_log": ("status", 0.84, "run log"),
    "report": ("status", 0.82, "report document"),
}

STALE_TRACE_KINDS = {
    "draft",
    "external_project",
    "invalidated_report",
    "plan",
}


def extract_promotions(events: list[dict[str, Any]]) -> list[PromotionCandidate]:
    candidates: list[PromotionCandidate] = []
    for event in events:
        candidates.extend(_extract_from_event(event))
    _mark_superseded(candidates)
    return candidates


def _extract_from_event(event: dict[str, Any]) -> list[PromotionCandidate]:
    raw_text = (event.get("text") or "").strip()
    trace_meta, text = _split_trace_prefix(raw_text)
    if not text:
        return []
    meta = {**_meta(event), **trace_meta}
    manual_type = meta.get("remember_type")
    trace_kind = str(meta.get("trace_kind") or meta.get("kind") or "").strip().lower()
    event_id = event["id"]
    out: list[PromotionCandidate] = []

    if manual_type:
        promoted_type = _normalize_manual_type(str(manual_type))
        if promoted_type:
            out.append(PromotionCandidate(
                event_id=event_id,
                promoted_type=promoted_type,
                text=text,
                confidence=0.96,
                reason="manual remember type",
                meta={**meta, "source": "manual"},
            ))
            return out

    if trace_kind == "supersession":
        out.append(PromotionCandidate(event_id, "correction", _clean_match_from_text(text), 0.88, "supersession edge", meta=meta.copy()))
        return out

    for pattern in CORRECTION_PATTERNS:
        if match := pattern.search(text):
            out.append(PromotionCandidate(event_id, "correction", _clean_correction(match, text), 0.9, "correction phrase", meta=meta.copy()))
            return out

    for pattern in LESSON_PATTERNS:
        if match := pattern.search(text):
            out.append(PromotionCandidate(event_id, "lesson", _clean_match(match, text), 0.76, "lesson or observation phrase", meta=meta.copy()))
            return out

    for pattern in PROJECT_PATTERNS:
        if match := pattern.search(text):
            out.append(PromotionCandidate(event_id, "project_fact", _clean_project_match(match, text), 0.84, "project phrase", meta=meta.copy()))
            return out

    for pattern in DECISION_PATTERNS:
        if match := pattern.search(text):
            out.append(PromotionCandidate(event_id, "decision", _clean_match(match, text), 0.88, "decision phrase", meta=meta.copy()))
            break

    for pattern in PLAN_PATTERNS:
        if match := pattern.search(text):
            out.append(PromotionCandidate(event_id, "decision", _clean_match(match, text), 0.72, "plan phrase", meta={**meta, "kind": "plan"}))
            break

    for pattern in TRACK_PATTERNS:
        if match := pattern.search(text):
            out.append(PromotionCandidate(event_id, "track_record", _clean_match(match, text), 0.78, "completion phrase", meta=meta.copy()))
            break

    for pattern in RISK_PATTERNS:
        if match := pattern.search(text):
            out.append(PromotionCandidate(event_id, "lesson", _clean_match(match, text), 0.72, "risk or failure phrase", meta=meta.copy()))
            break

    if not out and event.get("event_type") in {"decision", "reflection", "metric"}:
        promoted_type = "decision" if event.get("event_type") == "decision" else "lesson"
        out.append(PromotionCandidate(event_id, promoted_type, text, 0.62, "canonical event type", meta=meta.copy()))

    if not out and trace_kind in TRACE_KIND_PROMOTIONS:
        promoted_type, confidence, reason = TRACE_KIND_PROMOTIONS[trace_kind]
        out.append(PromotionCandidate(event_id, promoted_type, _clean_match_from_text(text), confidence, reason, meta=meta.copy()))

    if not out and trace_kind in STALE_TRACE_KINDS:
        return []

    return out


def _normalize_manual_type(value: str) -> str | None:
    aliases = {
        "rule": "correction",
        "correction": "correction",
        "decision": "decision",
        "lesson": "lesson",
        "risk": "risk",
        "project": "project_fact",
        "project_fact": "project_fact",
        "status": "status",
        "track_record": "track_record",
        "done": "track_record",
    }
    return aliases.get(value.strip().lower())


def _clean_match(match: re.Match[str], fallback: str) -> str:
    value = (match.group(1) if match.lastindex else fallback).strip()
    if not value:
        value = fallback.strip()
    return value.rstrip(" .") + "."


def _clean_correction(match: re.Match[str], fallback: str) -> str:
    value = (match.group(1) if match.lastindex else fallback).strip()
    full = match.group(0).lower()
    if full.startswith(("don't ", "do not ")):
        value = "Do not " + value
    elif full.startswith("never "):
        value = "Never " + value
    elif full.startswith("always "):
        value = "Always " + value
    if not value:
        value = fallback.strip()
    return value.rstrip(" .") + "."


def _clean_project_match(match: re.Match[str], fallback: str) -> str:
    value = fallback.strip()
    return value.rstrip(" .") + "."


def _clean_match_from_text(text: str) -> str:
    value = text.strip()
    return value.rstrip(" .") + "."


def _meta(event: dict[str, Any]) -> dict[str, Any]:
    meta = event.get("meta") or event.get("meta_json") or {}
    if isinstance(meta, str):
        try:
            return json.loads(meta)
        except json.JSONDecodeError:
            return {}
    return meta if isinstance(meta, dict) else {}


def _split_trace_prefix(text: str) -> tuple[dict[str, Any], str]:
    match = re.match(r"^\[(?P<meta>[^\]]+)\]\s*(?P<body>.*)$", text, flags=re.S)
    if not match:
        return {}, text
    meta_text = match.group("meta")
    trace_meta = {
        f"trace_{key}": value
        for key, value in re.findall(r"\b(source_id|session|thread|actor|kind|turn|created_at|started_at)=([^ ]+)", meta_text)
    }
    body = match.group("body").strip()
    return trace_meta, body or text


def _mark_superseded(candidates: list[PromotionCandidate]) -> None:
    _apply_trace_supersession_edges(candidates)

    product_name_decisions = [
        c for c in candidates
        if c.promoted_type in {"decision", "project_fact"} and _names_product(c.text)
    ]
    if len(product_name_decisions) > 1:
        winner = product_name_decisions[-1]
        for candidate in product_name_decisions[:-1]:
            candidate.current_state = "superseded"
            candidate.meta["superseded_by"] = winner.event_id

    for idx, candidate in enumerate(candidates):
        lower = candidate.text.lower()
        if "not mindcompiler" in lower or "not engream" in lower or "not engram" in lower:
            for previous in candidates[:idx]:
                prev_lower = previous.text.lower()
                if "mindcompiler" in prev_lower or "engram" in prev_lower:
                    previous.current_state = "superseded"
                    previous.meta["superseded_by"] = candidate.event_id

        if _is_active_intent_boundary(lower):
            for previous in candidates[:idx]:
                prev_lower = previous.text.lower()
                if previous.meta.get("kind") == "plan" or "next run" in prev_lower:
                    previous.current_state = "superseded"
                    previous.meta["superseded_by"] = candidate.event_id

        if candidate.promoted_type == "track_record":
            current_tokens = _tokens(lower)
            for previous in candidates[:idx]:
                if previous.meta.get("kind") != "plan":
                    continue
                previous_tokens = _tokens(previous.text)
                if len(current_tokens & previous_tokens) >= 3:
                    previous.current_state = "superseded"
                    previous.meta["superseded_by"] = candidate.event_id

        if _is_no_final_decision(lower):
            current_tokens = _tokens(lower)
            for previous in candidates[:idx]:
                if previous.promoted_type != "decision":
                    continue
                if len(current_tokens & _tokens(previous.text)) >= 2:
                    previous.current_state = "superseded"
                    previous.meta["superseded_by"] = candidate.event_id

        if candidate.promoted_type == "decision":
            for previous in candidates[:idx]:
                if previous.promoted_type != "decision":
                    continue
                if _should_supersede_decision(previous.text, candidate.text):
                    previous.current_state = "superseded"
                    previous.meta["superseded_by"] = candidate.event_id


def _apply_trace_supersession_edges(candidates: list[PromotionCandidate]) -> None:
    by_trace_source: dict[str, list[PromotionCandidate]] = {}
    for candidate in candidates:
        source_id = str(candidate.meta.get("trace_source_id") or "")
        if source_id:
            by_trace_source.setdefault(source_id, []).append(candidate)

    for candidate in candidates:
        trace_kind = str(candidate.meta.get("trace_kind") or candidate.meta.get("kind") or "").lower()
        if trace_kind != "supersession":
            continue
        match = re.search(r"(?P<old>\S+)\s+is\s+superseded_by\s+(?P<new>\S+)", candidate.text)
        if not match:
            continue
        old_source = match.group("old").rstrip(".")
        new_source = match.group("new").rstrip(".")
        candidate.meta["supersedes_trace_source_id"] = old_source
        candidate.meta["superseded_by_trace_source_id"] = new_source
        for previous in by_trace_source.get(old_source, []):
            previous.current_state = "superseded"
            previous.meta["superseded_by_trace_source_id"] = new_source
            previous.meta["superseded_by"] = candidate.event_id


def _names_product(text: str) -> bool:
    lower = text.lower()
    return "product name" in lower or "name is" in lower or "called" in lower


def _is_active_intent_boundary(lower: str) -> bool:
    has_intent = "active goal" in lower or "active intent" in lower or "kanban" in lower or "mission" in lower
    has_boundary = "background context" in lower or "source of truth" in lower or "do not infer" in lower
    return has_intent and has_boundary


def _is_no_final_decision(lower: str) -> bool:
    return "no final decision" in lower or "not resolved" in lower or "unresolved" in lower


def _should_supersede_decision(previous: str, current: str) -> bool:
    prev_lower = previous.lower()
    current_lower = current.lower()
    if _project_names(prev_lower) != _project_names(current_lower):
        return False
    if "no final decision" in current_lower:
        return True
    prev_tokens = _subject_tokens(prev_lower)
    current_tokens = _subject_tokens(current_lower)
    overlap = prev_tokens & current_tokens
    if len(overlap) < 3:
        return False
    has_decision_shape = any(marker in current_lower for marker in (" should ", " threshold ", " run on ", " is "))
    has_replacement_signal = previous.strip() != current.strip() and (
        "not " in current_lower
        or "because" in current_lower
        or any(char.isdigit() for char in previous + current)
        or "instead" in current_lower
    )
    return has_decision_shape and has_replacement_signal


def _project_names(lower: str) -> set[str]:
    return set(re.findall(r"\bproject\s+([a-z0-9_-]+)", lower))


def _subject_tokens(lower: str) -> set[str]:
    return {token for token in _tokens(lower) if token not in STOPWORDS}


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9_]+", text.lower()) if len(token) > 2}
