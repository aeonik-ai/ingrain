# Hermes Test Report

## Sandbox Provider Load

Command shape:

```bash
PYTHONDONTWRITEBYTECODE=1 \
HERMES_HOME=/private/tmp/hermes-ingrain-test \
PYTHONPATH=/Users/benlloyd/Desktop/REPO/ingrain/src:/Users/benlloyd/Desktop/REPO/hermes-agent \
python3 - <<'PY'
# install provider, load through Hermes plugin discovery, initialize, sync one turn, prefetch
PY
```

Observed result:

```text
installed=/private/tmp/hermes-ingrain-test/plugins/ingrain/__init__.py
loaded=True
available=True
tools=4
context_has_learned_experience=True
context_has_vector_database=True
```

Interpretation:

- The Hermes user-plugin path works in a sandbox profile.
- Hermes can discover and instantiate the Ingrain provider.
- The provider exposes four tools: `ingrain_recall`, `ingrain_remember`, `ingrain_compile`, `ingrain_report`.
- The provider can sync a turn and hydrate learned experience.
- The vector-database phrase appears in the hydrated correction because the learned rule is negative: "do not call Ingrain a vector database". This is expected for v0.

## OpenViking Availability

Initial Hermes plugin discovery found the bundled OpenViking provider, but it was not available in this shell:

```text
openviking available=False
```

Reason: `OPENVIKING_ENDPOINT` was not configured in the current environment.

## Live OpenViking Smoke Test

OpenViking was then installed into an isolated temp virtualenv and run locally during the first integration pass:

```text
OpenViking HTTP Server is running on 127.0.0.1:1933
health={"status":"ok","healthy":true,"version":"0.3.17","auth_mode":"dev"}
```

Hermes' bundled provider initialized against that endpoint:

```text
available=True
client=True
tools=['viking_search', 'viking_read', 'viking_browse', 'viking_remember', 'viking_add_resource']
```

The live resource-retrieval benchmark returned `96/120` during the first integration pass. The current deterministic learned-experience comparison has since expanded to ten universes and scores Ingrain at `200/200`.

Limit: OpenViking long-term memory extraction requires model credentials. In the isolated temp server, `viking_remember` stored a session message, but commit-time extraction failed because no `OPENAI_API_KEY` or `OPENAI_ADMIN_KEY` was present. That is why the launch eval distinguishes:

- `Hermes + OpenViking-style retrieval`: deterministic local raw-retrieval baseline.
- `ingrain compare --live-openviking`: real OpenViking resource upload/index/search/read path.

This report should not be read as a general OpenViking benchmark. It checks whether the Ingrain launch scenarios are more naturally handled as learned experience than as raw resource retrieval.

## Current OpenViking Recheck

The later live provider matrix did not score OpenViking because no healthy OpenViking server was reachable at `http://127.0.0.1:1933`.

This was rechecked on 2026-05-19 before launch cleanup:

| Attempt | Result |
|---|---|
| Existing `/private/tmp/openviking-venv` with OpenViking 0.3.17 | `openviking health` failed because no server was reachable. Direct `llama_cpp.Llama(...)` initialization against the cached GGUF embedder raised `ValueError: Failed to create llama_context`. |
| Clean Python 3.11 venv at `/private/tmp/openviking-uv311` with `openviking[local-embed]==0.3.17` | Installation completed, but direct GGUF initialization still raised `ValueError: Failed to create llama_context`. |
| Fresh OpenViking home at `/private/tmp/openviking-fresh-home` | Server startup reached the StreamableHTTP session-manager log line, but `/health` remained unreachable and the process had to be stopped. |

Current interpretation: OpenViking remains a real integration target, but it is not part of the committed live LES provider score until a healthy server is available. The repo should keep saying `blocked`, not `0`, for OpenViking in the provider matrix.
