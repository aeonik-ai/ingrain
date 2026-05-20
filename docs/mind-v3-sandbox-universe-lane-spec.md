# Aeonik MIND V3 Sandbox Universe Lane Spec

Status: adapter v0 implemented; live scoring blocked pending MIND V3 live eval environment

Owner: Aeonik Ingrain

Target repo: `<repo-root>`

MIND repo: `<redacted-local-path>/Desktop/REPO/aeonik/apps/server`

## Goal

Add an experimental Aeonik MIND V3 lane to Sandbox Universe Eval so the same turn-by-turn traces can be tested against Aeonik's event-sourced memory layer.

The first goal is evidence, not a launch claim. The lane should answer:

> Can MIND V3, used as a Hermes sidecar memory substrate, recover the same learned experience signals that Ingrain, Hindsight, OpenViking, and Hermes default memory are judged on?

## Non-Goals

- Do not claim MIND V3 beats Hindsight, OpenViking, Hermes default, or Ingrain unless a real run supports the exact claim.
- Do not present mock MIND runs as real provider results.
- Do not make MIND V3 own Hermes active goals, missions, Kanban columns, scheduling, or task lifecycle.
- Do not add a second task system.
- Do not use removed MIND event types such as `doc`, `memory`, `state`, or `synopsis`.

## Lane Name

Preferred provider lane:

```text
aeonik-mind-v3-sidecar
```

Accepted short aliases for local CLI ergonomics:

```text
mind-v3
aeonik-mind
```

The public docs should call this an experimental internal lane until it has real local run artifacts.

## Hypothesis

MIND V3 may be strong at provenance, event shape, project memory, and durable source history. It may be weaker than Ingrain at learned-experience judgment unless it has a compiler or synthesis layer that promotes corrections, stale-plan warnings, source-truth precedence, and completed outcomes into compact behavior-shaping context.

The useful outcome is not only the score. The useful outcome is knowing whether Ingrain should borrow more from MIND V3's event model, project frames, edges, or search surfaces.

## Evidence Rules

Every MIND row must be one of:

| Status | Meaning | Public score allowed? |
|---|---|---|
| `live` | A real local MIND V3 API or in-process MemoryAPI path ran against the trace and returned output. | Yes |
| `blocked` | The lane could not run; command logs show the exact missing dependency, service, or env. | No |
| `mock` | A unit-test-only adapter used mock storage. | No |

Mock storage is acceptable for adapter tests. It is not acceptable as provider proof.

## Canonical MIND Mapping

The adapter must write only canonical MIND V3 event types:

| Sandbox trace input | MIND event type | Notes |
|---|---|---|
| Source of truth document | `artifact` | Preserve `source_id`, `kind`, `created_at`, project, and universe ID in metadata. |
| User correction | `reflection` | Store as learned correction, not active intent. |
| Decision | `decision` | Preserve supersession edges when present. |
| Assistant action or attempted work | `action` | Include session, thread, turn, and outcome if known. |
| Failure or observation | `observation` | Use for run failures, blocked installs, stale-result observations. |
| Completed outcome | `metric` or `reflection` | Use `metric` for measured completion state; use `reflection` for the learned lesson. |
| Query turn | `interaction` | The final eval query should be traceable. |

Required metadata for content-like events:

```json
{
  "source_type": "document",
  "source_system": "ingrain_sandbox",
  "category": "living"
}
```

The adapter may extend metadata with `universe_id`, `level`, `source_id`, `session_id`, `thread_id`, `turn`, `trace_kind`, and `supersedes`.

## Integration Plan

### Phase 1 - Discovery

Confirm the real local MIND run path from `<redacted-local-path>/Desktop/REPO/aeonik/apps/server` using `uv run`.

Candidate commands to test:

```bash
cd <redacted-local-path>/Desktop/REPO/aeonik/apps/server
uv run python -m mind.serve --mock
uv run python api.py
uv run pytest mind/tests/ -v
```

Record exact command output under:

```text
docs/evidence/mind-v3-sandbox-lane/commands/
```

### Phase 2 - Adapter

Implement an optional Sandbox Universe provider named `aeonik-mind-v3-sidecar`.

The provider should:

- create an isolated agent/project namespace per eval run
- ingest source docs and trace turns into MIND
- query MIND using the real local API or MemoryAPI path
- synthesize a single output string from returned MIND context
- run through the existing Sandbox Universe scorer unchanged
- write raw output and command logs

### Phase 3 - Real Run

Run at least:

```bash
ingrain universe-eval --provider aeonik-mind-v3-sidecar --level 3
```

Then, if stable:

```bash
ingrain universe-eval --level 5
```

The full matrix may include the MIND lane only when it has live or blocked evidence. Do not silently omit failures.

### Phase 4 - Analysis

Compare MIND V3 against the current lanes by failure mode:

- stale claim leakage
- source-truth precedence
- cross-thread continuity
- active-goal/Kanban boundary
- repeated-work synthesis
- source traceability
- compactness
- abstention discipline

If MIND fails because raw retrieval is not enough, document the missing compiler behavior rather than hiding the failure.

## Hermes Boundary

Hermes owns intent:

- active goals
- missions
- Kanban columns
- scheduling
- task lifecycle
- what the agent should do next

MIND V3 and Ingrain own experience:

- durable corrections
- prior decisions
- lessons
- stale-plan warnings
- completed outcomes
- prior failures
- source evidence

If Hermes goals, missions, or Kanban say something is active, Hermes wins. If MIND recalls an old plan, that plan is background context only unless the current Hermes state makes it active.

## Acceptance Criteria

- `docs/sandbox-universe-eval-spec.md` lists the MIND V3 lane as experimental.
- `ingrain universe-eval --provider aeonik-mind-v3-sidecar --level 3` returns either a real scored run or a blocked result with command evidence. Current status: blocked because the local MIND path is present, but live eval env variables are not configured.
- Focused MIND-only runs live under `docs/evidence/mind-v3-sandbox-lane/`.
- Full matrix MIND runs, once live env is configured, should live under `docs/evidence/sandbox-universe-v0/raw/aeonik-mind-v3-sidecar/` and `docs/evidence/sandbox-universe-v0/commands/aeonik-mind-v3-sidecar/`.
- No public doc contains a mock MIND score as provider evidence.
- Mapping tests verify that no removed MIND event types are emitted.
- README and eval docs are updated only after real or blocked artifacts exist.
- Work is committed and pushed in coherent increments.

## Heartbeat Loop

Every 10 minutes, continue from this spec:

1. Discover or recheck the real local MIND path.
2. Build the smallest real-or-blocked provider lane.
3. Add tests for event mapping and blocked-provider reporting.
4. Run L3 with MIND V3.
5. If L3 is stable, run L5 full matrix with MIND included.
6. Update reports, charts, graph data, and public docs only with real evidence.
7. Commit and push coherent increments.

Stop the loop when the acceptance criteria are complete and the repo has a clean public-facing audit.
