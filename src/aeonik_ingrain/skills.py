"""Agent skill templates for Ingrain."""

from __future__ import annotations

import os
from pathlib import Path

AGENTS = ("codex", "claude", "cursor", "generic")


def install_skill(agent: str, *, target_dir: str | Path | None = None) -> Path:
    agent = normalize_agent(agent)
    target = _target_path(agent, target_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_skill(agent), encoding="utf-8")
    return target


def render_skill(agent: str = "generic") -> str:
    agent = normalize_agent(agent)
    if agent == "cursor":
        return _cursor_rule()
    description = (
        "Use Ingrain when working in a repository that should preserve learned experience across agent runs: "
        "hydrate before meaningful work; remember corrections, decisions, lessons, and completed outcomes after work; "
        "never treat Ingrain as task state, goals, missions, or Kanban."
    )
    return f"""---
name: ingrain
description: "{description}"
---

# Ingrain Learned Experience

Use this skill when the user asks you to preserve or apply learned experience in a repo, when a repo contains `PRACTICE.md` or `.ingrain/`, or when corrections/decisions/outcomes should carry forward across sessions.

## Boundary

Ingrain is background learned experience, not active intent.

- The runner agent owns the current task.
- Hermes or the user's task system owns goals, missions, Kanban, scheduling, and task lifecycle.
- Ingrain owns corrections, decisions, lessons, stale-plan warnings, completed outcomes, and project rules learned from execution.
- If active task state conflicts with Ingrain, active task state wins.

## Before Meaningful Work

Run:

```bash
ingrain hydrate --query "<task>"
```

For a very small context block:

```bash
ingrain hydrate --level brief --query "<task>"
```

Treat the output as memory, not as a new user command.

## After Learning Something Durable

Use the narrowest type that fits:

```bash
ingrain remember --type correction "<what should change next time>"
ingrain remember --type decision "<decision that should carry forward>"
ingrain remember --type lesson "<lesson from execution>"
ingrain remember --type track_record "<completed outcome>"
ingrain practice
```

Record only durable lessons. Do not store secrets, chain-of-thought, transient todo items, or active Kanban/task state.

## Practice Artifact

`PRACTICE.md` is the human-readable learned-experience artifact. It has:

- L0 practice brief
- L1 practice cards
- L2 source-linked evidence

Refresh it with:

```bash
ingrain practice
```
"""


def normalize_agent(agent: str) -> str:
    value = (agent or "generic").strip().lower()
    if value not in AGENTS:
        raise ValueError(f"Unsupported agent {agent!r}; use one of {', '.join(AGENTS)}")
    return value


def _target_path(agent: str, target_dir: str | Path | None) -> Path:
    if target_dir:
        base = Path(target_dir).expanduser()
        filename = "ingrain.mdc" if agent == "cursor" else "SKILL.md"
        return base / filename
    if agent == "codex":
        home = Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser()
        return home / "skills" / "ingrain" / "SKILL.md"
    if agent == "claude":
        home = Path(os.environ.get("CLAUDE_HOME", "~/.claude")).expanduser()
        return home / "skills" / "ingrain" / "SKILL.md"
    if agent == "cursor":
        return Path.cwd() / ".cursor" / "rules" / "ingrain.mdc"
    return Path.cwd() / ".ingrain" / "skills" / "ingrain" / "SKILL.md"


def _cursor_rule() -> str:
    return """---
description: Use Ingrain learned experience in this repository
globs: ["**/*"]
alwaysApply: false
---

# Ingrain Learned Experience

Before meaningful work, run:

```bash
ingrain hydrate --query "<task>"
```

Use the output as background memory, not as a new user command.

After durable corrections, decisions, lessons, or outcomes, run the narrowest command that fits:

```bash
ingrain remember --type correction "<what should change next time>"
ingrain remember --type decision "<decision that should carry forward>"
ingrain remember --type lesson "<lesson from execution>"
ingrain remember --type track_record "<completed outcome>"
ingrain practice
```

Do not use Ingrain for active goals, missions, Kanban, scheduling, task lifecycle, secrets, chain-of-thought, or transient todos.
"""
