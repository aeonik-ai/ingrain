# Current Hermes Map

Verified against the official upstream repo:

```text
repo: https://github.com/NousResearch/hermes-agent.git
branch: origin/main
commit: a0bd11d02 fix(tests): catch up 25 stale tests after recent merges (#28626)
fetched: 2026-05-19
```

The local checkout at `/Users/benlloyd/Desktop/REPO/hermes-agent` was 22 commits behind before fetch, so this map is based on `origin/main`, not the stale local `HEAD`.

## Memory Provider Surface

Official files checked:

- `agent/memory_provider.py`
- `agent/memory_manager.py`
- `agent/agent_init.py`
- `plugins/memory/__init__.py`
- `plugins/memory/openviking/__init__.py`

Current facts:

- Hermes activates one external provider from `memory.provider` in config.
- User memory providers live at `$HERMES_HOME/plugins/<name>/__init__.py`.
- Bundled providers in `plugins/memory/<name>/` take precedence on name collisions.
- `MemoryManager` rejects a second external provider; built-in memory remains separate.
- Provider tools are injected into the normal tool schema when the provider is active.

Lifecycle hooks Ingrain supports or intentionally respects:

- `initialize(session_id, hermes_home, platform, agent_context, agent_identity, ...)`
- `system_prompt_block()`
- `prefetch(query, session_id=...)`
- `sync_turn(user_content, assistant_content, session_id=...)`
- `on_session_end(messages)`
- `on_session_switch(new_session_id, parent_session_id=..., reset=...)`
- `on_memory_write(action, target, content, metadata=...)`
- `on_delegation(task, result, child_session_id=...)`
- `shutdown()`

## Current Intent Surfaces

Official files checked:

- `hermes_cli/goals.py`
- `website/docs/user-guide/features/goals.md`
- `hermes_cli/kanban.py`
- `hermes_cli/kanban_db.py`
- `tools/kanban_tools.py`
- `website/docs/user-guide/features/kanban.md`

Current facts:

- `/goal` is Hermes' persistent standing objective loop.
- `/subgoal` appends acceptance criteria to the active `/goal`.
- Goal state persists in `SessionDB.state_meta` under `goal:<session_id>`.
- Kanban is Hermes' durable task board with SQLite state, dispatcher-spawned workers, and `kanban_*` tools.
- Kanban state lives in `~/.hermes/kanban.db` or per-board DBs under `~/.hermes/kanban/boards/<slug>/`.
- No formal top-level `mission` primitive was found in current upstream. If Hermes or a profile exposes missions now or later, Ingrain treats them as Hermes-owned active intent.

## Ingrain Boundary

Hermes owns intent:

- goals
- subgoals
- missions or mission-like profile objectives
- Kanban boards and columns
- scheduling
- task lifecycle
- what the agent should do next

Ingrain owns experience:

- corrections
- decisions
- lessons
- stale-plan warnings
- completed outcomes
- prior failures
- project rules learned from execution

Precedence:

- If Hermes `/goal`, `/subgoal`, missions, or Kanban say something is active, Hermes wins.
- If Ingrain recalls an old plan, it is background context only.
- If Ingrain has a correction or stale-plan warning, it can influence execution quality.
- Ingrain must not create, move, close, schedule, unblock, archive, or revive tasks by itself.

Short version:

> Hermes owns intent. Ingrain owns experience.
> Kanban decides what is active. Ingrain remembers what was learned.

## OpenViking Map

The current official OpenViking provider is still named `openviking`, requires `OPENVIKING_ENDPOINT`, exposes `viking_search`, `viking_read`, `viking_browse`, `viking_remember`, and `viking_add_resource`, and runs through the same single external-provider slot.

That means:

- `memory.provider: openviking` and `memory.provider: ingrain` cannot both be live providers today.
- Ingrain sidecar mode can coexist with OpenViking live provider mode.
- Provider chaining remains a future Hermes/Ingrain integration path, not a v0 assumption.
