# Learned Experience Results

Ingrain is evaluated on one narrow question:

> Did prior agent experience become current, compact, source-linked guidance for the next run?

This is not a general memory benchmark. It does not claim Ingrain is better than Hindsight, OpenViking, or any other Hermes provider as a full memory backend.

## LES-Core

Command:

```bash
PYTHONPATH=src python3 -m aeonik_ingrain.cli eval
```

Result:

| Eval | Score | What it means |
|---|---:|---|
| LES-Core | 100/100 | The committed v0 launch fixtures pass: project recall, correction carry-forward, stale-plan avoidance, track-record recall, and compactness. |

LES-Core is a regression gate for Ingrain behavior. It is not a provider leaderboard.

## LES-Hard v0

LES-Hard is the tougher Ingrain self-eval. It expands the scenario set to include implicit corrections, unresolved conflicts, missing evidence, project namespace collisions, blocked-provider claims, and current-status premise traps.

Command:

```bash
PYTHONPATH=src python3 -m aeonik_ingrain.cli les-hard
```

Current result:

| Eval | Score | What it means |
|---|---:|---|
| LES-Hard v0 | 542/560 | Actual Ingrain compiler and hydration path across 28 preregistered local scenarios. |

The score is intentionally not perfect. The remaining misses are useful product gaps: project namespace precision, missing-evidence abstention, blocked-provider wording, and unresolved conflicts without an explicit resolution marker.

## Live Provider Matrix

The live Hermes provider matrix is separate and only contains real provider runs:

| Provider | Current result |
|---|---:|
| Hermes default memory | 88/100 |
| Hermes + Ingrain | 100/100 |
| Hindsight local embedded | 62/100 |
| Hermes OpenViking provider | 30/100 |
| Direct OpenViking resource retrieval | 88/100 |

Hindsight runs through the real Hermes provider in local embedded mode with an OpenAI-backed local Hindsight daemon. It passes the simple correction universe, partially handles sandbox recovery and launch-claim safety, but misses exact correction polarity in product-name and goals/mission-boundary cases.

OpenViking now has two real results. The Hermes provider lane scores `30/100` because it returns search metadata without enough hydrated lesson text for this learned-experience smoke test. The direct resource-retrieval harness scores `88/100` by uploading, indexing, searching, and reading scenario resources through the OpenViking HTTP API.

Artifacts:

- LES-Hard v0: [evidence/les-hard-v0/report.md](evidence/les-hard-v0/report.md)
- Live provider matrix: [evidence/live-les-provider-matrix/report.md](evidence/live-les-provider-matrix/report.md)
- Hindsight local run: [evidence/live-hindsight-local/report.md](evidence/live-hindsight-local/report.md)
- Hindsight probe: [evidence/live-les-provider-matrix/commands/hindsight/hindsight-probe.json](evidence/live-les-provider-matrix/commands/hindsight/hindsight-probe.json)
- OpenViking resource retrieval: [evidence/live-openviking-resource/report.md](evidence/live-openviking-resource/report.md)
- OpenViking setup recheck: [evidence/openviking-startup-recheck.md](evidence/openviking-startup-recheck.md)

## Claim Boundary

Safe public wording:

> Ingrain is a learned experience layer for autonomous agents. On the committed LES-Hard v0 self-eval, it scores `542/560`; in the current live Hermes smoke matrix, the Ingrain provider scores `100/100`.

Do not say:

> Ingrain is better memory than Hindsight or OpenViking.

The stronger and more accurate point is:

> Hindsight is a broader memory system. OpenViking is a resource and context database. Ingrain is the smaller learned-experience layer for corrections, decisions, stale-plan warnings, completed outcomes, and run-specific judgment.
