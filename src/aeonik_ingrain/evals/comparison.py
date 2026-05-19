"""Sandboxed learned-experience comparison harness.

This does not call a live model. It compares memory substrates:
- default Hermes-style curated memory
- OpenViking-style raw semantic retrieval
- Ingrain promotion + compilation + hydration
"""

from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aeonik_ingrain.compiler.hydrate import hydrate
from aeonik_ingrain.compiler.pages import compile_store
from aeonik_ingrain.db import IngrainStore

WORD_RE = re.compile(r"[A-Za-z0-9_]+")


@dataclass(frozen=True)
class Scenario:
    name: str
    query: str
    events: tuple[str, ...]
    expected: tuple[str, ...]
    forbidden: tuple[str, ...] = ()
    default_memory: tuple[str, ...] = ()


SCENARIOS = (
    Scenario(
        name="correction_after_failure",
        query="write the public launch framing",
        events=(
            "The assistant called Aeonik Ingrain a generic memory layer.",
            "No, that's wrong. Don't call this a memory layer; call it a learned experience layer for autonomous agents.",
        ),
        expected=("learned experience", "autonomous agents"),
        forbidden=("generic memory layer",),
    ),
    Scenario(
        name="stale_product_name",
        query="what is the product name?",
        events=(
            "Decision: The product name is MindCompiler.",
            "Decision: Product name is Aeonik Ingrain, not MindCompiler.",
        ),
        expected=("Product name is Aeonik Ingrain",),
        forbidden=("The product name is MindCompiler",),
    ),
    Scenario(
        name="approval_judgment",
        query="draft investor-facing launch copy",
        events=(
            "The assistant announced an unapproved roadmap item as shipped.",
            "From now on, do not announce unapproved investor-facing features as shipped. Offer approval-safe alternatives.",
        ),
        expected=("approval-safe", "unapproved investor-facing"),
        forbidden=("The assistant announced an unapproved roadmap item as shipped",),
    ),
    Scenario(
        name="kanban_boundary",
        query="continue the Hermes goal and update project work",
        events=(
            "Decision: Hermes owns active goals, subgoals, missions, Kanban columns, scheduling, and task lifecycle.",
            "Decision: Ingrain stores learned experience only. If Ingrain recalls an old plan, treat it as background context unless Hermes says it is active.",
        ),
        expected=("Hermes owns active goals", "Ingrain stores learned experience", "background context"),
        forbidden=("Ingrain owns active goals", "create tasks"),
    ),
    Scenario(
        name="sandbox_recovery",
        query="install a dependency and run verification",
        events=(
            "Failed: dependency install failed because network access was restricted in the sandbox.",
            "From now on, request escalation before dependency installs or network-backed package resolution.",
        ),
        expected=("request escalation", "dependency installs"),
        forbidden=(),
    ),
    Scenario(
        name="track_record",
        query="what work is already done?",
        events=(
            "Completed: Built CLI, SQLite ledger, compiler, hydration, Hermes provider, and LES-100 eval.",
            "Tests passed: compileall and deterministic CLI eval succeeded.",
        ),
        expected=("SQLite ledger", "Hermes provider", "LES-100 eval"),
        forbidden=(),
    ),
)


def run_comparison() -> dict[str, Any]:
    modes = {
        "Hermes default memory": _run_default_mode,
        "Hermes + OpenViking-style retrieval": _run_openviking_style_mode,
        "Hermes + Ingrain": _run_ingrain_mode,
    }
    results: dict[str, Any] = {"scenarios": [], "modes": {}}
    for mode_name, runner in modes.items():
        total = 0
        per = []
        for scenario in SCENARIOS:
            output = runner(scenario)
            score = _score_output(output, scenario)
            total += score
            per.append({"scenario": scenario.name, "score": score, "max": 20, "output_chars": len(output)})
        results["modes"][mode_name] = {"score": total, "max": len(SCENARIOS) * 20, "scenarios": per}
    results["scenarios"] = [s.name for s in SCENARIOS]
    results["note"] = "OpenViking mode is a deterministic raw-retrieval baseline, not a live OpenViking server benchmark."
    return results


def format_comparison(result: dict[str, Any]) -> str:
    lines = ["Learned Experience Comparison", ""]
    for mode, data in result["modes"].items():
        lines.append(f"{mode:<39} {data['score']}/{data['max']}")
    lines.extend(["", "Scenario breakdown:"])
    for scenario in result["scenarios"]:
        parts = []
        for mode, data in result["modes"].items():
            score = next(item["score"] for item in data["scenarios"] if item["scenario"] == scenario)
            parts.append(f"{mode}={score}/20")
        lines.append(f"- {scenario}: " + "; ".join(parts))
    lines.extend(["", result.get("note", "")])
    return "\n".join(lines).strip()


def _run_default_mode(scenario: Scenario) -> str:
    # Hermes default memory is useful but bounded and curated. In this substrate
    # test, it only gets explicit user/profile memory, not automatic promotion.
    return "\n".join(scenario.default_memory)


def _run_openviking_style_mode(scenario: Scenario) -> str:
    # OpenViking-style retrieval finds relevant raw fragments, but does not
    # decide current truth or promote corrections into behavior rules.
    query_tokens = _tokens(scenario.query)
    ranked = sorted(scenario.events, key=lambda text: len(_tokens(text) & query_tokens), reverse=True)
    return "\n".join(ranked[:4])


def _run_ingrain_mode(scenario: Scenario) -> str:
    with tempfile.TemporaryDirectory(prefix="ingrain-compare-") as tmp:
        store = IngrainStore(Path(tmp) / ".ingrain")
        for idx, text in enumerate(scenario.events):
            store.add_event(
                source="comparison_fixture",
                runner="hermes",
                event_type="interaction",
                actor="user" if idx % 2 else "assistant",
                text=text,
                created_at=f"2026-05-19T00:00:{idx:02d}+00:00",
            )
        compile_store(store)
        return hydrate(store, query=scenario.query, limit=10)


def _score_output(output: str, scenario: Scenario) -> int:
    lower = output.lower()
    expected_hits = sum(1 for item in scenario.expected if item.lower() in lower)
    expected_score = 14 if expected_hits == len(scenario.expected) else int(round(14 * expected_hits / max(1, len(scenario.expected))))
    forbidden_hits = sum(1 for item in scenario.forbidden if item.lower() in lower)
    forbidden_score = 4 if forbidden_hits == 0 else 0
    compact_score = 2 if len(output) <= 2500 else 0
    return expected_score + forbidden_score + compact_score


def _tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in WORD_RE.finditer(text or "") if len(m.group(0)) > 2}
