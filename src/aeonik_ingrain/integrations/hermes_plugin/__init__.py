"""Hermes plugin: auto-record session events + consolidate at session end.

This is the "trigger-based execution" path: install once, then Hermes
automatically records each tool/turn into Ingrain's ledger and runs the
LLM consolidator at session end. No user action required after install.

Layout (when installed at ~/.hermes/plugins/ingrain-auto/):

  ~/.hermes/plugins/ingrain-auto/
    __init__.py        ← this file (copied by `ingrain install hermes-plugin`)
    plugin.yaml        ← name + description manifest

The plugin's register(ctx) wires:

  post_tool_call:    record tool calls and their outputs to the ledger
  on_session_end:    invoke `ingrain consolidate` to promote cards
  /ingrain (slash):  manual query / status / why commands

NOTE: this module imports lazily to keep Hermes startup fast. Ingrain
itself must be installed (`pipx install aeonik-ingrain`) for the plugin
to do anything meaningful. If aeonik_ingrain is not on PATH, the plugin
no-ops with a single warning log entry.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Tracks whether this session has recorded any events yet — used by
# on_session_end to skip the consolidate step on empty sessions.
_session_state: dict[str, dict[str, Any]] = {}
_state_lock = threading.Lock()


def _ingrain_home() -> Path:
    """The directory where Ingrain stores its SQLite ledger.

    Default: ~/.hermes/ingrain/ (sits inside Hermes's home so it survives
    across sessions and is backed up alongside Hermes state).
    """
    hermes_home = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
    home = Path(os.environ.get("INGRAIN_HOME", str(hermes_home / "ingrain")))
    home.mkdir(parents=True, exist_ok=True)
    return home


def _ingrain_binary() -> str | None:
    """Locate the `ingrain` CLI. Returns None if not installed."""
    return shutil.which("ingrain")


def _record_event(session_id: str, text: str, *, actor: str = "user", event_type: str = "interaction") -> None:
    """Record one event into the Ingrain ledger via the CLI.

    Non-blocking: spawned in a background thread so it never delays the
    agent's turn. Errors are logged but never raised.
    """
    binary = _ingrain_binary()
    if not binary or not text:
        return

    def _do() -> None:
        try:
            subprocess.run(
                [
                    binary, "--home", str(_ingrain_home()),
                    "record",
                    "--source", "hermes_plugin",
                    "--runner", "hermes",
                    "--event-type", event_type,
                    "--actor", actor,
                    "--session-id", session_id,
                    text,
                ],
                capture_output=True,
                timeout=10,
            )
        except Exception as exc:  # noqa: BLE001 — never raise into Hermes
            logger.debug(f"ingrain plugin: record failed silently: {exc}")

    threading.Thread(target=_do, daemon=True).start()
    with _state_lock:
        s = _session_state.setdefault(session_id, {"events": 0})
        s["events"] += 1


# -------------------------------------------------------------------------------------------------
# Hermes lifecycle callbacks
# -------------------------------------------------------------------------------------------------


def _on_post_tool_call(*, session_id: str = "default", tool_name: str = "", tool_input: Any = None, tool_result: Any = None, **kwargs: Any) -> None:
    """Record tool invocations as events.

    Skipped for read-only tools that are too noisy to track (ls, read_file).
    """
    NOISY_TOOLS = {"read_file", "list_directory", "ls"}
    if tool_name in NOISY_TOOLS:
        return

    # Build a concise event description
    input_summary = str(tool_input)[:300] if tool_input is not None else ""
    text = f"tool={tool_name} input={input_summary}"
    _record_event(session_id, text, actor="assistant", event_type="action")


def _on_session_end(*, session_id: str = "default", **kwargs: Any) -> None:
    """Consolidate the events recorded this session into learned-experience cards.

    Runs synchronously in the background thread Hermes provides for session-end
    hooks. Logs but never raises. If `ingrain` is not installed or
    consolidation fails, the session simply ends without writing cards
    — the events are still in the ledger for later manual `ingrain consolidate`.
    """
    with _state_lock:
        events = _session_state.get(session_id, {}).get("events", 0)
        _session_state.pop(session_id, None)

    if events == 0:
        return

    binary = _ingrain_binary()
    if not binary:
        logger.info("ingrain plugin: aeonik-ingrain CLI not on PATH; skipping session-end consolidate")
        return

    try:
        subprocess.run(
            [binary, "--home", str(_ingrain_home()), "consolidate", "--limit", "200"],
            capture_output=True,
            timeout=120,
        )
        logger.info(f"ingrain plugin: consolidated session {session_id} ({events} events)")
    except subprocess.TimeoutExpired:
        logger.warning(f"ingrain plugin: consolidate timed out on session {session_id}")
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"ingrain plugin: consolidate failed silently: {exc}")


# -------------------------------------------------------------------------------------------------
# Slash command
# -------------------------------------------------------------------------------------------------


def _handle_slash(args: list[str], **kwargs: Any) -> str:
    """Handle `/ingrain <subcommand>` slash commands.

    Subcommands:
        status                  — show plugin + ledger state
        why <query>             — audit trail for matching cards
        consolidate             — force a consolidation pass now
        hydrate <query>         — print the hydrated context for a query
    """
    binary = _ingrain_binary()
    if not binary:
        return "[ingrain plugin] `ingrain` CLI not installed. Install with `pipx install aeonik-ingrain`."

    if not args:
        return "Usage: /ingrain {status|why <query>|consolidate|hydrate <query>}"

    sub = args[0]
    rest = args[1:]
    cmd: list[str] = [binary, "--home", str(_ingrain_home())]

    if sub == "status":
        cmd += ["report"]
    elif sub == "why":
        if not rest:
            return "Usage: /ingrain why <query>"
        cmd += ["why"] + rest
    elif sub == "consolidate":
        cmd += ["consolidate", "--limit", str(rest[0]) if rest else "200"]
    elif sub == "hydrate":
        if not rest:
            return "Usage: /ingrain hydrate <query>"
        cmd += ["hydrate", "--query", " ".join(rest)]
    else:
        return f"Unknown subcommand: {sub}. Try: status, why, consolidate, hydrate."

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    except subprocess.TimeoutExpired:
        return "[ingrain plugin] timed out."


# -------------------------------------------------------------------------------------------------
# register() — what Hermes calls at plugin load
# -------------------------------------------------------------------------------------------------


def register(ctx: Any) -> None:
    """Wire Ingrain into Hermes via post_tool_call + on_session_end + /ingrain."""
    ctx.register_hook("post_tool_call", _on_post_tool_call)
    ctx.register_hook("on_session_end", _on_session_end)
    ctx.register_command(
        "ingrain",
        handler=_handle_slash,
        description="Ingrain learned-experience layer — auto-consolidate at session end.",
    )


__all__ = ["register", "_on_post_tool_call", "_on_session_end", "_handle_slash"]
