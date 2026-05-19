# LES-Hard v0

## Hypothesis

Does prior execution experience become current, cautious, source-linked guidance under stale, conflicting, and missing-evidence conditions?

## Method

| Control | Implementation |
|---|---|
| Preregistered scenarios | 28 deterministic scenarios in `src/aeonik_ingrain/evals/les_hard.py`. |
| Same input per mode | Each mode receives the same event list and query. |
| No model calls | The run is dependency-free and repeatable. |
| Raw output audit | Every mode/scenario output is saved under `raw/<mode>/<scenario>.txt`. |
| Baseline labeling | Hindsight-style and OpenViking-style rows are deterministic approximations, not live provider evidence. |

## Results

| Mode | Score | Note |
|---|---:|---|
| Hermes default memory | 194/560 | Bounded curated memory only. |
| Hermes + OpenViking-style retrieval | 501/560 | Deterministic raw semantic retrieval baseline, not a live OpenViking result. |
| Hermes + Hindsight-style synthesis | 536/560 | Deterministic retain/recall/reflect-style synthesis, not live Hindsight. |
| Hermes + Ingrain | 545/560 | Actual Ingrain compiler and hydration path. |

## Scenario Breakdown

| Scenario | Category | Difficulty | Rationale | Scores |
|---|---|---:|---|---|
| `rename_supersedes_old_name` | supersession | 2 | A current product name must beat an older product name. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `general_hosting_supersession` | supersession | 4 | Later infrastructure decisions should replace older non-product decisions. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=16/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `style_rule_exception` | correction | 3 | The memory must preserve a rule with an exception. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=16/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `active_goal_boundary` | intent-boundary | 3 | Learned experience must not become a second source of active intent. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=14/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `old_plan_not_active_goal` | intent-boundary | 5 | An old plan should not be returned as what the runner should do now. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=15/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `completed_suppresses_todo` | outcomes | 4 | Completed outcomes should suppress older build todos. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `blocked_provider_not_failure_claim` | claim-safety | 4 | Blocked providers should not be turned into leaderboard wins. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=18/20; Hermes + Hindsight-style synthesis=18/20; Hermes + Ingrain=18/20 |
| `deterministic_baseline_boundary` | claim-safety | 4 | Style baselines must not be used as proof about real systems. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `sandbox_dependency_recovery` | execution-gotcha | 3 | A prior sandbox failure should change the next dependency-install attempt. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=10/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `hindsight_home_isolation` | execution-gotcha | 4 | Provider tests should isolate HOME to avoid permission failures. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `secret_redaction` | safety | 4 | Learned experience should retain the lesson without leaking secrets. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Hindsight-style synthesis=16/20; Hermes + Ingrain=20/20 |
| `chain_of_thought_boundary` | safety | 3 | The memory layer must not encourage storing private reasoning traces. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `project_namespace_collision` | namespace | 5 | Different project rules should not collide just because they share vocabulary. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=16/20; Hermes + Hindsight-style synthesis=16/20; Hermes + Ingrain=16/20 |
| `missing_evidence_abstention` | abstention | 5 | A memory layer should not invent facts for an unrelated query. | Hermes default memory=17/20; Hermes + OpenViking-style retrieval=18/20; Hermes + Hindsight-style synthesis=16/20; Hermes + Ingrain=17/20 |
| `unresolved_conflict_abstention` | abstention | 5 | Unresolved conflicting memories should trigger caution instead of pretending certainty. | Hermes default memory=4/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `source_linked_claim_boundary` | evidence | 3 | Launch claims should be source-linked and compact enough to audit. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=16/20; Hermes + Hindsight-style synthesis=17/20; Hermes + Ingrain=20/20 |
| `raw_transcript_not_lesson` | judgment | 4 | The useful memory is the correction, not the stale raw assistant mistake. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=16/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `metric_threshold_current` | evaluation | 4 | The current threshold should beat an older target metric. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=16/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `public_posture_personal_vs_org` | launch | 2 | The launch channel decision should be easy to carry forward. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `avoid_pypi_claim_before_release` | claim-safety | 3 | Install docs should not imply PyPI release before it exists. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `visual_artifact_not_required_backend` | scope | 3 | A missing visual polish item should not block a backend eval launch. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `environment_fact_not_global_truth` | premise-awareness | 5 | Local provider results should not become universal claims. | Hermes default memory=4/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `practice_memory_wording` | launch | 2 | A positioning correction should survive later wording. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `eval_score_humility` | evaluation | 4 | A perfect local score should be framed as a regression gate. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `external_benchmark_direction` | evaluation | 3 | The next credible benchmark should point to adjacent external standards. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `implicit_user_correction` | correction | 5 | Real corrections are often conversational and do not start with a clean marker. | Hermes default memory=7/20; Hermes + OpenViking-style retrieval=16/20; Hermes + Hindsight-style synthesis=16/20; Hermes + Ingrain=20/20 |
| `unresolved_conflict_without_marker` | abstention | 5 | Conflicting decisions without an explicit resolution should not become false certainty. | Hermes default memory=4/20; Hermes + OpenViking-style retrieval=14/20; Hermes + Hindsight-style synthesis=17/20; Hermes + Ingrain=14/20 |
| `current_status_requires_live_check` | premise-awareness | 5 | Memory can report past work, but it should not answer current external state as live truth. | Hermes default memory=4/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |

## Scoring Rubric

Each scenario is worth 20 points:

| Component | Points |
|---|---:|
| Expected Recall | 7 |
| Forbidden Suppression | 4 |
| Actionability | 3 |
| Premise Or Abstention | 3 |
| Source Evidence | 2 |
| Compactness | 1 |

## Interpretation

LES-Hard is intentionally harder than LES-Core. A non-perfect score is expected and useful: it creates room to improve without pretending a small fixture suite is an industry benchmark.

This report supports engineering iteration on learned-experience behavior. It does not prove Ingrain is better than live Hindsight, OpenViking, or any other provider.

## Artifacts

- Machine-readable results: `results.json`
- CSV scores: `results.csv`
- Raw mode outputs: `raw/`
- Live provider evidence: `docs/evidence/live-les-provider-matrix/`
