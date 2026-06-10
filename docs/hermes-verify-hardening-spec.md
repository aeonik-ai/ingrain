# Hermes Verify Hardening Spec

`ingrain verify hermes` is a public trust command. Its output must be
repeatable, safe to publish as an evidence receipt, and honest about blocked
provider evidence.

## Scope

This hardening pass keeps the verifier focused on observability. It must not
change Hermes capture, consolidation, or provider semantics.

## Requirements

- A live canary probe must be repeatable against the same Ingrain store.
- Live canary seeding must not leave previous probes as high-priority current
  corrections that can satisfy later probes.
- A `blocked` verifier result must return a non-zero CLI exit status.
- Receipt snippets must redact secret-shaped standalone tokens as well as
  key-value pairs.
- Local verification should report whether the store database existed before
  the verifier touched it.
- Unit tests must cover these behaviors without claiming mocked subprocess
  output as live provider evidence.

## Acceptance

- `python -m compileall src tests`
- `python -m unittest discover -s tests -v`
- `python -m pytest tests -q -o addopts=`
- `PYTHONPATH=src python -m aeonik_ingrain.cli eval`
- Local Hermes verification reports package, plugin, store, and hydration state.
- Two consecutive live canary probes against the same isolated store both pass
  against a real Hermes CLI, or the evidence is labeled `blocked` with the exact
  blocker.
