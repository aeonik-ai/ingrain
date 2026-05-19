# Learned Experience Results

Ingrain is evaluated on one narrow question:

> Did prior agent experience become current, compact, source-linked guidance for the next run?

This is not a general memory benchmark. It does not claim Ingrain is better than live Hindsight, OpenViking, or any other Hermes provider as a full memory backend.

## Current Deterministic Result

Command:

```bash
PYTHONPATH=src python3 -m aeonik_ingrain.cli compare --output-dir docs/evidence/deterministic-les-comparison
```

Result:

| Mode | Score | What it means |
|---|---:|---|
| Hermes default memory | 40/200 | Bounded curated memory only. |
| Hermes + OpenViking-style retrieval | 172/200 | Raw retrieval finds the right fragments, but often returns stale and current memories together. |
| Hermes + Hindsight-style synthesis | 196/200 | Strong deterministic retain/recall/reflect-style synthesis. This is not live Hindsight. |
| Hermes + Ingrain | 200/200 | Actual Ingrain compiler and hydration path. |

The Hindsight-style row is intentionally strong and intentionally labeled. It models a plausible synthesized-memory behavior, but it does not exercise Hindsight's real graph, entity, temporal, cloud, or local runtime.

## What The Eval Tests

The comparison uses ten preregistered universes:

| Universe | Difficulty | Pressure |
|---|---:|---|
| `correction_after_failure` | 1 | Carry a direct correction into future launch framing. |
| `stale_product_name` | 2 | Prefer the newer product-name decision. |
| `approval_judgment` | 2 | Convert a prior launch mistake into future judgment. |
| `kanban_boundary` | 3 | Keep goals, missions, and Kanban out of memory state. |
| `sandbox_recovery` | 3 | Change execution behavior after a sandbox failure. |
| `track_record` | 3 | Report completed outcomes. |
| `active_goal_stale_plan` | 4 | Prevent an old plan from becoming active intent. |
| `completed_vs_todo` | 4 | Suppress an old todo after completion. |
| `preference_exception` | 5 | Preserve an exception-bearing rule, not just a preference. |
| `source_linked_actionability` | 5 | Keep claim boundaries source-linked and directly usable. |

Each universe is worth 20 points:

| Component | Points |
|---|---:|
| Expected lesson recall | 8 |
| Stale or forbidden suppression | 4 |
| Actionability | 4 |
| Source evidence | 2 |
| Compactness | 2 |

## Why Ingrain Edged The Hindsight-Style Baseline

The Hindsight-style baseline scored `196/200`. Its miss was the first universe: it retained and synthesized the correction, but still carried the stale phrase from the failed launch framing.

Ingrain scored `200/200` because the compiler promoted the correction as current practice memory and hydration returned source-linked guidance without the stale claim.

That is the narrow product claim:

> Ingrain is a practice-memory layer for runner agents. It is optimized for the lessons that should change the next run.

## Live Provider Matrix

The live Hermes provider matrix is separate:

| Provider | Current result |
|---|---:|
| Hermes default memory | 88/100 |
| Hermes + Ingrain | 100/100 |
| Hindsight | blocked |
| OpenViking | blocked |

Hindsight is blocked in this environment because no Hindsight package, service URL, or API key is available to the installed Hermes runtime. OpenViking is blocked because no healthy server was reachable at `http://127.0.0.1:1933`.

Artifacts:

- Deterministic comparison: [evidence/deterministic-les-comparison/report.md](evidence/deterministic-les-comparison/report.md)
- Live provider matrix: [evidence/live-les-provider-matrix/report.md](evidence/live-les-provider-matrix/report.md)
- Hindsight probe: [evidence/live-les-provider-matrix/commands/hindsight/hindsight-probe.json](evidence/live-les-provider-matrix/commands/hindsight/hindsight-probe.json)
- OpenViking recheck: [evidence/openviking-startup-recheck.md](evidence/openviking-startup-recheck.md)

## Claim Boundary

Safe public wording:

> On deterministic learned-experience universes, Ingrain scored `200/200`, ahead of a strong labeled Hindsight-style synthesis baseline at `196/200`.

Do not say:

> Ingrain is better memory than Hindsight.

The stronger and more accurate point is:

> Hindsight is the broader memory system. Ingrain is the smaller practice-memory layer for corrections, decisions, stale-plan warnings, completed outcomes, and run-specific judgment.
