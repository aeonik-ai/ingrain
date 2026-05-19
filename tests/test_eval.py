import unittest

from aeonik_ingrain.evals.comparison import run_comparison
from aeonik_ingrain.evals.live_les import UNIVERSES, format_live_les, score_live_output
from aeonik_ingrain.evals.live_openviking import _candidate_read_uris, format_live_openviking_comparison
from aeonik_ingrain.evals.runner import run_eval


class EvalTests(unittest.TestCase):
    def test_les_eval_scores_full(self):
        result = run_eval(include_comparison=False)
        self.assertEqual(result["total"], 100)

    def test_ingrain_scores_higher_on_learned_experience_fixtures(self):
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

    def test_live_les_score_rewards_current_lesson_and_blocks_stale_claim(self):
        universe = UNIVERSES[0]
        score = score_live_output(
            "Call it a learned experience layer for autonomous agents.",
            universe,
        )
        self.assertEqual(score["score"], 20)

        stale = score_live_output(
            "Aeonik Ingrain is a generic memory backend for Hermes.",
            universe,
        )
        self.assertLess(stale["score"], score["score"])

    def test_live_les_formatter_reports_blocked_providers(self):
        text = format_live_les(
            {
                "name": "Live LES-100 Provider Eval",
                "claim": "test",
                "score_threshold": 90,
                "max_total": 100,
                "environment": {
                    "hermes_root": "/tmp/hermes",
                    "hermes_python": "/tmp/hermes/venv/bin/python",
                    "hermes_available": False,
                    "openviking_endpoint": "http://127.0.0.1:1933",
                    "hindsight_env_present": False,
                },
                "providers": {
                    "hindsight": {
                        "status": "blocked",
                        "blocked_reason": "no credentials",
                    }
                },
                "universes": [{"name": "u1"}],
                "artifact_dir": "/tmp/out",
            }
        )
        self.assertIn("hindsight: blocked", text)
        self.assertIn("no credentials", text)


if __name__ == "__main__":
    unittest.main()
