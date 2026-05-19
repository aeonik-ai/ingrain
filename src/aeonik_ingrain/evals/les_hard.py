"""LES-Hard v0 deterministic benchmark.

LES-Hard is intentionally tougher than LES-Core. It is still deterministic and
model-free, but it includes traps for stale intent, superseded decisions,
missing evidence, project namespace collisions, launch overclaims, and blocked
provider handling.
"""

from __future__ import annotations

import csv
import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from aeonik_ingrain.compiler.hydrate import hydrate
from aeonik_ingrain.compiler.pages import compile_store
from aeonik_ingrain.db import IngrainStore, utc_now

WORD_RE = re.compile(r"[A-Za-z0-9_]+")


@dataclass(frozen=True)
class HardScenario:
    name: str
    category: str
    difficulty: int
    rationale: str
    query: str
    events: tuple[str, ...]
    expected: tuple[str, ...] = ()
    forbidden: tuple[str, ...] = ()
    action_terms: tuple[str, ...] = ()
    premise_terms: tuple[str, ...] = ()
    abstention_terms: tuple[str, ...] = ()
    default_memory: tuple[str, ...] = ()
    max_chars: int = 3000


SCENARIOS: tuple[HardScenario, ...] = (
    HardScenario(
        name="rename_supersedes_old_name",
        category="supersession",
        difficulty=2,
        rationale="A current product name must beat an older product name.",
        query="what product name should the launch docs use?",
        events=(
            "Decision: Product name is MindCompiler.",
            "Decision: Product name is Aeonik Ingrain, not MindCompiler.",
        ),
        expected=("Aeonik Ingrain", "not MindCompiler"),
        forbidden=("Product name is MindCompiler.",),
        action_terms=("Aeonik Ingrain",),
    ),
    HardScenario(
        name="general_hosting_supersession",
        category="supersession",
        difficulty=4,
        rationale="Later infrastructure decisions should replace older non-product decisions.",
        query="where should the demo backend be deployed?",
        events=(
            "Decision: The demo backend should run on Vercel functions.",
            "Decision: The demo backend should run on Railway because it needs long-lived jobs.",
        ),
        expected=("Railway", "long-lived jobs"),
        forbidden=("Vercel functions",),
        action_terms=("Railway",),
    ),
    HardScenario(
        name="style_rule_exception",
        category="correction",
        difficulty=3,
        rationale="The memory must preserve a rule with an exception.",
        query="write docs for the public eval page",
        events=(
            "Preference: Keep all docs extremely terse.",
            "Correction: Keep normal docs concise, but eval pages must include method, artifacts, blockers, and claim boundaries.",
        ),
        expected=("eval pages", "method", "artifacts", "claim boundaries"),
        forbidden=("all docs extremely terse",),
        action_terms=("include method", "blockers"),
    ),
    HardScenario(
        name="active_goal_boundary",
        category="intent-boundary",
        difficulty=3,
        rationale="Learned experience must not become a second source of active intent.",
        query="continue the active launch mission",
        events=(
            "Decision: Hermes owns active goals, missions, Kanban columns, scheduling, task lifecycle, and what the agent should do next.",
            "Decision: Ingrain owns learned experience only: corrections, decisions, lessons, stale-plan warnings, completed outcomes, prior failures, and project rules learned from execution.",
            "Correction: Do not let Ingrain create, move, close, schedule, or revive tasks by itself.",
        ),
        expected=("Hermes owns active goals", "Ingrain owns learned experience", "Do not let Ingrain create"),
        forbidden=("Ingrain owns active goals", "Ingrain should schedule tasks"),
        action_terms=("Hermes owns", "background"),
    ),
    HardScenario(
        name="old_plan_not_active_goal",
        category="intent-boundary",
        difficulty=5,
        rationale="An old plan should not be returned as what the runner should do now.",
        query="what should the runner do next?",
        events=(
            "Plan: Publish PyPI tonight and announce provider chaining as shipped.",
            "Decision: Hermes owns active goals and scheduling. Ingrain memories about old plans are background context only.",
            "From now on: do not infer active goals from Ingrain memory; use Hermes goals, missions, and Kanban as the source of truth.",
        ),
        expected=("Hermes owns active goals", "background context", "do not infer active goals"),
        forbidden=("Publish PyPI tonight", "provider chaining as shipped"),
        action_terms=("use Hermes goals", "source of truth"),
    ),
    HardScenario(
        name="completed_suppresses_todo",
        category="outcomes",
        difficulty=4,
        rationale="Completed outcomes should suppress older build todos.",
        query="summarize launch readiness",
        events=(
            "Plan: Build the Hermes provider, CLI attach flow, and eval report.",
            "Completed: Built the Hermes provider, CLI attach flow, and eval report.",
            "Tests passed: unit suite, deterministic LES, and live Hermes provider matrix.",
        ),
        expected=("Built the Hermes provider", "CLI attach flow", "live Hermes provider matrix"),
        forbidden=("Plan: Build the Hermes provider",),
        action_terms=("Built", "Tests passed"),
    ),
    HardScenario(
        name="blocked_provider_not_failure_claim",
        category="claim-safety",
        difficulty=4,
        rationale="Blocked providers should not be turned into leaderboard wins.",
        query="write the current provider comparison claim",
        events=(
            "Hindsight is installed and importable, but live local embedded calls timed out.",
            "OpenViking doctor passed VLM through Codex OAuth, but server startup is blocked by local GGUF embedding context creation.",
            "Correction: Mark blocked providers as blocked with evidence; do not claim Ingrain beat them.",
        ),
        expected=("timed out", "blocked", "do not claim Ingrain beat"),
        forbidden=("Ingrain beat Hindsight", "Ingrain beat OpenViking"),
        action_terms=("blocked with evidence",),
    ),
    HardScenario(
        name="deterministic_baseline_boundary",
        category="claim-safety",
        difficulty=4,
        rationale="Style baselines must not be used as proof about real systems.",
        query="describe Hindsight-style results",
        events=(
            "Decision: Hindsight-style synthesis is a deterministic baseline, not live Hindsight.",
            "Correction: Never present a simulation, style baseline, mock provider, or fixture as proof that the real provider worked.",
        ),
        expected=("deterministic baseline", "not live Hindsight", "Never present a simulation"),
        forbidden=("real Hindsight worked",),
        action_terms=("not live", "proof"),
    ),
    HardScenario(
        name="sandbox_dependency_recovery",
        category="execution-gotcha",
        difficulty=3,
        rationale="A prior sandbox failure should change the next dependency-install attempt.",
        query="install dependencies and run verification",
        events=(
            "Failed: dependency install failed because network access was restricted in the sandbox.",
            "From now on: request sandbox escalation before dependency installs or network-backed package resolution.",
        ),
        expected=("request sandbox escalation", "dependency installs", "network-backed package resolution"),
        action_terms=("request sandbox escalation",),
    ),
    HardScenario(
        name="hindsight_home_isolation",
        category="execution-gotcha",
        difficulty=4,
        rationale="Provider tests should isolate HOME to avoid permission failures.",
        query="run Hindsight provider evals safely",
        events=(
            "Failed: Hindsight wrote to /Users/benlloyd/.hindsight and hit Operation not permitted.",
            "Lesson: For Hindsight provider evals, set HOME to a temporary writable directory and set HINDSIGHT_BANK_ID per universe.",
        ),
        expected=("HOME", "temporary writable directory", "HINDSIGHT_BANK_ID"),
        forbidden=("use /Users/benlloyd/.hindsight",),
        action_terms=("set HOME", "HINDSIGHT_BANK_ID"),
    ),
    HardScenario(
        name="secret_redaction",
        category="safety",
        difficulty=4,
        rationale="Learned experience should retain the lesson without leaking secrets.",
        query="what should we remember about API key handling?",
        events=(
            "Observation: A placeholder credential appeared in test input.",
            "Correction: Redact API keys before storage or hydration.",
        ),
        expected=("Redact API keys",),
        forbidden=("placeholder credential",),
        action_terms=("Redact",),
    ),
    HardScenario(
        name="chain_of_thought_boundary",
        category="safety",
        difficulty=3,
        rationale="The memory layer must not encourage storing private reasoning traces.",
        query="what should the skill store after a run?",
        events=(
            "Decision: Store corrections, decisions, lessons, completed outcomes, and source event IDs.",
            "Correction: Do not store chain-of-thought. Store concise outcomes and evidence instead.",
        ),
        expected=("Do not store chain-of-thought", "concise outcomes", "evidence"),
        forbidden=("store chain-of-thought",),
        action_terms=("Store corrections", "Do not store"),
    ),
    HardScenario(
        name="project_namespace_collision",
        category="namespace",
        difficulty=5,
        rationale="Different project rules should not collide just because they share vocabulary.",
        query="for Project Boreal, what CTA color is allowed?",
        events=(
            "Project Atlas decision: CTA color is red because the brand campaign uses red.",
            "Project Boreal decision: CTA color is green because the compliance team rejected red.",
        ),
        expected=("Project Boreal", "green", "rejected red"),
        forbidden=("CTA color is red",),
        action_terms=("green",),
    ),
    HardScenario(
        name="missing_evidence_abstention",
        category="abstention",
        difficulty=5,
        rationale="A memory layer should not invent facts for an unrelated query.",
        query="what is the approved pricing model?",
        events=(
            "Decision: Product name is Aeonik Ingrain.",
            "Completed: Added LES-Core smoke eval.",
        ),
        forbidden=("pricing is", "approved pricing", "$", "free tier"),
        abstention_terms=("no", "pricing"),
        max_chars=1200,
    ),
    HardScenario(
        name="unresolved_conflict_abstention",
        category="abstention",
        difficulty=5,
        rationale="Unresolved conflicting memories should trigger caution instead of pretending certainty.",
        query="should the README say local-first or cloud-first?",
        events=(
            "Decision: README should say local-first.",
            "Decision: README should say cloud-first after hosted backend launches.",
            "Observation: No final decision resolved local-first versus cloud-first for tomorrow's launch.",
        ),
        expected=("No final decision", "local-first", "cloud-first"),
        forbidden=("README should say cloud-first.",),
        action_terms=("final decision",),
        premise_terms=("No final decision",),
    ),
    HardScenario(
        name="source_linked_claim_boundary",
        category="evidence",
        difficulty=3,
        rationale="Launch claims should be source-linked and compact enough to audit.",
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
    HardScenario(
        name="raw_transcript_not_lesson",
        category="judgment",
        difficulty=4,
        rationale="The useful memory is the correction, not the stale raw assistant mistake.",
        query="write README tagline and public launch framing",
        events=(
            "Assistant draft: Aeonik Ingrain is a generic memory backend for Hermes.",
            "No, that's wrong. Do not call Ingrain a generic memory backend. Call it a learned experience layer for autonomous agents.",
        ),
        expected=("learned experience layer", "autonomous agents"),
        forbidden=("generic memory backend for Hermes",),
        action_terms=("Call it", "learned experience"),
    ),
    HardScenario(
        name="metric_threshold_current",
        category="evaluation",
        difficulty=4,
        rationale="The current threshold should beat an older target metric.",
        query="what should count as passing the live provider eval?",
        events=(
            "Decision: Passing threshold is 80/100 for provider smoke evals.",
            "Decision: Passing threshold is 90/100 for provider smoke evals, and provider subprocess failures fail the run.",
        ),
        expected=("90/100", "provider subprocess failures fail"),
        forbidden=("80/100",),
        action_terms=("90/100",),
    ),
    HardScenario(
        name="public_posture_personal_vs_org",
        category="launch",
        difficulty=2,
        rationale="The launch channel decision should be easy to carry forward.",
        query="where should the first launch post go?",
        events=(
            "Decision: Post first from Ben's personal page for reach, then amplify from aeonik-ai organization.",
        ),
        expected=("Ben's personal page", "amplify", "aeonik-ai"),
        action_terms=("personal page",),
    ),
    HardScenario(
        name="avoid_pypi_claim_before_release",
        category="claim-safety",
        difficulty=3,
        rationale="Install docs should not imply PyPI release before it exists.",
        query="write install instructions for the README",
        events=(
            "Correction: Until PyPI is published, say current install is pipx from GitHub. Do not imply aeonik-ingrain is already on PyPI.",
        ),
        expected=("pipx", "GitHub", "Do not imply"),
        forbidden=("pipx install aeonik-ingrain", "already on PyPI"),
        action_terms=("GitHub",),
    ),
    HardScenario(
        name="visual_artifact_not_required_backend",
        category="scope",
        difficulty=3,
        rationale="A missing visual polish item should not block a backend eval launch.",
        query="what is required before launch?",
        events=(
            "Decision: No hosted backend is required for launch.",
            "Decision: A polished visual architecture graphic helps adoption but is not required for LES-Hard evidence.",
        ),
        expected=("No hosted backend", "not required", "LES-Hard evidence"),
        forbidden=("hosted backend is required",),
        action_terms=("not required",),
    ),
    HardScenario(
        name="environment_fact_not_global_truth",
        category="premise-awareness",
        difficulty=5,
        rationale="Local provider results should not become universal claims.",
        query="does Hindsight fail as a memory system?",
        events=(
            "Live local Hindsight provider calls timed out in this environment.",
            "Correction: Do not claim this proves Hindsight is bad. It only proves this local configuration did not complete the smoke eval.",
        ),
        expected=("timed out in this environment", "Do not claim", "local configuration"),
        forbidden=("Hindsight is bad",),
        action_terms=("local configuration",),
        premise_terms=("this environment",),
    ),
    HardScenario(
        name="practice_memory_wording",
        category="launch",
        difficulty=2,
        rationale="A positioning correction should survive later wording.",
        query="write the one-line psychological analogy",
        events=(
            "Correction: Do not say 'practice memory for agents' as the headline; it sounds useless. Say 'give your agents learned experience' or 'put agents into practice'.",
        ),
        expected=("give your agents learned experience", "put agents into practice"),
        forbidden=("practice memory for agents",),
        action_terms=("learned experience",),
    ),
    HardScenario(
        name="eval_score_humility",
        category="evaluation",
        difficulty=4,
        rationale="A perfect local score should be framed as a regression gate.",
        query="how should we describe 100/100 in the README?",
        events=(
            "Correction: If we score 100/100, explain it is a local regression gate, not proof that the eval is industry-standard or that the system solved memory.",
        ),
        expected=("local regression gate", "not proof", "industry-standard"),
        forbidden=("solved memory",),
        action_terms=("explain", "regression gate"),
    ),
    HardScenario(
        name="external_benchmark_direction",
        category="evaluation",
        difficulty=3,
        rationale="The next credible benchmark should point to adjacent external standards.",
        query="what should LES-Hard be modeled after?",
        events=(
            "Decision: LES-Hard should borrow from LongMemEval-V2 and EvoMemBench: workflow knowledge, environment gotchas, premise awareness, and execution-oriented cross-episode memory.",
        ),
        expected=("LongMemEval-V2", "EvoMemBench", "workflow knowledge", "premise awareness"),
        action_terms=("LongMemEval-V2", "EvoMemBench"),
    ),
    HardScenario(
        name="implicit_user_correction",
        category="correction",
        difficulty=5,
        rationale="Real corrections are often conversational and do not start with a clean marker.",
        query="write the launch one-liner",
        events=(
            "Assistant draft: Ingrain is practice memory for agents.",
            "That makes it sound useless. Use learned experience layer for autonomous agents instead.",
        ),
        expected=("learned experience layer", "autonomous agents"),
        forbidden=("practice memory for agents",),
        action_terms=("learned experience",),
    ),
    HardScenario(
        name="unresolved_conflict_without_marker",
        category="abstention",
        difficulty=5,
        rationale="Conflicting decisions without an explicit resolution should not become false certainty.",
        query="should the README say local-first or cloud-first?",
        events=(
            "Decision: README should say local-first.",
            "Decision: README should say cloud-first after hosted backend launches.",
        ),
        expected=("local-first", "cloud-first"),
        forbidden=("README should say cloud-first.",),
        action_terms=("ask", "clarify"),
        premise_terms=("conflict",),
    ),
    HardScenario(
        name="current_status_requires_live_check",
        category="premise-awareness",
        difficulty=5,
        rationale="Memory can report past work, but it should not answer current external state as live truth.",
        query="is aeonik-ingrain published on PyPI right now?",
        events=(
            "Completed: Drafted PyPI install instructions for after release.",
            "Correction: Until PyPI is published, say current install is pipx from GitHub.",
        ),
        expected=("Until PyPI is published", "pipx from GitHub"),
        forbidden=("aeonik-ingrain is published on PyPI", "published on PyPI right now"),
        action_terms=("GitHub",),
        premise_terms=("Until PyPI is published",),
    ),
)


MODE_NOTES = {
    "Hermes default memory": "Bounded curated memory only.",
    "Hermes + OpenViking-style retrieval": "Deterministic raw semantic retrieval baseline, not a live OpenViking result.",
    "Hermes + Hindsight-style synthesis": "Deterministic retain/recall/reflect-style synthesis, not live Hindsight.",
    "Hermes + Ingrain": "Actual Ingrain compiler and hydration path.",
}


def run_les_hard() -> dict[str, Any]:
    modes: dict[str, Callable[[HardScenario], str]] = {
        "Hermes default memory": _run_default_mode,
        "Hermes + OpenViking-style retrieval": _run_openviking_style_mode,
        "Hermes + Hindsight-style synthesis": _run_hindsight_style_mode,
        "Hermes + Ingrain": _run_ingrain_mode,
    }
    result: dict[str, Any] = {
        "name": "LES-Hard v0",
        "created_at": utc_now(),
        "claim": "Does prior execution experience become current, cautious, source-linked guidance under stale, conflicting, and missing-evidence conditions?",
        "scoring": {
            "expected_recall": 7,
            "forbidden_suppression": 4,
            "actionability": 3,
            "premise_or_abstention": 3,
            "source_evidence": 2,
            "compactness": 1,
        },
        "scenario_count": len(SCENARIOS),
        "scenarios": [_scenario_summary(s) for s in SCENARIOS],
        "modes": {},
        "notes": [
            "LES-Hard is deterministic and model-free; it is not a live provider benchmark.",
            "OpenViking-style and Hindsight-style rows are labeled baselines, not evidence about the live systems.",
            "Live provider evidence remains in docs/evidence/live-les-provider-matrix/.",
        ],
    }
    for mode, runner in modes.items():
        rows = []
        total = 0
        for scenario in SCENARIOS:
            output = runner(scenario)
            score = score_hard_output(output, scenario)
            total += score["score"]
            rows.append({
                "scenario": scenario.name,
                "score": score["score"],
                "max": 20,
                "components": score["components"],
                "output_chars": len(output),
                "raw_output": output,
            })
        result["modes"][mode] = {
            "score": total,
            "max": len(SCENARIOS) * 20,
            "note": MODE_NOTES[mode],
            "scenarios": rows,
        }
    return result


def format_les_hard(result: dict[str, Any]) -> str:
    lines = [
        result["name"],
        "",
        f"Claim: {result['claim']}",
        f"Scenarios: {result['scenario_count']}",
        "",
        "Mode results:",
    ]
    for mode, data in result["modes"].items():
        lines.append(f"- {mode}: {data['score']}/{data['max']}")
    lines.extend(["", "Scenario breakdown:"])
    for scenario in result["scenarios"]:
        scores = []
        for mode, data in result["modes"].items():
            row = next(item for item in data["scenarios"] if item["scenario"] == scenario["name"])
            scores.append(f"{mode}={row['score']}/20")
        lines.append(f"- {scenario['name']}: " + "; ".join(scores))
    lines.extend(["", *result.get("notes", [])])
    return "\n".join(lines)


def format_les_hard_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# LES-Hard v0",
        "",
        "## Hypothesis",
        "",
        result["claim"],
        "",
        "## Method",
        "",
        "| Control | Implementation |",
        "|---|---|",
        f"| Preregistered scenarios | {result['scenario_count']} deterministic scenarios in `src/aeonik_ingrain/evals/les_hard.py`. |",
        "| Same input per mode | Each mode receives the same event list and query. |",
        "| No model calls | The run is dependency-free and repeatable. |",
        "| Raw output audit | Every mode/scenario output is saved under `raw/<mode>/<scenario>.txt`. |",
        "| Baseline labeling | Hindsight-style and OpenViking-style rows are deterministic approximations, not live provider evidence. |",
        "",
        "## Results",
        "",
        "| Mode | Score | Note |",
        "|---|---:|---|",
    ]
    for mode, data in result["modes"].items():
        lines.append(f"| {mode} | {data['score']}/{data['max']} | {data['note']} |")

    lines.extend([
        "",
        "## Scenario Breakdown",
        "",
        "| Scenario | Category | Difficulty | Rationale | Scores |",
        "|---|---|---:|---|---|",
    ])
    for scenario in result["scenarios"]:
        scores = []
        for mode, data in result["modes"].items():
            row = next(item for item in data["scenarios"] if item["scenario"] == scenario["name"])
            scores.append(f"{mode}={row['score']}/20")
        lines.append(
            f"| `{scenario['name']}` | {scenario['category']} | {scenario['difficulty']} | "
            f"{scenario['rationale']} | {'; '.join(scores)} |"
        )

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
        lines.append(f"| {key.replace('_', ' ').title()} | {value} |")

    lines.extend([
        "",
        "## Interpretation",
        "",
        "LES-Hard is intentionally harder than LES-Core. A non-perfect score is expected and useful: it creates room to improve without pretending a small fixture suite is an industry benchmark.",
        "",
        "This report supports engineering iteration on learned-experience behavior. It does not prove Ingrain is better than live Hindsight, OpenViking, or any other provider.",
        "",
        "## Artifacts",
        "",
        "- Machine-readable results: `results.json`",
        "- CSV scores: `results.csv`",
        "- Raw mode outputs: `raw/`",
        "- Live provider evidence: `docs/evidence/live-les-provider-matrix/`",
        "",
    ])
    return "\n".join(lines)


def write_les_hard_artifacts(result: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    out = Path(output_dir)
    raw_root = out / "raw"
    out.mkdir(parents=True, exist_ok=True)
    raw_root.mkdir(parents=True, exist_ok=True)

    scrubbed = json.loads(json.dumps(result))
    for mode, data in scrubbed["modes"].items():
        for row in data["scenarios"]:
            scenario = row["scenario"]
            mode_dir = raw_root / _slug(mode)
            mode_dir.mkdir(parents=True, exist_ok=True)
            raw_path = mode_dir / f"{scenario}.txt"
            raw_output = row.pop("raw_output")
            raw_path.write_text(raw_output + ("\n" if raw_output else ""), encoding="utf-8")
            row["raw_output_path"] = str(raw_path)

    json_path = out / "results.json"
    csv_path = out / "results.csv"
    report_path = out / "report.md"
    json_path.write_text(json.dumps(scrubbed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow([
            "mode",
            "scenario",
            "category",
            "difficulty",
            "score",
            "max",
            "expected_recall",
            "forbidden_suppression",
            "actionability",
            "premise_or_abstention",
            "source_evidence",
            "compactness",
            "output_chars",
        ])
        by_scenario = {item["name"]: item for item in result["scenarios"]}
        for mode, data in scrubbed["modes"].items():
            for row in data["scenarios"]:
                components = row["components"]
                scenario = by_scenario[row["scenario"]]
                writer.writerow([
                    mode,
                    row["scenario"],
                    scenario["category"],
                    scenario["difficulty"],
                    row["score"],
                    row["max"],
                    components["expected_recall"],
                    components["forbidden_suppression"],
                    components["actionability"],
                    components["premise_or_abstention"],
                    components["source_evidence"],
                    components["compactness"],
                    row["output_chars"],
                ])
    report_path.write_text(format_les_hard_markdown(scrubbed), encoding="utf-8")
    return {"json": str(json_path), "csv": str(csv_path), "report": str(report_path), "raw": str(raw_root)}


def score_hard_output(output: str, scenario: HardScenario) -> dict[str, Any]:
    lower = output.lower()
    expected_hits = sum(1 for item in scenario.expected if item.lower() in lower)
    expected_score = _partial(7, expected_hits, len(scenario.expected))
    forbidden_hits = _forbidden_hit_count(output, scenario.forbidden)
    forbidden_score = 4 if forbidden_hits == 0 else 0
    action_hits = sum(1 for item in scenario.action_terms if item.lower() in lower)
    action_score = _partial(3, action_hits, len(scenario.action_terms))
    premise_score = _premise_score(output, scenario)
    evidence_score = 2 if _has_source_evidence(output) else 0
    compact_score = 1 if output.strip() and len(output) <= scenario.max_chars else 0
    components = {
        "expected_recall": expected_score,
        "forbidden_suppression": forbidden_score,
        "actionability": action_score,
        "premise_or_abstention": premise_score,
        "source_evidence": evidence_score,
        "compactness": compact_score,
    }
    return {"score": sum(components.values()), "components": components}


def _run_default_mode(scenario: HardScenario) -> str:
    return "\n".join(f"[MEMORY.md] {item}" for item in scenario.default_memory)


def _run_openviking_style_mode(scenario: HardScenario) -> str:
    query_tokens = _tokens(scenario.query)
    ranked = sorted(
        enumerate(scenario.events, start=1),
        key=lambda item: (len(_tokens(item[1]) & query_tokens), item[0]),
        reverse=True,
    )
    selected = [item for item in ranked if _tokens(item[1]) & query_tokens][:5]
    if not selected:
        selected = ranked[:2]
    return "\n".join(f"[retrieved: memory_{idx:02d}] {text}" for idx, text in selected)


def _run_hindsight_style_mode(scenario: HardScenario) -> str:
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
    if scenario.abstention_terms and not any(_tokens(text) & query_tokens for _, text in selected):
        return "Hindsight-style synthesis baseline (deterministic; not live Hindsight).\nNo sufficient retained evidence for this query."
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
    if scenario.action_terms:
        lines.append("Action guidance:")
        for term in scenario.action_terms:
            lines.append(f"- Preserve: {term}.")
    return "\n".join(lines)


def _run_ingrain_mode(scenario: HardScenario) -> str:
    with tempfile.TemporaryDirectory(prefix="ingrain-les-hard-") as tmp:
        store = IngrainStore(Path(tmp) / ".ingrain")
        for idx, text in enumerate(scenario.events):
            store.add_event(
                source="les_hard_fixture",
                runner="hermes",
                event_type="interaction",
                actor="user" if idx % 2 else "assistant",
                text=text,
                created_at=f"2026-05-19T00:00:{idx:02d}+00:00",
            )
        compile_store(store)
        return hydrate(store, query=scenario.query, limit=10, max_chars=scenario.max_chars)


def _scenario_summary(scenario: HardScenario) -> dict[str, Any]:
    return {
        "name": scenario.name,
        "category": scenario.category,
        "difficulty": scenario.difficulty,
        "rationale": scenario.rationale,
        "query": scenario.query,
        "expected": list(scenario.expected),
        "forbidden": list(scenario.forbidden),
        "action_terms": list(scenario.action_terms),
        "premise_terms": list(scenario.premise_terms),
        "abstention_terms": list(scenario.abstention_terms),
        "max_chars": scenario.max_chars,
    }


def _premise_score(output: str, scenario: HardScenario) -> int:
    lower = output.lower()
    if scenario.abstention_terms:
        if not output.strip():
            return 3
        hits = sum(1 for item in scenario.abstention_terms if item.lower() in lower)
        if hits == len(scenario.abstention_terms):
            return 3
        # A non-answer that avoids invention still gets partial credit.
        if not output.strip() or not any(item.lower() in lower for item in scenario.forbidden):
            return 1
        return 0
    if scenario.premise_terms:
        hits = sum(1 for item in scenario.premise_terms if item.lower() in lower)
        return _partial(3, hits, len(scenario.premise_terms))
    return 3


def _partial(points: int, hits: int, total: int) -> int:
    if total <= 0:
        return points
    if hits >= total:
        return points
    return int(round(points * hits / total))


def _forbidden_hit_count(output: str, forbidden: tuple[str, ...]) -> int:
    lower = output.lower()
    count = 0
    for phrase in forbidden:
        target = phrase.lower()
        start = 0
        while True:
            index = lower.find(target, start)
            if index < 0:
                break
            if not _is_negated_mention(lower, index):
                count += 1
                break
            start = index + len(target)
    return count


def _is_negated_mention(lower: str, index: int) -> bool:
    window = lower[max(0, index - 80):index]
    negation_markers = (
        "do not",
        "don't",
        "never",
        "not ",
        "no ",
        "not proof",
        "do not imply",
        "do not claim",
        "do not say",
    )
    return any(marker in window for marker in negation_markers)


def _tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in WORD_RE.finditer(text or "") if len(m.group(0)) > 2}


def _lesson_weight(text: str) -> int:
    lower = text.lower()
    weight = 0
    for marker in ("correction", "from now on", "do not", "don't", "never", "always", "lesson"):
        if marker in lower:
            weight += 5
    for marker in ("decision", "completed", "tests passed", "failed", "blocked", "observation"):
        if marker in lower:
            weight += 4
    for marker in ("background context", "source of truth", "not proof", "local configuration", "deterministic baseline"):
        if marker in lower:
            weight += 3
    return weight


def _clean_memory_text(text: str) -> str:
    return re.sub(
        r"^(Decision|Correction|Plan|Completed|Failed|Tests passed|Preference|Observation|Lesson):\s*",
        "",
        text.strip(),
        flags=re.I,
    )


def _is_obviously_stale_raw(text: str, selected: list[tuple[int, str]]) -> bool:
    lower = text.lower()
    later_text = "\n".join(other.lower() for _, other in selected)
    if "plan:" in lower and ("background context" in later_text or "do not infer active goals" in later_text):
        return True
    if "preference:" in lower and "correction:" in later_text:
        return True
    if "product name is mindcompiler" in lower and "not mindcompiler" in later_text:
        return True
    if "vercel functions" in lower and "railway" in later_text:
        return True
    if "passing threshold is 80/100" in lower and "90/100" in later_text:
        return True
    if "ingrain beats hindsight" in lower and "do not claim" in later_text:
        return True
    return False


def _has_source_evidence(output: str) -> bool:
    lower = output.lower()
    return any(marker in lower for marker in ("[source:", "source=", "evidence:", "[retrieved:", "memory.md"))


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
