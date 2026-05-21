"""Tests for the `ingrain why` audit-trail CLI command.

Uses subprocess to invoke the CLI module so we exercise the full argparse
+ IngrainStore path.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from aeonik_ingrain.db import IngrainStore


def _ingrain(home: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "aeonik_ingrain.cli", "--home", str(home), *args],
        capture_output=True,
        text=True,
    )


class TestIngrainWhy(unittest.TestCase):
    def _make_store(self, home: Path) -> tuple[IngrainStore, str, str]:
        store = IngrainStore(home)
        store.initialize()
        ref = store.add_event(
            source="test", runner="test", event_type="interaction", actor="user",
            text="Do not push to main without running tests.",
        )
        promo_id = store.add_promotion(
            event_id=ref.id,
            promoted_type="correction",
            text="Do not push to main without running tests.",
            confidence=0.95,
            reason="explicit user imperative",
            meta={"source": "hermes_consolidator"},
        )
        return store, ref.id, promo_id

    def test_why_finds_matching_card(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            store, event_id, promo_id = self._make_store(home)
            proc = _ingrain(home, "why", "push to main")
            self.assertEqual(proc.returncode, 0)
            self.assertIn("Found 1 matching card", proc.stdout)
            self.assertIn("correction", proc.stdout)
            self.assertIn(event_id, proc.stdout)
            self.assertIn("explicit user imperative", proc.stdout)
            self.assertIn("hermes_consolidator", proc.stdout)

    def test_why_no_match_returns_helpful_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            store, _, _ = self._make_store(home)
            proc = _ingrain(home, "why", "unrelated banana phrase")
            self.assertEqual(proc.returncode, 0)
            self.assertIn("No cards match", proc.stdout)

    def test_why_no_match_finds_event_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            store = IngrainStore(home)
            store.initialize()
            store.add_event(
                source="test", runner="test", event_type="interaction", actor="user",
                text="The QA team meets on Tuesdays.",
            )
            # No promotion exists, so cards are empty. But the text appears in the event.
            proc = _ingrain(home, "why", "qa team meets")
            self.assertEqual(proc.returncode, 0)
            self.assertIn("No cards match", proc.stdout)
            self.assertIn("but 1 event", proc.stdout.lower())

    def test_why_case_insensitive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self._make_store(home)
            proc = _ingrain(home, "why", "PUSH TO MAIN")
            self.assertIn("Found 1 matching card", proc.stdout)

    def test_why_empty_query_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self._make_store(home)
            # argparse requires at least one positional, so we test with " " instead.
            proc = _ingrain(home, "why", " ")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("non-empty", proc.stderr)


if __name__ == "__main__":
    unittest.main()
