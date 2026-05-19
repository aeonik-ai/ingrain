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

## Deterministic Learned-Experience Comparison

Command:

```bash
PYTHONPATH=src python3 -m aeonik_ingrain.cli compare --output-dir docs/evidence/deterministic-les-comparison
```

Result:

```text
Hermes default memory                  40/200
Hermes + OpenViking-style retrieval   172/200
Hermes + Hindsight-style synthesis    196/200
Hermes + Ingrain                      200/200
```

The Hindsight-style row is a deterministic retain/recall/reflect-style synthesis baseline, not live Hindsight. See [learned-experience-results.md](learned-experience-results.md) and [evidence/deterministic-les-comparison/report.md](evidence/deterministic-les-comparison/report.md).

## Live LES Provider Matrix

Command:

```bash
PYTHONPATH=src python3 -m aeonik_ingrain.cli live-eval --output-dir docs/evidence/live-les-provider-matrix --report docs/live-eval-report.md
```

Result:

```text
Hermes default memory  88/100
Hermes + Ingrain      100/100
Hindsight             fail: local embedded timeout
OpenViking            blocked
```

The live harness sends five preregistered universes through actual Hermes provider APIs and records raw outputs plus command logs under [docs/evidence/live-les-provider-matrix](evidence/live-les-provider-matrix/).

Why Hermes default lost points: default memory returned both the stale statement and the later correction in several universes. Ingrain compiled the later correction into current learned experience and suppressed the stale claim in hydration.

Why Hindsight/OpenViking did not produce positive scores here: Hindsight is now installed in the Hermes runtime and the provider probe succeeds, but local embedded retain/reflect calls time out without a usable local LLM/service configuration. OpenViking doctor passes after configuring VLM through Codex OAuth, but server startup still fails in the official local GGUF embedding path with `ValueError: Failed to create llama_context`. See [OpenViking startup recheck](evidence/openviking-startup-recheck.md). The harness does not simulate those providers.

## Claim Boundary

On these preregistered local smoke-test universes, this run supports only a narrow launch claim: Ingrain's Hermes provider passes the current learned-experience carry-forward gate. It does not show Ingrain is a better general-purpose memory backend than Hindsight, OpenViking, or any other Hermes provider.
