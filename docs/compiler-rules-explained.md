# Compiler Rules Explained

How Ingrain decides which events from a trace become *learned experience*.

This is a short tour of `src/aeonik_ingrain/compiler/rules.py` for people who want to understand or extend the promotion logic without reading 380 lines of regex. If you've used Ingrain and wondered "why didn't it remember that?", this is the doc.

> **As of v0.2, the regex compiler is no longer the recommended path.** The default is `ingrain consolidate`, which uses Hermes's own model to classify events. The regex compiler stays as a no-LLM fallback and for backwards compatibility, but it has known false-positive problems on conversational data (it matches "the key is", "always", "do not" as imperative corrections — see `reports/longmemeval-oracle-smoke12/ingrain-sidecar/` for evidence). See [`src/aeonik_ingrain/integrations/hermes_consolidator/`](../src/aeonik_ingrain/integrations/hermes_consolidator/) for the consolidator. This doc remains accurate for understanding the regex fallback and the supersession rules — both still apply.

## What "compiling" means

Ingrain ingests an event stream — chat messages, run logs, source documents — and writes each event into a SQLite ledger. *Compiling* is the step that reads the ledger and promotes a subset of those events into typed "practice cards" that get re-hydrated into future agent turns.

Cards have a type (`correction`, `decision`, `lesson`, `project_fact`, `track_record`, `risk`, `status`), a confidence, a reason, and a `current_state` (`current` or `superseded`).

```
events  --[promotion rules]-->  practice candidates  --[supersession]-->  cards
```

## Promotion: how an event becomes a candidate

`extract_promotions(events)` walks each event and asks: does this match one of the promotion patterns? Patterns are checked in order; the first match wins.

### 1. Manual override

If the event's meta dict contains `remember_type` (set by the `ingrain remember --type=X` CLI), that wins immediately. This is the "you can always force it" escape hatch.

```python
{"remember_type": "correction"} -> correction (confidence 0.96)
```

Aliases (e.g. `rule -> correction`, `done -> track_record`) are normalized in `_normalize_manual_type`.

### 2. Supersession edges from traces

If the event's `trace_kind` is `supersession`, it gets promoted as a correction with confidence 0.88. The text typically looks like `doc_A is superseded_by doc_B` — this also fires the trace-supersession bookkeeping (see "Supersession" below).

### 3. Regex pattern matching

Otherwise the rules check for patterns characteristic of each card type:

| Card type | Confidence | Patterns (representative) |
|---|---:|---|
| `correction` | 0.90 | `correction:`, `remember:`, `do not X`, `don't X`, `never X`, `always X`, `from now on:`, `no, that's wrong`, `use X instead` |
| `lesson` | 0.76 | `^lesson:`, `^observation:` |
| `project_fact` | 0.84 | `^project:`, `active project:` |
| `decision` | 0.88 | `decision:`, `we decided to`, `the decision is` |
| `plan` (as decision) | 0.72 | `^plan:`, `the plan is` (saved as decision with `meta.kind="plan"`) |
| `track_record` | 0.78 | `^completed:`, `^shipped:`, `^fixed:`, `^tests? passed` |
| `risk` (as lesson) | 0.72 | `blocked:`, `failed:`, `timed out`, `avoid X` |

The cleaner functions (`_clean_correction`, `_clean_match`) normalize phrasing: a "don't deploy on Friday" gets stored as "Do not deploy on Friday." with a trailing period. This is mostly cosmetic but it makes downstream card text consistent.

### 4. Canonical event types

If no regex matched but the event's `event_type` is one of `decision`, `reflection`, `metric`, the event still gets promoted at lower confidence (0.62). This catches events that were structurally labeled but didn't use the magic phrases.

### 5. Trace-kind fallbacks

If still nothing fired and the event has a `trace_kind` we recognize:

| trace_kind | Promoted to | Confidence |
|---|---|---:|
| `source_of_truth` | `project_fact` | 0.94 |
| `roadmap` | `project_fact` | 0.82 |
| `run_log` | `status` | 0.84 |
| `report` | `status` | 0.82 |

Trace kinds that look like noise (`draft`, `external_project`, `invalidated_report`, `plan`) are dropped — they're not promoted to candidates.

### 6. Nothing matches

The event stays in the ledger as raw history but doesn't appear as a card. This is the design: most events are not learned experience.

## Why this design

The patterns look brittle — and they are. The bet is that explicit "do not X" / "remember X" phrases are the *easiest* signal a human gives an agent, and capturing the easy ones well is more valuable than tuning subtle ML for ambiguous cases. Confidence is exposed so downstream consumers (the practice-card surface) can weight or hide low-confidence cards.

If a pattern is too aggressive (false positives spammed into memory), reduce its confidence rather than removing it — the surface filters by confidence threshold. If a pattern is too narrow (false negatives), prefer adding a new pattern with appropriate confidence to widening an existing one.

## Supersession: how cards become stale

Once candidates exist, `_mark_superseded` walks the list and flips `current_state` to `superseded` based on five rules:

### 1. Trace supersession edges

If a supersession event in the trace says `doc_A is superseded_by doc_B`, every candidate whose `trace_source_id` equals `doc_A` is marked superseded.

### 2. Product naming

If multiple decisions/project_facts look like product names (`name is X`, `called X`, `product name X`), only the most recent one survives. Older ones get superseded.

```
Decision 1: "Product name is MindCompiler."
Decision 2: "Use Ingrain. Not MindCompiler."
-> Decision 1 is marked superseded; Decision 2 wins.
```

### 3. Explicit "not X" corrections

If a later candidate says `not mindcompiler` / `not engram`, earlier candidates mentioning those terms are marked superseded.

### 4. Active-intent boundary

If a candidate says "active goal" or "active intent" AND mentions "background context" or "source of truth", any earlier plan-shaped candidate or `next run` candidate gets superseded. This implements the Hermes-vs-Ingrain ownership boundary: when active intent is asserted, stale plans are demoted.

### 5. Track-record completes a plan

When a `track_record` candidate appears, any earlier plan candidate that shares ≥3 tokens with it gets superseded.

```
Plan: "Ship the v0 audit and push the cleanup."
Track record: "Shipped v0 audit; cleanup pushed."
-> Plan is marked superseded.
```

### 6. "No final decision yet" suppresses earlier decisions

If a later candidate matches `no final decision` / `not resolved` / `unresolved` and shares ≥2 tokens with an earlier decision, the earlier decision is marked superseded.

### 7. Decision-shape supersession

A later decision supersedes an earlier one *in the same project* when:
- They share ≥3 non-stopword subject tokens, AND
- The later one has a "decision shape" marker (` should `, ` threshold `, ` run on `, ` is `), AND
- The later one is a textual replacement (contains `not `, `because`, a digit, or `instead`).

This catches "we said the threshold was 5; we now think it's 7" patterns without superseding every related decision.

## Worked example: the Banana Test

From `examples/banana-test.md`:

```
Remember: For this project, yellow CTA buttons are called bananas. Never ship bananas in enterprise demos.
```

What the compiler does:

1. The leading `Remember: ...` matches `CORRECTION_PATTERNS` (confidence 0.90, reason "correction phrase").
2. Card written: `correction` with text "For this project, yellow CTA buttons are called bananas. Never ship bananas in enterprise demos."
3. Next session: the practice surface re-hydrates this correction into the agent's context. The agent now knows not to ship bananas.

## What the compiler will NOT pick up

Things that look like learned experience to a human but won't match any pattern:

- A checklist: `"- Run tests\n- Run secret scan\n- Verify evidence links"` — no per-line trigger phrase. Ingest these as a `source_of_truth` trace-kind doc instead.
- A status report: `"21 tests passed."` — does match `^tests? passed` and becomes a `track_record`, but the related details ("which test file?", "on which commit?") aren't extracted.
- A subtle implication: "I noticed the new pricing scheme makes the discount feature obsolete." — no pattern fires. If this matters, the human should say "Remember: the discount feature is obsolete under the new pricing scheme."

This is the design boundary. Ingrain is a learned-experience layer; it works best when humans tag their teaching explicitly.

## Where to extend

If you want to add a new card type or promotion pattern:

1. Add the regex to `rules.py` near similar patterns.
2. Add a clean-up function if the matched text needs normalizing.
3. Pick a confidence calibrated against existing patterns (corrections at 0.90 are explicit; canonical-type fallbacks at 0.62 are noisy).
4. Add a test case in `tests/test_compile_hydrate.py` covering both a positive match and a confusable negative.
5. Run `python -m unittest tests/test_compile_hydrate.py`.

If the pattern overlaps with an existing one, place yours *first* if it should win, or last if it's a fallback. The first-match-wins ordering is load-bearing.

## See also

- `src/aeonik_ingrain/compiler/rules.py` — the source
- `src/aeonik_ingrain/compiler/hydrate.py` — how cards get re-hydrated into agent context
- `tests/test_compile_hydrate.py` — promotion test cases that pin behavior
- `examples/correction-carry-forward.md` — end-to-end demo of a correction being recalled across sessions
