# INSTALL.md — install Ingrain into your AI agent

This document is an **install runbook** that you (the user) can paste into your AI agent. The agent reads this file and executes the right install path for itself.

> **Agent reading this**: identify which one you are, then execute the matching section below. If you're not sure, run the **Any agent** section.

---

## TL;DR for the user

```bash
pipx install "git+https://github.com/benlloydg/ingrain.git"
```

Then tell your agent: *"Read `INSTALL.md` in the Ingrain repo and install yourself."*

---

## Prerequisites

- Python 3.10 or newer.
- A real LLM runtime. Either:
  - **Hermes Agent** at `~/.hermes/hermes-agent/` (recommended — Ingrain's consolidator uses `hermes -z`, no API keys needed), or
  - Some other agent runtime you already use (Claude Code, Cursor, Codex, etc.). Ingrain still works; you just won't get auto-consolidation at session end.

Verify Python:

```bash
python3 --version  # must be ≥ 3.10
```

---

## Any agent — base install (do this first)

```bash
pipx install "git+https://github.com/benlloydg/ingrain.git"
ingrain --version
ingrain doctor
```

**Verify**: `ingrain doctor` should print "Database exists: True" after `ingrain init`. If the binary is missing, your `~/.local/bin` (or pipx bin path) is not on PATH — fix that and retry.

```bash
mkdir -p ~/projects/example && cd ~/projects/example
ingrain init
```

**Verify**: a `.ingrain/` directory now exists with `mind.db` inside.

You now have an empty ledger. The next steps depend on which agent you are.

---

## If you are **Hermes Agent**

Hermes gets the deepest integration. Two things to install: the memory-provider plugin (so Hermes default memory can be augmented or replaced), and the auto-consolidate lifecycle plugin (so consolidation runs automatically at session end).

### Step 1: install the auto-consolidate plugin (RECOMMENDED)

```bash
ingrain install hermes-plugin
```

**Verify**: `ls ~/.hermes/plugins/ingrain-auto/` should show `__init__.py` and `plugin.yaml`. Restart Hermes for the plugin to load.

After restart, every Hermes session will:
- Record each tool call into the Ingrain ledger via `post_tool_call`
- Run `ingrain consolidate` automatically at session end via `on_session_end`

No further config needed. The user can immediately ask questions and you'll have learned experience carrying forward.

### Step 2 (optional): install the memory-provider plugin

Skip this if you want Hermes default memory to keep working. Only do it if the user explicitly wants Ingrain to *replace* default memory in Hermes's `memory.provider` slot.

```bash
ingrain install hermes
hermes config set memory.provider ingrain
```

**Verify**: `hermes config show | grep provider` should show `provider: ingrain`. This replaces Hermes's default memory backend; you can revert with `hermes config set memory.provider default`.

### Step 3: verify the cross-repo install (if the user wants to run benchmarks)

```bash
pipx install "git+https://github.com/benlloydg/sandbox-universe.git"
sandbox-universe list-lanes
```

**Verify**: should print `ingrain`, `ingrain-sidecar`, `ingrain-llm-sidecar`.

---

## If you are **Claude Code**

Claude Code gets the skill-based integration. The skill teaches Claude Code to call `ingrain hydrate` before meaningful work and `ingrain remember` after corrections, decisions, or completed outcomes.

### Step 1: install the Claude skill

```bash
ingrain skill install claude
```

**Verify**: a new skill file should be written to your Claude skills directory. Run `ingrain skill show claude` to print its content for inspection.

The skill is a CLAUDE.md-style instruction file that Claude Code reads at session start. It teaches Claude to:
- Run `ingrain hydrate --level brief --query "<task>"` at the start of meaningful work
- Run `ingrain remember --type correction "<...>"` when the user issues a correction
- Run `ingrain remember --type decision "<...>"` when a durable decision is made
- Run `ingrain remember --type track_record "<...>"` after a completed outcome

### Step 2: tell the user

You don't have a session-end hook (Claude Code doesn't expose one the way Hermes does), so the user will need to occasionally run `ingrain consolidate` manually or via a periodic cron. Mention this so they know.

---

## If you are **Cursor**

```bash
ingrain skill install cursor
```

**Verify**: a `.cursorrules` file (or `.cursor/rules/ingrain.md` on newer Cursor) gets written to the project. Cursor will read it automatically on next file edit.

Same caveat as Claude Code: no automatic session-end hook. Run `ingrain consolidate` manually or via cron.

---

## If you are **Codex** (OpenAI Codex CLI)

```bash
ingrain skill install codex
```

**Verify**: a Codex-format skill file is written. Same caveat as above.

---

## If you are some other agent

Use the generic skill:

```bash
ingrain skill install generic
```

This writes a markdown instruction file. Include it in your system prompt or read it at session start. Same caveat: run `ingrain consolidate` manually or via cron.

---

## After install — sanity check

Have the user run this as a one-time test:

```bash
ingrain remember --type correction "Do not push to main without running tests."
ingrain remember --type project_fact "Production database is Postgres, not SQLite."
ingrain consolidate           # If Hermes is installed, this runs the LLM consolidator.
ingrain practice --no-compile # If you ran consolidate. Otherwise omit --no-compile.
ingrain hydrate --query "about to push to main"
```

**Verify**: the `hydrate` output contains both the correction and the Postgres fact. If yes, install is complete.

For an audit-trail demo:

```bash
ingrain why "push"
```

**Verify**: shows the source event ID, confidence, reason, and timestamp for the correction card.

---

## If something fails

1. Run `ingrain doctor` — most install issues show up here.
2. Re-read the `Prerequisites` section. Most failures are wrong Python version or missing Hermes.
3. Check the [CHANGELOG.md](CHANGELOG.md) for v0.2 known issues.
4. Open an issue at https://github.com/benlloydg/ingrain/issues.

## What NOT to do

- Don't install Ingrain into a system Python — use pipx or a venv.
- Don't store secrets in `ingrain remember`. The `security.py` redaction pass catches common patterns but is not a substitute for not pasting credentials.
- Don't treat `ingrain remember` as a task list. Ingrain is learned-experience, not Kanban. Hermes owns active intent.

## What "successful install" looks like

A fresh Hermes session, on a freshly-installed Ingrain, that:

1. Runs `ingrain hydrate` at turn 0 as part of its skill
2. Sees a `<aeonik_ingrain_context>` block in its first system prompt
3. Acts on a stale-plan warning or a correction from a previous session

If you see all three, the loop is closed.
