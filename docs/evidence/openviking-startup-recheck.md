# OpenViking Startup Recheck

Date: 2026-05-19

Purpose: verify whether OpenViking could be scored in the live LES provider matrix instead of being marked blocked.

## Result

OpenViking remains blocked for the committed live LES provider matrix because no healthy OpenViking server was reachable at `http://127.0.0.1:1933`.

This is not scored as a failed OpenViking result. It is an environment/runtime blocker.

## Attempts

| Attempt | Outcome |
|---|---|
| Existing temp install `/private/tmp/openviking-venv` with OpenViking 0.3.17 | CLI was present, but `openviking health` could not reach `http://localhost:1933/health`. |
| Existing cached local embedder model | Direct `llama_cpp.Llama(model_path=..., embedding=True, ...)` initialization failed with `ValueError: Failed to create llama_context`. |
| Clean Python 3.11 venv `/private/tmp/openviking-uv311` | `uv pip install --python /private/tmp/openviking-uv311/bin/python 'openviking[local-embed]==0.3.17'` completed. |
| Clean Python 3.11 direct embedder check | The same GGUF initialization failed with `ValueError: Failed to create llama_context`. |
| Fresh OpenViking home `/private/tmp/openviking-fresh-home` | Server startup reached the StreamableHTTP session-manager log line, but `/health` remained unreachable and the server process was stopped. |
| Fresh OpenViking doctor with default config | Embedding passed, but VLM failed because no model provider was configured. |
| Fresh OpenViking doctor with `openai-codex` VLM and `CODEX_HOME=/Users/benlloyd/.codex` | All doctor checks passed: config, Python, native engine, AGFS, local embedding file, VLM via Codex OAuth, disk. |
| Fresh OpenViking server with passing doctor config | Startup still failed before health because `llama_cpp.Llama(..., embedding=True)` raised `ValueError: Failed to create llama_context` while loading `/private/tmp/openviking-fresh-home/.cache/openviking/models/bge-small-zh-v1.5-f16.gguf`. |
| Direct llama-cpp parameter probes | Explicit `n_ctx`, `n_batch`, `n_gpu_layers`, and `pooling_type` variants still failed with `Failed to create llama_context`. |

## Launch Interpretation

The public result should remain:

```text
OpenViking: blocked
```

The repo should not claim a current live OpenViking LES score until the server passes health and the live harness can upload, index, search, and read scenario resources in that runtime.

The current blocker is narrower than before: OpenViking can see a valid VLM path through Codex OAuth, but its official local GGUF embedding runtime fails during context creation on this machine. A deterministic embedding shim could make the HTTP server start, but that would not be a clean real OpenViking provider result and should not be used for launch evidence.

The older OpenViking smoke test in `docs/hermes-test-report.md` remains useful compatibility history, but it is not the current provider-matrix evidence.
