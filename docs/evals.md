# Evals

Aeonik Ingrain ships with deterministic, local evals. They do not require an LLM or network access.

## Current Sandbox Universe Results

Data source: [Sandbox Universe v0 results CSV](evidence/sandbox-universe-v0/results.csv). Scores are `0-100` per test. The L4/L5 tests are intentionally hard, so a non-perfect score is expected and useful.

```text
Claims L3
  Hermes default       55 |###########.........|
  Ingrain sidecar      90 |##################..|
  Ingrain provider     90 |##################..|
  Hindsight local      53 |###########.........|
  OpenViking           25 |#####...............|

Setup L3
  Hermes default       55 |###########.........|
  Ingrain sidecar      69 |##############......|
  Ingrain provider     69 |##############......|
  Hindsight local      66 |#############.......|
  OpenViking           25 |#####...............|

Goals L3
  Hermes default       55 |###########.........|
  Ingrain sidecar      54 |###########.........|
  Ingrain provider     54 |###########.........|
  Hindsight local      48 |##########..........|
  OpenViking           25 |#####...............|

Rename L3
  Hermes default       55 |###########.........|
  Ingrain sidecar      82 |################....|
  Ingrain provider     82 |################....|
  Hindsight local      56 |###########.........|
  OpenViking           25 |#####...............|

Source L3
  Hermes default       55 |###########.........|
  Ingrain sidecar      66 |#############.......|
  Ingrain provider     66 |#############.......|
  Hindsight local      25 |#####...............|
  OpenViking           25 |#####...............|

Repeat L4
  Hermes default      100 |####################|
  Ingrain sidecar      37 |#######.............|
  Ingrain provider     37 |#######.............|
  Hindsight local      55 |###########.........|
  OpenViking           25 |#####...............|

Fork L4
  Hermes default       55 |###########.........|
  Ingrain sidecar      81 |################....|
  Ingrain provider     81 |################....|
  Hindsight local      32 |######..............|
  OpenViking           25 |#####...............|

Partial L4
  Hermes default       83 |#################...|
  Ingrain sidecar      59 |############........|
  Ingrain provider     59 |############........|
  Hindsight local      25 |#####...............|
  OpenViking           25 |#####...............|

Secret L5
  Hermes default       55 |###########.........|
  Ingrain sidecar      65 |#############.......|
  Ingrain provider     65 |#############.......|
  Hindsight local      20 |####................|
  OpenViking           20 |####................|

Metrics L5
  Hermes default       55 |###########.........|
  Ingrain sidecar      70 |##############......|
  Ingrain provider     70 |##############......|
  Hindsight local      25 |#####...............|
  OpenViking           25 |#####...............|
```

Short test labels map to the full universe IDs: `launch_claims_conflict_l3`, `provider_setup_recovery_l3`, `goals_missions_kanban_l3`, `rename_namespace_collision_l3`, `source_truth_vs_chat_l3`, `repeated_work_cross_thread_l4`, `thread_fork_reconciliation_l4`, `partial_completion_status_l4`, `adversarial_secret_status_l5`, and `conflicting_metrics_l5`.

## LES-Core

LES stands for **Learned Experience Score**. LES-Core is the deterministic smoke test for the v0 local regression suite.

`ingrain eval` scores five learned-experience dimensions:

| Dimension | What it checks |
|---|---|
| Cold-start project recall | Current project facts survive a fresh run. |
| Correction carry-forward | Corrections appear in future hydration. |
| Stale-plan avoidance | Superseded decisions do not return as current truth. |
| Track-record query | Completed outcomes can be reported. |
| Context compactness | Hydration stays small and relevant. |

The committed v0 local suite currently scores `100/100`. Treat that as a regression gate: every launch scenario we claim to support is passing. Do not treat it as an external benchmark, a provider leaderboard, or a universal score for agent memory. As the scenario set gets harder, the score should remain useful by making regressions visible.

The eval also checks the CLI + Skill adoption surface:

| Check | What it verifies |
|---|---|
| `PRACTICE.md generated` | The human-readable practice artifact can be written. |
| `Practice cards generated` | Source-linked practice cards are created under `.ingrain/practice/cards/`. |
| `Brief hydration generated` | `ingrain hydrate --level brief` returns a compact context block. |
| `Evidence hydration includes confidence` | `ingrain hydrate --level evidence` includes source-linked confidence metadata. |

## LES-Hard

`ingrain les-hard` is the harder Ingrain self-eval. It is designed to make the score less brittle than LES-Core by adding stale intent, superseded decisions, missing evidence, project namespace collisions, implicit corrections, launch overclaims, and blocked-provider claim safety.

Run:

```bash
ingrain les-hard
```

Current LES-Hard v0 result:

| Mode | Score | Meaning |
|---|---:|---|
| Ingrain | 542/560 | Actual Ingrain compiler and hydration path. |

The Ingrain score is intentionally not perfect. The current misses are useful: project namespace precision, missing-evidence abstention, blocked-provider phrasing, and unresolved conflicts without an explicit resolution marker.

Artifacts:

- [LES-Hard report](les-hard-report.md)
- [LES-Hard evidence](evidence/les-hard-v0/report.md)
- raw outputs under `docs/evidence/les-hard-v0/raw/`

## Live LES-Core Provider Smoke Eval

`ingrain live-eval` is the live provider smoke harness:

| Rule | Meaning |
|---|---|
| Preregistered universes | The same five scenarios are defined in code before providers run. |
| Same input per provider | Each provider receives the same events and query. |
| Raw outputs saved | Every provider output is written under `docs/evidence/live-les-provider-matrix/raw/`. |
| Command logs saved | Each subprocess command, return code, stderr, and Hermes home is written under `docs/evidence/live-les-provider-matrix/commands/`. |
| Real provider rows only | Hindsight and OpenViking are scored only if real local services/packages are available. |

Run:

```bash
ingrain live-eval
```

Current committed live result:

| Provider | Result | Interpretation |
|---|---:|---|
| Hermes default memory | 88/100 | Fails the 90 threshold because raw memory carries stale launch/product claims alongside the correction. |
| Hermes + Ingrain | 100/100 | Passes this small smoke test by promoting the current lesson and suppressing stale claims in hydration. |
| Hindsight local embedded | 62/100 | Real Hermes Hindsight provider with OpenAI-backed local embedded mode; misses exact correction polarity in several universes and repeats one forbidden comparative claim. |
| Hermes OpenViking provider | 30/100 | Real Hermes OpenViking provider against a healthy local OpenViking server; the provider returns search metadata without enough hydrated lesson text for this learned-experience smoke test. |

On these preregistered local smoke-test universes, this run supports only a narrow claim: Ingrain's Hermes provider can pass the current learned-experience carry-forward gate. It does not show that Ingrain is a better general-purpose memory system than Hindsight, OpenViking, or any other provider.

Run an optional live OpenViking resource-retrieval benchmark:

```bash
ingrain compare --openviking-endpoint http://127.0.0.1:1933
```

The live OpenViking harness uploads the same scenario markdown resources to OpenViking, waits for resource indexing, searches, reads returned file URIs, and scores the retrieved context. The current direct resource-retrieval result is `88/100` under [evidence/live-openviking-resource/report.md](evidence/live-openviking-resource/report.md). It is intentionally labeled as resource retrieval and is not a claim about OpenViking's long-term memory extraction behavior.

For machine-readable output:

```bash
ingrain eval --json
```

## Scenarios

- correction after failure
- stale product name
- approval judgment
- Kanban boundary
- sandbox recovery
- track record
- active-goal stale plan
- completed outcome vs old todo
- preference exception
- source-linked actionability

These are designed to catch cases where raw retrieval is not enough. The agent needs current, behavior-shaping context.

## Sandbox Universe Eval

The next tier is specified in [sandbox-universe-eval-spec.md](sandbox-universe-eval-spec.md).

It is intended to be harder than LES-Hard: multi-session, multi-thread, source-of-truth conflicts, repeated work, provider competition, trace graphs, and a Three.js visualization. The target difficulty is high enough that `60/100` should be considered strong for L3.

The experimental Aeonik MIND V3 lane is specified separately in [mind-v3-sandbox-universe-lane-spec.md](mind-v3-sandbox-universe-lane-spec.md). It should not be scored in public docs until real local MIND artifacts exist.

### How To Read The Scores

Sandbox Universe is a failure microscope, not a provider leaderboard.

Hermes default memory can score well because it preserves raw trace text with exact source IDs. That is useful recall, but it is not the same as learned-experience judgment. In the current run, Hermes default also has the highest stale/forbidden leak count, which is the behavior Ingrain is designed to reduce.

The useful question is not "who won memory." The useful questions are:

- Did the lane recover the current truth?
- Did it suppress stale or forbidden text?
- Did it keep source evidence traceable?
- Did it produce compact context a runner agent can safely use?

The scorer is deterministic and inspectable. See [sandbox-universe-scoring.md](sandbox-universe-scoring.md) for component examples and known limits.

Current L5 v0 result:

| Provider | Score | Interpretation |
|---|---:|---|
| Hermes default memory | 623/1000 | Strong raw trace recall, but still leaks forbidden/stale context in most hard universes. |
| Hermes default + Ingrain CLI/skill sidecar | 673/1000 | Strong learned-experience sidecar result; preserves Hermes default memory while injecting Ingrain practice context. |
| Hermes + Ingrain provider | 673/1000 | Strong learned-experience provider result after source-of-truth promotion and supersession handling. |
| Hindsight local embedded | 405/1000 | Real local provider run; useful partial recall with trace/source misses and two stale/forbidden leaks. |
| Hermes OpenViking provider | 245/1000 | Real provider run; current lane is weak on hydrated learned-experience traces. |

Level breakdown:

| Provider | L3 | L4 | L5 |
|---|---:|---:|---:|
| Hermes default memory | 275/500 | 238/300 | 110/200 |
| Hermes default + Ingrain CLI/skill sidecar | 361/500 | 177/300 | 135/200 |
| Hermes + Ingrain provider | 361/500 | 177/300 | 135/200 |
| Hindsight local embedded | 248/500 | 112/300 | 45/200 |
| Hermes OpenViking provider | 125/500 | 75/300 | 45/200 |

Current failure taxonomy:

| Provider | Forbidden Leaks | Missing Current Truth | Missing Source Trace |
|---|---:|---:|---:|
| Hermes default memory | 8 | 1 | 0 |
| Hermes default + Ingrain CLI/skill sidecar | 0 | 7 | 7 |
| Hermes + Ingrain provider | 0 | 7 | 7 |
| Hindsight local embedded | 2 | 8 | 10 |
| Hermes OpenViking provider | 0 | 10 | 10 |

### Ablation Note

The biggest recent Ingrain improvement came from a general mechanism, not fixture-specific tuning:

| Change | Ingrain L5 Score | Effect |
|---|---:|---|
| Before source-of-truth promotion and supersession-edge retirement | 410/1000 | Direct corrections were preserved, but source docs and reports were too lossy. |
| After source-of-truth promotion and supersession-edge retirement | 673/1000 | Source docs, reports, run logs, and stale-document retirement became available to hydration. |

The remaining hard miss is repeated-work/status synthesis. `repeated_work_cross_thread_l4` is still `37/100` for Ingrain, so the benchmark is still exposing a real product gap.

Artifacts:

- [Sandbox Universe report](sandbox-universe-report.md)
- [Sandbox Universe evidence](evidence/sandbox-universe-v0/report.md)
- [3D viewer](visualizations/sandbox-universe-3d.html)
- [Launch-readiness audit](launch-readiness-audit.md)
- [Scoring explanation](sandbox-universe-scoring.md)
- [Experimental MIND V3 lane spec](mind-v3-sandbox-universe-lane-spec.md)
