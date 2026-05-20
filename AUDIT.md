# Pre-Public Audit (2026-05-20)

Status of the Ingrain + Sandbox Universe split, written before either repo is flipped public.

## Repo split

| Repo | URL | Visibility | Purpose |
|---|---|---|---|
| `benlloydg/ingrain` | https://github.com/benlloydg/ingrain | **private** | Learned-experience layer (memory product) |
| `benlloydg/sandbox-universe` | https://github.com/benlloydg/sandbox-universe | **private** | Trace-level benchmark (eval) |
| `aeonik-ai/ingrain` | https://github.com/aeonik-ai/ingrain | private | Backup; pre-split snapshot |

Spec: [`docs/sandbox-universe-split-spec.md`](docs/sandbox-universe-split-spec.md).

## What landed

### `sandbox-universe`
- LICENSE (MIT), README, DESIGN.md, CONTRIBUTING.md, PROVENANCE.md, Makefile, CI.
- `src/sandbox_universe/`:
  - `types.py` — dataclasses (`SandboxUniverse`, `SourceDoc`, `TraceSession`, `TraceTurn`).
  - `scorer.py` — 9-component scorer, ported verbatim from Ingrain. **Parity verified** against the original on all 50 saved (lane, universe) pairs of v0 evidence — zero divergence.
  - `universes/__init__.py` — the 10 v0 universes, copied verbatim.
  - `lanes/__init__.py` — `LaneAdapter` Protocol + entry-point discovery.
  - `lanes/_hermes.py`, `hermes_default.py`, `hindsight.py`, `openviking.py` — three reference lanes that drive Hermes subprocesses.
  - `runner.py` — generic orchestration: probe + run + score + write artifacts.
  - `cli.py` — `sandbox-universe list-lanes / probe / run`.
- `reports/v0/` — frozen evidence (results.json, raw outputs, command logs, graph artifacts, report.md, CSV). Paths redacted.
- `analysis/sidecar_isolation.py` — paired-stats comparison hermes-default vs ingrain-sidecar with 95% bootstrap CI and exact sign test.
- `reports/v0/analysis/sidecar-isolation.md` — honest negative result at n=10 (mean Δ +5.0, CI [-13.8, +19.8], p≈0.344). Per-component breakdown is the substantive finding: sidecar trades current_truth/continuity for forbidden_suppression.
- `reports/v0/analysis/failure-walkthrough-repeated-work.md` — close reading of why hermes-default scored 100/100 on one universe, identifying a scorer-design bug and a v1 fix.
- `benchmarks/longmemeval/` — external-benchmark adapter (loader + scorer + runner + CLI + fixture-backed tests). Harness complete; user supplies dataset.
- **49 unit tests pass.**

### `ingrain`
- `docs/compiler-rules-explained.md` — promotion + supersession rules walkthrough.
- `docs/sandbox-universe-split-spec.md` — the migration spec.
- `src/aeonik_ingrain/integrations/sandbox_universe/lane.py` — `IngrainLane` + `IngrainSidecarLane` implementing the `LaneAdapter` protocol. Registered via `pyproject.toml` entry points under `sandbox_universe.lanes` group.
- `.github/workflows/ci.yml` — tests + LES-Core regression gate.
- `Makefile`.
- `pyproject.toml` URLs updated to `benlloydg/ingrain`; entry points added.
- README rewritten to point at the new `sandbox-universe` repo for the benchmark.
- All `docs/evidence/` local-path leaks redacted; moved-elsewhere docs deleted.
- **29 unit tests pass.**

### End-to-end split repro

In a fresh venv:

```bash
pip install -e ./sandbox-universe -e ./ingrain
python -c "
from sandbox_universe.lanes.hermes_default import HermesDefaultLane
from sandbox_universe.lanes import registered_lanes
from sandbox_universe.universes import UNIVERSES
from sandbox_universe.runner import run_benchmark
from pathlib import Path
run_benchmark(
    lanes=[HermesDefaultLane(), registered_lanes()['ingrain-sidecar']],
    universes=UNIVERSES,
    output_dir=Path('/tmp/sbu-repro'),
)
"
```

**Reproduced totals exactly:**
- hermes-default: 623/1000 (matches saved v0)
- ingrain-sidecar: 673/1000 (matches saved v0)

All 20 (lane, universe) per-universe scores match — zero divergence. The split is verified lossless.

## Residual duplication (acceptable)

The following are intentionally *not* deleted from Ingrain in this pass — they still work and removing them would break unrelated tests / CLI subcommands. Plan: delete in a follow-up after the next sandbox-universe release.

- `src/aeonik_ingrain/evals/sandbox_universe.py` — wires the `ingrain universe-eval` CLI subcommand and 11 tests in `tests/test_eval.py`. Functionally now a backup copy of the sandbox-universe code.
- `docs/launch-readiness-audit.md`, `docs/evals.md`, `docs/eval-standards.md`, `docs/visualizations/sandbox-universe-3d.html` — still useful in Ingrain; reference the new repo where they cite scores.
- `WORKLOG.md` has historical mentions of local paths — flagged for review.
- `src/aeonik_ingrain/evals/les_hard.py` test fixture contains a real `/Users/benlloyd/.hindsight` path as the *forbidden value* of a scenario. Redacting changes test semantics; left as-is.

## Open questions (defer to v1)

- **Aeonik MIND V3 lane**: removed from Ingrain docs; lives in sandbox-universe `aeonik-mind-v3-sidecar` only if/when implemented externally.
- **Reports inside the PyPI package**: currently `reports/v0/` ships in the GitHub repo only, not in the `sandbox-universe-eval` wheel. Confirm before publishing to PyPI.
- **Aeonik branding**: package name stays `aeonik-ingrain`. README still says "Aeonik Ingrain" in places — acceptable as the brand is established.

## Pre-public checklist

- [x] LaneAdapter integration (#14) — Ingrain entry points register both lanes.
- [x] Soft cleanup (#15) — moved docs deleted; README updated.
- [x] E2E split repro (#16) — fresh-venv reproduces v0 scores exactly.
- [x] CI workflows on both repos.
- [x] No `.env`, `.ingrain/`, `data/`, or `.claude/` committed (gitignored).
- [x] License + author attribution match across both repos.
- [x] All tests pass (49 + 29).
- [ ] One pair-programming pass with fresh eyes — recommended before flipping public.
- [ ] WORKLOG.md decision (redact or keep).

## How to verify what's here

```bash
# Sandbox Universe
cd sandbox-universe
make install
make check          # ruff + mypy + 49 tests
make analysis       # regenerates sidecar isolation report

# Ingrain
cd ingrain
make install
make test           # 29 tests
make eval           # LES-Core regression gate (no network, no LLM)
make les-hard       # LES-Hard self-eval (no network, no LLM)

# Cross-repo E2E (requires Hermes installed at ~/.hermes/hermes-agent)
python -m venv /tmp/sbu-env && source /tmp/sbu-env/bin/activate
pip install -e ./sandbox-universe -e ./ingrain
PYTHONPATH=./sandbox-universe/src python -c "
from sandbox_universe.lanes.hermes_default import HermesDefaultLane
from sandbox_universe.lanes import registered_lanes
from sandbox_universe.universes import UNIVERSES
from sandbox_universe.runner import run_benchmark
from pathlib import Path
run_benchmark(
    lanes=[HermesDefaultLane(), registered_lanes()['ingrain-sidecar']],
    universes=UNIVERSES,
    output_dir=Path('/tmp/sbu-repro'),
)
"
# Should reproduce hermes-default=623/1000 ingrain-sidecar=673/1000.
```

## Recommendation

Both repos are **ready to flip public** after one pair-programming pass for fresh eyes. The remaining checklist items are taste/polish, not correctness. The end-to-end repro proves the split is lossless. The honest negative result in `reports/v0/analysis/sidecar-isolation.md` and the failure walkthrough are the highest-signal artifacts a fresh reader should land on.
