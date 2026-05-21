# Hermes Test Report

## Sandbox Provider Load

Command shape:

```bash
PYTHONDONTWRITEBYTECODE=1 \
HERMES_HOME=/private/tmp/hermes-ingrain-test \
PYTHONPATH=<repo-root>/src:<redacted-local-path>/Desktop/REPO/hermes-agent \
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

The live resource-retrieval benchmark returned `96/120` during the first integration pass.

Limit: OpenViking long-term memory extraction requires model credentials. In the isolated temp server, `viking_remember` stored a session message, but commit-time extraction failed because no `OPENAI_API_KEY` or `OPENAI_ADMIN_KEY` was present.

The current live OpenViking path is:

```bash
ingrain compare --openviking-endpoint http://127.0.0.1:1933
```

This report should not be read as a general OpenViking benchmark. Current provider comparison evidence belongs in the live provider matrix only.

## Current OpenViking Recheck

The later live provider matrix now scores OpenViking against a healthy local OpenViking server at `http://127.0.0.1:1933`.

This was rechecked on 2026-05-19 before launch cleanup:

| Attempt | Result |
|---|---|
| Earlier local GGUF embedding path | Failed with `ValueError: Failed to create llama_context`; not used for launch evidence. |
| `uv tool install openviking` | Installed OpenViking 0.3.17. |
| API-backed OpenViking config | Doctor passes for config, Python, native engine, AGFS, OpenAI embedding, OpenAI VLM, and disk. |
| Local server `127.0.0.1:1933` | `/health` returns healthy. |

Current interpretation: OpenViking is no longer blocked. The Hermes OpenViking provider scores `30/100` on the learned-experience smoke matrix because it returns search metadata without enough hydrated lesson text. Direct OpenViking resource retrieval scores `88/100`; that result lives in `docs/evidence/live-openviking-resource/`.
