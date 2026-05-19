"""Deterministic LES-100 eval."""

from __future__ import annotations

import json
import tempfile
from importlib import resources
from pathlib import Path
from typing import Any

from aeonik_ingrain.compiler.hydrate import hydrate
from aeonik_ingrain.compiler.pages import compile_store
from aeonik_ingrain.db import IngrainStore, utc_now
from aeonik_ingrain.evals.comparison import format_comparison, run_comparison
from aeonik_ingrain.ingest.generic_jsonl import ingest_jsonl
from aeonik_ingrain.practice import write_practice_artifacts

FIXTURES = [
    "project_continuity.jsonl",
    "correction_carry_forward.jsonl",
    "stale_plan.jsonl",
    "track_record.jsonl",
]


def run_eval(*, output_home: str | Path | None = None, include_comparison: bool = True) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ingrain-eval-") as tmp:
        store = IngrainStore(Path(tmp) / ".ingrain")
        store.initialize()
        fixture_dir = resources.files("aeonik_ingrain.evals").joinpath("fixtures")
        for fixture in FIXTURES:
            ingest_jsonl(store, fixture_dir.joinpath(fixture), source="eval_fixture", runner="hermes")
        compile_store(store)
        practice_result = write_practice_artifacts(store, output_path=Path(tmp) / "PRACTICE.md")

        launch_context = hydrate(store, query="draft the launch post for Aeonik Ingrain", limit=12)
        brief_context = hydrate(store, query="draft the launch post for Aeonik Ingrain", limit=12, level="brief")
        evidence_context = hydrate(store, query="draft the launch post for Aeonik Ingrain", limit=12, level="evidence")
        status_context = hydrate(store, query="what has been completed", limit=12)

        scores = {
            "Cold-start project recall": _score_contains(launch_context, ["Aeonik Ingrain", "local-first", "runner agents"]),
            "Correction carry-forward": _score_contains(launch_context, ["unapproved investor-facing", "approval-safe"]),
            "Stale-plan avoidance": _score_stale_plan(launch_context),
            "Track-record query": _score_contains(status_context, ["Hermes integration", "LES-100 eval harness"]),
            "Context compactness": 20 if len(launch_context) <= 3500 else max(0, 20 - ((len(launch_context) - 3500) // 250)),
        }
        total = sum(scores.values())
        result = {
            "name": "Aeonik Ingrain LES-100 Eval (Learned Experience Score)",
            "created_at": utc_now(),
            "scores": scores,
            "total": total,
            "max_total": 100,
            "launch_context_chars": len(launch_context),
            "status_context_chars": len(status_context),
            "practice_checks": {
                "PRACTICE.md generated": Path(practice_result["practice_path"]).exists(),
                "Practice cards generated": practice_result["card_count"] > 0,
                "Brief hydration generated": "<aeonik_ingrain_brief>" in brief_context,
                "Evidence hydration includes confidence": "confidence:" in evidence_context,
            },
        }

    if include_comparison:
        result["comparison"] = run_comparison()

    if output_home:
        out_store = IngrainStore(output_home)
        out_store.initialize()
        _write_outputs(out_store.evals_dir, result)
    return result


def format_eval(result: dict[str, Any]) -> str:
    lines = [result["name"], ""]
    for key, value in result["scores"].items():
        lines.append(f"{key:<31} {value}/20")
    lines.extend(["", f"Total{'':<26} {result['total']}/100"])
    if result.get("practice_checks"):
        lines.extend(["", "Practice layer checks"])
        for key, value in result["practice_checks"].items():
            status = "pass" if value else "fail"
            lines.append(f"{key:<44} {status}")
    if result.get("comparison"):
        lines.extend(["", format_comparison(result["comparison"])])
    return "\n".join(lines)


def _write_outputs(out_dir: Path, result: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "latest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "latest.md").write_text("```text\n" + format_eval(result) + "\n```\n", encoding="utf-8")


def _score_contains(text: str, expected: list[str]) -> int:
    lower = text.lower()
    hits = sum(1 for item in expected if item.lower() in lower)
    if hits == len(expected):
        return 20
    if not expected:
        return 20
    return int(round(20 * hits / len(expected)))


def _score_stale_plan(text: str) -> int:
    lower = text.lower()
    has_current = "product name is aeonik ingrain" in lower or "aeonik ingrain, not mindcompiler" in lower
    has_old_as_current = "the product name is mindcompiler" in lower
    if has_current and not has_old_as_current:
        return 20
    if has_current:
        return 12
    return 0
