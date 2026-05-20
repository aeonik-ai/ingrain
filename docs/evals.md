# Evals

Aeonik Ingrain ships with deterministic, local evals. They do not require an LLM or network access.

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

Current L3 v0 result:

| Provider | Score | Interpretation |
|---|---:|---|
| Hermes default memory | 275/500 | Raw memory catches many facts but leaks stale trace context. |
| Hermes + Ingrain | 184/500 | Current Ingrain hydration is too lossy on explicit trace/source IDs for this benchmark. |
| Hindsight local embedded | 202/500 | Real local provider run; useful partial recall with trace misses. |
| Hermes OpenViking provider | 125/500 | Real provider run; current lane is weak on hydrated learned-experience traces. |

Artifacts:

- [Sandbox Universe report](sandbox-universe-report.md)
- [Sandbox Universe evidence](evidence/sandbox-universe-v0/report.md)
- [3D viewer](visualizations/sandbox-universe-3d.html)
