"""IngrainLane and IngrainSidecarLane: implement sandbox_universe.lanes.LaneAdapter.

These are registered via pyproject.toml entry points (`sandbox_universe.lanes`)
so an installed `aeonik-ingrain` automatically adds both to
`sandbox-universe run --lane ...`.

Provenance: subprocess scripts and supporting code ported byte-for-byte from
aeonik_ingrain/evals/sandbox_universe.py (INGRAIN_PROVIDER_SCRIPT,
INGRAIN_SIDECAR_SCRIPT, _make_ingrain_cli_shim, _install_hermes_provider).
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
from importlib import resources
from pathlib import Path
from typing import Any


# We deliberately do not import from sandbox_universe at module top level —
# the integration loads lazily so importing aeonik_ingrain doesn't require
# sandbox-universe to be installed.


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


INGRAIN_SIDECAR_SCRIPT = r'''
import json
import os
import subprocess
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
default_context = fresh.format_for_system_prompt("memory") or ""

ingrain_home = os.environ["INGRAIN_HOME"]
base = ["ingrain", "--home", ingrain_home]
for event in payload["events"]:
    subprocess.run(
        base
        + [
            "record",
            "--source",
            "sandbox_universe_sidecar",
            "--runner",
            "hermes-default-plus-ingrain-sidecar",
            "--event-type",
            "interaction",
            "--actor",
            "user",
            "--session-id",
            payload["name"],
            event,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
use_llm = os.environ.get("INGRAIN_USE_LLM_CONSOLIDATOR") == "1"
practice_args = ["practice", "--output", os.path.join(ingrain_home, "PRACTICE.md")]
if use_llm:
    cons = subprocess.run(base + ["consolidate", "--limit", "200"], capture_output=True, text=True)
    if cons.returncode != 0:
        print(f"[ingrain-llm-sidecar] consolidate failed (rc={cons.returncode}): {cons.stdout[:300]}", file=sys.stderr)
        subprocess.run(base + ["compile"], check=True, capture_output=True, text=True)
    else:
        # Consolidator wrote the cards. Practice must NOT re-run the regex
        # compiler (which would wipe them).
        practice_args.append("--no-compile")
else:
    subprocess.run(base + ["compile"], check=True, capture_output=True, text=True)
subprocess.run(base + practice_args, check=True, capture_output=True, text=True)
hydrated = subprocess.run(
    base + ["hydrate", "--level", "evidence", "--query", payload["query"], "--limit", "12", "--max-chars", "9000"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()

print("<hermes_default_memory>")
print(default_context)
print("</hermes_default_memory>")
tag = "ingrain_llm_sidecar" if use_llm else "ingrain_cli_skill_sidecar"
print(f"<{tag}>")
print(hydrated)
print(f"</{tag}>")
'''


def _install_hermes_provider(hermes_home: Path) -> Path:
    """Install Ingrain's Hermes provider plugin into a per-run hermes_home."""
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


def _make_ingrain_cli_shim(tmp: Path) -> Path:
    """Write a small bash shim that calls `python -m aeonik_ingrain.cli` with
    PYTHONPATH set, then return the bin dir to add to PATH."""
    bin_dir = tmp / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    shim = bin_dir / "ingrain"
    # The aeonik_ingrain package lives N parents up; resolve to its src/ root.
    src_root = Path(__file__).resolve().parents[3]
    shim.write_text(
        "#!/usr/bin/env bash\n"
        f'export PYTHONPATH="{src_root}${{PYTHONPATH:+:$PYTHONPATH}}"\n'
        f'exec "{sys.executable}" -m aeonik_ingrain.cli "$@"\n',
        encoding="utf-8",
    )
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return bin_dir


def _decode_timeout_stream(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _flatten_universe_events(universe: Any) -> list[str]:
    """Flatten a SandboxUniverse into source-prefixed event strings.

    Duplicated from sandbox_universe._hermes.flatten_universe_events so this
    module doesn't take a hard dependency on the import-time availability of
    that helper. The format is load-bearing — keep these two in sync.
    """
    events: list[str] = []
    for doc in universe.source_of_truth:
        events.append(
            f"[source_id={doc.id} kind={doc.kind} created_at={doc.created_at} "
            f"title={doc.title}] {doc.text}"
        )
    for session in universe.sessions:
        for turn in session.turns:
            events.append(
                f"[source_id={turn.id} session={session.id} thread={session.thread} "
                f"actor={turn.actor} kind={turn.kind} turn={turn.turn} "
                f"started_at={session.started_at}] {turn.text}"
            )
    for old, new in universe.supersedes:
        events.append(
            f"[source_id={universe.name}.edge.{old}.to.{new} kind=supersession] "
            f"{old} is superseded_by {new}."
        )
    return events


def _resolve_hermes_runtime(
    hermes_root: str | Path | None = None,
    hermes_python: str | Path | None = None,
) -> tuple[Path, Path, bool]:
    candidates: list[Path] = []
    if hermes_root:
        candidates.append(Path(hermes_root).expanduser())
    if os.environ.get("HERMES_AGENT_ROOT"):
        candidates.append(Path(os.environ["HERMES_AGENT_ROOT"]).expanduser())
    candidates.extend([
        Path.home() / ".hermes" / "hermes-agent",
        Path.home() / "Desktop" / "REPO" / "hermes-agent",
    ])
    root = next((c for c in candidates if c.exists()), candidates[0])
    python = Path(hermes_python).expanduser() if hermes_python else root / "venv" / "bin" / "python"
    return root, python, root.exists() and python.exists()


def _run_via_hermes(
    *,
    universe: Any,
    workdir: Path,
    script: str,
    env_builder,
    before_run=None,
    timeout: int = 240,
):
    """Run one universe through a Hermes subprocess, return a LaneResult-shaped dict.

    Returns a sandbox_universe.lanes.LaneResult — imported lazily here so
    importing this module doesn't require sandbox-universe to be installed.
    """
    from sandbox_universe.lanes import LaneResult  # lazy

    root, python, available = _resolve_hermes_runtime()
    if not available:
        return LaneResult(
            raw_output="",
            provider_error=f"Hermes runtime not found at {root}",
            command_log=[{"hermes_root": str(root), "hermes_python": str(python), "exists": False}],
        )

    with tempfile.TemporaryDirectory(prefix=f"sbu-ingrain-{universe.name}-", dir=str(workdir)) as tmp_name:
        tmp = Path(tmp_name)
        hermes_home = tmp / "hermes" / universe.name
        hermes_home.mkdir(parents=True, exist_ok=True)
        if before_run:
            before_run(hermes_home)
        payload_path = tmp / f"{universe.name}.json"
        payload_path.write_text(
            json.dumps(
                {"name": universe.name, "query": universe.query, "events": _flatten_universe_events(universe)},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env["HERMES_HOME"] = str(hermes_home)
        env.update(env_builder(tmp, universe, hermes_home))
        command = [str(python), "-c", script, str(payload_path)]

        timed_out = False
        timeout_error = ""
        try:
            proc = subprocess.run(
                command,
                cwd=str(root),
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            returncode = proc.returncode
            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            returncode = None
            stdout = _decode_timeout_stream(exc.stdout).strip()
            stderr = _decode_timeout_stream(exc.stderr).strip()
            timeout_error = f"provider subprocess timed out after {timeout}s"

        command_log = [{
            "command": [str(python), "-c", "<script>", str(payload_path)],
            "cwd": str(root),
            "hermes_home": str(hermes_home),
            "returncode": returncode,
            "stdout_chars": len(stdout),
            "stderr": stderr,
            "timed_out": timed_out,
            "timeout_seconds": timeout if timed_out else None,
        }]

        provider_error = timeout_error
        if returncode not in (None, 0) and not provider_error:
            provider_error = stderr or f"subprocess exited {returncode}"

        return LaneResult(
            raw_output=stdout,
            command_log=command_log,
            provider_error=provider_error,
        )


class IngrainLane:
    """LaneAdapter for Ingrain as a Hermes memory provider (uses `memory.provider=ingrain` slot)."""

    name = "ingrain"

    def __init__(self, *, timeout: int = 240) -> None:
        self._timeout = timeout
        root, python, available = _resolve_hermes_runtime()
        self._hermes_root = root
        self._hermes_python = python
        self._available = available

    def probe(self) -> dict[str, Any]:
        if not self._available:
            raise RuntimeError(
                f"Hermes runtime not found at {self._hermes_root}. "
                "Install Hermes Agent or set HERMES_AGENT_ROOT."
            )
        return {
            "installed": True,
            "hermes_root": str(self._hermes_root),
            "hermes_python": str(self._hermes_python),
        }

    def run(self, universe: Any, workdir: Path):
        def env_builder(tmp, _u, _h):
            bin_dir = _make_ingrain_cli_shim(tmp)
            return {"PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"}

        return _run_via_hermes(
            universe=universe,
            workdir=workdir,
            script=INGRAIN_PROVIDER_SCRIPT,
            env_builder=env_builder,
            before_run=_install_hermes_provider,
            timeout=self._timeout,
        )


class IngrainSidecarLane:
    """LaneAdapter for Hermes default memory + Ingrain CLI as a sidecar context layer.

    Uses the deterministic regex compiler (`ingrain compile`). Kept for v0
    parity and as the baseline for the LLM consolidator comparison.
    """

    name = "ingrain-sidecar"
    _use_llm = False

    def __init__(self, *, timeout: int = 240) -> None:
        self._timeout = timeout
        root, python, available = _resolve_hermes_runtime()
        self._hermes_root = root
        self._hermes_python = python
        self._available = available

    def probe(self) -> dict[str, Any]:
        if not self._available:
            raise RuntimeError(
                f"Hermes runtime not found at {self._hermes_root}. "
                "Install Hermes Agent or set HERMES_AGENT_ROOT."
            )
        return {
            "installed": True,
            "hermes_root": str(self._hermes_root),
            "hermes_python": str(self._hermes_python),
            "use_llm_consolidator": self._use_llm,
        }

    def run(self, universe: Any, workdir: Path):
        use_llm = self._use_llm

        def env_builder(tmp, u, hermes_home):
            bin_dir = _make_ingrain_cli_shim(tmp)
            env = {
                "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
                "INGRAIN_HOME": str(hermes_home / "ingrain-sidecar" / u.name),
            }
            if use_llm:
                env["INGRAIN_USE_LLM_CONSOLIDATOR"] = "1"
            return env

        return _run_via_hermes(
            universe=universe,
            workdir=workdir,
            script=INGRAIN_SIDECAR_SCRIPT,
            env_builder=env_builder,
            timeout=self._timeout,
        )


class IngrainLLMSidecarLane(IngrainSidecarLane):
    """Hermes default + Ingrain CLI using the LLM consolidator (no API key).

    Same shape as `ingrain-sidecar`, but `ingrain compile` is replaced by
    `ingrain consolidate`, which uses `hermes -z` to classify events. Whatever
    model Hermes is configured against is the consolidator.
    """

    name = "ingrain-llm-sidecar"
    _use_llm = True


__all__ = [
    "IngrainLane",
    "IngrainSidecarLane",
    "INGRAIN_PROVIDER_SCRIPT",
    "INGRAIN_SIDECAR_SCRIPT",
]
