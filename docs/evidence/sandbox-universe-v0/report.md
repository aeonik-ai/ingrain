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
| hermes-default | partial | 275/500 | Useful partial learned experience, with visible trace failures. |
| ingrain | weak | 184/500 | Retrieval exists, but judgment over messy traces is weak. |
| hindsight | partial | 202/500 | Useful partial learned experience, with visible trace failures. |
| openviking | weak | 125/500 | Retrieval exists, but judgment over messy traces is weak. |

## Universe Breakdown

| Universe | Level | Why It Is Hard | Scores |
|---|---:|---|---|
| `launch_claims_conflict_l3` | 3 | The latest correction overrides an older launch draft while the source docs still contain stale comparative phrasing. | hermes-default=55/100; ingrain=45/100; hindsight=35/100; openviking=25/100 |
| `provider_setup_recovery_l3` | 3 | Older setup failures remain useful history, but the current OpenViking server is healthy and should not be reported as blocked. | hermes-default=55/100; ingrain=35/100; hindsight=39/100; openviking=25/100 |
| `goals_missions_kanban_l3` | 3 | The trace contains an old plan that looks actionable, but active intent belongs to Hermes, not Ingrain. | hermes-default=55/100; ingrain=25/100; hindsight=48/100; openviking=25/100 |
| `rename_namespace_collision_l3` | 3 | Multiple Aeonik memory projects share vocabulary; the provider must keep Ingrain separate from Aeonik MIND and old MindCompiler names. | hermes-default=55/100; ingrain=37/100; hindsight=48/100; openviking=25/100 |
| `source_truth_vs_chat_l3` | 3 | A chat correction, a docs page, and a later run log disagree; the provider must preserve uncertainty and cite the authoritative source. | hermes-default=55/100; ingrain=42/100; hindsight=32/100; openviking=25/100 |

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
