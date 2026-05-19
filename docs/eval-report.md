# Aeonik Ingrain Eval Report

Generated on 2026-05-19 from local fixtures and the installed Hermes runtime on this machine.

## Deterministic LES-100

No LLM, network, or hosted service required.

```text
Aeonik Ingrain LES-100 Eval (Learned Experience Score)

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
Hindsight             blocked
OpenViking            blocked
```

The live harness sends five preregistered universes through actual Hermes provider APIs and records raw outputs plus command logs under [docs/evidence/live-les-provider-matrix](evidence/live-les-provider-matrix/).

Why Hermes default lost points: default memory returned both the stale statement and the later correction in several universes. Ingrain compiled the later correction into current learned experience and suppressed the stale claim in hydration.

Why Hindsight/OpenViking are blocked here: Hindsight packages/API keys were not available in the Hermes runtime, and no healthy OpenViking server was reachable at `http://127.0.0.1:1933`. A follow-up OpenViking recheck tried the existing OpenViking 0.3.17 install and a clean Python 3.11 OpenViking 0.3.17 install; the local GGUF embedder did not produce a healthy server in this environment. See [OpenViking startup recheck](evidence/openviking-startup-recheck.md). The harness does not simulate those providers.

## Claim Boundary

On these preregistered local universes, this run supports a narrow launch claim: Ingrain can improve learned-experience carry-forward over Hermes default memory. It does not show Ingrain is a better general-purpose memory backend than Hindsight, OpenViking, or any other Hermes provider.
