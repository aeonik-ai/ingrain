# Live LES-100 Provider Eval

## Hypothesis

A learned-experience layer should return the current lesson from prior runs, suppress stale claims, and keep the recall compact enough to inject into a runner agent.

## Method

| Control | Implementation |
|---|---|
| Preregistered universes | Five universes are defined in `src/aeonik_ingrain/evals/live_les.py` before providers run. |
| Same input per provider | Every provider receives the same event list and query for each universe. |
| Real provider APIs | Hermes default uses `tools.memory_tool.MemoryStore`; Ingrain loads through Hermes `plugins.memory.load_memory_provider('ingrain')`. |
| Raw output audit | Each provider output is saved under `raw/<provider>/<universe>.txt`. |
| Command audit | Each subprocess command log is saved under `commands/<provider>/<universe>.json`. |
| No modeled providers | Hindsight and OpenViking are scored only when a real package/service/server is available. |

## Environment

| Field | Value |
|---|---|
| Hermes root | `/Users/benlloyd/.hermes/hermes-agent` |
| Hermes python | `/Users/benlloyd/.hermes/hermes-agent/venv/bin/python` |
| Hermes available | `True` |
| Hindsight env present | `False` |
| OpenViking endpoint | `http://127.0.0.1:1933` |

## Results

| Provider | Status | Score | Notes |
|---|---|---:|---|
| hermes-default | fail | 88/100 | threshold 90/100 |
| ingrain | pass | 100/100 | threshold 90/100 |
| hindsight | blocked |  | Hindsight is not available: no usable Hindsight package/service/API key was detected by the Hermes provider. |
| openviking | blocked |  | OpenViking health check failed at http://127.0.0.1:1933; start a real server or set OPENVIKING_ENDPOINT. |

## Universe Breakdown

| Universe | Difficulty | Rationale | Scores |
|---|---:|---|---|
| `launch_framing_correction` | 1 | A user correction should become future launch-writing practice, not raw stale copy. | hermes-default=16/20; ingrain=20/20; hindsight=blocked; openviking=blocked |
| `product_rename_supersession` | 2 | The current decision must win over an older product-name decision. | hermes-default=16/20; ingrain=20/20; hindsight=blocked; openviking=blocked |
| `goals_missions_boundary` | 3 | Memory must improve judgment without becoming a second task system. | hermes-default=20/20; ingrain=20/20; hindsight=blocked; openviking=blocked |
| `sandbox_recovery` | 4 | A prior execution failure should alter the next attempt. | hermes-default=20/20; ingrain=20/20; hindsight=blocked; openviking=blocked |
| `launch_claim_safety` | 5 | Launch memory should prevent overclaiming against adjacent systems. | hermes-default=16/20; ingrain=20/20; hindsight=blocked; openviking=blocked |

## Scoring Rubric

Each universe is worth 20 points: expected lesson recall 14, forbidden stale claim suppression 4, compact non-empty output 2. The provider passes when total score is at least 90/100 and no provider subprocess fails.

## Interpretation

This proves a narrow launch claim: Ingrain's Hermes provider improves learned-experience carry-forward on these local universes. It does not prove that Ingrain is a better general-purpose memory backend than Hindsight, OpenViking, or any other provider.

## Artifacts

- Artifact directory: `/Users/benlloyd/Desktop/REPO/ingrain/docs/evidence/live-les-provider-matrix`
- Machine-readable results: `results.json` and `results.csv`
- Raw provider outputs: `raw/`
- Command logs: `commands/`
