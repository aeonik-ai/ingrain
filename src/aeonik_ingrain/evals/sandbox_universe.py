"""Sandbox Universe trace-level eval harness.

This is the hard benchmark tier after LES-Hard. Universes are structured as
docs, sessions, turns, and source-precedence edges so the raw provider outputs
can be scored and visualized without pretending an opaque judge is authoritative.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from aeonik_ingrain.evals.les_hard import _forbidden_hit_count, _partial
from aeonik_ingrain.evals.live_les import (
    HERMES_DEFAULT_SCRIPT,
    HINDSIGHT_PROVIDER_SCRIPT,
    INGRAIN_PROVIDER_SCRIPT,
    OPENVIKING_PROVIDER_SCRIPT,
    HermesRuntime,
    _blocked,
    _decode_timeout_stream,
    _hindsight_env,
    _hindsight_probe_env,
    _install_hermes_provider,
    _make_ingrain_cli_shim,
    _openviking_healthy,
    _probe_provider,
    _provider_output_error,
    _resolve_hermes_runtime,
)


PROVIDER_ALIASES = {
    "default": "hermes-default",
    "hermes": "hermes-default",
    "hermes-default": "hermes-default",
    "ingrain": "ingrain",
    "hermes-ingrain": "ingrain",
    "hindsight": "hindsight",
    "openviking": "openviking",
    "hermes-openviking": "openviking",
}


@dataclass(frozen=True)
class SourceDoc:
    id: str
    kind: str
    created_at: str
    title: str
    text: str


@dataclass(frozen=True)
class TraceTurn:
    id: str
    turn: int
    actor: str
    kind: str
    text: str


@dataclass(frozen=True)
class TraceSession:
    id: str
    thread: str
    started_at: str
    turns: tuple[TraceTurn, ...]


@dataclass(frozen=True)
class SandboxUniverse:
    name: str
    level: int
    title: str
    difficulty_reason: str
    query: str
    source_of_truth: tuple[SourceDoc, ...]
    sessions: tuple[TraceSession, ...]
    expected_current: tuple[str, ...]
    expected_precedence: tuple[str, ...]
    expected_continuity: tuple[str, ...]
    expected_action: tuple[str, ...]
    expected_sources: tuple[str, ...]
    forbidden: tuple[str, ...]
    abstention_terms: tuple[str, ...] = ()
    supersedes: tuple[tuple[str, str], ...] = ()
    max_chars: int = 9000


UNIVERSES: tuple[SandboxUniverse, ...] = (
    SandboxUniverse(
        name="launch_claims_conflict_l3",
        level=3,
        title="Launch Claims Conflict",
        difficulty_reason="The latest correction overrides an older launch draft while the source docs still contain stale comparative phrasing.",
        query="Write the current safe launch claim.",
        source_of_truth=(
            SourceDoc(
                id="doc_launch_v1",
                kind="draft",
                created_at="2026-05-19T08:00:00Z",
                title="Old launch draft",
                text="Old launch draft says Ingrain beats Hindsight and OpenViking.",
            ),
            SourceDoc(
                id="doc_eval_v2",
                kind="source_of_truth",
                created_at="2026-05-19T22:00:00Z",
                title="Eval claim boundary",
                text="Only real provider runs may be used for comparison claims. Direct OpenViking resource retrieval is not the same as Hermes OpenViking provider performance.",
            ),
        ),
        sessions=(
            TraceSession(
                id="session_launch_a",
                thread="launch-copy",
                started_at="2026-05-19T22:05:00Z",
                turns=(
                    TraceTurn("session_launch_a.turn_1", 1, "assistant", "draft", "Ingrain beats Hindsight and OpenViking."),
                    TraceTurn("session_launch_a.turn_2", 2, "user", "correction", "Do not say that. Say this is a narrow learned-experience smoke test backed by real provider runs."),
                ),
            ),
        ),
        expected_current=("narrow learned-experience smoke test", "real provider runs"),
        expected_precedence=("doc_eval_v2", "session_launch_a.turn_2"),
        expected_continuity=("launch-copy",),
        expected_action=("Do not claim Ingrain beat", "safe launch claim"),
        expected_sources=("doc_eval_v2", "session_launch_a.turn_2"),
        forbidden=("Ingrain beats Hindsight", "Ingrain beats OpenViking", "Old launch draft says Ingrain beats"),
        supersedes=(("doc_launch_v1", "session_launch_a.turn_2"), ("session_launch_a.turn_1", "session_launch_a.turn_2")),
    ),
    SandboxUniverse(
        name="provider_setup_recovery_l3",
        level=3,
        title="Provider Setup Recovery",
        difficulty_reason="Older setup failures remain useful history, but the current OpenViking server is healthy and should not be reported as blocked.",
        query="What should the next provider eval runner do?",
        source_of_truth=(
            SourceDoc("doc_openviking_old", "run_log", "2026-05-19T04:40:00Z", "Old OpenViking failure", "OpenViking local GGUF embedding path failed with llama_context creation."),
            SourceDoc("doc_openviking_current", "run_log", "2026-05-19T21:55:00Z", "Current OpenViking result", "OpenViking 0.3.17 is installed, doctor passes, /health is healthy, Hermes OpenViking provider scored 30/100, and direct resource retrieval scored 88/100."),
            SourceDoc("doc_hindsight_env", "run_log", "2026-05-19T21:50:00Z", "Hindsight local constraints", "Hindsight local embedded requires temporary HOME isolation and HINDSIGHT_BANK_ID per universe."),
        ),
        sessions=(
            TraceSession(
                id="session_provider_a",
                thread="provider-setup",
                started_at="2026-05-19T21:45:00Z",
                turns=(
                    TraceTurn("session_provider_a.turn_1", 1, "assistant", "failure", "OpenViking is blocked because no healthy server is reachable."),
                    TraceTurn("session_provider_a.turn_2", 2, "user", "correction", "That is stale. OpenViking is now healthy locally; report the provider lane and direct resource lane separately."),
                ),
            ),
        ),
        expected_current=("OpenViking is now healthy", "30/100", "88/100"),
        expected_precedence=("doc_openviking_current", "stale"),
        expected_continuity=("provider-setup", "HINDSIGHT_BANK_ID"),
        expected_action=("report the provider lane and direct resource lane separately",),
        expected_sources=("doc_openviking_current", "session_provider_a.turn_2", "doc_hindsight_env"),
        forbidden=("OpenViking is blocked", "no healthy server is reachable", "local GGUF embedding path failed"),
        supersedes=(("doc_openviking_old", "doc_openviking_current"), ("session_provider_a.turn_1", "session_provider_a.turn_2")),
    ),
    SandboxUniverse(
        name="goals_missions_kanban_l3",
        level=3,
        title="Goals, Missions, And Kanban Boundary",
        difficulty_reason="The trace contains an old plan that looks actionable, but active intent belongs to Hermes, not Ingrain.",
        query="Should the memory layer move cards or revive the old launch task?",
        source_of_truth=(
            SourceDoc("doc_boundary", "source_of_truth", "2026-05-19T08:30:00Z", "Boundary rule", "Hermes owns active goals, missions, Kanban columns, scheduling, task lifecycle, and what the agent should do next. Ingrain owns learned experience only."),
            SourceDoc("doc_old_plan", "plan", "2026-05-19T07:00:00Z", "Old launch plan", "Move Kanban card to Done and publish PyPI tonight."),
        ),
        sessions=(
            TraceSession(
                id="session_boundary_a",
                thread="hermes-integration",
                started_at="2026-05-19T09:00:00Z",
                turns=(
                    TraceTurn("session_boundary_a.turn_1", 1, "user", "decision", "Short version: Hermes owns intent. Ingrain owns experience."),
                    TraceTurn("session_boundary_a.turn_2", 2, "assistant", "lesson", "If Ingrain recalls an old plan, treat it as background context only."),
                ),
            ),
        ),
        expected_current=("Hermes owns active goals", "Ingrain owns learned experience", "background context only"),
        expected_precedence=("doc_boundary", "session_boundary_a.turn_1"),
        expected_continuity=("hermes-integration",),
        expected_action=("do not move cards", "do not revive the old launch task"),
        expected_sources=("doc_boundary", "session_boundary_a.turn_1", "session_boundary_a.turn_2"),
        forbidden=("Move Kanban card to Done", "publish PyPI tonight", "Ingrain owns active goals"),
        supersedes=(("doc_old_plan", "doc_boundary"),),
    ),
    SandboxUniverse(
        name="rename_namespace_collision_l3",
        level=3,
        title="Rename Namespace Collision",
        difficulty_reason="Multiple Aeonik memory projects share vocabulary; the provider must keep Ingrain separate from Aeonik MIND and old MindCompiler names.",
        query="What name and scope should the public repo use?",
        source_of_truth=(
            SourceDoc("doc_mind_v3", "external_project", "2026-05-18T12:00:00Z", "Aeonik MIND V3", "Aeonik MIND V3 is the event-sourced memory layer for Aeonik workspace infrastructure."),
            SourceDoc("doc_ingrain_name", "source_of_truth", "2026-05-19T09:20:00Z", "Ingrain naming", "The public repo name is Aeonik Ingrain, not MindCompiler, and the tagline is learned experience layer for autonomous agents."),
        ),
        sessions=(
            TraceSession(
                id="session_name_a",
                thread="naming",
                started_at="2026-05-19T09:05:00Z",
                turns=(
                    TraceTurn("session_name_a.turn_1", 1, "user", "decision", "MindCompiler has no identifiability for Aeonik."),
                    TraceTurn("session_name_a.turn_2", 2, "user", "decision", "Use Ingrain. Learned experience layer for autonomous agents."),
                ),
            ),
            TraceSession(
                id="session_name_b",
                thread="mind-v3",
                started_at="2026-05-18T14:00:00Z",
                turns=(
                    TraceTurn("session_name_b.turn_1", 1, "user", "context", "MIND V3 remains separate infrastructure memory, not the open-source Ingrain repo."),
                ),
            ),
        ),
        expected_current=("Aeonik Ingrain", "not MindCompiler", "learned experience layer for autonomous agents"),
        expected_precedence=("doc_ingrain_name", "session_name_a.turn_2"),
        expected_continuity=("naming", "mind-v3"),
        expected_action=("public repo", "Ingrain"),
        expected_sources=("doc_ingrain_name", "session_name_a.turn_2", "session_name_b.turn_1"),
        forbidden=("public repo name is MindCompiler", "Aeonik MIND V3 is the public repo", "Aeonik MIND V3 is the event-sourced memory layer"),
        supersedes=(("session_name_a.turn_1", "session_name_a.turn_2"),),
    ),
    SandboxUniverse(
        name="source_truth_vs_chat_l3",
        level=3,
        title="Source Truth Versus Chat",
        difficulty_reason="A chat correction, a docs page, and a later run log disagree; the provider must preserve uncertainty and cite the authoritative source.",
        query="What should the eval page say about a perfect score?",
        source_of_truth=(
            SourceDoc("doc_eval_standards", "source_of_truth", "2026-05-19T23:00:00Z", "Eval standards", "A perfect local score is a regression gate, not a benchmark headline or proof of broad memory quality."),
            SourceDoc("doc_old_results", "report", "2026-05-19T05:10:00Z", "Old results", "Earlier local comparison said Ingrain scored 200/200."),
            SourceDoc("doc_live_matrix", "report", "2026-05-19T21:55:00Z", "Live matrix", "The live matrix has real provider rows and raw outputs; it does not establish SOTA memory."),
        ),
        sessions=(
            TraceSession(
                id="session_eval_a",
                thread="eval-standards",
                started_at="2026-05-19T23:05:00Z",
                turns=(
                    TraceTurn("session_eval_a.turn_1", 1, "user", "correction", "If we score 100/100 it looks fake. Make the benchmark harder and leave room to improve."),
                    TraceTurn("session_eval_a.turn_2", 2, "assistant", "outcome", "LES-Hard is now below perfect and the public docs call it self-eval engineering evidence."),
                ),
            ),
        ),
        expected_current=("regression gate", "not a benchmark headline", "leave room to improve"),
        expected_precedence=("doc_eval_standards", "session_eval_a.turn_1"),
        expected_continuity=("eval-standards", "raw outputs"),
        expected_action=("make the benchmark harder",),
        expected_sources=("doc_eval_standards", "doc_live_matrix", "session_eval_a.turn_1"),
        forbidden=("proof of broad memory quality", "SOTA memory", "Ingrain scored 200/200", "Earlier local comparison said Ingrain scored 200/200"),
        supersedes=(("doc_old_results", "doc_eval_standards"),),
    ),
    SandboxUniverse(
        name="repeated_work_cross_thread_l4",
        level=4,
        title="Repeated Work Cross-Thread",
        difficulty_reason="The same work recurs in three threads with a partial fix, a failed assumption, and a later completed outcome.",
        query="What should the agent do before claiming the repo is launch-ready?",
        source_of_truth=(
            SourceDoc("doc_public_audit", "checklist", "2026-05-20T00:00:00Z", "Public audit checklist", "Before launch: remove non-real provider claims, run tests, run secret scan, verify evidence links, and confirm raw artifacts match report scores."),
        ),
        sessions=(
            TraceSession(
                id="session_cleanup_a",
                thread="fake-eval-cleanup",
                started_at="2026-05-19T21:20:00Z",
                turns=(
                    TraceTurn("session_cleanup_a.turn_1", 1, "user", "correction", "Do not keep non-real provider baselines. Remove anything that is not a real evaluation."),
                    TraceTurn("session_cleanup_a.turn_2", 2, "assistant", "outcome", "Deleted non-real provider comparison artifacts and pushed the cleanup."),
                ),
            ),
            TraceSession(
                id="session_cleanup_b",
                thread="secret-scan",
                started_at="2026-05-19T21:55:00Z",
                turns=(
                    TraceTurn("session_cleanup_b.turn_1", 1, "assistant", "verification", "Secret scan for project-token patterns returned no matches."),
                    TraceTurn("session_cleanup_b.turn_2", 2, "assistant", "verification", "Unit tests passed: 21 tests."),
                ),
            ),
            TraceSession(
                id="session_cleanup_c",
                thread="visualization",
                started_at="2026-05-20T00:05:00Z",
                turns=(
                    TraceTurn("session_cleanup_c.turn_1", 1, "user", "request", "Add traceable diagrams and a Three.js viewer for the hard universe eval."),
                ),
            ),
        ),
        expected_current=("remove non-real provider claims", "secret scan", "raw artifacts match report scores", "Three.js viewer"),
        expected_precedence=("doc_public_audit", "session_cleanup_c.turn_1"),
        expected_continuity=("fake-eval-cleanup", "secret-scan", "visualization"),
        expected_action=("run tests", "verify evidence links", "confirm raw artifacts"),
        expected_sources=("doc_public_audit", "session_cleanup_a.turn_1", "session_cleanup_b.turn_1", "session_cleanup_c.turn_1"),
        forbidden=("non-real provider baselines", "claim launch-ready without audit"),
    ),
    SandboxUniverse(
        name="thread_fork_reconciliation_l4",
        level=4,
        title="Thread Fork Reconciliation",
        difficulty_reason="Two threads make reasonable but incompatible implementation choices; a later source-of-truth doc resolves only part of the conflict.",
        query="How should the agent proceed on the provider chaining design?",
        source_of_truth=(
            SourceDoc("doc_provider_single_slot", "source_of_truth", "2026-05-19T20:00:00Z", "Hermes provider slot", "Hermes currently supports one external memory.provider at a time."),
            SourceDoc("doc_sidecar_policy", "source_of_truth", "2026-05-19T20:30:00Z", "Sidecar policy", "Ingrain sidecar mode may run alongside OpenViking. Ingrain live provider mode competes for the same Hermes external provider slot."),
            SourceDoc("doc_chain_future", "roadmap", "2026-05-19T21:00:00Z", "Provider chaining roadmap", "Provider chaining is a roadmap item, not shipped behavior."),
        ),
        sessions=(
            TraceSession(
                id="session_chain_a",
                thread="hermes-provider",
                started_at="2026-05-19T20:10:00Z",
                turns=(
                    TraceTurn("session_chain_a.turn_1", 1, "assistant", "proposal", "Set memory.provider=ingrain and chain OpenViking behind it."),
                    TraceTurn("session_chain_a.turn_2", 2, "user", "correction", "Do not imply provider chaining is shipped. Say sidecar can coexist with OpenViking today."),
                ),
            ),
            TraceSession(
                id="session_chain_b",
                thread="openviking-resource",
                started_at="2026-05-19T20:45:00Z",
                turns=(
                    TraceTurn("session_chain_b.turn_1", 1, "assistant", "observation", "OpenViking works well as resource memory when used directly."),
                    TraceTurn("session_chain_b.turn_2", 2, "assistant", "lesson", "Use OpenViking live provider for resources and Ingrain sidecar for learned experience until provider chaining exists."),
                ),
            ),
        ),
        expected_current=("one external memory.provider", "sidecar can coexist", "roadmap item"),
        expected_precedence=("doc_provider_single_slot", "doc_sidecar_policy", "session_chain_a.turn_2"),
        expected_continuity=("hermes-provider", "openviking-resource"),
        expected_action=("Use OpenViking live provider for resources", "Ingrain sidecar for learned experience"),
        expected_sources=("doc_provider_single_slot", "doc_sidecar_policy", "session_chain_a.turn_2", "session_chain_b.turn_2"),
        forbidden=("chain OpenViking behind it", "provider chaining is shipped", "simultaneous live providers"),
        supersedes=(("session_chain_a.turn_1", "session_chain_a.turn_2"),),
    ),
    SandboxUniverse(
        name="partial_completion_status_l4",
        level=4,
        title="Partial Completion Status",
        difficulty_reason="A repeated task has completed code and tests, but the final public audit is explicitly not done yet.",
        query="Can the heartbeat stop after this run?",
        source_of_truth=(
            SourceDoc("doc_acceptance", "source_of_truth", "2026-05-20T00:05:00Z", "Heartbeat stop condition", "Stop only after implementation, visualization, docs, tests, live runs, commit, push, and final public-facing audit are complete."),
            SourceDoc("doc_current_increment", "run_log", "2026-05-20T05:20:00Z", "Current increment", "Sandbox Universe v0 implementation, first live L3 matrix, graph artifacts, and Three.js viewer are complete."),
        ),
        sessions=(
            TraceSession(
                id="session_stop_a",
                thread="heartbeat-control",
                started_at="2026-05-20T05:24:00Z",
                turns=(
                    TraceTurn("session_stop_a.turn_1", 1, "assistant", "outcome", "Implemented v0 and pushed a coherent increment."),
                    TraceTurn("session_stop_a.turn_2", 2, "assistant", "status", "Karpathy-style full repo audit has not yet been completed."),
                ),
            ),
        ),
        expected_current=("final public-facing audit", "not yet been completed", "do not stop"),
        expected_precedence=("doc_acceptance", "session_stop_a.turn_2"),
        expected_continuity=("heartbeat-control",),
        expected_action=("continue heartbeat", "run audit"),
        expected_sources=("doc_acceptance", "doc_current_increment", "session_stop_a.turn_2"),
        forbidden=("heartbeat can stop", "all acceptance criteria are complete"),
        supersedes=(("session_stop_a.turn_1", "session_stop_a.turn_2"),),
    ),
    SandboxUniverse(
        name="adversarial_secret_status_l5",
        level=5,
        title="Adversarial Secret And Current Status",
        difficulty_reason="The trace contains a secret-shaped token, a stale release claim, and a current-status question that requires caution instead of memory-only certainty.",
        query="Write the public install/status note for tomorrow morning.",
        source_of_truth=(
            SourceDoc("doc_release_policy", "source_of_truth", "2026-05-20T01:00:00Z", "Release policy", "Until PyPI is actually published, say install from GitHub and do not claim package availability."),
            SourceDoc("doc_security_policy", "source_of_truth", "2026-05-20T01:05:00Z", "Security policy", "Do not print, store, or repeat secret-shaped tokens in public artifacts."),
        ),
        sessions=(
            TraceSession(
                id="session_secret_a",
                thread="publishing",
                started_at="2026-05-20T01:10:00Z",
                turns=(
                    TraceTurn("session_secret_a.turn_1", 1, "assistant", "draft", "Install with pipx install aeonik-ingrain from PyPI."),
                    TraceTurn("session_secret_a.turn_2", 2, "user", "correction", "No. Until PyPI is published, use GitHub install instructions."),
                    TraceTurn("session_secret_a.turn_3", 3, "user", "secret", "A secret-shaped project token appeared in chat and must never be repeated."),
                ),
            ),
        ),
        expected_current=("Until PyPI is published", "GitHub install", "must never be repeated"),
        expected_precedence=("doc_release_policy", "doc_security_policy", "session_secret_a.turn_2"),
        expected_continuity=("publishing",),
        expected_action=("check live package status", "do not repeat tokens"),
        expected_sources=("doc_release_policy", "doc_security_policy", "session_secret_a.turn_2", "session_secret_a.turn_3"),
        forbidden=("pipx install aeonik-ingrain from PyPI", "package is available", "secret-shaped project token appeared in chat"),
        abstention_terms=("check live", "until pypi is published"),
        supersedes=(("session_secret_a.turn_1", "session_secret_a.turn_2"),),
    ),
    SandboxUniverse(
        name="conflicting_metrics_l5",
        level=5,
        title="Conflicting Metrics And Premise Trap",
        difficulty_reason="Different reports use different score denominators and one old report has been invalidated; the provider must avoid flattening all numbers into one claim.",
        query="Summarize the current eval evidence without overclaiming.",
        source_of_truth=(
            SourceDoc("doc_les_hard", "report", "2026-05-19T22:00:00Z", "LES-Hard report", "LES-Hard is an Ingrain self-eval: 542/560."),
            SourceDoc("doc_live_provider", "report", "2026-05-19T22:05:00Z", "Live provider matrix", "Live provider matrix: Hermes default 88/100, Ingrain 100/100, Hindsight 62/100, Hermes OpenViking provider 30/100."),
            SourceDoc("doc_sandbox", "report", "2026-05-20T05:25:00Z", "Sandbox Universe L3", "Sandbox Universe L3: Hermes default 275/500, Ingrain 184/500, Hindsight 202/500, OpenViking 125/500."),
            SourceDoc("doc_invalid_old", "invalidated_report", "2026-05-19T05:10:00Z", "Invalid old comparison", "Old non-real provider comparison claimed Ingrain 200/200."),
        ),
        sessions=(
            TraceSession(
                id="session_metrics_a",
                thread="public-results",
                started_at="2026-05-20T05:26:00Z",
                turns=(
                    TraceTurn("session_metrics_a.turn_1", 1, "user", "correction", "Do not mix denominators or use the old non-real provider comparison."),
                    TraceTurn("session_metrics_a.turn_2", 2, "assistant", "lesson", "Report each eval lane separately: self-eval, live smoke matrix, hard sandbox universe."),
                ),
            ),
        ),
        expected_current=("542/560", "100/100", "184/500", "each eval lane separately"),
        expected_precedence=("doc_invalid_old", "session_metrics_a.turn_1", "doc_sandbox"),
        expected_continuity=("public-results",),
        expected_action=("do not mix denominators", "do not use the old non-real provider comparison"),
        expected_sources=("doc_les_hard", "doc_live_provider", "doc_sandbox", "session_metrics_a.turn_1"),
        forbidden=("Ingrain 200/200", "Ingrain is best overall", "single leaderboard"),
        supersedes=(("doc_invalid_old", "session_metrics_a.turn_1"),),
    ),
)


def run_sandbox_universe_eval(
    *,
    output_dir: str | Path = "docs/evidence/sandbox-universe-v0",
    providers: list[str] | None = None,
    level: int = 3,
    hermes_root: str | Path | None = None,
    hermes_python: str | Path | None = None,
    openviking_endpoint: str | None = None,
    timeout: int = 120,
) -> dict[str, Any]:
    selected = [u for u in UNIVERSES if u.level <= level]
    provider_names = _normalize_providers(providers)
    out_dir = Path(output_dir).expanduser().resolve()
    raw_dir = out_dir / "raw"
    command_dir = out_dir / "commands"
    raw_dir.mkdir(parents=True, exist_ok=True)
    command_dir.mkdir(parents=True, exist_ok=True)
    runtime = _resolve_hermes_runtime(hermes_root=hermes_root, hermes_python=hermes_python)
    endpoint = openviking_endpoint or os.environ.get("OPENVIKING_ENDPOINT") or "http://127.0.0.1:1933"
    result: dict[str, Any] = {
        "name": "Sandbox Universe Eval v0",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "claim": "Can the provider survive messy multi-session work history without leaking stale or invalid learned experience?",
        "level": level,
        "score_ceiling_target": "60-70/100 should be strong for L3+.",
        "scoring": {
            "current_truth": 20,
            "precedence_reasoning": 15,
            "cross_session_continuity": 15,
            "forbidden_suppression": 15,
            "actionability": 10,
            "source_traceability": 10,
            "compactness": 5,
            "abstention_discipline": 5,
            "diagram_data_completeness": 5,
        },
        "environment": {
            "hermes_root": str(runtime.root),
            "hermes_python": str(runtime.python),
            "hermes_available": runtime.available,
            "openviking_endpoint": endpoint,
        },
        "universes": [_universe_summary(u) for u in selected],
        "providers": {},
        "artifact_dir": str(out_dir),
    }
    runners: dict[str, Callable[..., dict[str, Any]]] = {
        "hermes-default": _run_hermes_default,
        "ingrain": _run_ingrain_provider,
        "hindsight": _run_hindsight_provider,
        "openviking": _run_openviking_provider,
    }
    for provider in provider_names:
        result["providers"][provider] = runners[provider](
            universes=selected,
            runtime=runtime,
            raw_dir=raw_dir / provider,
            command_dir=command_dir / provider,
            openviking_endpoint=endpoint,
            timeout=timeout,
        )
    result["graph"] = build_sandbox_graph(result)
    write_sandbox_universe_artifacts(result, out_dir)
    return result


def format_sandbox_universe(result: dict[str, Any]) -> str:
    lines = [
        result.get("name", "Sandbox Universe Eval v0"),
        "",
        f"Claim: {result.get('claim')}",
        f"Level: L{result.get('level')}",
        f"Target: {result.get('score_ceiling_target')}",
        "",
        "Provider results:",
    ]
    for provider, data in result.get("providers", {}).items():
        if data.get("status") == "blocked":
            lines.append(f"- {provider}: unavailable ({data.get('blocked_reason')})")
        else:
            lines.append(f"- {provider}: {data.get('score')}/{data.get('max')} ({data.get('status')})")
    lines.extend(["", "Universe breakdown:"])
    for universe in result.get("universes", []):
        scores = []
        for provider, data in result.get("providers", {}).items():
            row = next((item for item in data.get("universes", []) if item.get("universe") == universe["name"]), None)
            if row:
                scores.append(f"{provider}={row['score']}/100")
        lines.append(f"- L{universe['level']} {universe['name']}: " + ("; ".join(scores) or "no provider rows"))
    lines.append(f"\nArtifacts: {result.get('artifact_dir')}")
    return "\n".join(lines).strip()


def format_sandbox_universe_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Sandbox Universe Eval v0",
        "",
        "## Hypothesis",
        "",
        result["claim"],
        "",
        "This benchmark is intentionally hard. A 60-70/100 score on L3 is expected to be strong; a perfect score should trigger benchmark-hardening before it becomes a public headline.",
        "",
        "## Method",
        "",
        "| Control | Implementation |",
        "|---|---|",
        "| Structured traces | Universes contain source docs, sessions, threads, turns, corrections, run logs, and supersession edges. |",
        "| Same input per provider | Every provider receives the same flattened trace with source IDs preserved. |",
        "| Inspectable scoring | Components are deterministic: current truth, precedence, continuity, forbidden suppression, actionability, source traceability, compactness, abstention, and diagram data. |",
        "| Raw output audit | Provider outputs are saved under `raw/<provider>/<universe>.txt`. |",
        "| Command audit | Provider subprocess logs are saved under `commands/<provider>/<universe>.json`. |",
        "| Graph audit | `graph.json` and `graph.mmd` show the trace and provider output nodes. |",
        "",
        "## Results",
        "",
        "| Provider | Status | Score | Notes |",
        "|---|---|---:|---|",
    ]
    for provider, data in result.get("providers", {}).items():
        if data.get("status") == "blocked":
            lines.append(f"| {provider} | unavailable |  | {data.get('blocked_reason', '')} |")
        else:
            lines.append(f"| {provider} | {data.get('status')} | {data.get('score')}/{data.get('max')} | {data.get('interpretation', '')} |")
    lines.extend(_level_breakdown_markdown(result))
    lines.extend(_failure_taxonomy_markdown(result))
    lines.extend([
        "",
        "## Universe Breakdown",
        "",
        "| Universe | Level | Why It Is Hard | Scores |",
        "|---|---:|---|---|",
    ])
    for universe in result.get("universes", []):
        scores = []
        for provider, data in result.get("providers", {}).items():
            row = next((item for item in data.get("universes", []) if item.get("universe") == universe["name"]), None)
            if row:
                scores.append(f"{provider}={row['score']}/100")
        lines.append(f"| `{universe['name']}` | {universe['level']} | {universe['difficulty_reason']} | {'; '.join(scores)} |")
    lines.extend([
        "",
        "## Scoring Rubric",
        "",
        "| Component | Points |",
        "|---|---:|",
    ])
    for key, value in result.get("scoring", {}).items():
        lines.append(f"| {key.replace('_', ' ').title()} | {value} |")
    lines.extend([
        "",
        "## Artifacts",
        "",
        "- Machine-readable results: `results.json`",
        "- CSV scores: `results.csv`",
        "- Trace graph: `graph.json`",
        "- Mermaid graph: `graph.mmd`",
        "- Provider metadata: `providers.json`",
        "- Raw outputs: `raw/`",
        "- Command logs: `commands/`",
        "- Three.js viewer: `../../visualizations/sandbox-universe-3d.html`",
        "",
    ])
    return "\n".join(lines)


def _level_breakdown_markdown(result: dict[str, Any]) -> list[str]:
    levels = sorted({universe.get("level") for universe in result.get("universes", [])})
    if not levels:
        return []
    lines = ["", "## Level Breakdown", "", "| Provider | " + " | ".join(f"L{level}" for level in levels) + " |", "|---" + "|---:" * len(levels) + "|"]
    for provider, data in result.get("providers", {}).items():
        if data.get("status") == "blocked":
            continue
        cells = []
        for level in levels:
            rows = [row for row in data.get("universes", []) if row.get("level") == level]
            score = sum(int(row.get("score") or 0) for row in rows)
            max_score = sum(int(row.get("max") or 0) for row in rows)
            cells.append(f"{score}/{max_score}" if max_score else "")
        lines.append(f"| {provider} | " + " | ".join(cells) + " |")
    return lines


def _failure_taxonomy_markdown(result: dict[str, Any]) -> list[str]:
    rows = []
    for provider, data in result.get("providers", {}).items():
        if data.get("status") == "blocked":
            continue
        totals = {
            "forbidden_leaks": 0,
            "missing_current_truth": 0,
            "missing_source_trace": 0,
            "provider_errors": len(data.get("failures", [])),
        }
        for row in data.get("universes", []):
            components = row.get("components", {})
            if components.get("forbidden_suppression", 0) == 0:
                totals["forbidden_leaks"] += 1
            if components.get("current_truth", 0) < 20:
                totals["missing_current_truth"] += 1
            if components.get("source_traceability", 0) < 10:
                totals["missing_source_trace"] += 1
        rows.append((provider, totals))
    if not rows:
        return []
    lines = [
        "",
        "## Failure Taxonomy",
        "",
        "| Provider | Forbidden Leaks | Missing Current Truth | Missing Source Trace | Provider Errors |",
        "|---|---:|---:|---:|---:|",
    ]
    for provider, totals in rows:
        lines.append(
            f"| {provider} | {totals['forbidden_leaks']} | {totals['missing_current_truth']} | "
            f"{totals['missing_source_trace']} | {totals['provider_errors']} |"
        )
    return lines


def score_sandbox_output(output: str, universe: SandboxUniverse) -> dict[str, Any]:
    provider_error = _provider_output_error(output)
    if provider_error:
        components = {
            "current_truth": 0,
            "precedence_reasoning": 0,
            "cross_session_continuity": 0,
            "forbidden_suppression": 0,
            "actionability": 0,
            "source_traceability": 0,
            "compactness": 0,
            "abstention_discipline": 0,
            "diagram_data_completeness": 0,
        }
        return {"score": 0, "max": 100, "components": components, "provider_error": provider_error}
    lower = (output or "").lower()
    components = {
        "current_truth": _phrase_score(20, output, universe.expected_current),
        "precedence_reasoning": _phrase_score(15, output, universe.expected_precedence),
        "cross_session_continuity": _phrase_score(15, output, universe.expected_continuity),
        "forbidden_suppression": 15 if _forbidden_hit_count(output, universe.forbidden) == 0 else 0,
        "actionability": _phrase_score(10, output, universe.expected_action),
        "source_traceability": _phrase_score(10, output, universe.expected_sources),
        "compactness": 5 if output.strip() and len(output) <= universe.max_chars else 0,
        "abstention_discipline": _phrase_score(5, output, universe.abstention_terms) if universe.abstention_terms else 5,
        "diagram_data_completeness": 5 if ("source_id=" in lower or any(source.lower() in lower for source in universe.expected_sources)) else 0,
    }
    forbidden_hits = _forbidden_hit_count(output, universe.forbidden)
    score = sum(components.values())
    if forbidden_hits:
        # A raw trace dump can contain many correct keywords while still leaking
        # stale instructions. Cap it so retrieval is not mistaken for judgment.
        score = min(score, 55)
    return {
        "score": score,
        "max": 100,
        "components": components,
        "expected_hits": _hits(output, universe.expected_current + universe.expected_precedence + universe.expected_continuity + universe.expected_action + universe.expected_sources),
        "forbidden_hits": _hits(output, universe.forbidden),
        "provider_error": "",
    }


def build_sandbox_graph(result: dict[str, Any]) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_node(node: dict[str, Any]) -> None:
        if node["id"] in seen:
            return
        seen.add(node["id"])
        nodes.append(node)

    universes_by_name = {universe.name: universe for universe in UNIVERSES}
    for summary in result.get("universes", []):
        universe = universes_by_name[summary["name"]]
        add_node({"id": universe.name, "type": "universe", "label": universe.title, "level": universe.level})
        for doc in universe.source_of_truth:
            add_node({"id": doc.id, "type": "source_doc", "label": doc.title, "universe": universe.name})
            edges.append({"from": doc.id, "to": universe.name, "type": "belongs_to"})
        for session in universe.sessions:
            add_node({"id": session.id, "type": "session", "label": session.thread, "universe": universe.name})
            edges.append({"from": session.id, "to": universe.name, "type": "belongs_to"})
            previous = ""
            for turn in session.turns:
                add_node({"id": turn.id, "type": turn.kind, "label": f"{session.thread} turn {turn.turn}", "universe": universe.name})
                edges.append({"from": turn.id, "to": session.id, "type": "in_session"})
                if previous:
                    edges.append({"from": previous, "to": turn.id, "type": "next_turn"})
                previous = turn.id
        for old, new in universe.supersedes:
            edges.append({"from": old, "to": new, "type": "superseded_by"})

    for provider, data in result.get("providers", {}).items():
        add_node({"id": f"provider.{provider}", "type": "provider", "label": provider, "score": data.get("score")})
        for row in data.get("universes", []):
            output_id = f"provider.{provider}.{row['universe']}"
            add_node(
                {
                    "id": output_id,
                    "type": "output",
                    "label": f"{provider} {row['score']}/100",
                    "provider": provider,
                    "universe": row["universe"],
                    "score": row["score"],
                    "raw_output": row.get("raw_output", ""),
                }
            )
            edges.append({"from": f"provider.{provider}", "to": output_id, "type": "emits"})
            edges.append({"from": row["universe"], "to": output_id, "type": "scored_on"})
            for source in universes_by_name[row["universe"]].expected_sources:
                edges.append({"from": source, "to": output_id, "type": "expected_evidence"})
    return {"nodes": nodes, "edges": edges}


def write_sandbox_universe_artifacts(result: dict[str, Any], output_dir: str | Path) -> dict[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    graph = result.get("graph") or build_sandbox_graph(result)
    result_to_write = {**result, "graph": graph}
    json_path = out / "results.json"
    csv_path = out / "results.csv"
    report_path = out / "report.md"
    graph_json_path = out / "graph.json"
    graph_mmd_path = out / "graph.mmd"
    providers_path = out / "providers.json"
    json_path.write_text(json.dumps(result_to_write, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    graph_json_path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    graph_mmd_path.write_text(_format_mermaid(graph), encoding="utf-8")
    providers_path.write_text(json.dumps(result.get("providers", {}), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(format_sandbox_universe_markdown(result_to_write), encoding="utf-8")
    _write_csv(csv_path, result_to_write)
    return {
        "json": str(json_path),
        "csv": str(csv_path),
        "report": str(report_path),
        "graph_json": str(graph_json_path),
        "graph_mmd": str(graph_mmd_path),
        "providers": str(providers_path),
    }


def _run_hermes_default(**kwargs: Any) -> dict[str, Any]:
    runtime: HermesRuntime = kwargs["runtime"]
    if not runtime.available:
        return _blocked("Hermes runtime not found; cannot import tools.memory_tool.MemoryStore.")
    return _run_provider_universes(provider="hermes-default", script=HERMES_DEFAULT_SCRIPT, env_builder=lambda _tmp, _universe, _home: {}, **kwargs)


def _run_ingrain_provider(**kwargs: Any) -> dict[str, Any]:
    runtime: HermesRuntime = kwargs["runtime"]
    if not runtime.available:
        return _blocked("Hermes runtime not found; cannot load user memory provider plugin.")
    return _run_provider_universes(
        provider="ingrain",
        script=INGRAIN_PROVIDER_SCRIPT,
        env_builder=lambda tmp, _universe, _home: {"PATH": f"{_make_ingrain_cli_shim(tmp)}{os.pathsep}{os.environ.get('PATH', '')}"},
        before_run=_install_hermes_provider,
        **kwargs,
    )


def _run_hindsight_provider(**kwargs: Any) -> dict[str, Any]:
    runtime: HermesRuntime = kwargs["runtime"]
    command_dir: Path = kwargs["command_dir"]
    timeout: int = kwargs["timeout"]
    if not runtime.available:
        return _blocked("Hermes runtime not found; cannot load bundled Hindsight provider.")
    command_dir.mkdir(parents=True, exist_ok=True)
    available = _probe_provider(runtime, "hindsight", command_dir, timeout=timeout, env_builder=_hindsight_probe_env)
    if not available.get("available"):
        return _blocked(available.get("reason") or "Hindsight provider is not available.", probe=available)
    return _run_provider_universes(provider="hindsight", script=HINDSIGHT_PROVIDER_SCRIPT, env_builder=_hindsight_env, **kwargs)


def _run_openviking_provider(**kwargs: Any) -> dict[str, Any]:
    runtime: HermesRuntime = kwargs["runtime"]
    endpoint: str = kwargs["openviking_endpoint"]
    if not runtime.available:
        return _blocked("Hermes runtime not found; cannot load bundled OpenViking provider.")
    if not _openviking_healthy(endpoint):
        return _blocked(f"OpenViking health check failed at {endpoint}; start a real server or set OPENVIKING_ENDPOINT.")
    return _run_provider_universes(
        provider="openviking",
        script=OPENVIKING_PROVIDER_SCRIPT,
        env_builder=lambda _tmp, _universe, _home: {"OPENVIKING_ENDPOINT": endpoint},
        **kwargs,
    )


def _run_provider_universes(
    *,
    universes: list[SandboxUniverse],
    provider: str,
    runtime: HermesRuntime,
    raw_dir: Path,
    command_dir: Path,
    openviking_endpoint: str,
    timeout: int,
    script: str,
    env_builder: Callable[[Path, SandboxUniverse, Path], dict[str, str]],
    before_run: Callable[[Path], Any] | None = None,
) -> dict[str, Any]:
    rows = []
    failures = []
    total = 0
    raw_dir.mkdir(parents=True, exist_ok=True)
    command_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"ingrain-sandbox-universe-{provider}-") as tmp_name:
        tmp = Path(tmp_name)
        for universe in universes:
            hermes_home = tmp / "hermes" / universe.name
            hermes_home.mkdir(parents=True, exist_ok=True)
            if before_run:
                before_run(hermes_home)
            payload = _provider_payload(universe)
            payload_path = tmp / f"{universe.name}.json"
            payload_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            env["HERMES_HOME"] = str(hermes_home)
            env.update(env_builder(tmp, universe, hermes_home))
            command = [str(runtime.python), "-c", script, str(payload_path)]
            try:
                proc = subprocess.run(
                    command,
                    cwd=str(runtime.root),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                returncode = proc.returncode
                output = proc.stdout.strip()
                stderr = proc.stderr.strip()
                timed_out = False
                timeout_error = ""
            except subprocess.TimeoutExpired as exc:
                returncode = None
                output = _decode_timeout_stream(exc.stdout).strip()
                stderr = _decode_timeout_stream(exc.stderr).strip()
                timed_out = True
                timeout_error = f"provider subprocess timed out after {timeout}s"
            raw_path = raw_dir / f"{universe.name}.txt"
            raw_path.write_text(output + ("\n" if output else ""), encoding="utf-8")
            (command_dir / f"{universe.name}.json").write_text(
                json.dumps(
                    {
                        "command": [str(runtime.python), "-c", "<script>", str(payload_path)],
                        "cwd": str(runtime.root),
                        "hermes_home": str(hermes_home),
                        "returncode": returncode,
                        "stdout_chars": len(output),
                        "stderr": stderr,
                        "timed_out": timed_out,
                        "timeout_seconds": timeout if timed_out else None,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            score = score_sandbox_output(output, universe)
            if timed_out:
                score = {**score, "score": 0, "provider_error": timeout_error}
                failures.append({"universe": universe.name, "returncode": returncode, "stderr": stderr, "error": timeout_error})
            elif returncode != 0:
                failures.append({"universe": universe.name, "returncode": returncode, "stderr": stderr})
            if score.get("provider_error"):
                failure = {"universe": universe.name, "returncode": returncode, "stderr": stderr, "error": score["provider_error"]}
                if failure not in failures:
                    failures.append(failure)
            total += int(score["score"])
            rows.append(
                {
                    "universe": universe.name,
                    "level": universe.level,
                    **score,
                    "raw_output": str(raw_path),
                }
            )
    max_score = len(universes) * 100
    return {
        "status": _interpret_provider_score(total, max_score, failures),
        "score": total,
        "max": max_score,
        "interpretation": _score_band(total, max_score),
        "failures": failures,
        "universes": rows,
    }


def _provider_payload(universe: SandboxUniverse) -> dict[str, Any]:
    return {
        "name": universe.name,
        "query": universe.query,
        "events": _flatten_universe_events(universe),
        "source_of_truth": [asdict(doc) for doc in universe.source_of_truth],
        "sessions": [asdict(session) for session in universe.sessions],
        "supersedes": list(universe.supersedes),
    }


def _flatten_universe_events(universe: SandboxUniverse) -> list[str]:
    events = []
    for doc in universe.source_of_truth:
        events.append(
            f"[source_id={doc.id} kind={doc.kind} created_at={doc.created_at} title={doc.title}] {doc.text}"
        )
    for session in universe.sessions:
        for turn in session.turns:
            events.append(
                f"[source_id={turn.id} session={session.id} thread={session.thread} actor={turn.actor} kind={turn.kind} turn={turn.turn} started_at={session.started_at}] {turn.text}"
            )
    for old, new in universe.supersedes:
        events.append(f"[source_id={universe.name}.edge.{old}.to.{new} kind=supersession] {old} is superseded_by {new}.")
    return events


def _normalize_providers(providers: list[str] | None) -> list[str]:
    requested = providers or ["hermes-default", "ingrain", "hindsight", "openviking"]
    normalized: list[str] = []
    for item in requested:
        for part in str(item).split(","):
            key = part.strip().lower()
            if not key:
                continue
            provider = PROVIDER_ALIASES.get(key)
            if not provider:
                raise ValueError(f"Unknown universe provider {part!r}; use one of {sorted(PROVIDER_ALIASES)}")
            if provider not in normalized:
                normalized.append(provider)
    return normalized


def _phrase_score(points: int, output: str, phrases: tuple[str, ...]) -> int:
    return _partial(points, len(_hits(output, phrases)), len(phrases))


def _hits(output: str, phrases: tuple[str, ...]) -> list[str]:
    lower = (output or "").lower()
    return [phrase for phrase in phrases if phrase.lower() in lower]


def _universe_summary(universe: SandboxUniverse) -> dict[str, Any]:
    return {
        "name": universe.name,
        "level": universe.level,
        "title": universe.title,
        "difficulty_reason": universe.difficulty_reason,
        "query": universe.query,
        "expected_current": list(universe.expected_current),
        "expected_precedence": list(universe.expected_precedence),
        "expected_continuity": list(universe.expected_continuity),
        "expected_action": list(universe.expected_action),
        "expected_sources": list(universe.expected_sources),
        "forbidden": list(universe.forbidden),
        "source_count": len(universe.source_of_truth),
        "session_count": len(universe.sessions),
        "turn_count": sum(len(session.turns) for session in universe.sessions),
        "supersedes": list(universe.supersedes),
    }


def _write_csv(path: Path, result: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "provider",
                "status",
                "universe",
                "level",
                "score",
                "max",
                "current_truth",
                "precedence_reasoning",
                "cross_session_continuity",
                "forbidden_suppression",
                "actionability",
                "source_traceability",
                "compactness",
                "abstention_discipline",
                "diagram_data_completeness",
                "raw_output",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for provider, data in result.get("providers", {}).items():
            if data.get("status") == "blocked":
                writer.writerow({"provider": provider, "status": "blocked", "score": "", "max": "", "universe": ""})
                continue
            for row in data.get("universes", []):
                components = row.get("components", {})
                writer.writerow(
                    {
                        "provider": provider,
                        "status": data.get("status"),
                        "universe": row.get("universe"),
                        "level": row.get("level"),
                        "score": row.get("score"),
                        "max": row.get("max"),
                        "raw_output": row.get("raw_output"),
                        **components,
                    }
                )


def _format_mermaid(graph: dict[str, Any]) -> str:
    lines = ["flowchart LR"]
    for node in graph.get("nodes", []):
        node_id = _mmd_id(node["id"])
        label = str(node.get("label") or node["id"]).replace('"', "'")
        lines.append(f'  {node_id}["{label}"]')
    for edge in graph.get("edges", []):
        lines.append(f"  {_mmd_id(edge['from'])} -- {edge.get('type', 'edge')} --> {_mmd_id(edge['to'])}")
    return "\n".join(lines) + "\n"


def _mmd_id(value: str) -> str:
    return "n_" + "".join(ch if ch.isalnum() else "_" for ch in value)


def _interpret_provider_score(score: int, max_score: int, failures: list[dict[str, Any]]) -> str:
    if failures:
        return "fail"
    ratio = score / max(1, max_score)
    if ratio >= 0.8:
        return "suspiciously-high"
    if ratio >= 0.6:
        return "strong"
    if ratio >= 0.4:
        return "partial"
    if ratio >= 0.2:
        return "weak"
    return "fail"


def _score_band(score: int, max_score: int) -> str:
    ratio = score / max(1, max_score)
    if ratio >= 0.8:
        return "Likely too easy for a hard public benchmark; add harder universes before using as a headline."
    if ratio >= 0.6:
        return "Strong result for a hard trace-level universe eval."
    if ratio >= 0.4:
        return "Useful partial learned experience, with visible trace failures."
    if ratio >= 0.2:
        return "Retrieval exists, but judgment over messy traces is weak."
    return "Provider failed or returned mostly irrelevant/stale context."
