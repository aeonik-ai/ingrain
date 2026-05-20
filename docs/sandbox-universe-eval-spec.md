# Sandbox Universe Eval Spec

Status: implemented v0; future work should extend hard universes rather than inflate claims

Owner: Aeonik Ingrain

Target: build the next evaluation tier after LES-Hard, with real provider competition, turn-by-turn traceability, and visual artifacts that make the run inspectable instead of just scored.

## One-Line Goal

Build a preregistered, trace-level benchmark where autonomous-agent memory systems must recover the right learned experience across messy multi-session work, conflicting source-of-truth documents, corrections, repeated attempts, and stale plans.

## Why This Exists

LES-Core is a regression gate. LES-Hard is an Ingrain self-eval. The Sandbox Universe eval is the first serious public-facing pressure test:

- multiple sessions
- multiple threads
- source-of-truth documents
- turn-by-turn corrections
- stale decisions
- repeated work with partial failures
- active intent versus learned experience boundaries
- provider outputs saved raw
- graph and diagram artifacts generated from every run

The expected score should be low. A strong v0 system may land around `60/100`. A `100/100` should be suspicious unless the benchmark is too easy or the scorer has leaked fixture answers.

## Systems Under Test

The first implementation compares five real lanes:

| Lane | Meaning | Evidence requirement |
|---|---|---|
| Hermes default memory | Installed Hermes built-in memory APIs. | Raw provider output plus command log. |
| Hermes + Ingrain provider | Hermes loads Ingrain through `plugins.memory.load_memory_provider("ingrain")`. | Raw provider output, command log, compiled Ingrain evidence, source refs. |
| Hermes default + Ingrain CLI/skill sidecar | Hermes default memory remains active while Ingrain is used as an external practice/skill context layer through CLI hydration. | Raw output, command log, compiled Ingrain evidence, skill/CLI invocation evidence, source refs. |
| Hermes + Hindsight local | Hermes loads real Hindsight provider in local embedded mode. | Raw provider output, command log, probe output, temp HOME/bank isolation. |
| Hermes + OpenViking provider | Hermes loads real OpenViking provider against a healthy local OpenViking server. | Raw provider output, command log, OpenViking health record. |

The Ingrain provider lane and Ingrain CLI/skill sidecar lane are intentionally separate. The provider lane tests whether Ingrain can occupy Hermes' memory-provider slot. The sidecar lane tests the likely launch posture: keep Hermes default memory behavior and add Ingrain learned-experience context as practice before work.

Direct OpenViking resource retrieval may be kept as a diagnostic lane, but it must be labeled as resource retrieval, not as the Hermes OpenViking provider score.

### Experimental Aeonik MIND V3 Lane

The next implementation loop adds an experimental sixth lane:

| Lane | Meaning | Evidence requirement |
|---|---|---|
| Aeonik MIND V3 sidecar | Hermes default memory remains the runner baseline while Sandbox Universe traces are ingested into Aeonik MIND V3 as event-sourced memory. | Real local MIND API/MemoryAPI output plus command logs, or an explicit blocked result with command evidence. Mock storage may be used only for adapter tests and must not be presented as provider proof. |

This lane is specified in [mind-v3-sandbox-universe-lane-spec.md](mind-v3-sandbox-universe-lane-spec.md). It should stay experimental until real local MIND artifacts exist.

## Benchmark Name

Working CLI name:

```bash
ingrain universe-eval
```

Working docs name:

```text
Sandbox Universe Eval v0
```

This is intentionally less cute than LES. The public posture should be: serious benchmark, inspectable traces, hard failures.

## Difficulty Levels

Each universe has a level. The benchmark report must show scores by level and explain why each level is hard.

| Level | Name | Expected ceiling | What it tests |
|---|---|---:|---|
| L1 | Single-session correction | 80-90/100 | Basic correction carry-forward, stale phrase suppression, compact recall. |
| L2 | Multi-session supersession | 65-80/100 | Decisions change across sessions; old plans are useful history but not current truth. |
| L3 | Source-of-truth conflict | 45-70/100 | Docs, user corrections, run logs, and active tasks conflict; provider must follow precedence rules and cite why. |
| L4 | Cross-thread repeated work | 35-60/100 | Same project appears in multiple threads with repeated failed attempts, partial success, and naming collisions. |
| L5 | Adversarial launch audit | 20-50/100 | Overclaim traps, stale benchmark claims, secret-like tokens, unrelated project bleed, and missing evidence abstention. |

The first launch target is L3. We should not tune for `100/100`. If Ingrain scores above `75/100` on L3 v0, expand the universes before calling it launch-ready.

## Universe Shape

Each universe is a structured trace, not a flat prompt.

```json
{
  "id": "launch_claims_conflict_l3",
  "level": 3,
  "title": "Launch Claims Conflict",
  "difficulty_reason": "The latest user correction overrides an older README draft, but a source-of-truth doc still contains stale phrasing.",
  "source_of_truth": [
    {
      "id": "doc_launch_v1",
      "kind": "doc",
      "created_at": "2026-05-19T08:00:00Z",
      "text": "Old launch draft says Ingrain beats Hindsight."
    },
    {
      "id": "doc_eval_v2",
      "kind": "doc",
      "created_at": "2026-05-19T22:00:00Z",
      "text": "Only real provider runs may be used for comparison claims."
    }
  ],
  "sessions": [
    {
      "id": "session_a",
      "thread": "launch-copy",
      "turns": [
        {
          "turn": 1,
          "actor": "assistant",
          "kind": "draft",
          "text": "Ingrain beats Hindsight and OpenViking."
        },
        {
          "turn": 2,
          "actor": "user",
          "kind": "correction",
          "text": "Do not say that. Say this is a narrow learned-experience smoke test."
        }
      ]
    }
  ],
  "query": "Write the current safe launch claim.",
  "expected": [
    "narrow learned-experience smoke test",
    "real provider runs",
    "do not claim Ingrain beat Hindsight or OpenViking"
  ],
  "forbidden": [
    "Ingrain beats Hindsight",
    "Ingrain beats OpenViking"
  ]
}
```

## Required L3 Universes

Implement at least five L3 universes before claiming the spec is complete:

| Universe | Core trap | Why it is hard |
|---|---|---|
| `launch_claims_conflict_l3` | Old docs say "beats"; latest correction says "do not claim better." | Requires source precedence, correction carry-forward, and overclaim suppression. |
| `provider_setup_recovery_l3` | Earlier sandbox blocked installs; later real OpenViking install works; Hindsight has env constraints. | Requires temporal status tracking and action guidance without inventing a current blocker. |
| `goals_missions_kanban_l3` | A stale plan says to move Kanban; current boundary says Hermes owns intent. | Requires separating learned experience from active task state. |
| `rename_namespace_collision_l3` | MindCompiler, Ingrain, MIND V3, and Aeonik MIND appear in adjacent projects. | Requires project namespace precision and no cross-project contamination. |
| `source_truth_vs_chat_l3` | Chat says one thing; later source-of-truth doc supersedes it; a later run log partially contradicts both. | Requires explicit precedence and citation. |

Then add L4 and L5 universes until the benchmark is hard enough that the best lane does not exceed `70/100`.

## Scoring

Each universe is worth 100 points, then the suite score is averaged.

| Component | Points | What earns credit |
|---|---:|---|
| Current truth | 20 | Uses the latest valid decision/correction, not stale text. |
| Precedence reasoning | 15 | Correctly chooses among source docs, chat turns, run logs, and active-task boundaries. |
| Cross-session continuity | 15 | Recalls evidence across sessions and threads. |
| Forbidden suppression | 15 | Does not repeat stale claims, old names, secret-like tokens, or invalid goals. |
| Actionability | 10 | Produces the next useful behavior, not just a memory dump. |
| Source traceability | 10 | Includes source IDs or equivalent evidence refs. |
| Compactness | 5 | Keeps context usable for a runner agent. |
| Abstention discipline | 5 | Says when memory is insufficient or current status must be checked live. |
| Diagram data completeness | 5 | Emits enough structured edges/nodes for visualization. |

Pass/fail labels:

| Score | Interpretation |
|---:|---|
| 80-100 | Benchmark likely too easy or provider is exceptionally strong; expand before using as a headline. |
| 60-79 | Strong result for L3/L4; worth studying. |
| 40-59 | Useful partial learned experience. |
| 20-39 | Retrieval exists but judgment is weak. |
| 0-19 | Provider failed or returned mostly irrelevant/stale context. |

## Trace Artifacts

Every run must write:

```text
docs/evidence/sandbox-universe-v0/
  report.md
  results.json
  results.csv
  graph.json
  graph.mmd
  raw/<provider>/<universe>.txt
  commands/<provider>/<universe>.json
  providers.json
```

`graph.json` must be visualization-ready:

```json
{
  "nodes": [
    {"id": "session_a.turn_2", "type": "correction", "label": "Do not say beats"},
    {"id": "provider.ingrain.launch_claims_conflict_l3", "type": "output", "score": 72}
  ],
  "edges": [
    {"from": "session_a.turn_2", "to": "provider.ingrain.launch_claims_conflict_l3", "type": "supports"},
    {"from": "doc_launch_v1", "to": "session_a.turn_2", "type": "superseded_by"}
  ]
}
```

`graph.mmd` must render a Mermaid graph for the README/docs path.

## Visualization Requirements

Add two visualization surfaces:

1. A static Markdown/CSV view for GitHub:
   - provider x universe heatmap table
   - level breakdown
   - failure taxonomy
   - top stale-claim leaks

2. A Three.js viewer:
   - file target: `docs/visualizations/sandbox-universe-3d.html`
   - data input: `docs/evidence/sandbox-universe-v0/graph.json`
   - view: providers as columns, universes as rows/depth, score as height/color
   - interactions: hover/select node to show provider, universe, score, failure reasons, and raw artifact path
   - fallback: if Three.js CDN is unavailable, show a readable HTML table from the same data

The 3D view should not be decorative. It should answer: where did each system lose the trace?

## Implementation Plan

1. Add structured universe models in `src/aeonik_ingrain/evals/sandbox_universe.py`.
2. Add JSON fixtures under `src/aeonik_ingrain/evals/sandbox_universes/`.
3. Reuse the live provider execution code from `live_les.py`, but extend payloads to include docs, sessions, threads, source IDs, and turn numbers.
4. Add `ingrain universe-eval` with:
   - `--provider`
   - `--level`
   - `--output-dir`
   - `--report`
   - `--timeout`
   - `--openviking-endpoint`
5. Add the `ingrain-sidecar` lane:
   - ingest the same trace into Ingrain through the local ledger/CLI path
   - hydrate the same query as practice context
   - combine Hermes default memory output with the Ingrain practice context without replacing Hermes memory
   - save the command log and compiled evidence so the lane is auditable
6. Implement scorer components as inspectable functions, not opaque LLM judging.
7. Generate `results.json`, `results.csv`, `graph.json`, `graph.mmd`, and raw provider outputs.
8. Add tests for:
   - universe loading
   - scoring component math
   - graph generation
   - report generation
   - CLI smoke path without live providers
9. Run live provider matrix when dependencies are available.
10. Add `docs/visualizations/sandbox-universe-3d.html`.
11. Update README, eval docs, launch docs, and learned-experience results with cautious wording.
12. Run a public-facing audit:
    - no non-real provider baselines
    - no stale blocked-provider language
    - no secret leakage
    - no overclaiming against Hindsight/OpenViking
    - all evidence links resolve
    - raw artifacts match report scores

## Acceptance Criteria

The heartbeat should continue until all are true:

- `ingrain universe-eval --level 3` runs and writes artifacts.
- At least five real lanes are supported, including the Ingrain provider lane and the Ingrain CLI/skill sidecar lane.
- If a provider cannot run, the report labels it unavailable with command evidence rather than inventing a score.
- L3 contains at least five complex turn-by-turn universes.
- The best score on L3 is below `80/100`, or the benchmark has been made harder.
- `graph.json` and `graph.mmd` are generated.
- The Three.js viewer loads the generated graph and shows provider differences.
- Unit tests pass.
- Live provider commands have been run where the local machine supports them.
- README and docs explain that this is a hard trace benchmark, not a broad SOTA memory claim.
- A final repo audit has been run and fixes from that audit have been executed.

## Public Story

One-liner:

> Most memory evals ask "can you retrieve this fact?" Sandbox Universe asks "can you survive the messy history of real work?"

Short explanation:

> The benchmark turns agent history into inspectable universes: docs, sessions, threads, corrections, failed attempts, current decisions, and forbidden stale claims. Every provider gets the same trace. Every output is raw-auditable. Every score can be traced back to the turn that caused it.

Karpathy-safe posture:

> Do not trust a leaderboard number without the trace. This repo ships the trace, the raw outputs, the graph, and the misses.

## Stop Condition For Heartbeat

When the implementation, visualizations, docs, tests, live runs, commit, push, and final public-facing audit are complete, stop the heartbeat and leave a concise final status in the thread.
