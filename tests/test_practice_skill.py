import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from aeonik_ingrain.cli import main
from aeonik_ingrain.compiler.hydrate import hydrate
from aeonik_ingrain.compiler.pages import compile_store
from aeonik_ingrain.db import IngrainStore
from aeonik_ingrain.practice import write_practice_artifacts
from aeonik_ingrain.skills import install_skill, render_skill


class PracticeSkillTests(unittest.TestCase):
    def test_practice_artifacts_include_cards_and_boundary(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = IngrainStore(root / ".ingrain")
            store.add_event(
                source="test",
                runner="codex",
                event_type="interaction",
                text="Remember: Do not call Ingrain a vector database.",
            )
            compile_store(store)
            result = write_practice_artifacts(store, output_path=root / "PRACTICE.md")
            practice = Path(result["practice_path"]).read_text(encoding="utf-8")
            self.assertIn("not a task list", practice)
            self.assertIn("L0 Practice Brief", practice)
            self.assertEqual(result["card_count"], 1)
            self.assertTrue(any((store.practice_cards_dir).glob("*.md")))

    def test_tiered_hydration_levels(self):
        with TemporaryDirectory() as tmp:
            store = IngrainStore(Path(tmp) / ".ingrain")
            store.add_event(
                source="test",
                runner="codex",
                event_type="interaction",
                text="Decision: Product name is Aeonik Ingrain.",
            )
            compile_store(store)
            brief = hydrate(store, query="launch", level="brief")
            evidence = hydrate(store, query="launch", level="evidence")
            self.assertIn("<aeonik_ingrain_brief>", brief)
            self.assertIn("confidence:", evidence)

    def test_skill_template_installs(self):
        with TemporaryDirectory() as tmp:
            target = install_skill("codex", target_dir=Path(tmp))
            text = target.read_text(encoding="utf-8")
            self.assertIn("name: ingrain", text)
            self.assertIn("ingrain hydrate", text)
            self.assertIn("active intent", text)

    def test_cursor_skill_template_is_rule(self):
        text = render_skill("cursor")
        self.assertIn("alwaysApply", text)
        self.assertIn("ingrain remember", text)

    def test_cli_attach_writes_practice_and_skill(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / ".ingrain"
            with redirect_stdout(StringIO()):
                code = main([
                    "--home",
                    str(home),
                    "remember",
                    "--type",
                    "decision",
                    "Decision: Product name is Aeonik Ingrain.",
                ])
            self.assertEqual(code, 0)
            with redirect_stdout(StringIO()):
                code = main([
                    "--home",
                    str(home),
                    "attach",
                    "--agent",
                    "codex",
                    "--target-dir",
                    str(root / "skill"),
                    "--practice-path",
                    str(root / "PRACTICE.md"),
                ])
            self.assertEqual(code, 0)
            self.assertTrue((root / "PRACTICE.md").exists())
            self.assertTrue((root / "skill" / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
