# OpenViking Startup Recheck

Date: 2026-05-19

Purpose: verify whether OpenViking could be scored with real local infrastructure instead of being omitted from the live LES provider matrix.

## Result

OpenViking is now installed and healthy locally.

```text
openviking==0.3.17
health: {"status":"ok","healthy":true,"version":"0.3.17","auth_mode":"dev"}
```

The working launch setup uses API-backed OpenAI embedding and VLM configuration. The API key is stored outside this repo.

## Attempts

| Attempt | Outcome |
|---|---|
| Earlier local GGUF embedding path | Failed with `ValueError: Failed to create llama_context`; not used for launch evidence. |
| `uv tool install openviking` | Installed OpenViking 0.3.17 with `openviking`, `openviking-server`, `ov`, and `vikingbot` executables. |
| First API-backed config | Doctor rejected `embedding.dense.encoding_format` as an unknown config field. |
| Corrected API-backed config | Doctor passed config, Python, native engine, AGFS, `openai/text-embedding-3-small`, `openai/gpt-4o-mini`, and disk checks. |
| `openviking-server --host 127.0.0.1 --port 1933` | Server started and `/health` returned healthy. |
| `ingrain compare --openviking-endpoint http://127.0.0.1:1933` | Direct OpenViking resource retrieval scored `88/100`; artifacts are in `docs/evidence/live-openviking-resource/`. |
| `ingrain live-eval --provider openviking --openviking-endpoint http://127.0.0.1:1933` | Hermes OpenViking provider scored `30/100` in the full provider matrix; artifacts are in `docs/evidence/live-les-provider-matrix/`. |

## Interpretation

OpenViking is no longer blocked on this machine.

There are two different real results:

| Lane | Score | Meaning |
|---|---:|---|
| Direct OpenViking resource retrieval | 88/100 | OpenViking can upload, index, search, read, and return useful resource context for the preregistered universes. |
| Hermes OpenViking provider | 30/100 | The current Hermes provider lane returns mostly search metadata and abstracts, which is not enough hydrated lesson text for the learned-experience smoke test. |

Do not merge these into one claim. The resource lane validates OpenViking as a useful resource-memory substrate. The Hermes provider lane shows that the current Hermes integration needs better hydration before it is strong on this specific learned-experience task.
