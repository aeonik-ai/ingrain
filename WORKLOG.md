# Aeonik Ingrain Work Log

## 2026-05-19 00:25 PDT

- Created initial Aeonik Ingrain repo scaffold in `/Users/benlloyd/Desktop/REPO/ingrain`.
- Added Python package `aeonik_ingrain` with CLI entry points `ingrain` and `aeonik-ingrain`.
- Implemented local SQLite ledger, compiled markdown pages, deterministic promotion rules, hydration, Hermes ingest, and Hermes memory-provider template.
- Added README, docs, examples, MIT license, and initial tests.

## 2026-05-19 00:40 PDT

- Ran `python3 -m compileall src tests`; compile passed.
- System Python did not have `pytest`, so tests were converted to stdlib `unittest`.
- Ran initial `ingrain eval`; stale-plan score failed, which exposed a real supersession bug.
- Fixed event ordering and product-name supersession behavior.
- Fixed correction misclassification where a correction containing "shipped" could become track record.
- Added the first local LES-Core regression checks for Ingrain behavior.

Next:

- Re-run compile, unit tests, CLI eval, and install checks.
- Generate full eval report under `.ingrain/evals/latest.md`.
- Add live Hermes test-profile notes if local Hermes can be safely exercised without touching the active user profile.

## 2026-05-19 00:55 PDT

- Re-ran verification after fixes:
  - `python3 -m compileall src tests` passed.
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v` passed: 4 tests.
  - `ingrain eval` passed: LES-100 100/100.
- Generated full eval report at `docs/eval-report.md` and local artifacts under `.ingrain/evals/latest.*`.
- Installed Ingrain into a sandbox Hermes profile at `/private/tmp/hermes-ingrain-test`.
- Verified Hermes plugin discovery loads Ingrain, `is_available()` returns true, and four tools are exposed.
- Checked local Hermes plugin discovery for OpenViking. Bundled provider exists, but `OPENVIKING_ENDPOINT` is not configured, so live OpenViking benchmark was not run.
- Documented this in `docs/hermes-test-report.md`.

## 2026-05-19 01:05 PDT

- Fixed packaging metadata to use SPDX `license = "MIT"`.
- Verified local wheel build and install:
  - `python3 -m pip install --no-build-isolation --target /private/tmp/ingrain-install-target /Users/benlloyd/Desktop/REPO/ingrain` succeeded in the base environment.
  - Created `/private/tmp/ingrain-venv`, ran build-isolated venv install, and verified the installed `ingrain` console script.
  - `/private/tmp/ingrain-venv/bin/ingrain --home /private/tmp/ingrain-venv-eval eval` passed with LES-100 100/100.

## 2026-05-19 01:15 PDT

- Added hydration safety for prompt-injection markers.
- Fixed secret redaction so direct token patterns do not leak token prefixes.
- Added `tests/test_security.py` for redaction and prompt-injection withholding.
- Added launch copy and demo framing in `docs/launch.md`.

## 2026-05-19 01:20 PDT

- Re-ran verification after security hardening:
  - `python3 -m compileall src tests` passed.
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v` passed: 6 tests.
  - `ingrain eval` passed: LES-100 100/100.

## 2026-05-19 01:35 PDT

- Installed OpenViking 0.3.17 into `/private/tmp/openviking-venv` instead of mutating the active Hermes environment.
- Built and installed `llama-cpp-python` for OpenViking local embeddings.
- Started a local OpenViking server on `127.0.0.1:1933`; health check passed.
- Verified Hermes' bundled OpenViking provider can initialize against the server and exposes `viking_search`, `viking_read`, `viking_browse`, `viking_remember`, and `viking_add_resource`.
- Added `ingrain compare` to run a real OpenViking resource upload/index/search/read benchmark.
- Recorded this as compatibility history only; the current OpenViking evidence is the later `88/100` direct resource-retrieval run under `docs/evidence/live-openviking-resource/`.

## 2026-05-19 01:50 PDT

- Added a README architecture graphic at `assets/ingrain-architecture.svg`.
- Added a Mermaid diagram to the README so the repo explains the product at a glance.
- Updated install instructions to use the GitHub `pipx install` path until PyPI is live.
- Fixed project URLs to `https://github.com/aeonik-ai/ingrain`.
- Added `docs/publishing.md` with the PyPI release checklist.
- Updated launch docs with the recommended personal-account first, org-account amplification posture.

## 2026-05-19 02:05 PDT

- Updated the tagline to "Learned experience layer for autonomous agents."
- Clarified that LES-100 `100/100` is the expected score for the committed v0 fixture suite and should be read as a regression gate, not a universal benchmark claim.

## 2026-05-19 02:12 PDT

- Expanded LES as "Learned Experience Score" at the first README/eval output touchpoints so the acronym is not unexplained.

## 2026-05-19 02:40 PDT

- Fetched current official Hermes upstream and refreshed the compatibility map to `a0bd11d02`.
- Researched all eight Hermes memory providers from the upstream provider docs, bundled provider READMEs, and public provider docs/repos.
- Added `docs/hermes-memory-provider-comparison.md` with provider-by-provider positioning, a capability matrix, recommended use cases, and launch-safe framing.
- Added `assets/memory-provider-positioning.svg` as a shareable graphic for repo docs and launch content.

## 2026-05-19 03:10 PDT

- Ran a launch-safety editorial pass across README, eval docs, launch notes, provider comparison, and visual copy.
- Removed or softened overclaim language around "proof", provider leaderboards, OpenViking comparisons, and broad memory claims.
- Added explicit Hindsight positioning: Hindsight is the stronger general-purpose memory backend; Ingrain's claim is narrower, local, auditable practice memory for runner agents.
- Clarified LES-100 as a deterministic fixture/regression check, not an external benchmark or provider leaderboard.

## 2026-05-19 03:45 PDT

- Added the CLI + Skill adoption path:
  - `ingrain practice` writes `PRACTICE.md` and source-linked practice cards.
  - `ingrain skill install codex|claude|cursor|generic` writes agent skill instructions.
  - `ingrain attach` initializes, compiles practice artifacts, and installs a skill in one command.
- Added tiered hydration with `--level brief|cards|evidence`.
- Updated LES eval output with practice-layer checks for `PRACTICE.md`, cards, brief hydration, and evidence hydration.

## 2026-05-19 04:10 PDT

- Removed a modeled provider-comparison prototype before treating it as evidence.
- Added `ingrain live-eval`, a live-only LES provider matrix:
  - calls Hermes default memory through the installed Hermes `tools.memory_tool` API
  - calls Ingrain through Hermes' installed memory-provider plugin loader
  - probes Hindsight through Hermes and marks it blocked when no package/service/API key is available
  - checks OpenViking health and marks it blocked when no real server is reachable
- Ran the first live loop on the installed Hermes runtime:
  - Hermes default memory: `88/100`
  - Hermes + Ingrain: `100/100`
- Ran the expanded provider matrix on the same preregistered universes:
  - Hermes default memory: `88/100`
  - Hermes + Ingrain: `100/100`
  - Hindsight: blocked, no Hindsight package/service/API key detected
  - OpenViking: not scored in that early run because the server was not running
- Saved raw outputs and command logs under `docs/evidence/live-les-provider-matrix/`.
- Tightened loose `plan` and `project` promotion regexes after raw output showed harmless but noisy over-promotion in the goals/missions boundary universe.

## 2026-05-19 04:40 PDT

- Rechecked OpenViking before launch cleanup:
  - stopped the stale OpenViking server attempt after it failed to answer `/health`
  - verified the existing OpenViking 0.3.17 temp install could not reach a healthy server
  - installed OpenViking 0.3.17 with local embeddings into a clean Python 3.11 venv at `/private/tmp/openviking-uv311`
  - confirmed both the existing and clean installs failed local GGUF initialization with `ValueError: Failed to create llama_context`
  - confirmed a fresh OpenViking home reached server startup logs but still did not expose a healthy `/health`
- Added `docs/evidence/openviking-startup-recheck.md`.
- Clarified public docs so the historical OpenViking smoke result is not confused with the current live provider matrix.
- Softened evidence wording from "proves" to "supports" for public-facing scientific caution.

## 2026-05-19 05:10 PDT

- Explored a deterministic provider-comparison prototype and then removed it from the launch evidence path.
- Kept the useful compiler improvements from that exploration:
  - `Correction:` phrases are promoted as corrections
  - active-intent boundary memories supersede older plan memories
  - completed track-record memories can supersede older matching plans
- Updated `docs/learned-experience-results.md` to separate Ingrain self-evals from real provider runs.

## 2026-05-19 05:55 PDT

- Created the 10-minute heartbeat `continue-ingrain-les-hard-build` for continued autonomous work.
- Added `ingrain les-hard`, a harder Ingrain self-eval with 28 preregistered scenarios covering supersession, active-intent boundaries, provider claim safety, sandbox gotchas, secret redaction, project namespace collisions, abstention, premise awareness, implicit corrections, and unresolved conflicts.
- Saved LES-Hard raw outputs, CSV, JSON, and markdown report under `docs/evidence/les-hard-v0/` and mirrored the public report to `docs/les-hard-report.md`.
- Improved general compiler/hydration behavior surfaced by LES-Hard:
  - promote explicit `Lesson:` and `Observation:` lines
  - promote conversational "use X instead" corrections
  - preserve `Project ...` namespace text for project facts
  - supersede older same-subject decisions when a later decision clearly replaces them
  - preserve `Tests passed` track-record wording
  - filter specific hydration queries away from unrelated project namespaces
  - treat empty specific-query hydration as a valid abstention signal in LES-Hard
- Current LES-Hard v0 result:
  - Ingrain: `542/560`
- Updated README, eval standards, eval docs, learned-experience results, launch notes, and publishing notes with LES-Hard framing and claim boundaries.

## 2026-05-19 06:10 PDT

- Added `assets/ingrain-flow-animated.svg`, a self-contained animated SVG for the launch story:
  - agent run -> ledger -> promotions -> practice -> hydration -> better next run
  - no JavaScript, no build step, no Remotion dependency
- Added `docs/visual-demo.md` with the intended story beats, usage surfaces, and export options for social/video.
- Updated README and launch notes to link the animated visual and include it in the demo-video arc.

## 2026-05-19 21:55 PDT

- Removed non-real provider comparison artifacts and code:
  - deleted `src/aeonik_ingrain/evals/comparison.py`
  - deleted `docs/evidence/deterministic-les-comparison/`
  - removed provider comparison output from `ingrain eval`
  - made `ingrain les-hard` an Ingrain-only self-eval
- Installed and configured real OpenViking 0.3.17 locally with API-backed embedding/VLM settings outside the repo.
- Verified OpenViking health at `http://127.0.0.1:1933`.
- Added auditable direct OpenViking resource-retrieval artifacts under `docs/evidence/live-openviking-resource/`.
- Reran the full live provider matrix with real providers:
  - Hermes default memory: `88/100`
  - Ingrain Hermes provider: `100/100`
  - Hindsight local embedded: `62/100`
  - Hermes OpenViking provider: `30/100`
  - Direct OpenViking resource retrieval: `88/100`
- Updated README, eval docs, live reports, Hermes report, and OpenViking setup notes to remove stale blocked-provider language and separate resource retrieval from learned-experience provider behavior.
- Verification:
  - `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m aeonik_ingrain.cli eval`
  - audit for non-real provider-baseline wording returned no matches

## 2026-05-20 00:05 PDT

- Added `docs/sandbox-universe-eval-spec.md`, the spec for a harder turn-by-turn benchmark tier:
  - multi-session traces
  - multi-thread project history
  - source-of-truth conflicts
  - provider competition across Hermes default, Ingrain, Hindsight, and OpenViking
  - trace graphs, Mermaid output, and a Three.js visualization target
- Linked the spec from README and `docs/evals.md`.

## 2026-05-19 22:25 PDT

- Implemented the first runnable Sandbox Universe Eval v0 harness:
  - `ingrain universe-eval`
  - five L3 universes and one L4 universe in `src/aeonik_ingrain/evals/sandbox_universe.py`
  - deterministic 100-point component scoring per universe
  - raw provider outputs, command logs, `results.json`, `results.csv`, `providers.json`, `graph.json`, and `graph.mmd`
  - Three.js viewer at `docs/visualizations/sandbox-universe-3d.html`
- Ran the first full real L3 provider matrix:
  - Hermes default memory: `275/500`
  - Ingrain Hermes provider: `184/500`
  - Hindsight local embedded: `202/500`
  - Hermes OpenViking provider: `125/500`
- Key finding: the benchmark is now hard enough, and Ingrain's next improvement target is explicit trace/source-ID preservation in hydration.

## 2026-05-19 22:45 PDT

- Added more Sandbox Universe complexity:
  - `thread_fork_reconciliation_l4`
  - `partial_completion_status_l4`
  - `adversarial_secret_status_l5`
  - `conflicting_metrics_l5`
- Added level breakdown and failure taxonomy sections to the Sandbox Universe report.
- Improved trace metadata handling:
  - parses bracketed `source_id`, `thread`, `session`, `kind`, and turn metadata before promotion
  - keeps trace source IDs in hydration and compiled pages
  - fixes the prior malformed `turn=...` correction text in Ingrain output
- Ran a full real L5 provider matrix later superseded by the 2026-05-20 five-lane run.
- Key finding: Ingrain now preserves source IDs on direct corrections, but needs better source-of-truth document promotion and multi-doc current-truth synthesis.

## 2026-05-20 03:58 PDT

- Added the fifth Sandbox Universe lane:
  - `ingrain-sidecar` = Hermes default memory remains active while Ingrain is used through CLI/practice hydration.
  - This is separate from `ingrain`, where Ingrain occupies the Hermes memory-provider slot.
- Improved Ingrain compiler behavior:
  - source-of-truth docs, reports, run logs, and roadmap docs can promote without magic `Decision:` wording
  - stale drafts, external-project docs, invalidated reports, and old plans are not promoted by default
  - supersession edges can retire stale trace documents by source ID
- Hardened the provider harness:
  - subprocesses run in process groups and are killed on timeout
  - Hindsight local embedded evals use per-universe profiles and shorter idle timeout
  - the harness cleans Hindsight eval daemons after each Hindsight universe
- Ran the full real L5 provider matrix with localhost/network access for real OpenViking and Hindsight:
  - Hermes default memory: `623/1000`
  - Hermes default + Ingrain CLI/skill sidecar: `673/1000`
  - Ingrain Hermes provider: `673/1000`
  - Hindsight local embedded: `405/1000`
  - Hermes OpenViking provider: `245/1000`
- Key finding: source-of-truth promotion is a large general improvement for Ingrain, but repeated-work/status synthesis remains weak (`repeated_work_cross_thread_l4` is still `37/100`).
