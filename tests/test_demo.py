import unittest

from aeonik_ingrain.demo import run_demo


class DemoTests(unittest.TestCase):
    def test_correction_demo_runs(self):
        output = run_demo("correction")
        self.assertIn("Do not call this a memory layer", output)
        self.assertIn("learned experience layer for autonomous agents", output)
        self.assertIn("<aeonik_ingrain_context>", output)

    def test_banana_demo_runs(self):
        output = run_demo("banana")
        self.assertIn("bananas", output)
        self.assertIn("Never ship bananas", output)


if __name__ == "__main__":
    unittest.main()
