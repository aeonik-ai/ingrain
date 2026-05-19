"""Sandboxed learned-experience comparison harness.

This does not call a live model. It compares memory substrates:
- default Hermes-style curated memory
- OpenViking-style raw semantic retrieval
- Hindsight-style deterministic recall/reflect synthesis
- Ingrain promotion + compilation + hydration

The Hindsight-style mode is not live Hindsight. It is an honest local baseline
for the broad behavior Hindsight is built around: retain memories, retrieve
relevant items, and synthesize a compact reflection.
"""

from __future__ import annotations

import csv
import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aeonik_ingrain.compiler.hydrate import hydrate
from aeonik_ingrain.compiler.pages import compile_store
from aeonik_ingrain.db import IngrainStore, utc_now

WORD_RE = re.compile(r"[A-Za-z0-9_]+")


@dataclass(frozen=True)
class Scenario:
    name: str
    difficulty: int
    rationale: str
    query: str
    events: tuple[str, ...]
    expected: tuple[str, ...]
    forbidden: tuple[str, ...] = ()
    action_terms: tuple[str, ...] = ()
    default_memory: tuple[str, ...] = ()
    max_chars: int = 2500


SCENARIOS = (
    Scenario(
        name="correction_after_failure",
        difficulty=1,
        rationale="A direct user correction should shape later launch copy.",
        query="write the public launch framing",
        events=(
            "The assistant called Aeonik Ingrain a generic memory layer.",
            "No, that's wrong. Don't call this a memory layer; call it a learned experience layer for autonomous agents.",
        ),
        expected=("learned experience", "autonomous agents"),
        forbidden=("generic memory layer",),
        action_terms=("call it", "learned experience"),
    ),
    Scenario(
        name="stale_product_name",
        difficulty=2,
        rationale="A later decision must beat an older product-name decision.",
        query="what is the product name?",
        events=(
            "Decision: The product name is MindCompiler.",
            "Decision: Product name is Aeonik Ingrain, not MindCompiler.",
        ),
        expected=("Product name is Aeonik Ingrain",),
        forbidden=("The product name is MindCompiler",),
        action_terms=("Aeonik Ingrain",),
    ),
    Scenario(
        name="approval_judgment",
        difficulty=2,
        rationale="The memory should change judgment, not just recall a failure.",
        query="draft investor-facing launch copy",
        events=(
            "The assistant announced an unapproved roadmap item as shipped.",
            "From now on, do not announce unapproved investor-facing features as shipped. Offer approval-safe alternatives.",
        ),
        expected=("approval-safe", "unapproved investor-facing"),
        forbidden=("The assistant announced an unapproved roadmap item as shipped",),
        action_terms=("approval-safe", "do not announce"),
    ),
    Scenario(
        name="kanban_boundary",
        difficulty=3,
        rationale="Learned experience must not become a second active-task system.",
        query="continue the Hermes goal and update project work",
        events=(
            "Decision: Hermes owns active goals, subgoals, missions, Kanban columns, scheduling, and task lifecycle.",
            "Decision: Ingrain stores learned experience only. If Ingrain recalls an old plan, treat it as background context unless Hermes says it is active.",
        ),
        expected=("Hermes owns active goals", "Ingrain stores learned experience", "background context"),
        forbidden=("Ingrain owns active goals", "create tasks"),
        action_terms=("background context", "Hermes says"),
    ),
    Scenario(
        name="sandbox_recovery",
        difficulty=3,
        rationale="A prior execution failure should alter the next attempt.",
        query="install a dependency and run verification",
        events=(
            "Failed: dependency install failed because network access was restricted in the sandbox.",
            "From now on, request escalation before dependency installs or network-backed package resolution.",
        ),
        expected=("request escalation", "dependency installs"),
        forbidden=(),
        action_terms=("request escalation",),
    ),
    Scenario(
        name="track_record",
        difficulty=3,
        rationale="Completed outcomes should be reportable without reviving old todos.",
        query="what work is already done?",
        events=(
            "Completed: Built CLI, SQLite ledger, compiler, hydration, Hermes provider, and LES-100 eval.",
            "Tests passed: compileall and deterministic CLI eval succeeded.",
        ),
        expected=("SQLite ledger", "Hermes provider", "LES-100 eval"),
        forbidden=(),
        action_terms=("built", "succeeded"),
    ),
    Scenario(
        name="active_goal_stale_plan",
        difficulty=4,
        rationale="A remembered old plan must not turn into active intent.",
        query="what should the runner do next?",
        events=(
            "Plan: Publish PyPI tonight and announce provider chaining as done.",
            "Decision: Hermes owns active goals and scheduling. Ingrain memories about old plans are background context only.",
            "From now on, do not infer active goals from Ingrain memory; use Hermes goals, missions, and Kanban as the source of truth.",
        ),
        expected=("Hermes owns active goals", "background context", "do not infer active goals"),
        forbidden=("Publish PyPI tonight", "provider chaining as done"),
        action_terms=("use Hermes goals", "source of truth"),
    ),
    Scenario(
        name="completed_vs_todo",
        difficulty=4,
        rationale="A completed outcome should suppress an older build todo.",
        query="summarize launch readiness",
        events=(
            "Plan: Build the Hermes provider, CLI attach flow, and eval report.",
            "Completed: Built the Hermes provider, CLI attach flow, and eval report.",
            "Tests passed: unit suite, deterministic LES, and live Hermes provider matrix.",
        ),
        expected=("Built the Hermes provider", "CLI attach flow", "live Hermes provider matrix"),
        forbidden=("Plan: Build the Hermes provider",),
        action_terms=("Built the Hermes provider", "live Hermes provider matrix"),
    ),
    Scenario(
        name="preference_exception",
        difficulty=5,
        rationale="The current rule includes an exception, not a one-line preference.",
        query="write docs for the eval page",
        events=(
            "Preference: Keep all docs extremely terse.",
            "Correction: Keep normal docs concise, but eval pages must include method, artifacts, blockers, and claim boundaries.",
        ),
        expected=("eval pages", "method", "artifacts", "claim boundaries"),
        forbidden=("all docs extremely terse",),
        action_terms=("include method", "blockers"),
    ),
    Scenario(
        name="source_linked_actionability",
        difficulty=5,
        rationale="The output should be compact, source-linked, and directly usable.",
        query="prepare the final public claim boundary",
        events=(
            "Assistant draft said: Ingrain beats Hindsight as a general memory backend.",
            "Correction: Do not claim Ingrain beats Hindsight. Say the live run compares Ingrain to Hermes default memory and marks Hindsight blocked unless a real package/service/API key is available.",
            "Decision: Use Hindsight-style only as a labeled deterministic baseline when live Hindsight cannot run.",
        ),
        expected=("Hindsight blocked", "Hermes default memory", "Hindsight-style", "deterministic baseline"),
        forbidden=("Ingrain beats Hindsight as a general memory backend",),
        action_terms=("do not claim", "labeled deterministic baseline"),
    ),
)

MODE_NOTES = {
    "Hermes default memory": "Bounded curated memory only.",
    "Hermes + OpenViking-style retrieval": "Deterministic raw semantic retrieval baseline, not a live OpenViking benchmark.",
    "Hermes + Hindsight-style synthesis": "Deterministic retain/recall/reflect-style synthesis, not live Hindsight.",
    "Hermes + Ingrain": "Actual Ingrain compiler and hydration path.",
}


def run_comparison() -> dict[str, Any]:
    modes = {
        "Hermes default memory": _run_default_mode,
        "Hermes + OpenViking-style retrieval": _run_openviking_style_mode,
        "Hermes + Hindsight-style synthesis": _run_hindsight_style_mode,
        "Hermes + Ingrain": _run_ingrain_mode,
    }
    results: dict[str, Any] = {
        "name": "Deterministic Learned Experience Comparison",
        "created_at": utc_now(),
        "claim": "Does learned experience carry forward as current, compact, source-linked guidance?",
        "scoring": {
            "expected_lesson_recall": 8,
            "stale_or_forbidden_suppression": 4,
            "actionability": 4,
            "source_evidence": 2,
            "compactness": 2,
        },
        "scenarios": [],
        "modes": {},
    }
    for mode_name, runner in modes.items():
        total = 0
        per = []
        for scenario in SCENARIOS:
            output = runner(scenario)
            score = _score_output(output, scenario)
            total += score["score"]
            per.append({
                "scenario": scenario.name,
                "score": score["score"],
                "max": 20,
                "components": score["components"],
                "output_chars": len(output),
            })
        results["modes"][mode_name] = {
            "score": total,
            "max": len(SCENARIOS) * 20,
            "note": MODE_NOTES[mode_name],
            "scenarios": per,
        }
    results["scenarios"] = [
        {
            "name": s.name,
            "difficulty": s.difficulty,
            "rationale": s.rationale,
            "expected": list(s.expected),
            "forbidden": list(s.forbidden),
            "action_terms": list(s.action_terms),
        }
        for s in SCENARIOS
    ]
    results["notes"] = [
        "OpenViking-style retrieval is deterministic raw retrieval, not a live OpenViking server benchmark.",
        "Hindsight-style synthesis is deterministic retain/recall/reflect-style behavior, not live Hindsight.",
        "Live Hindsight should be scored by `ingrain live-eval` when a real Hindsight package/service/API key is configured.",
    ]
    return results


def format_comparison(result: dict[str, Any]) -> str:
    lines = ["Learned Experience Comparison", ""]
    for mode, data in result["modes"].items():
        lines.append(f"{mode:<39} {data['score']}/{data['max']}")
    lines.extend(["", "Scenario breakdown:"])
    for scenario in result["scenarios"]:
        name = scenario["name"] if isinstance(scenario, dict) else scenario
        parts = []
        for mode, data in result["modes"].items():
            score = next(item["score"] for item in data["scenarios"] if item["scenario"] == name)
            parts.append(f"{mode}={score}/20")
        lines.append(f"- {name}: " + "; ".join(parts))
    lines.extend([""])
    lines.extend(result.get("notes", []))
    return "\n".join(lines).strip()


def format_comparison_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Learned Experience Results",
        "",
        "## Hypothesis",
        "",
        "A runner-agent memory layer should carry corrections, decisions, completed outcomes, and stale-plan warnings into the next run as current, compact, source-linked guidance.",
        "",
        "## Method",
        "",
        "| Control | Implementation |",
        "|---|---|",
        "| Deterministic universes | Ten preregistered local scenarios in `src/aeonik_ingrain/evals/comparison.py`. |",
        "| Same input per mode | Each mode receives the same ordered event list and query. |",
        "| No model calls | The comparison is dependency-free and repeatable. |",
        "| Hindsight-style is labeled | The Hindsight row is a deterministic retain/recall/reflect-style baseline, not live Hindsight. |",
        "| Live Hindsight path | Use `ingrain live-eval` when a real Hindsight package/service/API key is configured. |",
        "",
        "## Results",
        "",
        "| Mode | Score | Note |",
        "|---|---:|---|",
    ]
    for mode, data in result["modes"].items():
        lines.append(f"| {mode} | {data['score']}/{data['max']} | {data.get('note', '')} |")

    lines.extend([
        "",
        "## Scenario Breakdown",
        "",
        "| Scenario | Difficulty | Rationale | Scores |",
        "|---|---:|---|---|",
    ])
    for scenario in result["scenarios"]:
        name = scenario["name"]
        scores = []
        for mode, data in result["modes"].items():
            row = next(item for item in data["scenarios"] if item["scenario"] == name)
            scores.append(f"{mode}={row['score']}/20")
        lines.append(f"| `{name}` | {scenario['difficulty']} | {scenario['rationale']} | {'; '.join(scores)} |")

    lines.extend([
        "",
        "## Scoring Rubric",
        "",
        "Each scenario is worth 20 points:",
        "",
        "| Component | Points |",
        "|---|---:|",
    ])
    for key, value in result["scoring"].items():
        label = key.replace("_", " ").title()
        lines.append(f"| {label} | {value} |")

    lines.extend([
        "",
        "## Interpretation",
        "",
        "The deterministic comparison supports a narrow engineering claim: Ingrain's compiler and hydration path are strong at turning prior execution experience into current practice memory. It does not show that Ingrain is a better general-purpose memory backend than live Hindsight, OpenViking, or any other Hermes provider.",
        "",
        "The Hindsight-style baseline is intentionally strong and intentionally labeled. It models synthesized recall from retained memories, but it does not exercise Hindsight's real graph, entity, temporal, cloud, or local runtime.",
        "",
        "## Artifacts",
        "",
        "- Machine-readable results: `docs/evidence/deterministic-les-comparison/results.json`",
        "- CSV scores: `docs/evidence/deterministic-les-comparison/results.csv`",
        "- Live provider matrix: `docs/evidence/live-les-provider-matrix/`",
        "",
    ])
    return "\n".join(lines)


def write_comparison_artifacts(result: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "results.json"
    csv_path = out / "results.csv"
    report_path = out / "report.md"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["mode", "scenario", "score", "max", "expected", "forbidden", "actionability", "source_evidence", "compactness", "output_chars"])
        for mode, data in result["modes"].items():
            for row in data["scenarios"]:
                components = row.get("components", {})
                writer.writerow([
                    mode,
                    row["scenario"],
                    row["score"],
                    row["max"],
                    components.get("expected", 0),
                    components.get("forbidden", 0),
                    components.get("actionability", 0),
                    components.get("source_evidence", 0),
                    components.get("compactness", 0),
                    row.get("output_chars", 0),
                ])
    report_path.write_text(format_comparison_markdown(result), encoding="utf-8")
    return {"json": str(json_path), "csv": str(csv_path), "report": str(report_path)}


def _run_default_mode(scenario: Scenario) -> str:
    # Hermes default memory is useful but bounded and curated. In this substrate
    # test, it only gets explicit user/profile memory, not automatic promotion.
    return "\n".join(f"[MEMORY.md] {item}" for item in scenario.default_memory)


def _run_openviking_style_mode(scenario: Scenario) -> str:
    # OpenViking-style retrieval finds relevant raw fragments, but does not
    # decide current truth or promote corrections into behavior rules.
    query_tokens = _tokens(scenario.query)
    ranked = sorted(
        enumerate(scenario.events, start=1),
        key=lambda item: len(_tokens(item[1]) & query_tokens),
        reverse=True,
    )
    return "\n".join(f"[retrieved: memory_{idx:02d}] {text}" for idx, text in ranked[:4])


def _run_hindsight_style_mode(scenario: Scenario) -> str:
    # Deterministic approximation of retain -> recall -> reflect:
    # retrieve relevant memories, prefer later lesson-like memories, and emit a
    # synthesized reflection with evidence IDs. This is deliberately not live
    # Hindsight and does not claim to measure Hindsight's real graph/runtime.
    query_tokens = _tokens(scenario.query)
    indexed = list(enumerate(scenario.events, start=1))
    ranked = sorted(
        indexed,
        key=lambda item: (
            _lesson_weight(item[1]),
            len(_tokens(item[1]) & query_tokens),
            item[0],
        ),
        reverse=True,
    )
    selected = [item for item in ranked if _lesson_weight(item[1]) > 0 or _tokens(item[1]) & query_tokens][:5]
    if not selected:
        selected = ranked[:3]

    lines = [
        "Hindsight-style synthesis baseline (deterministic; not live Hindsight).",
        "Current reflection:",
    ]
    for idx, text in sorted(selected, key=lambda item: item[0], reverse=True):
        if _is_obviously_stale_raw(text, selected):
            continue
        lines.append(f"- {_clean_memory_text(text)} [evidence: memory_{idx:02d}]")
    lines.append("Action guidance:")
    for term in scenario.action_terms:
        lines.append(f"- Preserve: {term}.")
    return "\n".join(lines)


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


def _score_output(output: str, scenario: Scenario) -> dict[str, Any]:
    lower = output.lower()
    expected_hits = sum(1 for item in scenario.expected if item.lower() in lower)
    expected_score = 8 if expected_hits == len(scenario.expected) else int(round(8 * expected_hits / max(1, len(scenario.expected))))
    forbidden_hits = sum(1 for item in scenario.forbidden if item.lower() in lower)
    forbidden_score = 4 if forbidden_hits == 0 else 0
    action_hits = sum(1 for item in scenario.action_terms if item.lower() in lower)
    action_score = 4 if not scenario.action_terms or action_hits == len(scenario.action_terms) else int(round(4 * action_hits / max(1, len(scenario.action_terms))))
    evidence_score = 2 if _has_source_evidence(output) else 0
    compact_score = 2 if output.strip() and len(output) <= scenario.max_chars else 0
    components = {
        "expected": expected_score,
        "forbidden": forbidden_score,
        "actionability": action_score,
        "source_evidence": evidence_score,
        "compactness": compact_score,
    }
    return {"score": sum(components.values()), "components": components}


def _tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in WORD_RE.finditer(text or "") if len(m.group(0)) > 2}


def _lesson_weight(text: str) -> int:
    lower = text.lower()
    weight = 0
    for marker in ("correction", "from now on", "do not", "don't", "never", "always"):
        if marker in lower:
            weight += 5
    for marker in ("decision", "completed", "tests passed", "failed", "blocked"):
        if marker in lower:
            weight += 4
    for marker in ("background context", "source of truth", "approval-safe", "hindsight-style"):
        if marker in lower:
            weight += 3
    return weight


def _clean_memory_text(text: str) -> str:
    return re.sub(r"^(Decision|Correction|Plan|Completed|Failed|Tests passed|Preference):\s*", "", text.strip(), flags=re.I)


def _is_obviously_stale_raw(text: str, selected: list[tuple[int, str]]) -> bool:
    lower = text.lower()
    later_text = "\n".join(other.lower() for _, other in selected)
    if "plan:" in lower and ("background context" in later_text or "do not infer active goals" in later_text):
        return True
    if "preference:" in lower and "correction:" in later_text:
        return True
    if "the product name is mindcompiler" in lower and "not mindcompiler" in later_text:
        return True
    if "ingrain beats hindsight as a general memory backend" in lower and "do not claim ingrain beats hindsight" in later_text:
        return True
    return False


def _has_source_evidence(output: str) -> bool:
    lower = output.lower()
    return any(marker in lower for marker in ("[source:", "source=", "evidence:", "[retrieved:", "memory.md"))
