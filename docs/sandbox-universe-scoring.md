# Sandbox Universe Scoring

Sandbox Universe is designed to make agent-memory failures inspectable. It is not an opaque judge and it is not a general memory leaderboard.

Every provider receives the same structured trace: source-of-truth documents, run logs, sessions, turns, corrections, and supersession edges. The provider output is saved raw, then scored deterministically against preregistered expected and forbidden phrases.

## What The Score Means

Each universe is worth 100 points:

| Component | Points | What It Rewards |
|---|---:|---|
| Current truth | 20 | Returns the latest valid correction, decision, status, or source-of-truth fact. |
| Precedence reasoning | 15 | Chooses the right source when old drafts, chat turns, run logs, and docs conflict. |
| Cross-session continuity | 15 | Connects evidence across sessions and threads. |
| Forbidden suppression | 15 | Avoids stale launch claims, old plans, invalid names, and secret-like text. |
| Actionability | 10 | Provides behavior the runner can use next, not just a dump of memory. |
| Source traceability | 10 | Includes source IDs or equivalent refs. |
| Compactness | 5 | Stays small enough to inject into a runner agent. |
| Abstention discipline | 5 | Says when current status should be checked live or evidence is missing. |
| Diagram data completeness | 5 | Emits enough source refs for graph visualization. |

If a provider leaks forbidden stale text, the scorer caps the universe score so raw retrieval is not mistaken for safe learned experience.

## Example: Raw Recall Can Look Strong

Hermes default memory often preserves the exact trace text. That helps with source IDs and phrase recall:

```text
[source_id=doc_eval_v2] Only real provider runs may be used...
[source_id=session_launch_a.turn_2] Do not say that...
```

That can score well on recall and traceability. It can also leak old trace text such as:

```text
Ingrain beats Hindsight and OpenViking.
```

That is why Hermes default can have a strong total score while still being unsafe as a learned-experience layer. The failure taxonomy is required context, not optional footnotes.

## Example: Learned Experience Judgment

Ingrain tries to compile the trace into current behavior:

```text
Corrections:
- Do not say that. Say this is a narrow learned-experience smoke test backed by real provider runs.

Current project facts:
- Only real provider runs may be used for comparison claims.
```

That loses some raw transcript breadth, but it reduces stale-claim leakage and creates context a runner agent can actually use.

## Known Limits

| Limit | Consequence |
|---|---|
| Phrase matching is deterministic but literal. | Semantically correct paraphrases may receive less credit. |
| Providers are run through a common harness. | Hindsight or OpenViking may do better in workflows optimized specifically for them. |
| The benchmark is local and preregistered. | It is useful engineering evidence, not an industry-standard external benchmark. |
| Ingrain sidecar and provider currently score the same. | The eval proves both modes work; it does not prove sidecar adds quality beyond compatibility. |
| Repeated-work/status synthesis remains weak. | `repeated_work_cross_thread_l4` is still the main Ingrain failure mode. |

## Best Use

Use the score to drive iteration:

1. Inspect the failed universe.
2. Read the raw output.
3. Identify the failure class.
4. Change one general mechanism.
5. Rerun the same preregistered universe.
6. Keep the change only if it improves score without increasing stale leaks.

The benchmark is most valuable when it makes failures hard to hide.

