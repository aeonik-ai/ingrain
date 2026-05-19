# Learned Experience Results

## Hypothesis

A runner-agent memory layer should carry corrections, decisions, completed outcomes, and stale-plan warnings into the next run as current, compact, source-linked guidance.

## Method

| Control | Implementation |
|---|---|
| Deterministic universes | Ten preregistered local scenarios in `src/aeonik_ingrain/evals/comparison.py`. |
| Same input per mode | Each mode receives the same ordered event list and query. |
| No model calls | The comparison is dependency-free and repeatable. |
| Hindsight-style is labeled | The Hindsight row is a deterministic retain/recall/reflect-style baseline, not live Hindsight. |
| Live Hindsight path | Use `ingrain live-eval` when a real Hindsight package/service/API key is configured. |

## Results

| Mode | Score | Note |
|---|---:|---|
| Hermes default memory | 40/200 | Bounded curated memory only. |
| Hermes + OpenViking-style retrieval | 172/200 | Deterministic raw semantic retrieval baseline, not a live OpenViking benchmark. |
| Hermes + Hindsight-style synthesis | 196/200 | Deterministic retain/recall/reflect-style synthesis, not live Hindsight. |
| Hermes + Ingrain | 200/200 | Actual Ingrain compiler and hydration path. |

## Scenario Breakdown

| Scenario | Difficulty | Rationale | Scores |
|---|---:|---|---|
| `correction_after_failure` | 1 | A direct user correction should shape later launch copy. | Hermes default memory=4/20; Hermes + OpenViking-style retrieval=16/20; Hermes + Hindsight-style synthesis=16/20; Hermes + Ingrain=20/20 |
| `stale_product_name` | 2 | A later decision must beat an older product-name decision. | Hermes default memory=4/20; Hermes + OpenViking-style retrieval=16/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `approval_judgment` | 2 | The memory should change judgment, not just recall a failure. | Hermes default memory=4/20; Hermes + OpenViking-style retrieval=16/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `kanban_boundary` | 3 | Learned experience must not become a second active-task system. | Hermes default memory=4/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `sandbox_recovery` | 3 | A prior execution failure should alter the next attempt. | Hermes default memory=4/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `track_record` | 3 | Completed outcomes should be reportable without reviving old todos. | Hermes default memory=4/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `active_goal_stale_plan` | 4 | A remembered old plan must not turn into active intent. | Hermes default memory=4/20; Hermes + OpenViking-style retrieval=16/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `completed_vs_todo` | 4 | A completed outcome should suppress an older build todo. | Hermes default memory=4/20; Hermes + OpenViking-style retrieval=16/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `preference_exception` | 5 | The current rule includes an exception, not a one-line preference. | Hermes default memory=4/20; Hermes + OpenViking-style retrieval=16/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |
| `source_linked_actionability` | 5 | The output should be compact, source-linked, and directly usable. | Hermes default memory=4/20; Hermes + OpenViking-style retrieval=16/20; Hermes + Hindsight-style synthesis=20/20; Hermes + Ingrain=20/20 |

## Scoring Rubric

Each scenario is worth 20 points:

| Component | Points |
|---|---:|
| Expected Lesson Recall | 8 |
| Stale Or Forbidden Suppression | 4 |
| Actionability | 4 |
| Source Evidence | 2 |
| Compactness | 2 |

## Interpretation

The deterministic comparison supports a narrow engineering claim: Ingrain's compiler and hydration path are strong at turning prior execution experience into current practice memory. It does not show that Ingrain is a better general-purpose memory backend than live Hindsight, OpenViking, or any other Hermes provider.

The Hindsight-style baseline is intentionally strong and intentionally labeled. It models synthesized recall from retained memories, but it does not exercise Hindsight's real graph, entity, temporal, cloud, or local runtime.

## Artifacts

- Machine-readable results: `docs/evidence/deterministic-les-comparison/results.json`
- CSV scores: `docs/evidence/deterministic-les-comparison/results.csv`
- Live provider matrix: `docs/evidence/live-les-provider-matrix/`
