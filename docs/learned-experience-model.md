# Learned Experience Model

Ingrain separates four things that often get blurred together:

```text
raw history       what happened
promotion         what matters
practice cards    source-linked lessons
PRACTICE.md       what should carry forward
hydration         what this turn needs
```

The goal is not to store more. The goal is to make future behavior more consistent with less context.

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

## Practice Cards

Practice cards are source-linked learned-experience units under `.ingrain/practice/cards/`.

Each card has:

- type
- status
- confidence
- source event ID
- guidance
- promotion reason

`PRACTICE.md` compiles those cards into a human-readable artifact for agents and people.

## Hydration

Hydration is compact, source-linked, and instruction-safe. It should help the agent act more consistently without becoming a second prompt written by an attacker.

Hydration has three levels:

```text
brief     L0 practice brief
cards     L1 normal agent context
evidence  L2 source-linked audit context
```
