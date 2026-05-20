# Launch Notes

## One-Liner

Aeonik Ingrain gives autonomous agents learned experience, so lessons from one run can shape the next.

## Hero

```text
Aeonik Ingrain
Put agents into practice.
Learned experience layer for autonomous agents.
```

## X / Twitter

Recommended account order:

1. Personal account posts the story and demo.
2. `aeonik-ai` quotes or reposts with the canonical repo link.
3. Pin the repo on the org profile.

Why: personal launch posts travel farther because they have a human author, while the org gives the repo durability and a place to accumulate stars, issues, and follow-up releases.

```text
Some agent failures are not bigger-memory problems.
They are learned-experience problems.

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

With Ingrain, the correction can carry forward without replaying the transcript.

We track the launch regression gate with LES-Core: Learned Experience Score.
For the harder benchmark, see LES-Hard v0: 28 preregistered learned-experience scenarios with raw artifacts and non-perfect results.
```

## LinkedIn

```text
We are open-sourcing Aeonik Ingrain: learned experience layer for autonomous agents.

The problem is not just that agents forget. The deeper problem is that their experience does not reliably shape future behavior.

Ingrain watches live runs, promotes durable lessons, compiles readable project memory, and hydrates future sessions with the small amount of context that matters.

It is local-first, eval-driven, and starts with Hermes Agent.

The goal is simple: put agents into practice.
```

Org repost:

```text
Aeonik Ingrain is live.

Learned experience layer for autonomous agents:
- local SQLite ledger
- deterministic compiler
- PRACTICE.md
- generated agent skill
- compact hydration
- Hermes integration
- LES-Core eval
- LES-Hard benchmark

Hermes owns intent. Ingrain owns experience.
```

Suggested visuals:

- Static repo image: `assets/ingrain-architecture.svg`
- Animated launch explainer: `assets/ingrain-flow-animated.svg`
- Visual plan and export notes: `docs/visual-demo.md`

## Demo Video

Title options:

```text
I Put Hermes Into Practice
Giving Hermes Learned Experience with Aeonik Ingrain
```

Arc:

1. Show a cold-start miss.
2. Correct Hermes once.
3. Play the animated flow: run -> ledger -> promotions -> practice -> hydration -> better next run.
4. Compile with Ingrain.
5. Start a clean session.
6. Show the correction carrying forward.
7. Show LES-Core, the live provider matrix, and the claim boundary.
8. Show LES-Hard as the credible proof page: harder scenarios, raw artifacts, and misses we still need to improve.
9. Explain why this is not RAG and not a vector database.

## Live Terminal Commands

```bash
ingrain demo correction
ingrain demo banana
ingrain attach --agent codex --target-dir ./.ingrain/skills/ingrain
ingrain hydrate --level brief --query "write launch copy"
ingrain compare
ingrain les-hard
ingrain eval
```

## Things Not To Claim

- model-weight learning
- sentience
- consciousness
- OpenViking replacement
- active goal, mission, or Kanban manager
- live OpenViking benchmark unless a real server was configured and tested
- "better than Hindsight" or "SOTA memory"
- universal memory benchmark claims
- provider leaderboard claims without real provider runs
