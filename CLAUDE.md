# CLAUDE.md — agent onboarding

If you are an AI agent (Claude Code, Cursor, Codex, etc.) opening this repo, read this first. It's a 90-second orientation.

## What this repo is

**Ingrain** is a *learned-experience layer* for AI agents — NOT a generic memory backend. It records corrections, decisions, and durable facts into a local SQLite ledger, consolidates them into typed cards via an LLM (using the user's Hermes-configured model — no API keys), and re-hydrates them into agent context on the next session.

The differentiator is `ingrain why <query>` — an audit trail showing which prior event led to any current "belief." No other memory system (MemGPT, Mem0, Letta, Zep) provides this.

Companion benchmark repo: [`benlloydg/sandbox-universe`](https://github.com/benlloydg/sandbox-universe). Five committed benchmark wins live there.

## Run this first to verify your env

```bash
make install     # pip install -e .
make test        # 63 unit tests, no LLM, no network. Must pass.
make eval        # LES-Core regression gate (deterministic, ~1s).
```

If `make test` doesn't pass, do not propose changes. Investigate first.

## Where things live (the only directory map you need)

```
src/aeonik_ingrain/
├── cli.py                        ← argparse + subcommand dispatch
├── db.py                         ← IngrainStore (SQLite). Public methods: add_event, list_events, add_promotion, list_promotions.
├── compiler/
│   ├── rules.py                  ← LEGACY regex compiler. Empirically broken on conversational data. Do not extend.
│   ├── hydrate.py                ← Cards → compact context block for the next turn.
│   └── pages.py                  ← compile_store(): clears + repopulates promotions table from events.
├── integrations/
│   ├── hermes_consolidator/      ← The v0.2 LLM consolidator. PRIMARY PATH. Replaces compiler/rules.py.
│   │   ├── consolidator.py       ← consolidate(store, ...) shells out to `hermes -z`, parses JSON cards.
│   │   └── prompts/consolidator.md  ← THE system prompt. Edit this when you want to change classification behavior.
│   ├── hermes_plugin/            ← Hermes lifecycle plugin. post_tool_call + on_session_end hooks.
│   └── sandbox_universe/lane.py  ← LaneAdapter implementations for the benchmark repo.
└── hermes_provider.py            ← The memory-provider plugin (alternative to sidecar; less common path).

tests/                            ← unittest, stdlib only. Naming: test_<module>.py
docs/research-arc.md              ← THE 10-minute narrative. Read this if you want context.
docs/archive/                     ← Pre-v0.2 historical docs. Do not cite as current.
```

## How to make a change safely

1. **Tests are the contract.** If you're changing scoring, prompt logic, supersession rules, or the consolidator output schema, also write a test that pins the new behavior. Otherwise the regex tests will silently allow regressions.
2. **Never modify `compiler/rules.py` to fix conversational misclassification.** It is intentionally deprecated. Fix the consolidator prompt or the consolidator pipeline instead. The LongMemEval Oracle 0/12 result documented in `docs/research-arc.md` is the receipt for this rule.
3. **Don't introduce dependencies.** `aeonik-ingrain` is zero-runtime-dep by design. Adding `requests`, `openai`, `anthropic`, or similar requires explicit user approval and a new entry in the AUDIT.
4. **Don't add API keys.** The consolidator runs through `hermes -z` so the user's existing Hermes config drives model selection. If you find yourself reaching for `os.environ['OPENAI_API_KEY']`, you're on the wrong path.
5. **Cards must cite real event IDs.** Defensive code in `consolidator.py` drops cards whose `event_id` isn't in the current batch. Don't bypass this — it's the audit-trail guarantee.
6. **`ingrain practice --no-compile`** is load-bearing. If you change practice-card generation, remember that the LLM-consolidator path passes `--no-compile` so the deterministic compile_store() doesn't wipe the consolidator's cards.

## Common gotchas

- **`hermes -z` inside the lane subprocess**: the outer Ingrain lane sets a sandboxed `HERMES_HOME` for provider isolation. The inner `hermes -z` consolidator call MUST pop `HERMES_HOME` from the env so it can find user auth at the real `~/.hermes`. This is implemented in `_run_hermes()` in `consolidator.py`. If consolidation suddenly returns empty in subprocess contexts, check the env propagation.
- **`hermes -z` with `--add-dir <some-dir>`** auto-loads CLAUDE.md from the surrounding repo and confuses the model. Use `--append-system-prompt <file>` instead. Documented in `benchmarks/longmemeval/answerer/claude_code.py` (in the sister repo).
- **The Sandbox Universe scorer is substring-matching only**. The bidirectional check is in `benchmarks/longmemeval/scorer.py` with explicit guards (shorter side ≥ 3 chars; "I don't know" doesn't trigger matches). Don't loosen these guards without re-running every committed eval.

## What to do if you're stuck

1. Read `docs/research-arc.md` (10 min). It explains the architectural pivot and why the current code looks the way it does.
2. Read the most recent commit message (`git log -1`). It usually explains the immediate context.
3. Check `AUDIT.md` for known open items.
4. Run `ingrain doctor` for environment diagnosis.

## What NOT to do

- Don't refactor the regex compiler. It's a deprecated path kept as a no-LLM fallback for users who insist on determinism.
- Don't add new card types beyond the v0.2 taxonomy (`correction`, `decision`, `lesson`, `project_fact`, `track_record`, `risk`, `status`) without an explicit user discussion. Wider taxonomies are easy to propose and hard to retire.
- Don't try to "improve" the consolidator prompt by making it more permissive. The Sandbox Universe v0 regex failure was precisely from over-promotion. Be specific about what gets promoted; the table in `prompts/consolidator.md` is the source of truth.
- Don't create new top-level docs without checking if one already exists. We just consolidated a lot of pre-v0.2 docs into `docs/archive/`.

## If you can read the sister repo

Run a benchmark to verify cross-repo install:

```bash
# Assumes ../sandbox-universe is checked out alongside this repo.
pip install -e ../sandbox-universe -e .
sandbox-universe list-lanes  # should include ingrain, ingrain-sidecar, ingrain-llm-sidecar
```

If that works, the entry-point registration is live and the cross-repo integration is healthy.
