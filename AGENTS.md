# Agent Instructions

## Evaluation Integrity Memory

Always unblock yourself before substituting a weaker result.

For Ingrain, provider and eval claims must come from real runs against the named system. If Hindsight, OpenViking, Hermes, or any other provider is blocked by install state, credentials, services, local runtime failures, or missing configuration, the evidence must say `blocked` with the exact blocker. Do not present a simulation, style baseline, mock provider, or fixture as proof that the real provider worked.

Allowed labels:
- `live`: the named provider actually ran.
- `deterministic baseline`: a local deterministic harness, not a real provider run.
- `style baseline`: a documented approximation of another system's behavior, not evidence about that system.
- `blocked`: the provider could not run, with command output and remediation.

Failure mode to avoid: proceeding with fake evals when the goal is real Hindsight/OpenViking evidence. The correct behavior is to install, configure, start services, request permissions, and keep working until a real blocker remains.
