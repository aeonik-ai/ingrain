import unittest

from aeonik_ingrain.evals.comparison import run_comparison
from aeonik_ingrain.evals.live_openviking import _candidate_read_uris, format_live_openviking_comparison
from aeonik_ingrain.evals.runner import run_eval


class EvalTests(unittest.TestCase):
    def test_les_eval_scores_full(self):
        result = run_eval(include_comparison=False)
        self.assertEqual(result["total"], 100)

    def test_ingrain_beats_retrieval_baselines_on_learned_experience(self):
        result = run_comparison()
        modes = result["modes"]
        self.assertGreater(modes["Hermes + Ingrain"]["score"], modes["Hermes + OpenViking-style retrieval"]["score"])
        self.assertGreater(modes["Hermes + OpenViking-style retrieval"]["score"], modes["Hermes default memory"]["score"])

    def test_live_openviking_uri_candidates_skip_summary_placeholders(self):
        result = {
            "result": {
                "resources": [
                    {"uri": "viking://resources/project/.overview.md"},
                    {"uri": "viking://resources/project/project.md"},
                    {"uri": "viking://resources/project/.abstract.md"},
                ]
            }
        }
        self.assertEqual(_candidate_read_uris(result), ["viking://resources/project/project.md"])

    def test_live_openviking_formatter_reports_score(self):
        text = format_live_openviking_comparison(
            {
                "name": "Live OpenViking Resource Retrieval Comparison",
                "endpoint": "http://127.0.0.1:1933",
                "score": 14,
                "max": 20,
                "scenarios": [{"scenario": "correction_after_failure", "score": 14, "max": 20, "read_uris": []}],
            }
        )
        self.assertIn("Score: 14/20", text)
        self.assertIn("correction_after_failure", text)


if __name__ == "__main__":
    unittest.main()
