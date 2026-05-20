import unittest

from aeonik_ingrain.evals.les_hard import SCENARIOS as HARD_SCENARIOS
from aeonik_ingrain.evals.les_hard import run_les_hard, score_hard_output
from aeonik_ingrain.evals.live_les import UNIVERSES, format_live_les, score_live_output
from aeonik_ingrain.evals.live_openviking import _candidate_read_uris, format_live_openviking_comparison
from aeonik_ingrain.evals.runner import run_eval
from aeonik_ingrain.evals.sandbox_universe import (
    UNIVERSES as SANDBOX_UNIVERSES,
    build_sandbox_graph,
    format_sandbox_universe_markdown,
    score_sandbox_output,
)


class EvalTests(unittest.TestCase):
    def test_les_eval_scores_full(self):
        result = run_eval()
        self.assertEqual(result["total"], 100)

    def test_les_hard_has_room_to_improve(self):
        result = run_les_hard()
        modes = result["modes"]
        ingrain = modes["Ingrain"]["score"]
        self.assertGreaterEqual(result["scenario_count"], 20)
        self.assertLess(ingrain, modes["Ingrain"]["max"])

    def test_les_hard_abstention_rewards_caution(self):
        scenario = next(item for item in HARD_SCENARIOS if item.name == "missing_evidence_abstention")
        cautious = score_hard_output("No sufficient retained evidence for pricing.", scenario)
        invented = score_hard_output("The approved pricing is $20 per seat.", scenario)
        self.assertGreater(cautious["score"], invented["score"])

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

    def test_live_les_provider_errors_score_zero(self):
        universe = UNIVERSES[0]
        score = score_live_output(
            '{"error": "Failed to reflect: operation not permitted"}',
            universe,
        )
        self.assertEqual(score["score"], 0)
        self.assertIn("Failed to reflect", score["provider_error"])

    def test_live_les_formatter_reports_blocked_providers(self):
        text = format_live_les(
            {
                "name": "Live LES-Core Provider Smoke Eval",
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

    def test_sandbox_universe_has_required_l3_complexity(self):
        l3 = [universe for universe in SANDBOX_UNIVERSES if universe.level == 3]
        self.assertGreaterEqual(len(l3), 5)
        for universe in l3:
            self.assertGreaterEqual(sum(len(session.turns) for session in universe.sessions), 1)
            self.assertGreaterEqual(len(universe.source_of_truth), 2)
            self.assertGreaterEqual(len(universe.expected_sources), 2)
        self.assertGreaterEqual(len([universe for universe in SANDBOX_UNIVERSES if universe.level == 4]), 3)
        self.assertGreaterEqual(len([universe for universe in SANDBOX_UNIVERSES if universe.level == 5]), 2)

    def test_sandbox_score_rewards_traceable_current_truth(self):
        universe = next(item for item in SANDBOX_UNIVERSES if item.name == "launch_claims_conflict_l3")
        good = score_sandbox_output(
            "Use a narrow learned-experience smoke test backed by real provider runs. "
            "Do not claim Ingrain beat Hindsight or OpenViking. "
            "Sources: doc_eval_v2 and session_launch_a.turn_2 from launch-copy. source_id=doc_eval_v2",
            universe,
        )
        stale = score_sandbox_output(
            "Ingrain beats Hindsight and Ingrain beats OpenViking. Source: doc_launch_v1.",
            universe,
        )
        self.assertGreater(good["score"], stale["score"])
        self.assertEqual(good["components"]["forbidden_suppression"], 15)
        self.assertEqual(stale["components"]["forbidden_suppression"], 0)

    def test_sandbox_graph_contains_supersession_edges(self):
        result = {
            "universes": [{"name": "launch_claims_conflict_l3"}],
            "providers": {
                "ingrain": {
                    "score": 72,
                    "universes": [
                        {
                            "universe": "launch_claims_conflict_l3",
                            "score": 72,
                            "raw_output": "raw/ingrain/launch_claims_conflict_l3.txt",
                        }
                    ],
                }
            },
        }
        graph = build_sandbox_graph(result)
        self.assertTrue(any(edge["type"] == "superseded_by" for edge in graph["edges"]))
        self.assertTrue(any(node["type"] == "output" and node["provider"] == "ingrain" for node in graph["nodes"]))

    def test_sandbox_markdown_links_graph_artifacts(self):
        text = format_sandbox_universe_markdown(
            {
                "claim": "test",
                "scoring": {"current_truth": 20},
                "universes": [{"name": "u", "level": 3, "difficulty_reason": "hard"}],
                "providers": {
                    "ingrain": {
                        "status": "partial",
                        "score": 40,
                        "max": 100,
                        "interpretation": "partial",
                        "universes": [{"universe": "u", "level": 3, "score": 40, "max": 100, "components": {}}],
                    }
                },
            }
        )
        self.assertIn("graph.json", text)
        self.assertIn("Three.js", text)
        self.assertIn("Level Breakdown", text)
        self.assertIn("Failure Taxonomy", text)


if __name__ == "__main__":
    unittest.main()
