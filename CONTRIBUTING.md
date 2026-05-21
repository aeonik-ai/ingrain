# Contributing to Ingrain

Thanks for the interest. Ingrain is small and still pre-v1; the path to contribution is intentionally narrow.

## What I'm looking for

- **Bugs in the consolidator prompt or output parsing.** If `ingrain consolidate` emits bad cards on a real conversation, open an issue with the events + the offending output. The prompt at `src/aeonik_ingrain/integrations/hermes_consolidator/prompts/consolidator.md` is the source of truth.
- **Bugs in `ingrain why` audit-trail output.** This is Ingrain's main differentiator; misattribution is the worst possible bug.
- **Hermes plugin lifecycle bugs.** `integrations/hermes_plugin/__init__.py` runs as a Hermes lifecycle hook. If a session ends and consolidation doesn't fire (or fires twice), I want to know.
- **External memory-system lanes for Sandbox Universe.** That repo's `CONTRIBUTING.md` documents the protocol; the most valuable thing anyone can submit is a MemGPT / Letta / Mem0 / Zep lane so we can stop relying on the author for cross-validation.

## What I'm not looking for (yet)

- New card types beyond the v0.2 taxonomy. The set is `correction`, `decision`, `lesson`, `project_fact`, `track_record`, `risk`, `status`. Wider taxonomies are easy to propose and hard to retire.
- Wrappers around `ingrain` for specific agents. Ingrain integrates via the CLI + skill pattern; users can write their own wrappers without needing them in core.
- Refactors of the regex compiler at `src/aeonik_ingrain/compiler/rules.py`. It's intentionally deprecated; the LLM consolidator is the path forward.

## Dev setup

```bash
git clone https://github.com/aeonik-ai/ingrain.git
cd ingrain
pip install -e ".[dev]"
make test      # 63 unit tests, no LLM, no network
make eval      # LES-Core regression gate
```

The cross-repo install pattern (with the benchmark repo):

```bash
pip install -e ./sandbox-universe -e ./ingrain
sandbox-universe list-lanes   # should show ingrain, ingrain-sidecar, ingrain-llm-sidecar
```

## Evaluation integrity

If you submit a PR that affects scoring, follow the conventions in [`AGENTS.md`](AGENTS.md):

- Label every run as `live` (real provider ran), `blocked` (with exact blocker), or `simulated`.
- Never present a mock/stub result as evidence the real provider worked.
- Real provider runs require raw outputs + command logs committed alongside.

I'll bounce PRs that don't follow these conventions.

## How decisions get made

I am the only maintainer right now. Decisions are made by me, in public, on issues and PRs. If you disagree with a direction, open an issue rather than a silent fork — I'd rather hear the disagreement.

## Where to start

If you want a small, useful contribution: pick a real conversation you had with an agent recently, run `ingrain consolidate` over the events, and post the raw output as a GitHub issue if the cards look wrong. That's the kind of data that drives prompt improvements.
