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
- Added deterministic comparison harness for learned experience substrates:
  - Hermes default memory
  - Hermes + OpenViking-style raw retrieval baseline
  - Hermes + Ingrain promotion/compile/hydrate

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
  - `/private/tmp/ingrain-venv/bin/ingrain --home /private/tmp/ingrain-venv-eval eval --no-comparison` passed with LES-100 100/100.

## 2026-05-19 01:15 PDT

- Added hydration safety for prompt-injection markers.
- Fixed secret redaction so direct token patterns do not leak token prefixes.
- Added `tests/test_security.py` for redaction and prompt-injection withholding.
- Added launch copy and demo framing in `docs/launch.md`.

## 2026-05-19 01:20 PDT

- Re-ran verification after security hardening:
  - `python3 -m compileall src tests` passed.
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v` passed: 6 tests.
  - `ingrain eval` passed: LES-100 100/100 and comparison Ingrain 120/120 vs OpenViking-style retrieval 108/120 vs default Hermes 36/120.

## 2026-05-19 01:35 PDT

- Installed OpenViking 0.3.17 into `/private/tmp/openviking-venv` instead of mutating the active Hermes environment.
- Built and installed `llama-cpp-python` for OpenViking local embeddings.
- Started a local OpenViking server on `127.0.0.1:1933`; health check passed.
- Verified Hermes' bundled OpenViking provider can initialize against the server and exposes `viking_search`, `viking_read`, `viking_browse`, `viking_remember`, and `viking_add_resource`.
- Added `ingrain compare --live-openviking` to run a real OpenViking resource upload/index/search/read benchmark.
- Live OpenViking resource-retrieval result: `96/120` on the learned-experience comparison scenarios.
- OpenViking long-term memory extraction was not fully benchmarked because the isolated server had no `OPENAI_API_KEY` or `OPENAI_ADMIN_KEY`; commit-time extraction logged a missing-credentials error.

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

- Removed the modeled Hindsight-style universe comparison before committing it as evidence.
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
  - OpenViking: blocked, no healthy server at `http://127.0.0.1:1933`
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

- Expanded the deterministic learned-experience comparison from 6 to 10 universes.
- Added explicit scoring components for expected lesson recall, stale/forbidden suppression, actionability, source evidence, and compactness.
- Added a clearly labeled `Hermes + Hindsight-style synthesis` baseline:
  - deterministic retain/recall/reflect-style behavior
  - not live Hindsight
  - not a general benchmark of Hindsight
- Improved general compiler rules:
  - `Correction:` phrases are promoted as corrections
  - active-intent boundary memories supersede older plan memories
  - completed track-record memories can supersede older matching plans
- Current deterministic comparison:
  - Hermes default memory: `40/200`
  - Hermes + OpenViking-style retrieval: `172/200`
  - Hermes + Hindsight-style synthesis: `196/200`
  - Hermes + Ingrain: `200/200`
- Added `docs/learned-experience-results.md` and deterministic artifacts under `docs/evidence/deterministic-les-comparison/`.
