# Launch Readiness Audit

Date: 2026-05-20

Scope: public-facing repo posture after Sandbox Universe Eval v0, with real Hermes default, Ingrain sidecar, Ingrain provider, Hindsight local, and OpenViking provider lanes.

## Verdict

Ready for a cautious open-source launch as a learned-experience layer, not as a broad memory-provider winner.

The repo now has inspectable evidence, raw provider outputs, command logs, deterministic scoring, a graph artifact, a Three.js viewer, and explicit no-overclaim language. The strongest launch claim is:

> Ingrain improves trace-level learned-experience behavior on this preregistered Sandbox Universe benchmark, especially source-of-truth promotion and stale-claim suppression. It still has visible misses on repeated-work and current-status synthesis.

## Technical Evaluator Framing

If this repo is read as a job-application or portfolio artifact, the strongest signal is not the score. The strongest signal is the work loop:

- identify a concrete agent failure class
- build a small system that addresses it
- design a hard local eval around the failure
- compare real provider lanes where available
- publish raw artifacts and command logs
- revise claims downward when the evidence is narrower than the ambition

Suggested one-paragraph framing:

> I built Ingrain, a learned-experience layer for autonomous coding agents, then built Sandbox Universe, a trace-level eval for stale-plan suppression, source-of-truth precedence, and cross-session judgment. The result is less a leaderboard than a failure microscope: it shows that raw memory can look strong while still leaking stale instructions, and it isolates where learned-experience systems need better synthesis.

Avoid leading with virality, winning, or broad provider comparisons. Lead with careful agent-systems research and the remaining failure modes.

## Issues Found And Fixed

| Issue | Risk | Fix |
|---|---|---|
| Ingrain source docs were too lossy. | Important source-of-truth docs did not promote unless they used magic phrasing like `Decision:`. | Added trace-kind promotion for `source_of_truth`, `report`, `run_log`, and `roadmap` docs. |
| Stale trace docs stayed active. | Old drafts and invalidated reports could pollute recall. | Added conservative stale trace-kind skipping and supersession-edge retirement by source ID. |
| Sidecar lane was missing. | The likely launch posture, Hermes default memory plus Ingrain CLI/skill, was not measured separately. | Added `ingrain-sidecar` as a fifth real lane. |
| Hindsight local mode leaked embedded processes. | Timed-out universes could distort later runs and burn CPU. | Added subprocess process-group timeouts, per-universe Hindsight profiles, short idle timeout, and cleanup after Hindsight universes. |
| OpenViking health was misread under sandboxed localhost. | A real available provider could be reported as unavailable. | Reran the real matrix with localhost/network permissions and recorded OpenViking as a scored real lane. |
| Older worklog scores could look current. | Readers might cite superseded numbers. | Marked the older L5 matrix as superseded and updated README/eval docs with the five-lane matrix. |

## Current Evidence

Current Sandbox Universe L5 result:

| Lane | Score |
|---|---:|
| Hermes default memory | 623/1000 |
| Hermes default + Ingrain CLI/skill sidecar | 673/1000 |
| Hermes + Ingrain provider | 673/1000 |
| Hindsight local embedded | 405/1000 |
| Hermes OpenViking provider | 245/1000 |

Artifacts:

- Report: [sandbox-universe-report.md](sandbox-universe-report.md)
- Raw evidence: [evidence/sandbox-universe-v0/report.md](evidence/sandbox-universe-v0/report.md)
- Graph JSON: [evidence/sandbox-universe-v0/graph.json](evidence/sandbox-universe-v0/graph.json)
- Mermaid graph: [evidence/sandbox-universe-v0/graph.mmd](evidence/sandbox-universe-v0/graph.mmd)
- 3D viewer: [visualizations/sandbox-universe-3d.html](visualizations/sandbox-universe-3d.html)
- Scoring explanation: [sandbox-universe-scoring.md](sandbox-universe-scoring.md)

## Remaining Risks

| Risk | Why It Matters | Public Posture |
|---|---|---|
| Repeated-work/status synthesis is still weak. | `repeated_work_cross_thread_l4` remains `37/100` for Ingrain. | Call it a product gap, not solved. |
| This is a local preregistered benchmark. | It is not LongMemEval, LoCoMo, BEAM, or EvoMemBench. | Do not claim SOTA memory. |
| Hindsight/OpenViking may improve with provider-specific tuning. | The current eval uses the same trace for fairness, not each system's ideal workflow. | Say "on this Sandbox Universe run", not "overall". |
| Ingrain provider and sidecar lanes currently score the same. | The harness proves both paths work, but not that sidecar adds extra benefit beyond Ingrain hydration alone. | Present sidecar as compatibility/adoption posture. |

## Verification

Latest local verification before commit:

- `PYTHONPATH=src python3 -m unittest discover -s tests -v` passed, 28 tests.
- `python3 -m compileall src tests` passed.
- `git diff --check` passed.
- Secret scan over current Sandbox Universe artifacts, docs, source, and tests found no real secret; only the redaction unit test contains a fake `api_key` fixture.
- Hindsight eval daemons were cleaned after the run; OpenViking remained running only while provider verification was needed.
