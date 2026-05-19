# Launch Notes

## One-Liner

Aeonik Ingrain gives autonomous agents learned experience, so every run can make the next one better.

## Hero

```text
Aeonik Ingrain
Put agents into practice.
Learned experience for autonomous agents.
```

## X / Twitter

Recommended account order:

1. Personal account posts the story and demo.
2. `aeonik-ai` quotes or reposts with the canonical repo link.
3. Pin the repo on the org profile.

Why: personal launch posts travel farther because they have a human author, while the org gives the repo durability and a place to accumulate stars, issues, and follow-up releases.

```text
Most agents do not need bigger memory.
They need learned experience.

Today we are open-sourcing Aeonik Ingrain.

It turns live agent runs, corrections, decisions, and repeated work into behavior that carries forward across sessions.

Put agents into practice.

Works with Hermes first. Local-first. No API key required.
```

Install line for the first post before PyPI is live:

```text
pipx install "git+https://github.com/aeonik-ai/ingrain.git"
```

Install line after PyPI is live:

```text
pipx install aeonik-ingrain
```

Follow-up:

```text
The demo is simple:

1. Correct the agent once.
2. Kill the session.
3. Start fresh.
4. Ask it to do related work.

With Ingrain, the correction carries forward without replaying the transcript.

We score this with LES-100: Learned Experience Score.
```

## LinkedIn

```text
We are open-sourcing Aeonik Ingrain: learned experience for autonomous agents.

The problem is not just that agents forget. The deeper problem is that their experience does not reliably change future behavior.

Ingrain watches live runs, promotes durable lessons, compiles readable project memory, and hydrates future sessions with the small amount of context that matters.

It is local-first, eval-driven, and starts with Hermes Agent.

The goal is simple: put agents into practice.
```

Org repost:

```text
Aeonik Ingrain is live.

Learned experience for autonomous agents:
- local SQLite ledger
- deterministic compiler
- compact hydration
- Hermes integration
- LES-100 eval

Hermes owns intent. Ingrain owns experience.
```

Suggested visual: `assets/ingrain-architecture.svg`.

## Demo Video

Title options:

```text
I Put Hermes Into Practice
Giving Hermes Learned Experience with Aeonik Ingrain
```

Arc:

1. Show default cold-start failure.
2. Correct Hermes once.
3. Compile with Ingrain.
4. Start a clean session.
5. Show the correction carrying forward.
6. Show LES-100 and the comparison harness.
7. Explain why this is not RAG and not a vector database.

## Live Terminal Commands

```bash
ingrain demo correction
ingrain demo banana
ingrain compare
ingrain eval
```

## Things Not To Claim

- model-weight learning
- sentience
- consciousness
- OpenViking replacement
- active goal, mission, or Kanban manager
- live OpenViking benchmark unless a real server was configured and tested
