"""Hermes dogfood verification for Aeonik Ingrain.

This module is intentionally read-mostly. It reports installation, store,
hydration, and optional live Hermes recall evidence without changing capture or
consolidation behavior.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import time
import uuid
from importlib import metadata
from pathlib import Path
from typing import Any, Callable

from aeonik_ingrain import __version__
from aeonik_ingrain.compiler.hydrate import hydrate
from aeonik_ingrain.db import IngrainStore

SubprocessRunner = Callable[[list[str], int], dict[str, Any]]


SECRETISH_RE = re.compile(
    r"(?i)(api[_-]?key\s*[:=]\s*\S+|secret\s*[:=]\s*\S+|token\s*[:=]\s*\S+|password\s*[:=]\s*\S+|ghp_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-(?:proj|svcacct|admin)-[A-Za-z0-9_-]+)"
)


def distribution_version(name: str) -> str | None:
    """Return installed distribution version or None if absent."""

    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def verify_hermes(
    *,
    hermes_home: str | Path | None = None,
    ingrain_home: str | Path | None = None,
    live: bool = False,
    hermes_bin: str | None = None,
    canary: str | None = None,
    expected: str | None = None,
    write_canary: bool = False,
    timeout: int = 90,
    subprocess_runner: SubprocessRunner | None = None,
) -> dict[str, Any]:
    """Verify Ingrain's Hermes dogfood integration state.

    Unit tests may pass ``subprocess_runner``. Production live checks call the
    real Hermes binary and label missing binaries or failures as blocked/failed;
    no fixture result is treated as live evidence.
    """

    h_home = Path(hermes_home).expanduser() if hermes_home else Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser()
    store = IngrainStore(ingrain_home)
    warnings: list[str] = []
    db_exists_before_verify = store.db_path.exists()
    db_readable_before_verify = _sqlite_db_readable(store.db_path)

    expected_dist = distribution_version("aeonik-ingrain")
    bare_dist = distribution_version("ingrain")
    if bare_dist:
        warnings.append("Bare `ingrain` distribution is installed; install package should be `aeonik-ingrain`.")
    if not expected_dist:
        warnings.append("Expected distribution `aeonik-ingrain` is not installed in this Python environment.")

    provider_plugin = h_home / "plugins" / "ingrain" / "__init__.py"
    auto_plugin = h_home / "plugins" / "ingrain-auto" / "__init__.py"
    memory_provider = _read_memory_provider(h_home / "config.yaml")
    if memory_provider == "ingrain":
        mode = "provider"
    elif provider_plugin.exists() or auto_plugin.exists():
        mode = "sidecar"
    else:
        mode = "none"

    live_result = _check_live_recall(
        store=store,
        live=live,
        hermes_bin=hermes_bin,
        canary=canary,
        expected=expected,
        write_canary=write_canary,
        timeout=timeout,
        subprocess_runner=subprocess_runner,
    )

    events = _safe_list(store.list_events)
    promotions = _safe_list(store.list_promotions)
    pages = _safe_list(store.list_compiled_pages)
    latest_event = _latest_by_created_at(events)
    latest_promotion = _latest_by_created_at(promotions)
    ratio = (len(events) / len(promotions)) if promotions else None
    if events and not promotions:
        warnings.append("Ledger has events but no promotions; run `ingrain consolidate` or `ingrain compile` and inspect quality.")
    elif ratio is not None and ratio >= 20:
        warnings.append(f"High event-to-promotion ratio ({ratio:.1f}); check consolidation quality.")

    hydrate_result = _check_hydrate(store, promotions, warnings)

    result: dict[str, Any] = {
        "ok": True,
        "verdict": "pass",
        "mode": mode,
        "python_version": platform.python_version(),
        "ingrain_version": __version__,
        "ingrain_binary": shutil.which("ingrain"),
        "package": {
            "expected_distribution": "aeonik-ingrain",
            "expected_distribution_present": expected_dist is not None,
            "expected_distribution_version": expected_dist,
            "wrong_bare_ingrain_distribution_present": bare_dist is not None,
            "wrong_bare_ingrain_distribution_version": bare_dist,
        },
        "hermes": {
            "home": str(h_home),
            "provider_plugin_installed": provider_plugin.exists(),
            "auto_plugin_installed": auto_plugin.exists(),
            "memory_provider": memory_provider,
        },
        "store": {
            "home": str(store.home),
            "db_path": str(store.db_path),
            "db_exists_before_verify": db_exists_before_verify,
            "db_readable_before_verify": db_readable_before_verify,
            "db_exists_after_verify": store.db_path.exists(),
            "db_readable": _sqlite_db_readable(store.db_path),
            "ledger_events": len(events),
            "promotions": len(promotions),
            "compiled_pages": len(pages),
            "event_to_promotion_ratio": ratio,
            "latest_event": _summarize_event(latest_event),
            "latest_promotion": _summarize_promotion(latest_promotion),
        },
        "hydrate": hydrate_result,
        "live_recall": live_result,
        "warnings": warnings,
    }

    blockers = []
    if not result["package"]["expected_distribution_present"]:
        blockers.append("Expected package distribution `aeonik-ingrain` is not installed.")
    if live_result.get("attempted") and live_result.get("status") == "blocked":
        blockers.append(live_result.get("blocker") or "Live Hermes recall blocked.")

    if blockers:
        result["ok"] = False
        result["verdict"] = "blocked"
        result["blockers"] = blockers
    elif warnings or not hydrate_result.get("ok") or (live_result.get("attempted") and not live_result.get("ok")):
        result["ok"] = False if live_result.get("attempted") and live_result.get("status") == "failed" else True
        result["verdict"] = "fail" if live_result.get("attempted") and live_result.get("status") == "failed" else "warn"

    return result


def _safe_list(fn: Callable[..., list[dict[str, Any]]]) -> list[dict[str, Any]]:
    try:
        return fn()
    except Exception:
        return []


def _sqlite_db_readable(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            conn.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
        finally:
            conn.close()
    except sqlite3.Error:
        return False
    return True


def _latest_by_created_at(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    return sorted(rows, key=lambda row: str(row.get("created_at") or row.get("updated_at") or ""))[-1]


def _summarize_event(event: dict[str, Any] | None) -> dict[str, Any] | None:
    if not event:
        return None
    return {
        "id": event.get("id"),
        "created_at": event.get("created_at"),
        "source": event.get("source"),
        "runner": event.get("runner"),
        "event_type": event.get("event_type"),
    }


def _summarize_promotion(promotion: dict[str, Any] | None) -> dict[str, Any] | None:
    if not promotion:
        return None
    return {
        "id": promotion.get("id"),
        "created_at": promotion.get("created_at"),
        "promoted_type": promotion.get("promoted_type"),
        "event_id": promotion.get("event_id"),
    }


def _read_memory_provider(config_path: Path) -> str | None:
    if not config_path.exists():
        return None
    try:
        lines = config_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None

    in_memory = False
    memory_indent = 0
    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if stripped.startswith("memory:"):
            # Supports both `memory: {provider: ingrain}` and block form.
            inline = stripped[len("memory:") :].strip()
            match = re.search(r"provider\s*:\s*['\"]?([^,'\"}\s]+)", inline)
            if match:
                return match.group(1)
            in_memory = True
            memory_indent = indent
            continue
        if in_memory and indent <= memory_indent and not raw.startswith(" "):
            in_memory = False
        if in_memory and stripped.startswith("provider:"):
            value = stripped.split(":", 1)[1].strip().strip('"\'')
            return value or None
    return None


def _check_hydrate(store: IngrainStore, promotions: list[dict[str, Any]], warnings: list[str]) -> dict[str, Any]:
    if not promotions:
        warnings.append("Hydration skipped because no promotions/cards exist.")
        return {"ok": False, "status": "skipped", "has_source_ids": False, "context_chars": 0}
    try:
        context = hydrate(store, query="what should I know before continuing this task", level="evidence")
    except Exception as exc:  # pragma: no cover - defensive receipt detail
        return {"ok": False, "status": "failed", "error": str(exc), "has_source_ids": False, "context_chars": 0}
    has_source = "[source:" in context
    has_wrapper = "<aeonik_ingrain_context>" in context
    ok = bool(context and has_source and has_wrapper)
    if not ok:
        warnings.append("Hydration did not return source-linked evidence context.")
    return {
        "ok": ok,
        "status": "pass" if ok else "warn",
        "has_source_ids": has_source,
        "has_context_wrapper": has_wrapper,
        "context_chars": len(context),
    }


def _check_live_recall(
    *,
    store: IngrainStore,
    live: bool,
    hermes_bin: str | None,
    canary: str | None,
    expected: str | None,
    write_canary: bool,
    timeout: int,
    subprocess_runner: SubprocessRunner | None,
) -> dict[str, Any]:
    if not live:
        return {"attempted": False, "ok": False, "status": "skipped"}

    should_write_canary = write_canary or not (expected or canary)
    verification_id = uuid.uuid4().hex[:8] if should_write_canary else None
    phrase = expected or canary or f"ingrain verify phrase {verification_id}"
    if should_write_canary:
        canary_text = f"Ingrain verification id {verification_id} canary phrase: {phrase}"
        canary_meta = {
            "remember_type": "project_fact",
            "verify_canary": True,
            "verification_id": verification_id,
            "transient": True,
        }
        event = store.add_event(
            source="ingrain_verify",
            runner="ingrain",
            event_type="interaction",
            actor="user",
            text=canary_text,
            meta=canary_meta,
        )
        store.add_promotion(
            event_id=event.id,
            promoted_type="project_fact",
            text=canary_text,
            confidence=1.0,
            reason="Temporary verification canary seeded by `ingrain verify hermes --live`.",
            meta=canary_meta,
        )
        store.write_compiled_page(
            path="verify/canary.md",
            title="Verification Canary",
            page_type="project_fact",
            content=f"# Verification Canary\n\n- {canary_text}\n",
            source_event_ids=[event.id],
        )

    resolved_hermes = shutil.which("hermes") if hermes_bin is None else hermes_bin
    if not resolved_hermes:
        return {
            "attempted": True,
            "ok": False,
            "status": "blocked",
            "canary": phrase,
            "blocker": "Hermes binary not found. Pass --hermes-bin or install Hermes CLI.",
        }

    prompt = "Ingrain verification probe. Without files or session_search, answer only the Ingrain canary phrase from active memory."
    if verification_id:
        prompt = (
            "Ingrain verification probe. Without files or session_search, answer only the canary phrase "
            f"for verification id {verification_id} from active memory. Ignore canaries with other verification ids."
        )
    command = [
        resolved_hermes,
        "chat",
        "-Q",
        "--toolsets",
        "memory",
        "-q",
        prompt,
    ]
    runner = subprocess_runner or (lambda command, timeout: _run_subprocess(command, timeout, env_overrides={"INGRAIN_HOME": str(store.home)}))
    started = time.monotonic()
    try:
        completed = runner(command, timeout)
    except Exception as exc:  # pragma: no cover - defensive receipt detail
        return {
            "attempted": True,
            "ok": False,
            "status": "blocked",
            "canary": phrase,
            "verification_id": verification_id,
            "command": command,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "blocker": str(exc),
        }
    output = f"{completed.get('stdout', '')}\n{completed.get('stderr', '')}".strip()
    ok = completed.get("exit_code") == 0 and phrase.lower() in output.lower()
    return {
        "attempted": True,
        "ok": ok,
        "status": "live" if ok else "failed",
        "canary": phrase,
        "verification_id": verification_id,
        "command": command,
        "exit_code": completed.get("exit_code"),
        "elapsed_seconds": completed.get("elapsed_seconds", round(time.monotonic() - started, 3)),
        "output_snippet": _redact(output[:1000]),
    }


def _run_subprocess(command: list[str], timeout: int, env_overrides: dict[str, str] | None = None) -> dict[str, Any]:
    started = time.monotonic()
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    proc = subprocess.run(command, text=True, capture_output=True, timeout=timeout, env=env, check=False)
    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def _redact(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        value = match.group(0)
        for separator in ("=", ":"):
            if separator in value:
                key = value.split(separator, 1)[0].rstrip()
                return f"{key}{separator}[REDACTED]"
        return "[REDACTED]"

    return SECRETISH_RE.sub(replace, text)


def format_markdown_receipt(result: dict[str, Any]) -> str:
    warnings = result.get("warnings") or []
    live = result.get("live_recall") or {}
    package = result.get("package") or {}
    hermes = result.get("hermes") or {}
    store = result.get("store") or {}
    hydrate_result = result.get("hydrate") or {}
    lines = [
        "# Ingrain Hermes Verification",
        "",
        f"- Verdict: **{result.get('verdict', 'unknown')}**",
        f"- Mode: `{result.get('mode', 'unknown')}`",
        f"- Ingrain version: `{result.get('ingrain_version', 'unknown')}`",
        f"- Python: `{result.get('python_version', 'unknown')}`",
        "",
        "## Package",
        "",
        f"- `aeonik-ingrain` present: {package.get('expected_distribution_present')}",
        f"- bare `ingrain` distribution present: {package.get('wrong_bare_ingrain_distribution_present')}",
        "",
        "## Hermes",
        "",
        f"- Home: `{hermes.get('home')}`",
        f"- Provider plugin installed: {hermes.get('provider_plugin_installed')}",
        f"- Auto plugin installed: {hermes.get('auto_plugin_installed')}",
        f"- Memory provider: `{hermes.get('memory_provider')}`",
        "",
        "## Store",
        "",
        f"- Home: `{store.get('home')}`",
        f"- Ledger events: {store.get('ledger_events')}",
        f"- Promotions/cards: {store.get('promotions')}",
        f"- Compiled pages: {store.get('compiled_pages')}",
        f"- Event-to-promotion ratio: {store.get('event_to_promotion_ratio')}",
        "",
        "## Hydration",
        "",
        f"- Status: `{hydrate_result.get('status')}`",
        f"- Source-linked evidence: {hydrate_result.get('has_source_ids')}",
        "",
        "## Live recall",
        "",
        f"- Attempted: {live.get('attempted')}",
        f"- Status: `{live.get('status')}`",
        f"- OK: {live.get('ok')}",
    ]
    if live.get("blocker"):
        lines.append(f"- Blocker: {live.get('blocker')}")
    command_value = live.get("command")
    if isinstance(command_value, list):
        lines.append(f"- Command: `{' '.join(str(part) for part in command_value)}`")
    if live.get("output_snippet"):
        lines.extend(["", "```text", str(live.get("output_snippet")), "```"])
    lines.extend(["", "## Warnings", ""])
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Common fixes",
            "",
            "- Install the correct package: `pip install aeonik-ingrain`.",
            "- Do not install bare PyPI package `ingrain`; that is a different project.",
            "- Install provider plugin: `ingrain install hermes --hermes-home ~/.hermes`.",
            "- Enable provider mode when intended: `hermes config set memory.provider ingrain`.",
            "- Compile or consolidate cards before expecting hydration: `ingrain compile` or `ingrain consolidate`.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def write_receipts(result: dict[str, Any], *, json_output: str | Path | None = None, markdown_output: str | Path | None = None) -> None:
    if json_output:
        path = Path(json_output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if markdown_output:
        path = Path(markdown_output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(format_markdown_receipt(result), encoding="utf-8")
