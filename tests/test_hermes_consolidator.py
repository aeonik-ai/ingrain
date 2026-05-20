"""Tests for the Hermes-backed consolidator.

The consolidator shells out to the local `hermes -z` binary. To keep tests
hermetic (no real Hermes / model dependency), we exercise `parse_cards`
(pure function) with a battery of fixture outputs and use a stub binary for
end-to-end tests.
"""

from __future__ import annotations

import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from aeonik_ingrain.db import IngrainStore
from aeonik_ingrain.integrations.hermes_consolidator import (
    ConsolidationResult,
    consolidate,
    parse_cards,
)


GOOD_OUTPUT = """\
```json
[
  {
    "event_id": "evt_aaa",
    "type": "correction",
    "text": "Do not push without running tests.",
    "confidence": 0.95,
    "reason": "explicit imperative",
    "supersedes": null
  }
]
```
"""

BARE_JSON = """\
[
  {"event_id": "evt_bbb", "type": "decision", "text": "Use Postgres.", "confidence": 0.9, "reason": "explicit"}
]
"""

WITH_PREAMBLE = """\
Sure, here are the cards:

```json
[
  {"event_id": "evt_ccc", "type": "lesson", "text": "Always run `make test` first.", "confidence": 0.85, "reason": "outcome"}
]
```

Let me know if you need anything else.
"""

EMPTY_ARRAY = "```json\n[]\n```"
MALFORMED = "I'm not sure what to promote, sorry."
NOT_AN_ARRAY = '```json\n{"oops": true}\n```'


class TestParseCards(unittest.TestCase):
    def test_well_formed_fenced_json(self) -> None:
        cards, err = parse_cards(GOOD_OUTPUT)
        self.assertEqual(err, "")
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["type"], "correction")

    def test_bare_json_array(self) -> None:
        cards, err = parse_cards(BARE_JSON)
        self.assertEqual(err, "")
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["text"], "Use Postgres.")

    def test_extracts_from_preamble_and_postamble(self) -> None:
        cards, err = parse_cards(WITH_PREAMBLE)
        self.assertEqual(err, "")
        self.assertEqual(len(cards), 1)

    def test_empty_array_is_ok(self) -> None:
        cards, err = parse_cards(EMPTY_ARRAY)
        self.assertEqual(err, "")
        self.assertEqual(cards, [])

    def test_no_json_in_output_returns_error(self) -> None:
        cards, err = parse_cards(MALFORMED)
        self.assertNotEqual(err, "")
        self.assertEqual(cards, [])

    def test_object_instead_of_array_returns_error(self) -> None:
        cards, err = parse_cards(NOT_AN_ARRAY)
        self.assertNotEqual(err, "")

    def test_empty_string_returns_error(self) -> None:
        cards, err = parse_cards("")
        self.assertNotEqual(err, "")

    def test_invalid_json_returns_error(self) -> None:
        cards, err = parse_cards("```json\n[{not valid json]\n```")
        self.assertNotEqual(err, "")

    def test_cards_missing_required_fields_are_dropped(self) -> None:
        # 'event_id' missing on the second entry
        text = '[{"event_id":"e1","type":"correction","text":"hi"},{"type":"correction","text":"hi"}]'
        cards, err = parse_cards(text)
        self.assertEqual(err, "")
        self.assertEqual(len(cards), 1)


class TestConsolidateWithStubHermes(unittest.TestCase):
    """End-to-end consolidate() with a stub `hermes` binary that prints a canned response."""

    def _make_stub(self, tmpdir: Path, response: str) -> Path:
        bin_dir = tmpdir / "bin"
        bin_dir.mkdir()
        stub = bin_dir / "hermes"
        # Print the fixture verbatim, regardless of arguments.
        # Use a heredoc inside the shell script for safety.
        body = "#!/usr/bin/env bash\ncat <<'STUB_EOF'\n" + response + "\nSTUB_EOF\n"
        stub.write_text(body, encoding="utf-8")
        stub.chmod(stub.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return stub

    def _make_store(self, tmpdir: Path) -> IngrainStore:
        store = IngrainStore(tmpdir / "ingrain")
        store.initialize()
        store.add_event(
            source="test", runner="test", event_type="interaction", actor="user",
            text="Do not deploy on Friday afternoons.",
        )
        store.add_event(
            source="test", runner="test", event_type="interaction", actor="assistant",
            text="The key is to be flexible.",  # generic chitchat, should be dropped
        )
        return store

    def test_consolidator_writes_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            store = self._make_store(tmp)
            # We need to get an actual event_id from the ledger to put in the stub response.
            events = store.list_events()
            evt_id = events[0]["id"]
            cards = [{
                "event_id": evt_id,
                "type": "correction",
                "text": "Do not deploy on Friday afternoons.",
                "confidence": 0.93,
                "reason": "explicit imperative",
                "supersedes": None,
            }]
            response = "```json\n" + json.dumps(cards) + "\n```"
            stub = self._make_stub(tmp, response)

            result = consolidate(store, hermes_binary=str(stub), limit=10)
            self.assertEqual(result.parse_error, "")
            self.assertEqual(result.cards_emitted, 1)
            promotions = store.list_promotions(state="current")
            self.assertEqual(len(promotions), 1)
            self.assertEqual(promotions[0]["promoted_type"], "correction")

    def test_consolidator_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            store = self._make_store(tmp)
            evt_id = store.list_events()[0]["id"]
            response = "```json\n" + json.dumps([{
                "event_id": evt_id, "type": "correction", "text": "x",
                "confidence": 0.9, "reason": "x",
            }]) + "\n```"
            stub = self._make_stub(tmp, response)

            result = consolidate(store, hermes_binary=str(stub), limit=10, dry_run=True)
            self.assertEqual(result.cards_emitted, 1)  # would have emitted
            self.assertEqual(len(store.list_promotions(state="current")), 0)  # but didn't

    def test_consolidator_drops_cards_with_unknown_event_id(self) -> None:
        # Defensive: Hermes might hallucinate event IDs. We only persist cards
        # whose event_id is in the actual ledger batch.
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            store = self._make_store(tmp)
            response = (
                '```json\n[{"event_id":"evt_hallucinated","type":"correction",'
                '"text":"fake","confidence":0.9,"reason":"made up"}]\n```'
            )
            stub = self._make_stub(tmp, response)

            result = consolidate(store, hermes_binary=str(stub), limit=10)
            self.assertEqual(result.cards_emitted, 0)
            self.assertEqual(len(store.list_promotions(state="current")), 0)

    def test_consolidator_handles_empty_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            store = IngrainStore(tmp / "empty")
            store.initialize()

            # No stub needed — consolidate short-circuits on empty events.
            result = consolidate(store, hermes_binary="/nonexistent/hermes")
            self.assertEqual(result.events_considered, 0)
            self.assertEqual(result.cards_emitted, 0)
            self.assertEqual(result.parse_error, "")

    def test_consolidator_reports_missing_hermes_binary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            store = self._make_store(tmp)
            result = consolidate(store, hermes_binary="/definitely/not/a/binary")
            self.assertEqual(result.cards_emitted, 0)
            self.assertIn("hermes binary", result.parse_error)


if __name__ == "__main__":
    unittest.main()
