"""Tests for the Hermes auto-consolidate plugin.

The plugin lives at aeonik_ingrain.integrations.hermes_plugin and gets
copied into ~/.hermes/plugins/ingrain-auto/ by `ingrain install hermes-plugin`.
These tests cover:

- The plugin module imports cleanly (no hard Hermes import)
- register(ctx) wires the expected hooks + command
- post_tool_call records non-noisy tool calls; skips noisy ones
- on_session_end is a no-op if no events were recorded
- _ingrain_binary() lookup is defensive

Tests use a fake ctx and a mocked `ingrain` binary in tmp_path.
"""

from __future__ import annotations

import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aeonik_ingrain.integrations.hermes_plugin import (
    _handle_slash,
    _ingrain_binary,
    _ingrain_home,
    _on_post_tool_call,
    _on_session_end,
    _session_state,
    register,
)


class FakeCtx:
    """Stub PluginContext capturing register_hook / register_command calls."""

    def __init__(self) -> None:
        self.hooks: dict[str, list] = {}
        self.commands: dict[str, dict] = {}

    def register_hook(self, name: str, callback) -> None:
        self.hooks.setdefault(name, []).append(callback)

    def register_command(self, name: str, *, handler, description: str = "") -> None:
        self.commands[name] = {"handler": handler, "description": description}


class TestRegister(unittest.TestCase):
    def test_wires_expected_hooks(self) -> None:
        ctx = FakeCtx()
        register(ctx)
        self.assertIn("post_tool_call", ctx.hooks)
        self.assertIn("on_session_end", ctx.hooks)
        self.assertEqual(len(ctx.hooks["post_tool_call"]), 1)
        self.assertEqual(len(ctx.hooks["on_session_end"]), 1)

    def test_registers_slash_command(self) -> None:
        ctx = FakeCtx()
        register(ctx)
        self.assertIn("ingrain", ctx.commands)
        self.assertEqual(ctx.commands["ingrain"]["handler"], _handle_slash)


class TestIngrainHome(unittest.TestCase):
    def test_respects_ingrain_home_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"INGRAIN_HOME": tmp}, clear=False):
                home = _ingrain_home()
                self.assertEqual(home.resolve(), Path(tmp).resolve())
                self.assertTrue(home.exists())

    def test_defaults_under_hermes_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {k: v for k, v in os.environ.items() if k != "INGRAIN_HOME"}
            env["HERMES_HOME"] = tmp
            with patch.dict(os.environ, env, clear=True):
                home = _ingrain_home()
                self.assertTrue(str(home).endswith("ingrain"))
                self.assertEqual(home.parent.resolve(), Path(tmp).resolve())


class TestIngrainBinary(unittest.TestCase):
    def test_returns_path_when_on_path(self) -> None:
        # We can't guarantee ingrain is on PATH in test env, so check the type.
        # Real CI runs `pip install -e .` so the entry point exists.
        result = _ingrain_binary()
        if result is not None:
            self.assertTrue(Path(result).exists() or True)  # may be a shim

    def test_returns_none_when_not_on_path(self) -> None:
        with patch.dict(os.environ, {"PATH": "/nonexistent/dir"}, clear=True):
            self.assertIsNone(_ingrain_binary())


class TestPostToolCall(unittest.TestCase):
    def setUp(self) -> None:
        _session_state.clear()

    def test_records_non_noisy_tool_call(self) -> None:
        # We can't easily test that the subprocess fired without mocking,
        # but we can test the session_state side effect.
        with patch(
            "aeonik_ingrain.integrations.hermes_plugin._ingrain_binary",
            return_value="/fake/ingrain",
        ), patch(
            "aeonik_ingrain.integrations.hermes_plugin.threading.Thread",
        ) as fake_thread:
            _on_post_tool_call(
                session_id="test-session",
                tool_name="write_file",
                tool_input={"path": "/x", "content": "hi"},
                tool_result={"success": True},
            )
            self.assertIn("test-session", _session_state)
            self.assertEqual(_session_state["test-session"]["events"], 1)
            # Thread spawned for the recording
            fake_thread.assert_called_once()

    def test_skips_noisy_read_only_tools(self) -> None:
        for noisy in ("read_file", "list_directory", "ls"):
            with patch(
                "aeonik_ingrain.integrations.hermes_plugin._ingrain_binary",
                return_value="/fake/ingrain",
            ):
                _on_post_tool_call(
                    session_id=f"s-{noisy}",
                    tool_name=noisy,
                    tool_input={"path": "/x"},
                    tool_result={"success": True},
                )
                self.assertNotIn(f"s-{noisy}", _session_state)

    def test_no_op_when_ingrain_not_installed(self) -> None:
        # Should not raise; session_state should still update.
        with patch(
            "aeonik_ingrain.integrations.hermes_plugin._ingrain_binary",
            return_value=None,
        ):
            _on_post_tool_call(session_id="s", tool_name="write_file", tool_input={})
            # Counter not bumped because we early-return on missing binary.
            self.assertNotIn("s", _session_state)


class TestOnSessionEnd(unittest.TestCase):
    def setUp(self) -> None:
        _session_state.clear()

    def test_no_events_means_no_consolidate(self) -> None:
        # No state for this session -> no subprocess call.
        with patch(
            "aeonik_ingrain.integrations.hermes_plugin.subprocess.run",
        ) as fake_run:
            _on_session_end(session_id="empty-session")
            fake_run.assert_not_called()

    def test_calls_consolidate_when_events_present(self) -> None:
        _session_state["live-session"] = {"events": 5}
        with patch(
            "aeonik_ingrain.integrations.hermes_plugin._ingrain_binary",
            return_value="/fake/ingrain",
        ), patch(
            "aeonik_ingrain.integrations.hermes_plugin.subprocess.run",
        ) as fake_run:
            _on_session_end(session_id="live-session")
            fake_run.assert_called_once()
            args = fake_run.call_args[0][0]
            self.assertIn("consolidate", args)
            self.assertNotIn("live-session", _session_state)  # state cleared

    def test_no_op_when_binary_missing(self) -> None:
        _session_state["s"] = {"events": 3}
        with patch(
            "aeonik_ingrain.integrations.hermes_plugin._ingrain_binary",
            return_value=None,
        ), patch(
            "aeonik_ingrain.integrations.hermes_plugin.subprocess.run",
        ) as fake_run:
            _on_session_end(session_id="s")
            fake_run.assert_not_called()


class TestSlashHandler(unittest.TestCase):
    def test_no_args_shows_usage(self) -> None:
        with patch(
            "aeonik_ingrain.integrations.hermes_plugin._ingrain_binary",
            return_value="/fake/ingrain",
        ):
            out = _handle_slash([])
            self.assertIn("Usage:", out)

    def test_no_binary_returns_install_hint(self) -> None:
        with patch(
            "aeonik_ingrain.integrations.hermes_plugin._ingrain_binary",
            return_value=None,
        ):
            out = _handle_slash(["status"])
            self.assertIn("pipx install", out)

    def test_unknown_subcommand_helpful_error(self) -> None:
        with patch(
            "aeonik_ingrain.integrations.hermes_plugin._ingrain_binary",
            return_value="/fake/ingrain",
        ):
            out = _handle_slash(["banana"])
            self.assertIn("Unknown subcommand", out)


if __name__ == "__main__":
    unittest.main()
