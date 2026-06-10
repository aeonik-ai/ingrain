# Rust Core Spec

This spec defines the first useful Rust contribution to Ingrain.

## Goal

Add a schema-compatible Rust read path for Ingrain stores. The Rust code should
prove that Ingrain's durable local core can be typed, tested, and reused without
replacing the Python Hermes integration or LLM consolidator.

## Why This Exists

Ingrain's most important runtime boundary is local evidence hydration:

- read source-linked learned-experience cards from SQLite;
- rank only relevant current cards for the next task;
- render compact background context with source IDs;
- inspect store health without mutating user data.

That boundary is small, durable, and a natural Rust fit. It is also useful to
users immediately as a fast independent verifier for existing stores.

## Scope

Add a Cargo workspace with:

- `crates/ingrain-core` — typed store reader, hydration engine, report model,
  and tests.
- `crates/ingrain-cli` — `ingrain-rs`, a small CLI for read-only store
  inspection and hydration.

The first Rust CLI commands:

```bash
ingrain-rs hydrate --home .ingrain --query "about to push" --level evidence
ingrain-rs report --home .ingrain --json
ingrain-rs verify-store --home .ingrain --json
```

## Non-Goals

- Do not rewrite the Python CLI.
- Do not replace Hermes provider hooks.
- Do not port the LLM consolidator.
- Do not add write paths until read-path parity is proven.
- Do not add dependencies that do not directly support the read path.

## Requirements

- Read the existing `mind.db` schema without migration.
- Never create or mutate the store for read-only commands.
- Support hydration levels `brief`, `cards`, and `evidence`.
- Preserve source IDs, confidence, reason, trace labels, context wrappers, and
  truncation behavior.
- Report store counts, latest event/promotion summaries, DB existence, DB
  readability, and event-to-promotion ratio.
- Return non-zero exits for unreadable stores or invalid arguments.
- Add Rust unit/integration tests for ranking, filtering, rendering,
  truncation, reporting, and SQLite reads.
- Add CI coverage for `cargo test`.

## Acceptance

- `cargo test --workspace`
- `cargo fmt --check`
- `cargo clippy --workspace --all-targets -- -D warnings`
- Existing Python tests still pass.
- Rust `hydrate` output matches the Python hydrator for representative fixture
  stores.
- Rust `verify-store --json` can inspect a real Ingrain store without changing
  its database file.

## Future Work

After read-path parity:

- add Rust deterministic compile parity for local no-LLM promotion;
- add `record --batch` for high-throughput JSONL ingestion;
- consider a Python bridge only if users need Rust core from the Python CLI.
