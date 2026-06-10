import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from aeonik_ingrain.cli import main
from aeonik_ingrain.compiler.hydrate import hydrate
from aeonik_ingrain.compiler.pages import compile_store
from aeonik_ingrain.db import IngrainStore
from aeonik_ingrain.verify import _redact, format_markdown_receipt, verify_hermes


class VerifyHermesTests(unittest.TestCase):
    def _store_with_card(self, root: Path) -> IngrainStore:
        store = IngrainStore(root / ".ingrain")
        event = store.add_event(
            source="hermes_live",
            runner="hermes",
            event_type="interaction",
            actor="user",
            text="Remember: Ingrain verify tests must cite source-linked cards.",
        )
        store.add_promotion(
            event_id=event.id,
            promoted_type="correction",
            text="Ingrain verify tests must cite source-linked cards.",
            confidence=0.91,
            reason="User correction",
        )
        store.write_compiled_page(
            path="corrections.md",
            title="Corrections",
            page_type="correction",
            content="- Ingrain verify tests must cite source-linked cards.",
            source_event_ids=[event.id],
        )
        return store

    def test_local_verify_reports_package_plugins_store_and_hydrate(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            hermes_home = root / "hermes"
            (hermes_home / "plugins" / "ingrain").mkdir(parents=True)
            (hermes_home / "plugins" / "ingrain" / "__init__.py").write_text("# provider", encoding="utf-8")
            (hermes_home / "plugins" / "ingrain-auto").mkdir(parents=True)
            (hermes_home / "plugins" / "ingrain-auto" / "__init__.py").write_text("# auto", encoding="utf-8")
            (hermes_home / "config.yaml").write_text("memory:\n  provider: ingrain\n", encoding="utf-8")
            store = self._store_with_card(root)

            with mock.patch("aeonik_ingrain.verify.distribution_version", side_effect=lambda name: "0.2.0" if name == "aeonik-ingrain" else None), mock.patch("aeonik_ingrain.verify.shutil.which", return_value="/usr/local/bin/ingrain"):
                result = verify_hermes(hermes_home=hermes_home, ingrain_home=store.home, live=False)

            self.assertTrue(result["ok"])
            self.assertEqual(result["mode"], "provider")
            self.assertEqual(result["ingrain_binary"], "/usr/local/bin/ingrain")
            self.assertTrue(result["package"]["expected_distribution_present"])
            self.assertFalse(result["package"]["wrong_bare_ingrain_distribution_present"])
            self.assertTrue(result["hermes"]["provider_plugin_installed"])
            self.assertTrue(result["hermes"]["auto_plugin_installed"])
            self.assertEqual(result["hermes"]["memory_provider"], "ingrain")
            self.assertEqual(result["store"]["ledger_events"], 1)
            self.assertEqual(result["store"]["promotions"], 1)
            self.assertEqual(result["store"]["compiled_pages"], 1)
            self.assertTrue(result["hydrate"]["ok"])
            self.assertTrue(result["hydrate"]["has_source_ids"])
            self.assertFalse(result["live_recall"]["attempted"])

    def test_local_verify_warns_about_wrong_bare_ingrain_package_and_no_promotions(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = IngrainStore(root / ".ingrain")
            store.add_event(source="hermes_live", runner="hermes", event_type="interaction", text="raw only")

            def fake_version(name: str):
                return {"aeonik-ingrain": "0.2.0", "ingrain": "9.9.9"}.get(name)

            with mock.patch("aeonik_ingrain.verify.distribution_version", side_effect=fake_version):
                result = verify_hermes(hermes_home=root / "hermes", ingrain_home=store.home, live=False)

            self.assertFalse(result["package"]["wrong_bare_ingrain_distribution_present"] is False)
            self.assertEqual(result["hydrate"]["status"], "skipped")
            self.assertIn("Bare `ingrain` distribution is installed", "\n".join(result["warnings"]))
            self.assertIn("Ledger has events but no promotions", "\n".join(result["warnings"]))

    def test_live_verify_uses_real_subprocess_result_and_can_be_blocked(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = self._store_with_card(root)

            def runner(command, timeout):
                return {"exit_code": 0, "stdout": "cobalt otter\n", "stderr": "", "elapsed_seconds": 0.1}

            result = verify_hermes(
                hermes_home=root / "hermes",
                ingrain_home=store.home,
                live=True,
                hermes_bin="/bin/hermes",
                canary="cobalt otter",
                expected="cobalt otter",
                subprocess_runner=runner,
            )
            self.assertTrue(result["live_recall"]["attempted"])
            self.assertEqual(result["live_recall"]["status"], "live")
            self.assertTrue(result["live_recall"]["ok"])
            self.assertIn("hermes", result["live_recall"]["command"][0])

            blocked = verify_hermes(hermes_home=root / "hermes", ingrain_home=store.home, live=True, hermes_bin="")
            self.assertEqual(blocked["live_recall"]["status"], "blocked")
            self.assertFalse(blocked["live_recall"]["ok"])

    def test_live_verify_canary_is_repeatable_after_session_compile(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = IngrainStore(root / ".ingrain")

            def runner(command, timeout):
                context = hydrate(IngrainStore(store.home), query=command[-1], limit=10)
                match = re.search(r"canary phrase: ([^\n\[]+)", context)
                if not match:
                    return {"exit_code": 0, "stdout": "missing canary", "stderr": "", "elapsed_seconds": 0.1}
                phrase = match.group(1).strip()
                compile_store(IngrainStore(store.home))
                return {"exit_code": 0, "stdout": phrase, "stderr": "", "elapsed_seconds": 0.1}

            with mock.patch("aeonik_ingrain.verify.distribution_version", side_effect=lambda name: "0.2.0" if name == "aeonik-ingrain" else None):
                first = verify_hermes(
                    hermes_home=root / "hermes",
                    ingrain_home=store.home,
                    live=True,
                    hermes_bin="/bin/hermes",
                    subprocess_runner=runner,
                )
                second = verify_hermes(
                    hermes_home=root / "hermes",
                    ingrain_home=store.home,
                    live=True,
                    hermes_bin="/bin/hermes",
                    subprocess_runner=runner,
                )

            self.assertEqual(first["live_recall"]["status"], "live")
            self.assertEqual(second["live_recall"]["status"], "live")
            self.assertNotEqual(first["live_recall"]["canary"], second["live_recall"]["canary"])
            verify_cards = [p for p in store.list_promotions() if (p.get("meta") or {}).get("verify_canary")]
            self.assertTrue(verify_cards)
            self.assertTrue(all(card["promoted_type"] == "project_fact" for card in verify_cards))
            self.assertTrue(all("Remember the Ingrain verification canary" not in card["text"] for card in verify_cards))

    def test_cli_verify_hermes_json_and_markdown_receipt(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = self._store_with_card(root)
            receipt = root / "receipt.md"
            json_receipt = root / "receipt.json"
            with mock.patch("sys.stdout") as stdout:
                code = main([
                    "verify",
                    "hermes",
                    "--home",
                    str(store.home),
                    "--hermes-home",
                    str(root / "hermes"),
                    "--json",
                    "--output",
                    str(json_receipt),
                    "--markdown-output",
                    str(receipt),
                ])
            self.assertEqual(code, 0)
            self.assertTrue(receipt.exists())
            self.assertIn("Ingrain Hermes Verification", receipt.read_text(encoding="utf-8"))
            data = json.loads(json_receipt.read_text(encoding="utf-8"))
            self.assertIn("store", data)
            self.assertTrue(stdout.write.called)

    def test_cli_verify_hermes_blocked_exits_nonzero(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch("sys.stdout"):
                code = main([
                    "verify",
                    "hermes",
                    "--home",
                    str(root / ".ingrain"),
                    "--hermes-home",
                    str(root / "hermes"),
                    "--live",
                    "--hermes-bin",
                    "",
                    "--json",
                ])
            self.assertEqual(code, 1)

    def test_local_verify_reports_db_existence_before_touching_store(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "fresh-ingrain"

            with mock.patch("aeonik_ingrain.verify.distribution_version", side_effect=lambda name: "0.2.0" if name == "aeonik-ingrain" else None):
                result = verify_hermes(hermes_home=root / "hermes", ingrain_home=home, live=False)

            self.assertFalse(result["store"]["db_exists_before_verify"])
            self.assertFalse(result["store"]["db_readable_before_verify"])
            self.assertTrue(result["store"]["db_exists_after_verify"])
            self.assertTrue(result["store"]["db_readable"])

    def test_redact_masks_standalone_secret_tokens(self):
        text = _redact("token=abc ghp_ABC123 github_pat_ABC123 sk-proj-abcdef")
        self.assertIn("token=[REDACTED]", text)
        self.assertNotIn("ghp_ABC123", text)
        self.assertNotIn("github_pat_ABC123", text)
        self.assertNotIn("sk-proj-abcdef", text)

    def test_markdown_receipt_mentions_blockers_and_warnings(self):
        result = {
            "ok": False,
            "verdict": "blocked",
            "mode": "none",
            "package": {"expected_distribution_present": False, "wrong_bare_ingrain_distribution_present": True},
            "hermes": {"provider_plugin_installed": False, "auto_plugin_installed": False, "memory_provider": None},
            "store": {"home": "/tmp/ingrain", "ledger_events": 0, "promotions": 0, "compiled_pages": 0},
            "hydrate": {"status": "skipped", "ok": False},
            "live_recall": {"attempted": True, "status": "blocked", "ok": False, "blocker": "Hermes binary not found"},
            "warnings": ["Bare `ingrain` distribution is installed"],
        }
        md = format_markdown_receipt(result)
        self.assertIn("blocked", md)
        self.assertIn("Hermes binary not found", md)
        self.assertIn("pip install aeonik-ingrain", md)


if __name__ == "__main__":
    unittest.main()
