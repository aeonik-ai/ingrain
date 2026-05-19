# Evals

Aeonik Ingrain ships with deterministic, local evals. They do not require an LLM or network access.

## LES-Core

LES stands for **Learned Experience Score**. LES-Core is the deterministic smoke test for the v0 fixture suite.

`ingrain eval` scores five learned-experience dimensions:

| Dimension | What it checks |
|---|---|
| Cold-start project recall | Current project facts survive a fresh run. |
| Correction carry-forward | Corrections appear in future hydration. |
| Stale-plan avoidance | Superseded decisions do not return as current truth. |
| Track-record query | Completed outcomes can be reported. |
| Context compactness | Hydration stays small and relevant. |

The committed v0 fixture suite currently scores `100/100`. Treat that as a regression gate: every launch scenario we claim to support is passing. Do not treat it as an external benchmark, a provider leaderboard, or a universal score for agent memory. As the scenario set gets harder, the score should remain useful by making regressions visible.

The eval also checks the CLI + Skill adoption surface:

| Check | What it verifies |
|---|---|
| `PRACTICE.md generated` | The human-readable practice artifact can be written. |
| `Practice cards generated` | Source-linked practice cards are created under `.ingrain/practice/cards/`. |
| `Brief hydration generated` | `ingrain hydrate --level brief` returns a compact context block. |
| `Evidence hydration includes confidence` | `ingrain hydrate --level evidence` includes source-linked confidence metadata. |

## Comparison Harness

The comparison harness stress-tests the differentiator: learned experience and judgment.

It compares four fixture substrates:

| Mode | Meaning |
|---|---|
| Hermes default memory | Bounded curated memory only. |
| Hermes + OpenViking-style retrieval | Raw semantic retrieval baseline; finds fragments but does not resolve current truth. |
| Hermes + Hindsight-style synthesis | Deterministic retain/recall/reflect-style synthesis; not live Hindsight. |
| Hermes + Ingrain | Promotion, supersession, compilation, and compact hydration. |

The OpenViking row is intentionally described as `OpenViking-style retrieval`: it is a deterministic local retrieval baseline, not a live OpenViking server benchmark and not a full evaluation of OpenViking. The Hindsight row is intentionally described as `Hindsight-style synthesis`: it is a deterministic local synthesis baseline, not live Hindsight and not a full evaluation of Hindsight.

Run:

```bash
ingrain eval
```

Run only the comparison table:

```bash
ingrain compare
```

Write machine-readable comparison artifacts:

```bash
ingrain compare --output-dir docs/evidence/deterministic-les-comparison
```

Current deterministic comparison result:

| Mode | Score |
|---|---:|
| Hermes default memory | 40/200 |
| Hermes + OpenViking-style retrieval | 172/200 |
| Hermes + Hindsight-style synthesis | 196/200 |
| Hermes + Ingrain | 200/200 |

See [learned-experience-results.md](learned-experience-results.md) for the polished results page and claim boundary.

## LES-Hard

`ingrain les-hard` is the harder deterministic benchmark. It is designed to make the score less brittle than LES-Core by adding stale intent, superseded decisions, missing evidence, project namespace collisions, implicit corrections, launch overclaims, and blocked-provider claim safety.

Run:

```bash
ingrain les-hard
```

Current LES-Hard v0 result:

| Mode | Score | Meaning |
|---|---:|---|
| Hermes default memory | 194/560 | Bounded curated memory only. |
| Hermes + OpenViking-style retrieval | 501/560 | Deterministic raw retrieval baseline, not live OpenViking. |
| Hermes + Hindsight-style synthesis | 536/560 | Deterministic retain/recall/reflect-style baseline, not live Hindsight. |
| Hermes + Ingrain | 545/560 | Actual Ingrain compiler and hydration path. |

The Ingrain score is intentionally not perfect. The current misses are useful: project namespace precision, missing-evidence abstention, blocked-provider phrasing, and unresolved conflicts without an explicit resolution marker.

Artifacts:

- [LES-Hard report](les-hard-report.md)
- [LES-Hard evidence](evidence/les-hard-v0/report.md)
- raw outputs under `docs/evidence/les-hard-v0/raw/`

## Live LES-Core Provider Smoke Eval

`ingrain live-eval` is the live provider smoke harness. It is designed to be scientifically safer than the deterministic comparison table:

| Rule | Meaning |
|---|---|
| Preregistered universes | The same five scenarios are defined in code before providers run. |
| Same input per provider | Each provider receives the same events and query. |
| Raw outputs saved | Every provider output is written under `docs/evidence/live-les-provider-matrix/raw/`. |
| Command logs saved | Each subprocess command, return code, stderr, and Hermes home is written under `docs/evidence/live-les-provider-matrix/commands/`. |
| No simulated provider rows | Hindsight and OpenViking are scored only if real local services/packages are available. |

Run:

```bash
ingrain live-eval
```

Current committed live result:

| Provider | Result | Interpretation |
|---|---:|---|
| Hermes default memory | 88/100 | Fails the 90 threshold because raw memory carries stale launch/product claims alongside the correction. |
| Hermes + Ingrain | 100/100 | Passes this small smoke test by promoting the current lesson and suppressing stale claims in hydration. |
| Hindsight | fail in current local embedded run | Hermes found real Hindsight packages, but local embedded calls timed out without a usable local LLM/service configuration. |
| OpenViking | blocked | Doctor passes after configuring Codex OAuth for VLM, but server startup still fails in the official local GGUF embedding path; see [OpenViking startup recheck](evidence/openviking-startup-recheck.md). |

On these preregistered local smoke-test universes, this run supports only a narrow claim: Ingrain's Hermes provider can pass the current learned-experience carry-forward gate. It does not show that Ingrain is a better general-purpose memory system than Hindsight, OpenViking, or any other provider.

Run an optional live OpenViking resource-retrieval benchmark:

```bash
ingrain compare --live-openviking --openviking-endpoint http://127.0.0.1:1933
```

The live OpenViking harness uploads the same scenario fixtures to OpenViking, waits for resource indexing, searches, reads returned file URIs, and scores the retrieved context. It is intentionally labeled as resource retrieval. OpenViking's long-term memory extraction path requires model credentials; without those credentials, `viking_remember` can record a session message but extraction fails at commit time.

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
