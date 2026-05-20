# Sandbox Universe Eval v0

## Hypothesis

Can the provider survive messy multi-session work history without leaking stale or invalid learned experience?

This benchmark is intentionally hard. A 60-70/100 score on L3 is expected to be strong; a perfect score should trigger benchmark-hardening before it becomes a public headline.

## Method

| Control | Implementation |
|---|---|
| Structured traces | Universes contain source docs, sessions, threads, turns, corrections, run logs, and supersession edges. |
| Same input per provider | Every provider receives the same flattened trace with source IDs preserved. |
| Inspectable scoring | Components are deterministic: current truth, precedence, continuity, forbidden suppression, actionability, source traceability, compactness, abstention, and diagram data. |
| Raw output audit | Provider outputs are saved under `raw/<provider>/<universe>.txt`. |
| Command audit | Provider subprocess logs are saved under `commands/<provider>/<universe>.json`. |
| Graph audit | `graph.json` and `graph.mmd` show the trace and provider output nodes. |

## Results

| Provider | Status | Score | Notes |
|---|---|---:|---|
| hermes-default | strong | 623/1000 | Strong result for a hard trace-level universe eval. |
| ingrain-sidecar | strong | 673/1000 | Strong result for a hard trace-level universe eval. |
| ingrain | strong | 673/1000 | Strong result for a hard trace-level universe eval. |
| hindsight | partial | 405/1000 | Useful partial learned experience, with visible trace failures. |
| openviking | weak | 245/1000 | Retrieval exists, but judgment over messy traces is weak. |

## Level Breakdown

| Provider | L3 | L4 | L5 |
|---|---:|---:|---:|
| hermes-default | 275/500 | 238/300 | 110/200 |
| ingrain-sidecar | 361/500 | 177/300 | 135/200 |
| ingrain | 361/500 | 177/300 | 135/200 |
| hindsight | 248/500 | 112/300 | 45/200 |
| openviking | 125/500 | 75/300 | 45/200 |

## Failure Taxonomy

| Provider | Forbidden Leaks | Missing Current Truth | Missing Source Trace | Provider Errors |
|---|---:|---:|---:|---:|
| hermes-default | 8 | 1 | 0 | 0 |
| ingrain-sidecar | 0 | 7 | 7 | 0 |
| ingrain | 0 | 7 | 7 | 0 |
| hindsight | 2 | 8 | 10 | 0 |
| openviking | 0 | 10 | 10 | 0 |

## Universe Breakdown

| Universe | Level | Why It Is Hard | Scores |
|---|---:|---|---|
| `launch_claims_conflict_l3` | 3 | The latest correction overrides an older launch draft while the source docs still contain stale comparative phrasing. | hermes-default=55/100; ingrain-sidecar=90/100; ingrain=90/100; hindsight=53/100; openviking=25/100 |
| `provider_setup_recovery_l3` | 3 | Older setup failures remain useful history, but the current OpenViking server is healthy and should not be reported as blocked. | hermes-default=55/100; ingrain-sidecar=69/100; ingrain=69/100; hindsight=66/100; openviking=25/100 |
| `goals_missions_kanban_l3` | 3 | The trace contains an old plan that looks actionable, but active intent belongs to Hermes, not Ingrain. | hermes-default=55/100; ingrain-sidecar=54/100; ingrain=54/100; hindsight=48/100; openviking=25/100 |
| `rename_namespace_collision_l3` | 3 | Multiple Aeonik memory projects share vocabulary; the provider must keep Ingrain separate from Aeonik MIND and old MindCompiler names. | hermes-default=55/100; ingrain-sidecar=82/100; ingrain=82/100; hindsight=56/100; openviking=25/100 |
| `source_truth_vs_chat_l3` | 3 | A chat correction, a docs page, and a later run log disagree; the provider must preserve uncertainty and cite the authoritative source. | hermes-default=55/100; ingrain-sidecar=66/100; ingrain=66/100; hindsight=25/100; openviking=25/100 |
| `repeated_work_cross_thread_l4` | 4 | The same work recurs in three threads with a partial fix, a failed assumption, and a later completed outcome. | hermes-default=100/100; ingrain-sidecar=37/100; ingrain=37/100; hindsight=55/100; openviking=25/100 |
| `thread_fork_reconciliation_l4` | 4 | Two threads make reasonable but incompatible implementation choices; a later source-of-truth doc resolves only part of the conflict. | hermes-default=55/100; ingrain-sidecar=81/100; ingrain=81/100; hindsight=32/100; openviking=25/100 |
| `partial_completion_status_l4` | 4 | A repeated task has completed code and tests, but the final public audit is explicitly not done yet. | hermes-default=83/100; ingrain-sidecar=59/100; ingrain=59/100; hindsight=25/100; openviking=25/100 |
| `adversarial_secret_status_l5` | 5 | The trace contains a secret-shaped token, a stale release claim, and a current-status question that requires caution instead of memory-only certainty. | hermes-default=55/100; ingrain-sidecar=65/100; ingrain=65/100; hindsight=20/100; openviking=20/100 |
| `conflicting_metrics_l5` | 5 | Different reports use different score denominators and one old report has been invalidated; the provider must avoid flattening all numbers into one claim. | hermes-default=55/100; ingrain-sidecar=70/100; ingrain=70/100; hindsight=25/100; openviking=25/100 |

## Scoring Rubric

| Component | Points |
|---|---:|
| Current Truth | 20 |
| Precedence Reasoning | 15 |
| Cross Session Continuity | 15 |
| Forbidden Suppression | 15 |
| Actionability | 10 |
| Source Traceability | 10 |
| Compactness | 5 |
| Abstention Discipline | 5 |
| Diagram Data Completeness | 5 |

## Artifacts

- Machine-readable results: `results.json`
- CSV scores: `results.csv`
- Trace graph: `graph.json`
- Mermaid graph: `graph.mmd`
- Provider metadata: `providers.json`
- Raw outputs: `raw/`
- Command logs: `commands/`
- Three.js viewer: `../../visualizations/sandbox-universe-3d.html`
