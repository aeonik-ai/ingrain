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

## Launch Interpretation

The public result should remain:

```text
OpenViking: blocked
```

The repo should not claim a current live OpenViking LES score until the server passes health and the live harness can upload, index, search, and read scenario resources in that runtime.

The older OpenViking smoke test in `docs/hermes-test-report.md` remains useful compatibility history, but it is not the current provider-matrix evidence.
