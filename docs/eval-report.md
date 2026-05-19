# Aeonik Ingrain Eval Report

Generated from deterministic local fixtures. No LLM, network, or hosted service required.

```text
Aeonik Ingrain LES-100 Eval

Cold-start project recall       20/20
Correction carry-forward        20/20
Stale-plan avoidance            20/20
Track-record query              20/20
Context compactness             20/20

Total                           100/100

Learned Experience Comparison

Hermes default memory                   36/120
Hermes + OpenViking-style retrieval     108/120
Hermes + Ingrain                        120/120

Scenario breakdown:
- correction_after_failure: Hermes default memory=6/20; Hermes + OpenViking-style retrieval=16/20; Hermes + Ingrain=20/20
- stale_product_name: Hermes default memory=6/20; Hermes + OpenViking-style retrieval=16/20; Hermes + Ingrain=20/20
- approval_judgment: Hermes default memory=6/20; Hermes + OpenViking-style retrieval=16/20; Hermes + Ingrain=20/20
- kanban_boundary: Hermes default memory=6/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Ingrain=20/20
- sandbox_recovery: Hermes default memory=6/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Ingrain=20/20
- track_record: Hermes default memory=6/20; Hermes + OpenViking-style retrieval=20/20; Hermes + Ingrain=20/20

OpenViking mode is a deterministic raw-retrieval baseline, not a live OpenViking server benchmark.
```

## Live OpenViking Check

OpenViking 0.3.17 was installed into an isolated temp virtualenv and run locally on `127.0.0.1:1933`. Hermes' bundled OpenViking provider initialized successfully against that server and exposed:

```text
viking_search, viking_read, viking_browse, viking_remember, viking_add_resource
```

The live resource-retrieval benchmark produced:

```text
Live OpenViking Resource Retrieval Comparison

Endpoint: http://127.0.0.1:1933
Score: 96/120

Scenario breakdown:
- correction_after_failure: 14/20
- stale_product_name: 14/20
- approval_judgment: 14/20
- kanban_boundary: 18/20
- sandbox_recovery: 18/20
- track_record: 18/20
```

Important caveat: this checked OpenViking's live resource upload, indexing, search, and read path. OpenViking's long-term memory extraction path failed in the isolated temp server because no `OPENAI_API_KEY` or `OPENAI_ADMIN_KEY` was configured. The repo therefore keeps the default comparison deterministic and offers the live check as `ingrain compare --live-openviking`.

## Interpretation

LES-100 measures the learned-experience substrate: project recall, correction carry-forward, stale-plan avoidance, track-record reporting, and compact hydration.

The comparison harness is intentionally deterministic. `Hermes + OpenViking-style retrieval` means raw semantic retrieval over the same fixture history, not a live OpenViking server benchmark. It shows the distinction: retrieval can find relevant fragments, but Ingrain promotes current lessons and suppresses stale truth.
