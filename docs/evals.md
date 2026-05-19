# Evals

Aeonik Ingrain ships with deterministic, local evals. They do not require an LLM or network access.

## LES-100

LES stands for **Learned Experience Score**. The `100` is the maximum score in the v0 fixture suite.

`ingrain eval` scores five learned-experience dimensions:

| Dimension | What it checks |
|---|---|
| Cold-start project recall | Current project facts survive a fresh run. |
| Correction carry-forward | Corrections appear in future hydration. |
| Stale-plan avoidance | Superseded decisions do not return as current truth. |
| Track-record query | Completed outcomes can be reported. |
| Context compactness | Hydration stays small and relevant. |

The committed v0 fixture suite should score `100/100`. Treat that as a regression gate: every launch scenario we claim to support is passing. Do not treat it as an external benchmark, a provider leaderboard, or a universal score for agent memory. As the scenario set gets harder, the score should remain useful by making regressions visible.

The eval also checks the CLI + Skill adoption surface:

| Check | What it verifies |
|---|---|
| `PRACTICE.md generated` | The human-readable practice artifact can be written. |
| `Practice cards generated` | Source-linked practice cards are created under `.ingrain/practice/cards/`. |
| `Brief hydration generated` | `ingrain hydrate --level brief` returns a compact context block. |
| `Evidence hydration includes confidence` | `ingrain hydrate --level evidence` includes source-linked confidence metadata. |

## Comparison Harness

The comparison harness stress-tests the differentiator: learned experience and judgment.

It compares three fixture substrates:

| Mode | Meaning |
|---|---|
| Hermes default memory | Bounded curated memory only. |
| Hermes + OpenViking-style retrieval | Raw semantic retrieval baseline; finds fragments but does not resolve current truth. |
| Hermes + Ingrain | Promotion, supersession, compilation, and compact hydration. |

The OpenViking row is intentionally described as `OpenViking-style retrieval`: it is a deterministic local retrieval baseline, not a live OpenViking server benchmark and not a full evaluation of OpenViking. This keeps the eval runnable without services while showing the Ingrain-specific behavior distinction honestly.

Run:

```bash
ingrain eval
```

Run only the comparison table:

```bash
ingrain compare
```

## Live LES Provider Eval

`ingrain live-eval` is the launch evidence harness. It is designed to be scientifically safer than the deterministic comparison table:

| Rule | Meaning |
|---|---|
| Preregistered universes | The same five scenarios are defined in code before providers run. |
| Same input per provider | Each provider receives the same events and query. |
| Raw outputs saved | Every provider output is written under `docs/evidence/live-les-provider-matrix/raw/`. |
| Command logs saved | Each subprocess command, return code, stderr, and Hermes home is written under `docs/evidence/live-les-provider-matrix/commands/`. |
| No modeled provider rows | Hindsight and OpenViking are scored only if real local services/packages are available. |

Run:

```bash
ingrain live-eval
```

Current committed live result:

| Provider | Result | Interpretation |
|---|---:|---|
| Hermes default memory | 88/100 | Fails the 90 threshold because raw memory carries stale launch/product claims alongside the correction. |
| Hermes + Ingrain | 100/100 | Passes by promoting the current lesson and suppressing stale claims in hydration. |
| Hindsight | blocked | Hermes provider found no Hindsight package, service URL, or API key in this environment. |
| OpenViking | blocked | No healthy OpenViking server was reachable at `http://127.0.0.1:1933`. |

This proves a narrow claim: Ingrain's Hermes provider can improve learned-experience carry-forward on these local universes. It does not prove that Ingrain is a better general-purpose memory system than Hindsight, OpenViking, or any other provider.

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

These are designed to catch cases where raw retrieval is not enough. The agent needs current, behavior-shaping context.
