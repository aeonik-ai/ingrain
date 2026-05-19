# Hermes Notes

Current upstream map: [hermes-current-map.md](hermes-current-map.md).
Memory-provider comparison: [hermes-memory-provider-comparison.md](hermes-memory-provider-comparison.md).

Hermes has built-in memory plus one external memory-provider slot.

```text
Hermes built-in memory: always active
External provider slot: one provider at a time
```

Ingrain can run as:

- a sidecar CLI that ingests Hermes state and prints hydration context
- a CLI + Skill practice layer that keeps `PRACTICE.md` beside the repo
- a live provider that owns the external slot

This means Ingrain and OpenViking can be used together in sidecar mode today, but not as simultaneous live providers unless Hermes gains provider chaining.

Recommended v0 default:

```bash
ingrain attach --agent codex
ingrain ingest hermes
ingrain practice
ingrain hydrate --level brief --query "continue this Hermes project"
```

This keeps the current Hermes memory provider intact.

## Goals, Missions, And Kanban Boundary

Ingrain is not the source of truth for active intent.

Hermes owns active goals, missions, Kanban columns, scheduling, task lifecycle, and what the agent should do next.

Ingrain owns corrections, decisions, lessons, stale-plan warnings, completed outcomes, prior failures, and project rules learned from execution.

Precedence:

- If Hermes goals, missions, or Kanban say something is active, Hermes wins.
- If Ingrain recalls an old plan, it is background context only.
- If Ingrain has a correction or stale-plan warning, it can influence how Hermes performs the task, but it cannot create, move, close, or schedule tasks by itself.

Short version:

> Hermes owns intent. Ingrain owns experience.
> Kanban decides what is active. Ingrain remembers what was learned.

## Recommended V0 Use

Use Ingrain in the provider slot when the bottleneck is behavioral carry-forward:

- user corrections
- stale-plan avoidance
- project decisions
- completed outcomes

Use OpenViking when the bottleneck is resource retrieval:

- docs
- references
- browsable knowledge
- large semantic search
