# Live OpenViking Resource Retrieval Eval

Generated: `2026-05-20T04:48:45.291763+00:00`

## Method

This is a real OpenViking server run. The harness uploads each preregistered LES-Core universe as a markdown resource, waits for indexing, searches with the universe query, reads returned resource URIs, and scores the retrieved text.

It is intentionally labeled as resource retrieval. It does not claim to exercise OpenViking's long-term memory extraction behavior.

## Environment

| Field | Value |
|---|---|
| Endpoint | `http://127.0.0.1:1933` |
| Health | `{"auth_mode": "dev", "healthy": true, "status": "ok", "version": "0.3.17"}` |
| Raw output | `docs/evidence/live-openviking-resource/raw` |

## Results

Score: `88/100`

| Scenario | Score | Expected | Forbidden | Read URIs |
|---|---:|---|---|---|
| launch_framing_correction | 16/20 | learned experience layer, autonomous agents | is a generic memory backend | viking://resources/launch_framing_correction/launch_framing_correction.md<br>viking://resources/launch_framing_correction_1/launch_framing_correction.md<br>viking://resources/product_rename_supersession/product_rename_supersession.md |
| product_rename_supersession | 16/20 | Product name is Aeonik Ingrain, not MindCompiler | Product name is MindCompiler. | viking://resources/product_rename_supersession_1/product_rename_supersession.md<br>viking://resources/product_rename_supersession/product_rename_supersession.md<br>viking://resources/launch_framing_correction/launch_framing_correction.md |
| goals_missions_boundary | 20/20 | Hermes owns active goals, Ingrain owns learned experience, Do not let Ingrain create | Ingrain owns active goals, Ingrain should schedule tasks | viking://resources/goals_missions_boundary/goals_missions_boundary.md<br>viking://resources/goals_missions_boundary_1/goals_missions_boundary.md<br>viking://resources/launch_framing_correction/launch_framing_correction.md |
| sandbox_recovery | 20/20 | request sandbox escalation, dependency installs, network-backed package resolution | none | viking://resources/sandbox_recovery/sandbox_recovery.md<br>viking://resources/sandbox_recovery_1/sandbox_recovery.md<br>viking://resources/goals_missions_boundary/goals_missions_boundary.md |
| launch_claim_safety | 16/20 | Do not claim Ingrain is better, narrow learned-experience layer, resource memory | Ingrain beats Hindsight | viking://resources/launch_claim_safety_1/launch_claim_safety.md<br>viking://resources/launch_claim_safety/launch_claim_safety.md<br>viking://resources/launch_framing_correction/launch_framing_correction.md |

## Interpretation

This is a live OpenViking resource-retrieval benchmark. It does not exercise OpenViking long-term memory extraction unless the server is configured with model credentials.

This result is useful for validating OpenViking as a resource-memory substrate. It should not be described as a head-to-head learned-experience benchmark unless OpenViking's memory extraction path is separately configured and tested.
