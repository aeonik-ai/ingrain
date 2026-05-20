import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from aeonik_ingrain.compiler.hydrate import hydrate
from aeonik_ingrain.compiler.pages import compile_store
from aeonik_ingrain.db import IngrainStore


class CompileHydrateTests(unittest.TestCase):
    def test_correction_carries_forward(self):
        with TemporaryDirectory() as tmp:
            store = IngrainStore(Path(tmp) / ".ingrain")
            store.add_event(
                source="test",
                runner="hermes",
                event_type="interaction",
                actor="user",
                text="Remember: Do not announce unapproved features as shipped.",
            )
            compile_store(store)
            context = hydrate(store, query="draft launch copy")
            self.assertIn("unapproved features", context)
            self.assertIn("Background learned experience", context)

    def test_stale_product_name_is_superseded(self):
        with TemporaryDirectory() as tmp:
            store = IngrainStore(Path(tmp) / ".ingrain")
            store.add_event(source="test", runner="hermes", event_type="interaction", text="Decision: The product name is MindCompiler.")
            store.add_event(source="test", runner="hermes", event_type="interaction", text="Decision: Product name is Aeonik Ingrain, not MindCompiler.")
            compile_store(store)
            context = hydrate(store, query="what is the product name")
            self.assertIn("Product name is Aeonik Ingrain", context)
            self.assertNotIn("The product name is MindCompiler", context)

    def test_stale_plan_phrase_does_not_create_extra_plan_promotion(self):
        with TemporaryDirectory() as tmp:
            store = IngrainStore(Path(tmp) / ".ingrain")
            store.add_event(
                source="test",
                runner="hermes",
                event_type="interaction",
                text=(
                    "Decision: Ingrain owns learned experience only: corrections, decisions, "
                    "lessons, stale-plan warnings, completed outcomes, prior failures, and "
                    "project rules learned from execution."
                ),
            )
            compile_store(store)
            promotions = store.list_promotions()
            self.assertEqual(len(promotions), 1)
            self.assertIn("stale-plan warnings", promotions[0]["text"])

    def test_source_of_truth_trace_promotes_without_magic_phrase(self):
        with TemporaryDirectory() as tmp:
            store = IngrainStore(Path(tmp) / ".ingrain")
            store.add_event(
                source="test",
                runner="hermes",
                event_type="interaction",
                text=(
                    "[source_id=doc_boundary kind=source_of_truth created_at=2026-05-19T08:30:00Z] "
                    "Hermes owns active goals, missions, Kanban columns, scheduling, task lifecycle, "
                    "and what the agent should do next. Ingrain owns learned experience only."
                ),
            )
            compile_store(store)
            context = hydrate(store, query="Should the memory layer move cards?")
            self.assertIn("Hermes owns active goals", context)
            self.assertIn("source_id=doc_boundary", context)

    def test_supersession_edge_removes_stale_trace_document(self):
        with TemporaryDirectory() as tmp:
            store = IngrainStore(Path(tmp) / ".ingrain")
            store.add_event(
                source="test",
                runner="hermes",
                event_type="interaction",
                text=(
                    "[source_id=doc_openviking_old kind=run_log created_at=2026-05-19T04:40:00Z] "
                    "OpenViking is blocked because no healthy server is reachable."
                ),
            )
            store.add_event(
                source="test",
                runner="hermes",
                event_type="interaction",
                text=(
                    "[source_id=doc_openviking_current kind=run_log created_at=2026-05-19T21:55:00Z] "
                    "OpenViking is now healthy locally; report provider and direct resource lanes separately."
                ),
            )
            store.add_event(
                source="test",
                runner="hermes",
                event_type="interaction",
                text="[source_id=provider.edge kind=supersession] doc_openviking_old is superseded_by doc_openviking_current.",
            )
            compile_store(store)
            context = hydrate(store, query="OpenViking provider status")
            self.assertIn("OpenViking is now healthy locally", context)
            self.assertIn("source_id=doc_openviking_current", context)
            self.assertNotIn("no healthy server is reachable", context)


if __name__ == "__main__":
    unittest.main()
