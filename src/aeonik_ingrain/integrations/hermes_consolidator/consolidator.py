"""Hermes-backed consolidator.

Reads recent events from an IngrainStore, formats them for Hermes, runs
`hermes -z` with the consolidator prompt, parses the JSON output, and writes
the resulting cards back to the store.

No external API keys. Hermes uses whatever model the user configured.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aeonik_ingrain.db import IngrainStore

PROMPT_PATH = Path(__file__).parent / "prompts" / "consolidator.md"

# Match the FIRST fenced JSON code block in the model output. Hermes models
# sometimes wrap output in ```json ... ``` or plain ``` ... ```.
JSON_FENCE = re.compile(r"```(?:json)?\s*(\[.*?\])\s*```", re.DOTALL)


@dataclass(frozen=True)
class ConsolidationResult:
    """Outcome of one consolidator run."""

    events_considered: int
    cards_emitted: int
    promotion_ids: list[str] = field(default_factory=list)
    raw_hermes_output: str = ""
    parse_error: str = ""

    @property
    def ok(self) -> bool:
        return not self.parse_error


# -------------------------------------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------------------------------------


def consolidate(
    store: IngrainStore,
    *,
    limit: int = 50,
    hermes_binary: str | None = None,
    skills: str = "none",
    toolsets: str = "hermes-cli",
    timeout: int = 120,
    dry_run: bool = False,
) -> ConsolidationResult:
    """Run a consolidation pass.

    Reads the most recent `limit` events from the store, runs them through
    Hermes (`hermes -z`), parses the JSON output, and (unless `dry_run`) writes
    cards back to the store via `IngrainStore.add_promotion`.

    Returns a ConsolidationResult with the count of events considered, cards
    emitted, the IDs of cards written, the raw Hermes output (for forensics),
    and any parse error message.
    """
    events = store.list_events(limit=limit)
    if not events:
        return ConsolidationResult(events_considered=0, cards_emitted=0)

    binary = hermes_binary or shutil.which("hermes")
    if not binary or not Path(binary).exists():
        return ConsolidationResult(
            events_considered=len(events),
            cards_emitted=0,
            parse_error=f"hermes binary not found (looked at {binary or '$PATH'})",
        )

    prompt = _build_prompt(events)
    raw = _run_hermes(binary, prompt, skills=skills, toolsets=toolsets, timeout=timeout)

    cards, parse_error = parse_cards(raw)
    if parse_error:
        return ConsolidationResult(
            events_considered=len(events),
            cards_emitted=0,
            raw_hermes_output=raw,
            parse_error=parse_error,
        )

    if dry_run:
        return ConsolidationResult(
            events_considered=len(events),
            cards_emitted=len(cards),
            raw_hermes_output=raw,
        )

    promotion_ids: list[str] = []
    valid_event_ids = {e["id"] for e in events}
    for card in cards:
        # Defensive: only persist cards whose source event is in the batch.
        if card.get("event_id") not in valid_event_ids:
            continue
        promotion_id = store.add_promotion(
            event_id=card["event_id"],
            promoted_type=card["type"],
            text=card["text"],
            confidence=float(card.get("confidence", 0.7)),
            reason=card.get("reason", "hermes consolidator"),
            meta={"source": "hermes_consolidator", "model": "hermes"},
        )
        promotion_ids.append(promotion_id)

    return ConsolidationResult(
        events_considered=len(events),
        cards_emitted=len(promotion_ids),
        promotion_ids=promotion_ids,
        raw_hermes_output=raw,
    )


def parse_cards(raw_output: str) -> tuple[list[dict[str, Any]], str]:
    """Extract the JSON card array from Hermes's output.

    Returns (cards, error). error is empty on success.

    Tolerates:
    - Output wrapped in ```json fences
    - Output that's bare JSON (no fences)
    - Trailing/leading whitespace
    """
    if not raw_output or not raw_output.strip():
        return [], "empty hermes output"

    text = raw_output.strip()

    # Try fenced block first.
    match = JSON_FENCE.search(text)
    if match:
        json_text = match.group(1)
    else:
        # Bare JSON array? Find the first '[' and last ']'.
        start = text.find("[")
        end = text.rfind("]")
        if start < 0 or end <= start:
            return [], f"no JSON array found in output (first 200 chars: {text[:200]!r})"
        json_text = text[start : end + 1]

    try:
        cards = json.loads(json_text)
    except json.JSONDecodeError as exc:
        return [], f"JSON decode failed: {exc} (first 200 chars: {json_text[:200]!r})"

    if not isinstance(cards, list):
        return [], f"expected JSON array, got {type(cards).__name__}"

    # Validate each card has the required fields.
    valid: list[dict[str, Any]] = []
    for i, c in enumerate(cards):
        if not isinstance(c, dict):
            continue
        if not all(k in c for k in ("event_id", "type", "text")):
            continue
        valid.append(c)

    if len(valid) != len(cards):
        # Soft validation: drop malformed entries but report ok.
        pass

    return valid, ""


# -------------------------------------------------------------------------------------------------
# Internal: prompt assembly + hermes invocation
# -------------------------------------------------------------------------------------------------


def _build_prompt(events: list[dict[str, Any]]) -> str:
    """Assemble the consolidator prompt with the system instructions and events block."""
    system = PROMPT_PATH.read_text(encoding="utf-8")
    events_block = _format_events(events)
    return (
        system
        + "\n\n"
        + "---\n\n"
        + "## Events to consolidate\n\n"
        + events_block
        + "\n\n"
        + "Output your JSON array now."
    )


def _format_events(events: list[dict[str, Any]]) -> str:
    """Format event rows as a readable block for the model.

    Each event becomes a short paragraph with id, type, actor, and text. We
    deliberately omit raw meta_json to keep the prompt focused.
    """
    lines = []
    for e in events:
        eid = e.get("id", "?")
        actor = e.get("actor", "?")
        kind = e.get("event_type", "?")
        text = (e.get("text") or "").strip()
        if not text:
            continue
        lines.append(f"[id={eid} actor={actor} kind={kind}]\n{text}")
    return "\n\n".join(lines) if lines else "(no events)"


def _run_hermes(
    binary: str,
    prompt: str,
    *,
    skills: str = "none",
    toolsets: str = "hermes-cli",
    timeout: int = 120,
) -> str:
    """Run `hermes -z` and return the stdout, stripped.

    `--skills none` and `-t hermes-cli` keep the consolidator focused — no skill
    activations, minimal toolset. The consolidator's job is pure
    classification, no tool use.

    We pop HERMES_HOME from the environment so the consolidator uses the user's
    real ~/.hermes (and finds their auth). Some Ingrain lanes set a sandboxed
    HERMES_HOME for the outer process; that sandbox must not propagate to the
    inner `hermes -z` call.
    """
    import os

    env = os.environ.copy()
    env.pop("HERMES_HOME", None)

    cmd = [
        binary,
        "-z",
        prompt,
        "--skills",
        skills,
        "-t",
        toolsets,
        "--ignore-rules",
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return ""
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").strip()


__all__ = ["consolidate", "parse_cards", "ConsolidationResult", "PROMPT_PATH"]
