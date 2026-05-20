"""Live learned-experience eval harness.

This harness is deliberately narrower than the deterministic fixture eval:
it sends preregistered universe events through actual provider APIs and saves
raw outputs for audit. It does not model unavailable providers.
"""

from __future__ import annotations

import csv
import json
import os
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any, Callable


@dataclass(frozen=True)
class LiveUniverse:
    name: str
    difficulty: int
    query: str
    events: tuple[str, ...]
    expected: tuple[str, ...]
    forbidden: tuple[str, ...] = ()
    rationale: str = ""


UNIVERSES: tuple[LiveUniverse, ...] = (
    LiveUniverse(
        name="launch_framing_correction",
        difficulty=1,
        query="write README tagline and public launch framing",
        events=(
            "Assistant draft: Aeonik Ingrain is a generic memory backend for Hermes.",
            "No, that's wrong. Do not call Ingrain a generic memory backend. Call it a learned experience layer for autonomous agents.",
        ),
        expected=("learned experience layer", "autonomous agents"),
        forbidden=("is a generic memory backend",),
        rationale="A user correction should become future launch-writing practice, not raw stale copy.",
    ),
    LiveUniverse(
        name="product_rename_supersession",
        difficulty=2,
        query="what product name should be used in launch docs?",
        events=(
            "Decision: Product name is MindCompiler.",
            "Decision: Product name is Aeonik Ingrain, not MindCompiler.",
        ),
        expected=("Product name is Aeonik Ingrain", "not MindCompiler"),
        forbidden=("Product name is MindCompiler.",),
        rationale="The current decision must win over an older product-name decision.",
    ),
    LiveUniverse(
        name="goals_missions_boundary",
        difficulty=3,
        query="continue the active launch mission and recall memory boundaries",
        events=(
            "Decision: Hermes owns active goals, missions, Kanban columns, scheduling, task lifecycle, and what the agent should do next.",
            "Decision: Ingrain owns learned experience only: corrections, decisions, lessons, stale-plan warnings, completed outcomes, prior failures, and project rules learned from execution.",
            "Correction: Do not let Ingrain create, move, close, schedule, or revive tasks by itself.",
        ),
        expected=("Hermes owns active goals", "Ingrain owns learned experience", "Do not let Ingrain create"),
        forbidden=("Ingrain owns active goals", "Ingrain should schedule tasks"),
        rationale="Memory must improve judgment without becoming a second task system.",
    ),
    LiveUniverse(
        name="sandbox_recovery",
        difficulty=4,
        query="install dependencies and run verification",
        events=(
            "Failed: dependency install failed because network access was restricted in the sandbox.",
            "From now on: request sandbox escalation before dependency installs or network-backed package resolution.",
        ),
        expected=("request sandbox escalation", "dependency installs", "network-backed package resolution"),
        forbidden=(),
        rationale="A prior execution failure should alter the next attempt.",
    ),
    LiveUniverse(
        name="launch_claim_safety",
        difficulty=5,
        query="write launch claims comparing Ingrain, Hindsight, and OpenViking",
        events=(
            "Assistant draft said Ingrain beats Hindsight and OpenViking.",
            "Correction: Do not claim Ingrain is better than Hindsight or OpenViking. Say it is a narrow learned-experience layer that pairs with resource memory.",
        ),
        expected=("Do not claim Ingrain is better", "narrow learned-experience layer", "resource memory"),
        forbidden=("Ingrain beats Hindsight",),
        rationale="Launch memory should prevent overclaiming against adjacent systems.",
    ),
)


PROVIDER_ALIASES = {
    "default": "hermes-default",
    "hermes": "hermes-default",
    "hermes-default": "hermes-default",
    "ingrain": "ingrain",
    "hermes-ingrain": "ingrain",
    "hindsight": "hindsight",
    "openviking": "openviking",
    "openviking-ingrain": "openviking",
}


@dataclass(frozen=True)
class HermesRuntime:
    root: Path
    python: Path

    @property
    def available(self) -> bool:
        return self.root.exists() and self.python.exists()


def run_live_les(
    *,
    output_dir: str | Path | None = None,
    providers: list[str] | None = None,
    hermes_root: str | Path | None = None,
    hermes_python: str | Path | None = None,
    openviking_endpoint: str | None = None,
    timeout: int = 90,
) -> dict[str, Any]:
    """Run the live LES harness and persist auditable artifacts."""

    provider_names = _normalize_providers(providers)
    out_dir = Path(output_dir) if output_dir else Path(".ingrain") / "evals" / "live-les"
    out_dir = out_dir.expanduser().resolve()
    raw_dir = out_dir / "raw"
    command_dir = out_dir / "commands"
    raw_dir.mkdir(parents=True, exist_ok=True)
    command_dir.mkdir(parents=True, exist_ok=True)

    runtime = _resolve_hermes_runtime(hermes_root=hermes_root, hermes_python=hermes_python)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    result: dict[str, Any] = {
        "name": "Live LES-Core Provider Smoke Eval",
        "created_at": created_at,
        "claim": "Does the provider return current learned experience from preregistered smoke-test universes?",
        "score_threshold": 90,
        "max_total": 100,
        "universes": [asdict(u) for u in UNIVERSES],
        "environment": {
            "hermes_root": str(runtime.root),
            "hermes_python": str(runtime.python),
            "hermes_available": runtime.available,
            "openviking_endpoint": openviking_endpoint or os.environ.get("OPENVIKING_ENDPOINT") or "http://127.0.0.1:1933",
            "hindsight_env_present": _hindsight_env_present(),
        },
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
        provider_raw_dir = raw_dir / provider
        provider_command_dir = command_dir / provider
        provider_raw_dir.mkdir(parents=True, exist_ok=True)
        provider_command_dir.mkdir(parents=True, exist_ok=True)
        result["providers"][provider] = runners[provider](
            runtime=runtime,
            raw_dir=provider_raw_dir,
            command_dir=provider_command_dir,
            openviking_endpoint=openviking_endpoint,
            timeout=timeout,
        )

    _write_artifacts(out_dir, result)
    return result


def format_live_les(result: dict[str, Any]) -> str:
    lines = [
        result.get("name", "Live LES-Core Provider Smoke Eval"),
        "",
        f"Claim: {result.get('claim')}",
        f"Score threshold: {result.get('score_threshold', 90)}/{result.get('max_total', 100)}",
        "",
        "Environment:",
    ]
    env = result.get("environment", {})
    lines.append(f"- Hermes root: {env.get('hermes_root')}")
    lines.append(f"- Hermes python: {env.get('hermes_python')}")
    lines.append(f"- Hermes available: {env.get('hermes_available')}")
    lines.append(f"- OpenViking endpoint: {env.get('openviking_endpoint')}")
    lines.append(f"- Hindsight env present: {env.get('hindsight_env_present')}")
    lines.extend(["", "Provider results:"])
    for provider, data in result.get("providers", {}).items():
        status = data.get("status")
        if status == "blocked":
            lines.append(f"- {provider}: blocked ({data.get('blocked_reason')})")
            continue
        score = data.get("score")
        max_score = data.get("max", result.get("max_total", 100))
        pass_fail = "pass" if data.get("passed_threshold") else "fail"
        lines.append(f"- {provider}: {score}/{max_score} ({pass_fail})")
    lines.extend(["", "Universe breakdown:"])
    for universe in result.get("universes", []):
        parts = []
        for provider, data in result.get("providers", {}).items():
            if data.get("status") == "blocked":
                parts.append(f"{provider}=blocked")
                continue
            row = next((item for item in data.get("universes", []) if item.get("universe") == universe["name"]), None)
            if row:
                parts.append(f"{provider}={row['score']}/20")
        lines.append(f"- {universe['name']}: " + "; ".join(parts))
    lines.extend([
        "",
        "Scoring rubric per universe: expected lesson recall 14, forbidden stale claim suppression 4, compact non-empty output 2.",
        f"Artifacts: {result.get('artifact_dir')}",
    ])
    return "\n".join(lines).strip()


def format_live_les_markdown(result: dict[str, Any]) -> str:
    env = result.get("environment", {})
    lines = [
        "# Live LES-Core Provider Smoke Eval",
        "",
        "## Hypothesis",
        "",
        "A learned-experience layer should return the current lesson from prior runs, suppress stale claims, and keep the recall compact enough to inject into a runner agent. This is a provider smoke test, not an external memory benchmark.",
        "",
        "## Method",
        "",
        "| Control | Implementation |",
        "|---|---|",
        "| Preregistered universes | Five smoke-test universes are defined in `src/aeonik_ingrain/evals/live_les.py` before providers run. |",
        "| Same input per provider | Every provider receives the same event list and query for each universe. |",
        "| Real provider APIs | Hermes default uses `tools.memory_tool.MemoryStore`; Ingrain loads through Hermes `plugins.memory.load_memory_provider('ingrain')`. |",
        "| Raw output audit | Each provider output is saved under `raw/<provider>/<universe>.txt`. |",
        "| Command audit | Each subprocess command log is saved under `commands/<provider>/<universe>.json`. |",
        "| Real provider rows only | Hindsight and OpenViking are scored only when a real package/service/server is available. |",
        "",
        "## Environment",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Hermes root | `{env.get('hermes_root')}` |",
        f"| Hermes python | `{env.get('hermes_python')}` |",
        f"| Hermes available | `{env.get('hermes_available')}` |",
        f"| Hindsight env present | `{env.get('hindsight_env_present')}` |",
        f"| OpenViking endpoint | `{env.get('openviking_endpoint')}` |",
        "",
        "## Results",
        "",
        "| Provider | Status | Score | Notes |",
        "|---|---|---:|---|",
    ]
    for provider, data in result.get("providers", {}).items():
        if data.get("status") == "blocked":
            lines.append(f"| {provider} | blocked |  | {data.get('blocked_reason', '')} |")
        else:
            status = "pass" if data.get("passed_threshold") else "fail"
            note = f"threshold {result.get('score_threshold', 90)}/{result.get('max_total', 100)}"
            failures = data.get("failures") or []
            if failures:
                first = failures[0].get("error") or failures[0].get("stderr") or "provider subprocess failed"
                note = f"{note}; first failure: {str(first)[:140]}"
            lines.append(f"| {provider} | {status} | {data.get('score')}/{data.get('max')} | {note} |")

    lines.extend([
        "",
        "## Universe Breakdown",
        "",
        "| Universe | Difficulty | Rationale | Scores |",
        "|---|---:|---|---|",
    ])
    for universe in result.get("universes", []):
        scores = []
        for provider, data in result.get("providers", {}).items():
            if data.get("status") == "blocked":
                scores.append(f"{provider}=blocked")
                continue
            row = next((item for item in data.get("universes", []) if item.get("universe") == universe["name"]), None)
            if row:
                scores.append(f"{provider}={row['score']}/20")
        lines.append(f"| `{universe['name']}` | {universe.get('difficulty')} | {universe.get('rationale', '')} | {'; '.join(scores)} |")

    lines.extend([
        "",
        "## Scoring Rubric",
        "",
        "Each universe is worth 20 points: expected lesson recall 14, forbidden stale claim suppression 4, compact non-empty output 2. The provider passes when total score is at least 90/100 and no provider subprocess fails.",
        "",
        "## Interpretation",
        "",
        "On these preregistered local smoke-test universes, this run can support only the narrow claim that a provider carried forward the expected learned-experience snippets. It does not show that Ingrain is a better general-purpose memory backend than Hindsight, OpenViking, or any other provider. A 100/100 here means the provider passed this small regression gate; it is not a public SOTA claim.",
        "",
        "## Artifacts",
        "",
        f"- Artifact directory: `{result.get('artifact_dir')}`",
        "- Machine-readable results: `results.json` and `results.csv`",
        "- Raw provider outputs: `raw/`",
        "- Command logs: `commands/`",
        "",
    ])
    return "\n".join(lines)


def score_live_output(output: str, universe: LiveUniverse) -> dict[str, Any]:
    provider_error = _provider_output_error(output)
    if provider_error:
        return {
            "score": 0,
            "max": 20,
            "expected_score": 0,
            "forbidden_score": 0,
            "compact_score": 0,
            "expected_hits": [],
            "missing_expected": list(universe.expected),
            "forbidden_hits": [],
            "output_chars": len(output or ""),
            "provider_error": provider_error,
        }
    lower = (output or "").lower()
    expected_hits = [item for item in universe.expected if item.lower() in lower]
    forbidden_hits = [item for item in universe.forbidden if item.lower() in lower]
    expected_score = int(round(14 * len(expected_hits) / max(1, len(universe.expected))))
    forbidden_score = 4 if not forbidden_hits else 0
    compact_score = 2 if output.strip() and len(output) <= 6000 else 0
    total = expected_score + forbidden_score + compact_score
    return {
        "score": total,
        "max": 20,
        "expected_score": expected_score,
        "forbidden_score": forbidden_score,
        "compact_score": compact_score,
        "expected_hits": expected_hits,
        "missing_expected": [item for item in universe.expected if item not in expected_hits],
        "forbidden_hits": forbidden_hits,
        "output_chars": len(output or ""),
        "provider_error": "",
    }


def _run_hermes_default(
    *,
    runtime: HermesRuntime,
    raw_dir: Path,
    command_dir: Path,
    openviking_endpoint: str | None,
    timeout: int,
) -> dict[str, Any]:
    if not runtime.available:
        return _blocked("Hermes runtime not found; cannot import tools.memory_tool.MemoryStore.")
    return _run_provider_universes(
        provider="hermes-default",
        runtime=runtime,
        raw_dir=raw_dir,
        command_dir=command_dir,
        timeout=timeout,
        script=HERMES_DEFAULT_SCRIPT,
        env_builder=lambda _tmp, _universe, _hermes_home: {},
    )


def _run_ingrain_provider(
    *,
    runtime: HermesRuntime,
    raw_dir: Path,
    command_dir: Path,
    openviking_endpoint: str | None,
    timeout: int,
) -> dict[str, Any]:
    if not runtime.available:
        return _blocked("Hermes runtime not found; cannot load user memory provider plugin.")
    return _run_provider_universes(
        provider="ingrain",
        runtime=runtime,
        raw_dir=raw_dir,
        command_dir=command_dir,
        timeout=timeout,
        script=INGRAIN_PROVIDER_SCRIPT,
        env_builder=lambda tmp, _universe, _hermes_home: {"PATH": f"{_make_ingrain_cli_shim(tmp)}{os.pathsep}{os.environ.get('PATH', '')}"},
        before_run=_install_hermes_provider,
    )


def _run_hindsight_provider(
    *,
    runtime: HermesRuntime,
    raw_dir: Path,
    command_dir: Path,
    openviking_endpoint: str | None,
    timeout: int,
) -> dict[str, Any]:
    if not runtime.available:
        return _blocked("Hermes runtime not found; cannot load bundled Hindsight provider.")
    available = _probe_provider(runtime, "hindsight", command_dir, timeout=timeout, env_builder=_hindsight_probe_env)
    if not available.get("available"):
        reason = available.get("reason") or "Hindsight provider is not available."
        return _blocked(reason, probe=available)
    return _run_provider_universes(
        provider="hindsight",
        runtime=runtime,
        raw_dir=raw_dir,
        command_dir=command_dir,
        timeout=timeout,
        script=HINDSIGHT_PROVIDER_SCRIPT,
        env_builder=_hindsight_env,
    )


def _run_openviking_provider(
    *,
    runtime: HermesRuntime,
    raw_dir: Path,
    command_dir: Path,
    openviking_endpoint: str | None,
    timeout: int,
) -> dict[str, Any]:
    if not runtime.available:
        return _blocked("Hermes runtime not found; cannot load bundled OpenViking provider.")
    endpoint = openviking_endpoint or os.environ.get("OPENVIKING_ENDPOINT") or "http://127.0.0.1:1933"
    if not _openviking_healthy(endpoint):
        return _blocked(f"OpenViking health check failed at {endpoint}; start a real server or set OPENVIKING_ENDPOINT.")
    return _run_provider_universes(
        provider="openviking",
        runtime=runtime,
        raw_dir=raw_dir,
        command_dir=command_dir,
        timeout=timeout,
        script=OPENVIKING_PROVIDER_SCRIPT,
        env_builder=lambda _tmp, _universe, _hermes_home: {"OPENVIKING_ENDPOINT": endpoint},
    )


def _run_provider_universes(
    *,
    provider: str,
    runtime: HermesRuntime,
    raw_dir: Path,
    command_dir: Path,
    timeout: int,
    script: str,
    env_builder: Callable[[Path, LiveUniverse, Path], dict[str, str]],
    before_run: Callable[[Path], Any] | None = None,
) -> dict[str, Any]:
    rows = []
    total = 0
    failures = []
    with tempfile.TemporaryDirectory(prefix=f"ingrain-live-les-{provider}-") as tmp_name:
        tmp = Path(tmp_name)
        for universe in UNIVERSES:
            hermes_home = tmp / "hermes" / universe.name
            hermes_home.mkdir(parents=True, exist_ok=True)
            if before_run:
                before_run(hermes_home)
            payload_path = tmp / f"{universe.name}.json"
            payload_path.write_text(json.dumps(asdict(universe), indent=2) + "\n", encoding="utf-8")
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            env["HERMES_HOME"] = str(hermes_home)
            env.update(env_builder(tmp, universe, hermes_home))
            command = [str(runtime.python), "-c", script, str(payload_path)]
            timed_out = False
            timeout_error = ""
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
            except subprocess.TimeoutExpired as exc:
                timed_out = True
                returncode = None
                output = _decode_timeout_stream(exc.stdout).strip()
                stderr = _decode_timeout_stream(exc.stderr).strip()
                timeout_error = f"provider subprocess timed out after {timeout}s"
            (raw_dir / f"{universe.name}.txt").write_text(output + ("\n" if output else ""), encoding="utf-8")
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
            score = score_live_output(output, universe)
            if timed_out:
                score = {
                    **score,
                    "score": 0,
                    "expected_score": 0,
                    "forbidden_score": 0,
                    "compact_score": 0,
                    "provider_error": timeout_error,
                }
                failures.append({"universe": universe.name, "returncode": returncode, "stderr": stderr, "error": timeout_error})
            elif returncode != 0:
                failures.append({"universe": universe.name, "returncode": returncode, "stderr": stderr})
            if score.get("provider_error"):
                failure = {"universe": universe.name, "returncode": returncode, "stderr": stderr, "error": score["provider_error"]}
                if failure not in failures:
                    failures.append(failure)
            total += score["score"]
            rows.append({"universe": universe.name, **score, "raw_output": str(raw_dir / f"{universe.name}.txt")})
    status = "pass" if total >= 90 and not failures else "fail"
    return {
        "status": status,
        "score": total,
        "max": len(UNIVERSES) * 20,
        "passed_threshold": total >= 90 and not failures,
        "failures": failures,
        "universes": rows,
    }


def _probe_provider(
    runtime: HermesRuntime,
    provider: str,
    command_dir: Path,
    *,
    timeout: int,
    env_builder: Callable[[Path, Path], dict[str, str]] | None = None,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"ingrain-live-les-probe-{provider}-") as tmp_name:
        tmp = Path(tmp_name)
        hermes_home = tmp / "hermes"
        env = os.environ.copy()
        env["HERMES_HOME"] = str(hermes_home)
        if env_builder:
            env.update(env_builder(tmp, hermes_home))
        proc = subprocess.run(
            [str(runtime.python), "-c", PROVIDER_PROBE_SCRIPT, provider],
            cwd=str(runtime.root),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    output = (proc.stdout or "").strip()
    data: dict[str, Any]
    try:
        data = json.loads(output) if output else {}
    except json.JSONDecodeError:
        data = {"available": False, "reason": output or proc.stderr.strip()}
    data["returncode"] = proc.returncode
    data["stderr"] = proc.stderr.strip()
    (command_dir / f"{provider}-probe.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if proc.returncode != 0:
        data["available"] = False
        data["reason"] = data.get("reason") or data.get("stderr") or f"provider probe exited {proc.returncode}"
    return data


def _write_artifacts(out_dir: Path, result: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "report.md").write_text(format_live_les_markdown(result), encoding="utf-8")
    rows = []
    for provider, data in result.get("providers", {}).items():
        if data.get("status") == "blocked":
            rows.append({
                "provider": provider,
                "status": "blocked",
                "score": "",
                "max": result.get("max_total", 100),
                "universe": "",
                "blocked_reason": data.get("blocked_reason", ""),
            })
            continue
        for universe in data.get("universes", []):
            rows.append({
                "provider": provider,
                "status": data.get("status"),
                "score": universe.get("score"),
                "max": universe.get("max"),
                "universe": universe.get("universe"),
                "blocked_reason": "",
            })
    with (out_dir / "results.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["provider", "status", "score", "max", "universe", "blocked_reason"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


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
                raise ValueError(f"Unknown live LES provider {part!r}; use one of {sorted(PROVIDER_ALIASES)}")
            if provider not in normalized:
                normalized.append(provider)
    return normalized


def _resolve_hermes_runtime(*, hermes_root: str | Path | None, hermes_python: str | Path | None) -> HermesRuntime:
    root_candidates = []
    if hermes_root:
        root_candidates.append(Path(hermes_root).expanduser())
    if os.environ.get("HERMES_AGENT_ROOT"):
        root_candidates.append(Path(os.environ["HERMES_AGENT_ROOT"]).expanduser())
    root_candidates.extend([
        Path.home() / ".hermes" / "hermes-agent",
        Path.home() / "Desktop" / "REPO" / "hermes-agent",
    ])
    root = next((candidate for candidate in root_candidates if candidate.exists()), root_candidates[0])
    python = Path(hermes_python).expanduser() if hermes_python else root / "venv" / "bin" / "python"
    return HermesRuntime(root=root, python=python)


def _make_ingrain_cli_shim(tmp: Path) -> Path:
    bin_dir = tmp / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    shim = bin_dir / "ingrain"
    src_root = Path(__file__).resolve().parents[2]
    shim.write_text(
        "#!/usr/bin/env bash\n"
        f"export PYTHONPATH=\"{src_root}${{PYTHONPATH:+:$PYTHONPATH}}\"\n"
        f"exec \"{sys.executable}\" -m aeonik_ingrain.cli \"$@\"\n",
        encoding="utf-8",
    )
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return bin_dir


def _hindsight_env(tmp: Path, universe: LiveUniverse, hermes_home: Path) -> dict[str, str]:
    home = tmp / "hindsight-home"
    home.mkdir(parents=True, exist_ok=True)
    hermes_env = _load_simple_env(Path.home() / ".hermes" / ".env")
    merged_env = {**hermes_env, **os.environ}
    mode = merged_env.get("HINDSIGHT_MODE") or "local_embedded"
    if mode in ("local", "local_embedded"):
        _write_hindsight_local_config(hermes_home, universe)
    env = {
        "HOME": str(home),
        "HINDSIGHT_BANK_ID": f"ingrain-les-{universe.name}",
        "HINDSIGHT_MODE": mode,
    }
    for key in (
        "HINDSIGHT_LLM_API_KEY",
        "HINDSIGHT_API_KEY",
        "HINDSIGHT_API_URL",
        "HINDSIGHT_TIMEOUT",
        "HINDSIGHT_IDLE_TIMEOUT",
        "HINDSIGHT_API_LLM_BASE_URL",
    ):
        if merged_env.get(key):
            env[key] = merged_env[key]
    env.setdefault("HINDSIGHT_TIMEOUT", "240")
    env.setdefault("HINDSIGHT_IDLE_TIMEOUT", "300")
    return env


def _hindsight_probe_env(tmp: Path, hermes_home: Path) -> dict[str, str]:
    return _hindsight_env(tmp, UNIVERSES[0], hermes_home)


def _load_simple_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def _write_hindsight_local_config(hermes_home: Path, universe: LiveUniverse) -> None:
    config_dir = hermes_home / "hindsight"
    config_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "mode": "local_embedded",
        "profile": "ingrain-live-les",
        "bank_id": f"ingrain-les-{universe.name}",
        "memory_mode": "tools",
        "recall_budget": "high",
        "recall_prefetch_method": "reflect",
        "auto_retain": False,
        "retain_async": False,
        "retain_context": "Aeonik Ingrain live learned-experience eval",
        "retain_tags": ["ingrain-live-les", universe.name],
        "llm_provider": "openai",
        "llm_model": "gpt-4o-mini",
        "timeout": 240,
        "idle_timeout": 300,
    }
    (config_dir / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _decode_timeout_stream(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _install_hermes_provider(hermes_home: Path) -> Path:
    target_dir = hermes_home / "plugins" / "ingrain"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "__init__.py"
    source = resources.files("aeonik_ingrain").joinpath("hermes_provider.py")
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    (target_dir / "plugin.yaml").write_text(
        "name: ingrain\n"
        "description: Aeonik Ingrain learned experience provider for Hermes.\n",
        encoding="utf-8",
    )
    return target


def _hindsight_env_present() -> bool:
    hermes_env = _load_simple_env(Path.home() / ".hermes" / ".env")
    keys = (
        "HINDSIGHT_API_KEY",
        "HINDSIGHT_API_URL",
        "HINDSIGHT_LLM_API_KEY",
        "HINDSIGHT_MODE",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "OPENROUTER_API_KEY",
    )
    return any(bool(os.environ.get(key) or hermes_env.get(key)) for key in keys)


def _openviking_healthy(endpoint: str) -> bool:
    url = endpoint.rstrip("/") + "/health"
    try:
        with urllib.request.urlopen(url, timeout=2) as response:  # noqa: S310
            return 200 <= response.status < 300
    except (OSError, urllib.error.URLError):
        return False


def _provider_output_error(output: str) -> str:
    text = (output or "").strip()
    if not text:
        return ""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, dict) and data.get("error"):
        return str(data["error"])
    lower = text.lower()
    markers = (
        "failed to retain",
        "failed to recall",
        "failed to reflect",
        "traceback",
        "permissionerror",
        "operation not permitted",
    )
    if any(marker in lower for marker in markers):
        return text[:1000]
    return ""


def _blocked(reason: str, **extra: Any) -> dict[str, Any]:
    return {"status": "blocked", "blocked_reason": reason, **extra}


HERMES_DEFAULT_SCRIPT = r'''
import json
import sys

from tools.memory_tool import MemoryStore, memory_tool

payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
store = MemoryStore(memory_char_limit=12000)
store.load_from_disk()
for event in payload["events"]:
    result = json.loads(memory_tool("add", target="memory", content=event, store=store))
    if not result.get("success"):
        print(json.dumps(result), file=sys.stderr)
fresh = MemoryStore(memory_char_limit=12000)
fresh.load_from_disk()
print(fresh.format_for_system_prompt("memory") or "")
'''


INGRAIN_PROVIDER_SCRIPT = r'''
import json
import os
import sys

from plugins.memory import load_memory_provider

payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
provider = load_memory_provider("ingrain")
if provider is None:
    raise SystemExit("ingrain provider not found")
if not provider.is_available():
    raise SystemExit("ingrain provider not available")
provider.initialize(
    "live-les-session",
    hermes_home=os.environ["HERMES_HOME"],
    platform="cli",
    agent_context="primary",
)
for event in payload["events"]:
    provider.sync_turn(event, "", session_id="live-les-session")
print(provider.prefetch(payload["query"], session_id="live-les-session") or "")
provider.shutdown()
'''


PROVIDER_PROBE_SCRIPT = r'''
import importlib.util
import json
import os
import sys

from plugins.memory import load_memory_provider

name = sys.argv[1]
provider = load_memory_provider(name)
imports = {
    "hindsight": bool(importlib.util.find_spec("hindsight")),
    "hindsight_client": bool(importlib.util.find_spec("hindsight_client")),
    "hindsight_embed": bool(importlib.util.find_spec("hindsight_embed")),
}
env = {
    key: bool(os.environ.get(key))
    for key in (
        "HINDSIGHT_API_KEY",
        "HINDSIGHT_API_URL",
        "HINDSIGHT_MODE",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "OPENROUTER_API_KEY",
    )
}
available = bool(provider and provider.is_available())
reason = ""
if not provider:
    reason = f"{name} provider not found in Hermes."
elif not available and name == "hindsight":
    reason = "Hindsight is not available: no usable Hindsight package/service/API key was detected by the Hermes provider."
elif not available:
    reason = f"{name} provider is not available."
print(json.dumps({"provider": name, "available": available, "imports": imports, "env": env, "reason": reason}, sort_keys=True))
'''


HINDSIGHT_PROVIDER_SCRIPT = r'''
import json
import os
import sys

from plugins.memory import load_memory_provider

payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
provider = load_memory_provider("hindsight")
if provider is None:
    raise SystemExit("hindsight provider not found")
if not provider.is_available():
    raise SystemExit("hindsight provider not available")
provider.initialize(
    "live-les-session",
    hermes_home=os.environ["HERMES_HOME"],
    platform="cli",
    agent_context="primary",
)
for event in payload["events"]:
    provider.handle_tool_call("hindsight_retain", {"content": event, "context": payload["name"], "tags": ["ingrain-live-les"]})
print(provider.handle_tool_call("hindsight_reflect", {"query": payload["query"]}) or "")
provider.shutdown()
'''


OPENVIKING_PROVIDER_SCRIPT = r'''
import json
import os
import sys

from plugins.memory import load_memory_provider

payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
provider = load_memory_provider("openviking")
if provider is None:
    raise SystemExit("openviking provider not found")
if not provider.is_available():
    raise SystemExit("openviking provider not available")
provider.initialize(
    "live-les-session",
    hermes_home=os.environ["HERMES_HOME"],
    platform="cli",
    agent_context="primary",
)
for event in payload["events"]:
    provider.handle_tool_call("viking_remember", {"content": event, "category": "pattern"})
provider.on_session_end([{"role": "user", "content": event} for event in payload["events"]])
recall = provider.prefetch(payload["query"], session_id="live-les-session")
search = provider.handle_tool_call("viking_search", {"query": payload["query"], "limit": 5, "mode": "auto"})
print((recall or "") + "\n" + (search or ""))
provider.shutdown()
'''
