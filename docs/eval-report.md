# Aeonik Ingrain Eval Report

Generated on 2026-05-19 from local fixtures and the installed Hermes runtime on this machine.

## Deterministic LES-Core

No LLM, network, or hosted service required.

```text
Aeonik Ingrain LES-Core Smoke Eval (Learned Experience Score)

Cold-start project recall       20/20
Correction carry-forward        20/20
Stale-plan avoidance            20/20
Track-record query              20/20
Context compactness             20/20

Total                           100/100

Practice layer checks
PRACTICE.md generated                        pass
Practice cards generated                     pass
Brief hydration generated                    pass
Evidence hydration includes confidence       pass
```

Interpretation: `100/100` means the deterministic launch fixtures pass. It is a regression gate for the compiler, hydration, and practice artifacts, not an external provider benchmark.

## Live LES Provider Matrix

Command:

```bash
PYTHONPATH=src python3 -m aeonik_ingrain.cli live-eval --output-dir docs/evidence/live-les-provider-matrix --report docs/live-eval-report.md
```

Result:

```text
Hermes default memory  88/100
Hermes + Ingrain      100/100
Hindsight local        62/100
Hermes OpenViking      30/100
OpenViking resource    88/100
```

The live harness sends five preregistered universes through actual Hermes provider APIs and records raw outputs plus command logs under [docs/evidence/live-les-provider-matrix](evidence/live-les-provider-matrix/).

Why Hermes default lost points: default memory returned both the stale statement and the later correction in several universes. Ingrain compiled the later correction into current learned experience and suppressed the stale claim in hydration.

Why Hindsight/OpenViking did not pass here: Hindsight runs in local embedded mode through the real Hermes provider and an OpenAI-backed local Hindsight daemon, but its reflect output missed exact correction polarity in several universes. The Hermes OpenViking provider now runs against a healthy local OpenViking server, but its provider output is mostly search metadata and abstracts, not hydrated lesson text. Direct OpenViking resource retrieval scores `88/100` when the harness uploads, indexes, searches, and reads the same scenario resources through the OpenViking HTTP API.

## Claim Boundary

On these preregistered local smoke-test universes, this run supports only a narrow launch claim: Ingrain's Hermes provider passes the current learned-experience carry-forward gate. It does not show Ingrain is a better general-purpose memory backend than Hindsight, OpenViking, or any other Hermes provider.
