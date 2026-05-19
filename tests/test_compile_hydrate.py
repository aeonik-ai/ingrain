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


if __name__ == "__main__":
    unittest.main()
