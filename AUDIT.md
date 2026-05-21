# Public-Readiness Audit (v0.2, 2026-05-20)

State of the Ingrain repo for a public release at v0.2. Living document — update at every release.

## Repos

| Repo | URL | Visibility | Purpose |
|---|---|---|---|
| `benlloydg/ingrain` | https://github.com/benlloydg/ingrain | private (pending public) | Learned-experience layer (the memory product) |
| `benlloydg/sandbox-universe` | https://github.com/benlloydg/sandbox-universe | private (pending public) | Trace-level benchmark + cross-validation harness |
| `aeonik-ai/ingrain` | https://github.com/aeonik-ai/ingrain | private | Pre-split snapshot; archive only |

## v0.2 evidence summary

Three benchmark wins, one external:

| Benchmark | n | hermes-default | ingrain-llm-sidecar | Δ |
|---|---:|---:|---:|---:|
| **LongMemEval Oracle stratified (external)** | 50 | 0.434 | **0.588** | **+0.154 / +35.6% relative** |
| CarryForward v0.1 (custom carry-forward) | 20 | 0.882 | 0.924 | +0.042 |
| Sandbox Universe v0 (our benchmark) | 10 | 0.623 | 0.673 | +0.050 |
| Plus: LongMemEval _s 50-Q (long haystacks) | 50 | 0.002 | _running_ | _TBD — predicted >0.20_ |

n=50 LongMemEval Oracle: 12 per-question wins, 0 losses, 38 ties. The sidecar architecture is empirically `≥ default` by construction.

Raw evidence in [`sandbox-universe/reports/`](https://github.com/benlloydg/sandbox-universe/tree/main/reports).

## Architecture (v0.2)

- **LLM consolidator** (`integrations/hermes_consolidator/`): replaces the regex compiler. Uses `hermes -z` so the consolidator runs against whatever model the user has Hermes configured against. No external API key.
- **Sidecar lane** (`integrations/sandbox_universe/lane.py:IngrainLLMSidecarLane`): Hermes default memory + Ingrain compiled cards in the same prompt. By construction ≥ default.
- **`ingrain why <query>`**: audit-trail CLI. Shows source events for any card matching the query. Product property no other memory system has.
- **Hermes auto-consolidate plugin** (`integrations/hermes_plugin/`): post_tool_call + on_session_end hooks. `ingrain install hermes-plugin` installs into `~/.hermes/plugins/ingrain-auto/`. Restart Hermes to activate.
- **`ingrain record --batch <jsonl>`**: 400x speedup on bulk ingest (needed for long-haystack benchmarks like LongMemEval _s).

The deterministic regex compiler (`compiler/rules.py`) is now a no-LLM fallback. Empirically broken on conversational data (LongMemEval Oracle, 0/12 score). Not recommended for new deployments; kept for backward compatibility.

## Public-readiness checklist

### Code

- [x] LICENSE (MIT)
- [x] pyproject.toml URLs point to `benlloydg/ingrain`
- [x] CI workflow runs tests + LES-Core gate on every push
- [x] Makefile with `make install / test / lint / check / eval / les-hard`
- [x] 63 unit tests pass
- [x] No `.env`, `.ingrain/`, `data/`, `.claude/` committed (gitignored)
- [x] No API keys or auth tokens in source

### Documentation

- [x] README leads with v0.2 evidence
- [x] README has install instructions
- [x] Compiler-rules-explained.md has v0.2 banner pointing at LLM consolidator
- [ ] **TODO**: docs/ has ~10 stale pre-v0.2 docs that need deletion or rewrite (see "Known cleanup work" below)
- [ ] **TODO**: WORKLOG.md still has local paths and is a stream-of-consciousness log; either redact or move to `.work/`

### Evidence

- [x] All 4 benchmark runs (Oracle smoke, Oracle 50-Q, CarryForward, Sandbox Universe v0) committed to sandbox-universe `reports/`
- [x] Sandbox Universe v0 has provenance (PROVENANCE.md) + redacted paths
- [x] LongMemEval Oracle 50-Q has per-question raw/answers/results + summary

### Cross-repo install story

- [x] `pip install -e ./sandbox-universe -e ./ingrain` works
- [x] `sandbox-universe list-lanes` discovers `ingrain` + `ingrain-sidecar` + `ingrain-llm-sidecar`
- [x] E2E repro verified at n=50 on Oracle and CarryForward

## Known cleanup work before going public

These don't affect correctness but affect first-read perception:

1. **WORKLOG.md** has local paths and chat-log feel. Decide: redact, move to `.work/`, or rewrite as semver CHANGELOG.
2. **docs/ has ~10 stale files** (evals.md, launch.md, launch-readiness-audit.md, learned-experience-results.md, les-hard-report.md, live-eval-report.md, live-hindsight-local-report.md, hermes-test-report.md, mind-v3-sandbox-lane-report.md, publishing.md, sandbox-universe-split-spec.md). Most should be deleted (commit history preserves) or moved to `docs/archive/`.
3. **`integrations/hermes/` top-level dir** is legacy. The new layout is `src/aeonik_ingrain/integrations/{hermes_provider, hermes_consolidator, hermes_plugin, sandbox_universe}/`. Confirm the top-level dir is unused and delete.
4. **`src/aeonik_ingrain/evals/les_hard.py`** has a hardcoded `/Users/benlloyd/.hindsight` in a test fixture (it's the "forbidden value" of a real scenario). Either parameterize or leave as honest historical content.
5. **`examples/launch-demo.md`** is pre-launch tone; rewrite as a real `ingrain consolidate` workflow.

## Open questions (no decision yet)

- **Aeonik branding**: package name stays `aeonik-ingrain`; some docs reference "Aeonik Ingrain". Decide: full Aeonik prefix or shorten to "Ingrain"?
- **PyPI publishing**: not yet published. Decide when to flip.
- **External lane submissions**: framework is ready (entry points), but no external lanes exist yet. Consider a "Wanted: Memory System Lane PRs" CONTRIBUTING entry.

## Recommendation

After the LongMemEval `_s` 50-Q run lands (in progress as of this commit), this v0.2 evidence is sufficient to:

- Flip both repos to public
- Link in a portfolio / job application
- Invite external lane submissions

The cleanup work above is taste/polish — none of it blocks public visibility, but landing 1–3 from the "Known cleanup" list before going public makes the first-read experience significantly better.

## Verification

```bash
# Ingrain
cd ingrain
make install
make test       # 63 tests
make eval       # LES-Core (regression gate, no LLM, no network)
make les-hard   # LES-Hard (self-eval)

# Sandbox Universe
cd ../sandbox-universe
make install
make check      # 49+ tests + lint + typecheck
make analysis   # regenerates sidecar isolation analysis

# Cross-repo (requires Hermes installed at ~/.hermes/hermes-agent)
python -m benchmarks.longmemeval \
    --data /path/to/longmemeval_oracle \
    --lane ingrain-llm-sidecar \
    --answerer claude-code \
    --output /tmp/repro
```
