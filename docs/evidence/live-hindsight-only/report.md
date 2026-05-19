# Live LES-Core Provider Smoke Eval

## Hypothesis

A learned-experience layer should return the current lesson from prior runs, suppress stale claims, and keep the recall compact enough to inject into a runner agent. This is a provider smoke test, not an external memory benchmark.

## Method

| Control | Implementation |
|---|---|
| Preregistered universes | Five smoke-test universes are defined in `src/aeonik_ingrain/evals/live_les.py` before providers run. |
| Same input per provider | Every provider receives the same event list and query for each universe. |
| Real provider APIs | Hermes default uses `tools.memory_tool.MemoryStore`; Ingrain loads through Hermes `plugins.memory.load_memory_provider('ingrain')`. |
| Raw output audit | Each provider output is saved under `raw/<provider>/<universe>.txt`. |
| Command audit | Each subprocess command log is saved under `commands/<provider>/<universe>.json`. |
| No simulated provider rows | Hindsight and OpenViking are scored only when a real package/service/server is available. |

## Environment

| Field | Value |
|---|---|
| Hermes root | `/Users/benlloyd/.hermes/hermes-agent` |
| Hermes python | `/Users/benlloyd/.hermes/hermes-agent/venv/bin/python` |
| Hermes available | `True` |
| Hindsight env present | `True` |
| OpenViking endpoint | `http://127.0.0.1:1933` |

## Results

| Provider | Status | Score | Notes |
|---|---|---:|---|
| hindsight | fail | 0/100 | threshold 90/100; first failure: provider subprocess timed out after 25s |

## Universe Breakdown

| Universe | Difficulty | Rationale | Scores |
|---|---:|---|---|
| `launch_framing_correction` | 1 | A user correction should become future launch-writing practice, not raw stale copy. | hindsight=0/20 |
| `product_rename_supersession` | 2 | The current decision must win over an older product-name decision. | hindsight=0/20 |
| `goals_missions_boundary` | 3 | Memory must improve judgment without becoming a second task system. | hindsight=0/20 |
| `sandbox_recovery` | 4 | A prior execution failure should alter the next attempt. | hindsight=0/20 |
| `launch_claim_safety` | 5 | Launch memory should prevent overclaiming against adjacent systems. | hindsight=0/20 |

## Scoring Rubric

Each universe is worth 20 points: expected lesson recall 14, forbidden stale claim suppression 4, compact non-empty output 2. The provider passes when total score is at least 90/100 and no provider subprocess fails.

## Interpretation

On these preregistered local smoke-test universes, this run can support only the narrow claim that a provider carried forward the expected learned-experience snippets. It does not show that Ingrain is a better general-purpose memory backend than Hindsight, OpenViking, or any other provider. A 100/100 here means the provider passed this small regression gate; it is not a public SOTA claim.

## Artifacts

- Artifact directory: `/Users/benlloyd/Desktop/REPO/ingrain/docs/evidence/live-hindsight-only`
- Machine-readable results: `results.json` and `results.csv`
- Raw provider outputs: `raw/`
- Command logs: `commands/`
