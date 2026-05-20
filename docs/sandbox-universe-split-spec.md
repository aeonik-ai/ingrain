# Sandbox Universe Split Spec

Status: proposed
Owner: Aeonik Ingrain
Goal: extract the Sandbox Universe benchmark into its own repo so it can be cited as a neutral artifact, while Ingrain remains an open-source memory product that ships a reference lane.

## Why

A benchmark scored by one of the systems it ranks has an inherent conflict-of-interest signal. Every credible agent benchmark — SWE-bench, GAIA, LongMemEval, AgentBench — lives in its own repo. Splitting also gives Ingrain a cleaner product story (memory layer, not eval framework with a memory layer attached) and lowers the bar for other memory systems (MemGPT, A-MEM, Letta, Zep) to submit lanes.

## Repo layout after the split

### `sandbox-universe/` (new, MIT, public)

```
sandbox-universe/
  README.md                          # benchmark-first framing, leaderboard, "how to submit a lane"
  DESIGN.md                          # why these 9 components, why L3/L4/L5, what was excluded
  CONTRIBUTING.md                    # how to add a universe, how to submit a lane
  LICENSE                            # MIT
  pyproject.toml                     # package: sandbox-universe-eval, zero runtime deps
  src/sandbox_universe/
    __init__.py
    universes/
      __init__.py                    # UNIVERSES registry
      launch_claims_conflict_l3.py
      provider_setup_recovery_l3.py
      ... (10 universes, one file each — easier to diff than the current single 1663-line file)
    types.py                         # SandboxUniverse, SourceDoc, TraceSession, TraceTurn
    scorer.py                        # the 9-component deterministic scorer
    runner.py                        # generic harness: load lane, run universes, write artifacts
    lanes/
      __init__.py                    # LaneAdapter protocol + registry
      hermes_default.py              # reference lane
      hindsight.py                   # reference lane
      openviking.py                  # reference lane
    cli.py                           # `sandbox-universe run --lane <name>`
  tests/
    test_scorer.py
    test_universes.py
  reports/
    v0/                              # frozen v0 evidence — exactly what Ingrain currently ships
      report.md
      results.json
      raw/<lane>/<universe>.txt
      commands/<lane>/<universe>.json
      graph.json
      graph.mmd
```

### `ingrain/` (current repo, MIT, public)

```
ingrain/
  README.md                          # memory-product-first framing
  src/aeonik_ingrain/
    ...                              # unchanged
    integrations/
      sandbox_universe/
        __init__.py
        lane.py                      # implements LaneAdapter for ingrain + ingrain-sidecar
        README.md                    # "how Ingrain plugs into Sandbox Universe"
    evals/
      runner.py                      # LES-Core, LES-Hard remain here
      les_hard.py
      live_les.py                    # provider-installation utilities used by lane.py too
      # sandbox_universe.py is REMOVED — generic harness moved to new repo
  pyproject.toml                     # adds `sandbox-universe-eval` as dev dep
```

## Lane adapter interface

The contract every provider implements. Lives in `sandbox-universe/src/sandbox_universe/lanes/__init__.py`.

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class LaneAdapter(Protocol):
    """A memory provider that can answer queries against a Sandbox Universe trace."""

    name: str                        # e.g. "ingrain-sidecar"

    def probe(self) -> dict:
        """Return health info: installed?, version, dependencies present. Raises on hard failure."""

    def run(self, universe: "SandboxUniverse", workdir: Path) -> "LaneResult":
        """Run the universe through this provider, return raw output + command log."""


@dataclass(frozen=True)
class LaneResult:
    raw_output: str                  # provider's answer to universe.query
    command_log: list[dict]          # subprocess calls, env, exit codes — for audit
    provider_error: str = ""         # non-empty if the lane failed; scorer should zero-score
    artifacts: dict[str, Path] = field(default_factory=dict)  # extra evidence files
```

Lanes are registered via entry points (`sandbox_universe.lanes` group) so external packages — including Ingrain — can register without modifying the benchmark repo.

```toml
# in ingrain/pyproject.toml
[project.entry-points."sandbox_universe.lanes"]
ingrain = "aeonik_ingrain.integrations.sandbox_universe.lane:IngrainLane"
ingrain-sidecar = "aeonik_ingrain.integrations.sandbox_universe.lane:IngrainSidecarLane"
```

The benchmark repo discovers all installed lanes at runtime. `sandbox-universe run --lane ingrain-sidecar` works whenever Ingrain is pip-installed in the same env.

## Versioning

- **Universe fixtures are versioned** in the benchmark repo as `v0`, `v1`, etc. v0 is frozen on split.
- **Score format is versioned** alongside fixtures. v0 scorer never changes; new components ship in v1.
- **Lanes are unversioned** — they pin to a fixture version when reporting.
- **Reports are immutable**: `reports/v0/` is never edited. A v0.1 re-run would land in `reports/v0/2026-06-01/` or similar.
- **Ingrain's CI** pins to a specific Sandbox Universe tag (`sandbox-universe-eval==0.1.0`) so benchmark updates don't silently shift Ingrain's self-reported score.

## What moves vs. what stays

### Moves to `sandbox-universe/`
- `src/aeonik_ingrain/evals/sandbox_universe.py`:
  - `SourceDoc`, `TraceTurn`, `TraceSession`, `SandboxUniverse` → `types.py`
  - `UNIVERSES` tuple → split into `universes/<name>.py` files
  - scoring functions → `scorer.py`
  - generic runner loop → `runner.py`
  - `HERMES_DEFAULT_SCRIPT`, `HINDSIGHT_PROVIDER_SCRIPT`, `OPENVIKING_PROVIDER_SCRIPT` → `lanes/{hermes_default,hindsight,openviking}.py`
- `docs/sandbox-universe-eval-spec.md` → `DESIGN.md` (rewritten)
- `docs/sandbox-universe-scoring.md` → folded into `DESIGN.md`
- `docs/sandbox-universe-report.md` → `reports/v0/report.md`
- `docs/evidence/sandbox-universe-v0/` → `reports/v0/` (whole tree)

### Stays in `ingrain/`
- `src/aeonik_ingrain/evals/les_hard.py` and `live_les.py` — LES-Core/Hard are Ingrain's internal regression gates, not part of the public benchmark
- `INGRAIN_PROVIDER_SCRIPT` and `INGRAIN_SIDECAR_SCRIPT` — these become the body of the Ingrain lane in `integrations/sandbox_universe/lane.py`
- All compiler, ingest, db, security, practice code
- `docs/learned-experience-model.md`, `docs/philosophy.md`, `docs/hermes-*` — product docs
- LES-Hard evidence under `docs/evidence/les-hard-v0/`

### Gets rewritten on split
- Ingrain's `README.md` — reframe as memory product. Add a "Benchmarks" section that links to `sandbox-universe` and shows Ingrain's score.
- `docs/launch-readiness-audit.md` — remove sandbox-universe sections; link out instead.
- `WORKLOG.md` — note the split, link both repos.

### Gets deleted from `ingrain/` after split
- `src/aeonik_ingrain/evals/sandbox_universe.py` (moved)
- `docs/sandbox-universe-eval-spec.md`, `docs/sandbox-universe-scoring.md`, `docs/sandbox-universe-report.md` (moved)
- `docs/evidence/sandbox-universe-v0/` (moved)
- `docs/mind-v3-sandbox-universe-lane-spec.md` (moves to benchmark repo as a separate lane spec, OR stays if mind-v3 lane is Ingrain-specific — decide at migration time)

## Naming, license, ownership

- **Repo name**: `sandbox-universe` (short, ungoogleable-in-a-good-way, matches the artifact name)
- **Package name on PyPI**: `sandbox-universe-eval` (the `-eval` suffix avoids name collision and signals purpose)
- **License**: MIT, same as Ingrain
- **Author/maintainer**: same human, but `AUTHORS` lists "Sandbox Universe contributors" — sets expectation it's not single-vendor
- **Governance for new lanes**: PR-based, must include (a) lane code, (b) probe output, (c) one full evidence run on v0 universes, (d) signed statement that the fixtures were not used during the provider's training. Bar low enough to invite submissions, high enough to keep results auditable.

## Migration checklist

1. **Snapshot Ingrain at the split point** — tag `v0.1.0-pre-split` on `main`.
2. **Create new repo locally** at `../sandbox-universe/` (sibling). No GitHub remote yet.
3. **Copy files** (don't `git mv` — break history cleanly; the new repo gets a fresh `git init` with a single "Initial commit (extracted from ingrain@<sha>)" pointing at the snapshot tag for provenance).
4. **Refactor**:
   - Split `sandbox_universe.py` into the layout above.
   - Add `LaneAdapter` protocol and entry-point discovery.
   - Move reference lanes (hermes-default, hindsight, openviking) to `lanes/`.
   - Move v0 evidence under `reports/v0/`.
5. **Add `DESIGN.md`** (rewrite of current spec, scoped to benchmark-only concerns).
6. **Write `README.md`** — benchmark-first, includes the v0 leaderboard, links Ingrain as one reference lane.
7. **Write `CONTRIBUTING.md`** — how to add a universe, how to submit a lane.
8. **Set up tests + CI** in the new repo: `tests/test_scorer.py` (no provider needed), `tests/test_universes.py` (loadability checks).
9. **In Ingrain**: add `integrations/sandbox_universe/lane.py`, register entry points, drop the old eval file and docs, update Ingrain README to link the benchmark repo.
10. **Run end-to-end**: from a fresh venv, `pip install -e ./sandbox-universe -e ./ingrain && sandbox-universe run --lane ingrain-sidecar --universes-version v0` reproduces a score within 1% of `reports/v0/report.md`. If not, debug before publishing.
11. **Publish**: push `sandbox-universe` to GitHub (org or personal), then push the Ingrain post-split commit. Update Ingrain README with the new repo link.
12. **Announce**: one short blog post / README banner on both repos linking the other.

## Open questions

- Should the `aeonik-mind-v3` experimental lane move to the benchmark repo, stay in Ingrain, or live in a third repo? Defer until after split — easier to decide once the lane interface is concrete.
- Should `reports/` ship in the package or only on GitHub? Probably GitHub-only — keeps PyPI install lean.
- LongMemEval adapter (planned): goes in the benchmark repo as a parallel benchmark, not under `sandbox-universe`. Could be the same repo with a `longmemeval/` sibling, or a third repo `agent-memory-bench` that holds both. Punt until the adapter exists.

## Success criteria

- A Universes recruiter clicking `sandbox-universe` sees: a benchmark with a methodology doc, an honest leaderboard where Ingrain doesn't win every universe, multiple reference lanes, instructions to add your own.
- A potential Ingrain user clicking `ingrain` sees: a memory layer for agents, with a "benchmarked at 673/1000 on Sandbox Universe v0" line that links out to an independent-looking benchmark.
- An external memory-system author can submit a lane in under an hour using `CONTRIBUTING.md` + `lanes/hindsight.py` as a template.
