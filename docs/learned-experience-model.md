# Learned Experience Model

Ingrain separates four things that often get blurred together:

```text
raw history       what happened
promotion         what matters
compiled pages    what should carry forward
hydration         what this turn needs
```

The goal is not to store more. The goal is to make future behavior better with less context.

## Ledger

The ledger uses Aeonik MIND's canonical event types where possible:

```text
artifact, interaction, observation, action, decision, plan, goal, reflection,
metric, experiment, chunk
```

## Promotions

Promotions are learned-experience categories:

- correction
- decision
- project_fact
- lesson
- risk
- track_record
- status

A correction is not a ledger event type. It is promoted from observations, interactions, decisions, or reflections.

## Hydration

Hydration is compact, source-linked, and instruction-safe. It should help the agent act better without becoming a second prompt written by an attacker.
