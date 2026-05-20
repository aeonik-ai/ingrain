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
- LICENSE (MIT), README, DESIGN.md, CONTRIBUTING.md, PROVENANCE.md.
- `src/sandbox_universe/`:
  - `types.py` — dataclasses (`SandboxUniverse`, `SourceDoc`, `TraceSession`, `TraceTurn`).
  - `scorer.py` — 9-component scorer, ported verbatim from Ingrain. **Parity verified** against the original on all 50 saved (lane, universe) pairs of v0 evidence — zero divergence.
  - `universes/__init__.py` — the 10 v0 universes, copied verbatim.
  - `lanes/__init__.py` — `LaneAdapter` Protocol + entry-point discovery (`sandbox_universe.lanes` group).
  - `runner.py` — generic orchestration: probe + run + score + write artifacts.
  - `cli.py` — `sandbox-universe list-lanes / probe / run`.
- `reports/v0/` — frozen evidence: results.json, raw outputs, command logs, graph artifacts, report.md, CSV. Absolute paths rewritten to relative; local home-dir paths redacted.
- `analysis/sidecar_isolation.py` — paired-stats comparison hermes-default vs ingrain-sidecar with 95% bootstrap CI and exact sign test. Output: `reports/v0/analysis/sidecar-isolation.md`. **Honest negative result**: at n=10, sidecar effect is inconclusive (CI [-13.8, +19.8]; p≈0.344). The per-component breakdown shows the sidecar trades current_truth (-8.20) and continuity (-7.60) for forbidden_suppression (+12.00) — they are NOT the same intervention.
- `reports/v0/analysis/failure-walkthrough-repeated-work.md` — close reading of why hermes-default scored 100/100 on one universe, identifying a scorer-design bug (raw-dump cap should fire on structural signals, not just forbidden leaks).
- `benchmarks/longmemeval/` — external-benchmark adapter (loader + scorer + runner + CLI + fixture-backed tests). Scaffolding only; user supplies dataset.
- 49 unit tests pass (scorer, universes, runner orchestration with stub lanes, sidecar isolation stats, LongMemEval harness on a fixture).
- CI workflow (`.github/workflows/ci.yml`): pytest matrix 3.10/3.11/3.12 + ruff + mypy.
- Makefile: `make test`, `make lint`, `make typecheck`, `make analysis`, `make run LANE=...`.

### `ingrain`
- New `docs/compiler-rules-explained.md` — walkthrough of how `compiler/rules.py` promotes events to typed practice cards, including the supersession rules.
- New `docs/sandbox-universe-split-spec.md` — the migration spec.
- New `.github/workflows/ci.yml` — pytest matrix + LES-Core regression gate.
- New `Makefile`.
- `pyproject.toml` URLs updated to `github.com/benlloydg/ingrain`.
- All `docs/evidence/` local-path leaks redacted.
- 29 unit tests pass.

## What is NOT yet done (blockers for flipping public)

### 1. Ingrain LaneAdapter integration (task #14)

The new `sandbox-universe` repo's lane registry currently has the protocol and runner but **no installed reference lanes**. The `hermes-default`, `hindsight`, `openviking`, `ingrain`, and `ingrain-sidecar` lane implementations still live in `ingrain/src/aeonik_ingrain/evals/sandbox_universe.py` (the old file).

To finish:
- Port `HERMES_DEFAULT_SCRIPT`, `HINDSIGHT_PROVIDER_SCRIPT`, `OPENVIKING_PROVIDER_SCRIPT` (and the subprocess orchestration around them) into `sandbox-universe/src/sandbox_universe/lanes/{hermes_default,hindsight,openviking}.py` as reference lanes.
- Port `INGRAIN_PROVIDER_SCRIPT` and `INGRAIN_SIDECAR_SCRIPT` into `ingrain/src/aeonik_ingrain/integrations/sandbox_universe/lane.py` as `IngrainLane` and `IngrainSidecarLane`.
- Register the Ingrain lanes via `pyproject.toml` entry points under the `sandbox_universe.lanes` group.

This work was deliberately not done in this session because it requires a working Hermes Agent install to test, and the failure modes (env-var assembly, Hindsight HOME isolation, OpenViking health probe) are subtle enough that untested code would likely break.

### 2. Ingrain cleanup post-split (task #15)

After #1 lands, `ingrain/src/aeonik_ingrain/evals/sandbox_universe.py` should be deleted along with `docs/sandbox-universe-eval-spec.md`, `docs/sandbox-universe-scoring.md`, `docs/sandbox-universe-report.md`, and `docs/evidence/sandbox-universe-v0/`. Same for `docs/mind-v3-sandbox-universe-lane-spec.md` (move or delete depending on the MIND v3 decision in the open question below).

The Ingrain README should be rewritten to memory-product-first framing with a Benchmarks section linking the new `sandbox-universe` repo and showing Ingrain's score.

### 3. End-to-end split repro test (task #16)

From a fresh venv, `pip install -e ./sandbox-universe -e ./ingrain && sandbox-universe run --lane ingrain-sidecar --universes-version v0` should reproduce the v0 ingrain-sidecar score (673/1000) within 1%. This is the load-bearing test that the split was lossless.

Requires #1 to finish first, and a local Hermes/Hindsight/OpenViking install.

### 4. Residual local paths to review

- `WORKLOG.md` in Ingrain mentions `/Users/benlloyd/Desktop/REPO/ingrain` in several places. It's a historical log — either redact or move out of the public repo.
- `src/aeonik_ingrain/evals/les_hard.py` has hard-coded `/Users/benlloyd/.hindsight` in a test scenario (it's the *content* of a "forbidden value" — redacting would change test semantics). Decide whether to keep as-is (real-world scenario) or refactor the scenario to use a placeholder path.

## Open questions

- **Aeonik MIND V3 lane**: keep in Ingrain (since it's Aeonik-internal) or move to `sandbox-universe` as a reference lane? `docs/mind-v3-sandbox-universe-lane-spec.md` will need re-homing either way.
- **Reports inside the PyPI package**: currently `reports/v0/` ships in the GitHub repo only, not in the `sandbox-universe-eval` wheel. Confirm before publishing to PyPI.
- **Aeonik branding**: `pyproject.toml` lists `aeonik-ingrain` as the package name and "Aeonik" as the author. README still refers to "Aeonik Ingrain" in places. Decide whether to rebrand to plain "Ingrain" or keep the Aeonik prefix.

## Checklist before flipping public

When all of the following are true, both repos are safe to make public:

- [ ] Task #14: reference lanes installed in `sandbox-universe`, Ingrain lanes registered via entry points.
- [ ] Task #15: `evals/sandbox_universe.py` and related docs removed from Ingrain; README rewritten.
- [ ] Task #16: fresh-venv repro of v0 ingrain-sidecar score passes within 1%.
- [ ] WORKLOG.md and `les_hard.py` local-path decisions made.
- [ ] CI passing on both repos for at least one push.
- [ ] One pair-programming pass with someone other than the author (or codex/cursor in an audit role) — fresh eyes on the README and the public framing.
- [ ] No `.env`, `.ingrain/`, `data/`, or `.claude/` files in either repo (verified by `git ls-files`).
- [ ] License + author attribution match across both repos.

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
```

## Recommendation

Keep both repos **private** until tasks #14, #15, #16 are complete. The current state is a strong proof-of-concept for the split and a strong portfolio artifact, but it is not yet a self-contained running benchmark. Pair-program through the lane porting with someone who has Hermes installed.

Once those land, the audit can be re-run, the checklist closed, and the repos flipped to public.
