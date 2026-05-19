# CLI And Skill Spec

The recommended v0 adoption path is CLI + Skill.

```text
CLI        deterministic core that works anywhere
Skill      agent instructions for using the CLI correctly
PRACTICE.md human-readable learned-experience artifact
MCP        future live-tool surface
Provider   Hermes-specific advanced mode
```

## Install Story

```bash
pipx install "git+https://github.com/aeonik-ai/ingrain.git"
cd your-project
ingrain attach --agent codex
```

`ingrain attach` does four things:

1. Initializes `.ingrain/`.
2. Compiles current ledger events.
3. Writes `PRACTICE.md` and `.ingrain/practice/cards/*.md`.
4. Installs an agent skill unless `--no-skill` is passed.

## Skill Targets

```bash
ingrain skill install codex
ingrain skill install claude
ingrain skill install cursor
ingrain skill install generic
```

Use `--target-dir` for deterministic local installs:

```bash
ingrain skill install codex --target-dir ./.ingrain/skills/ingrain
```

## Agent Workflow

Before meaningful work:

```bash
ingrain hydrate --query "<task>"
```

After durable learning:

```bash
ingrain remember --type correction "<what should change next time>"
ingrain remember --type decision "<decision that should carry forward>"
ingrain remember --type lesson "<lesson from execution>"
ingrain remember --type track_record "<completed outcome>"
ingrain practice
```

## Practice Artifact

`PRACTICE.md` is not active task state. It is background learned experience.

It has three levels:

```text
L0 Practice Brief     compact scan
L1 Practice Cards     current corrections, decisions, lessons, outcomes
L2 Evidence           source event IDs and confidence
```

Hydration mirrors those levels:

```bash
ingrain hydrate --level brief --query "<task>"
ingrain hydrate --level cards --query "<task>"
ingrain hydrate --level evidence --query "<task>"
```

## Boundary

Ingrain must not store or mutate:

- active goals
- missions
- Kanban state
- scheduling
- task lifecycle
- transient todos
- secrets
- chain-of-thought

The runner agent owns the task. Ingrain owns learned experience.
