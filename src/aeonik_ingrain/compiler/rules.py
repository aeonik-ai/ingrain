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
    re.compile(r"\bremember\b[:,]?\s*(.+)", re.I),
    re.compile(r"\bdo not\b\s+(.+)", re.I),
    re.compile(r"\bdon't\b\s+(.+)", re.I),
    re.compile(r"\bnever\b\s+(.+)", re.I),
    re.compile(r"\balways\b\s+(.+)", re.I),
    re.compile(r"\bfrom now on\b[:,]?\s*(.+)", re.I),
    re.compile(r"\bno[, ]+that's wrong[.:]?\s*(.+)", re.I),
]

DECISION_PATTERNS = [
    re.compile(r"\bdecision\b[:,]?\s*(.+)", re.I),
    re.compile(r"\bwe decided\b\s*(?:that|to)?\s*(.+)", re.I),
    re.compile(r"\bthe decision is\b\s*(.+)", re.I),
]

PLAN_PATTERNS = [
    re.compile(r"\bplan\b[:,]?\s*(.+)", re.I),
    re.compile(r"\bthe plan is\b\s*(.+)", re.I),
]

PROJECT_PATTERNS = [
    re.compile(r"\bproject\b[:,]?\s*(.+)", re.I),
    re.compile(r"\bactive project\b[:,]?\s*(.+)", re.I),
]

TRACK_PATTERNS = [
    re.compile(r"^\s*completed\b[:,]?\s*(.+)", re.I),
    re.compile(r"^\s*shipped\b[:,]?\s*(.+)", re.I),
    re.compile(r"^\s*fixed\b[:,]?\s*(.+)", re.I),
    re.compile(r"^\s*tests? passed\b[:,]?\s*(.+)?", re.I),
]

RISK_PATTERNS = [
    re.compile(r"\bblocked\b[:,]?\s*(.+)", re.I),
    re.compile(r"\bfailed\b[:,]?\s*(.+)", re.I),
    re.compile(r"\bavoid\b\s+(.+)", re.I),
]


def extract_promotions(events: list[dict[str, Any]]) -> list[PromotionCandidate]:
    candidates: list[PromotionCandidate] = []
    for event in events:
        candidates.extend(_extract_from_event(event))
    _mark_superseded(candidates)
    return candidates


def _extract_from_event(event: dict[str, Any]) -> list[PromotionCandidate]:
    text = (event.get("text") or "").strip()
    if not text:
        return []
    meta = _meta(event)
    manual_type = meta.get("remember_type")
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
                meta={"source": "manual"},
            ))
            return out

    for pattern in CORRECTION_PATTERNS:
        if match := pattern.search(text):
            out.append(PromotionCandidate(event_id, "correction", _clean_correction(match, text), 0.9, "correction phrase"))
            return out

    for pattern in DECISION_PATTERNS:
        if match := pattern.search(text):
            out.append(PromotionCandidate(event_id, "decision", _clean_match(match, text), 0.88, "decision phrase"))
            break

    for pattern in PLAN_PATTERNS:
        if match := pattern.search(text):
            out.append(PromotionCandidate(event_id, "decision", _clean_match(match, text), 0.72, "plan phrase", meta={"kind": "plan"}))
            break

    for pattern in PROJECT_PATTERNS:
        if match := pattern.search(text):
            out.append(PromotionCandidate(event_id, "project_fact", _clean_match(match, text), 0.84, "project phrase"))
            break

    for pattern in TRACK_PATTERNS:
        if match := pattern.search(text):
            out.append(PromotionCandidate(event_id, "track_record", _clean_match(match, text), 0.78, "completion phrase"))
            break

    for pattern in RISK_PATTERNS:
        if match := pattern.search(text):
            out.append(PromotionCandidate(event_id, "lesson", _clean_match(match, text), 0.72, "risk or failure phrase"))
            break

    if not out and event.get("event_type") in {"decision", "reflection", "metric"}:
        promoted_type = "decision" if event.get("event_type") == "decision" else "lesson"
        out.append(PromotionCandidate(event_id, promoted_type, text, 0.62, "canonical event type"))

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


def _meta(event: dict[str, Any]) -> dict[str, Any]:
    meta = event.get("meta") or event.get("meta_json") or {}
    if isinstance(meta, str):
        try:
            return json.loads(meta)
        except json.JSONDecodeError:
            return {}
    return meta if isinstance(meta, dict) else {}


def _mark_superseded(candidates: list[PromotionCandidate]) -> None:
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


def _names_product(text: str) -> bool:
    lower = text.lower()
    return "product name" in lower or "name is" in lower or "called" in lower
