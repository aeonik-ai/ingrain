# The Research Arc

## When I tested my own AI-memory benchmark, it failed

A short writeup of the engineering and research arc behind [Aeonik Ingrain](https://github.com/benlloydg/ingrain) and [Sandbox Universe](https://github.com/benlloydg/sandbox-universe). Aimed at a reader who has 10 minutes and wants the honest version.

---

## What I built

Two related artifacts:

1. **Aeonik Ingrain** — a *learned-experience layer* for AI agents. Not a generic memory backend (MemGPT, Mem0, Letta, Zep do that). Ingrain's narrower bet is: every time the user corrects the agent, decides something durable, or finishes a task, that fact should change the agent's behavior in future sessions. It records events into a local SQLite ledger, consolidates them into typed cards (`correction`, `decision`, `lesson`, `project_fact`, `track_record`), and re-hydrates them into the agent's prompt on the next turn. Each card carries a source event ID, so when the agent does something wrong you can run `ingrain why "X"` and trace which prior event led to the behavior.

2. **Sandbox Universe** — a trace-level benchmark for agent memory plus a cross-validation harness that runs any memory system against external benchmarks. 10 hand-crafted "messy" conversations (corrections, supersessions, stale plans), plus a LongMemEval adapter, plus 20 hand-authored carry-forward scenarios — all scored through a deterministic substring-matching scorer (no LLM judge).

Both repos are open source under MIT.

## Where it started (and what I almost shipped)

The first version of Ingrain used a deterministic regex compiler. Patterns like `^correction[:,]?\s*(.+)` and `\bdo not\b\s+(.+)` extracted promoted cards. Sub-second compile times. No LLM needed.

I authored Sandbox Universe v0 to test it. The 10 universes are short, structured traces where the right answer requires picking the latest valid claim while suppressing stale ones. Ingrain scored 673/1000. Hermes default memory scored 623/1000. **+5 mean delta. The original story I almost shipped was "Ingrain wins on Sandbox Universe."**

Then I ran the sidecar-isolation analysis: 95% bootstrap CI on the per-universe delta was `[-13.8, +19.8]` and the sign test was 7-3 (p≈0.344). The +5 was not statistically distinguishable from zero at n=10. Honest read: the result was directional, not significant.

That was step one of finding out my evidence wasn't what I'd been telling myself.

## The external benchmark that ate the story

The conflict-of-interest concern about Sandbox Universe (same author as the system being scored) led me to LongMemEval (Wu et al. 2024) as cross-validation. I scaffolded an adapter, ran 12 stratified questions through both lanes:

- `hermes-default`: 0.361
- `ingrain-sidecar` (regex compiler): **0.000**

Zero. Out of twelve. Ingrain didn't just lose — it scored *nothing* against an external benchmark Ingrain's author did not author.

Looking at the raw lane outputs explained it. On real conversational data, Ingrain's `CORRECTION_PATTERNS` matched generic assistant chitchat — "the key is to listen", "always be flexible", "do not overcomplicate." The regex correctly recognized these phrases as imperative-shaped, but on conversation they're advice, not corrections. Ingrain dumped 12 of these into the agent's prompt as "user corrections" per question. The answerer LLM correctly returned "I don't know."

The Sandbox Universe traces had been short and densely written: roughly one explicit user correction per universe, surrounded by a bit of context. Ingrain's regex worked there because the design fit the data. On real conversation it produced 12x noise.

I'd built a system that worked on the benchmark I'd written for it and failed on the benchmark someone else had written.

## The architectural pivot

The regex compiler was the wrong abstraction. What it needed was an LLM that could read the events and decide which were corrections, decisions, or durable facts. The fix that made the constraint OK: the user runs Hermes Agent, which is already configured against some model (Claude, GPT, local, whatever). I could shell out to `hermes -z "..."` and let Hermes do the classifying. Cost lives in the user's existing subscription. No API keys for me to manage, no SDK pinning, no additional service.

The new module is ~150 lines in `src/aeonik_ingrain/integrations/hermes_consolidator/`. It builds a prompt that lists the recent events and asks Hermes for a JSON array of cards in the existing schema. Output gets parsed, validated against the in-batch event IDs (so the model can't hallucinate sources), and written to the same SQLite table the regex used to fill.

I re-ran the same LongMemEval 12-question smoke. Result: 0.0 → **0.547**. The model classified the events the regex had been confused by.

Then I found a *second* bug in the original sidecar. The `INGRAIN_SIDECAR_SCRIPT` computed Hermes default memory's output but only printed its character count, not the content. The "sidecar" had been Ingrain-only with a metadata banner about default memory. After fixing that one line — actually emitting `default_context` into the output — the lane became `default memory + Ingrain` in the same prompt. By construction, the new sidecar can't underperform default: it has all of default's content *plus* Ingrain's curated cards.

## The cross-validated result

Same 12 questions, re-run after both fixes: **0.547**. Then I ran a stratified n=50 with the same selection process:

| Lane | Mean (n=50) | Wins / Losses / Ties |
|---|---:|:---|
| `hermes-default` | 0.434 | 0 / 12 / 38 |
| **`ingrain-llm-sidecar`** | **0.588** | **12 / 0 / 38** |
| **Δ** | **+0.154 absolute / +35.6% relative** | |

12 per-question wins, **0 losses**, 38 ties. The asymmetry is consequence of the architecture: sidecar = default + Ingrain, so the worst case is "Ingrain's cards added nothing, but default was still there." Empirically that's what happened on the ties.

The biggest per-type win is on `knowledge-update` (0.146 → 0.750, +0.604) — exactly the use case Ingrain was designed for: a fact the user revised later in the conversation, where the agent has to pick the new value. The regex-based system would have promoted both; the LLM consolidator picks the later one and supersedes the earlier card.

I then ran on `longmemeval_s` — the subset with much longer haystacks (~510KB/question vs ~45KB on Oracle). Default memory's 12k char limit drops 95%+ of the haystack content; it scored 0.002 (essentially noise floor). Ingrain held 0.074 (~37x relative). Both lanes struggled absolutely — long context is genuinely hard — but Ingrain at least had signal where default had none.

Plus a hand-authored "carryforward" benchmark of 20 scenarios specifically designed to test the Monday-correction → Friday-agent-obeys-it case: Ingrain 0.924 vs default 0.882, both with 0 forbidden-content leaks.

Five benchmark rows. All wins. One external. The arc held.

## Honest read of what's still weak

A reviewer should not assume this is finished. Concretely:

1. **Sandbox Universe v0 has a scorer bug** I documented in [`failure-walkthrough-repeated-work.md`](https://github.com/benlloydg/sandbox-universe/blob/main/reports/v0/analysis/failure-walkthrough-repeated-work.md). On `repeated_work_cross_thread_l4`, `hermes-default` scored 100/100 by dumping the entire trace and accidentally hitting every expected substring. The raw-dump cap only fires on forbidden leaks; this universe doesn't have any, so the cap doesn't trigger. Fix is in the v1 backlog.

2. **No external lane submissions yet.** The `LaneAdapter` protocol + entry-point registration is shipped, the contributing docs exist, but no one outside the author has registered a lane. Until a MemGPT or Letta lane is submitted by their team and they don't win, "Ingrain is competitive" is a single-author claim.

3. **LongMemEval `_s` absolute scores are low.** Both lanes struggle. The 37x relative gap is real but the absolute number (0.074 for Ingrain) isn't impressive in a headline. The next consolidator-improvement target is multi-pass consolidation on long traces, where the prompt is currently a one-shot.

4. **Same-author benchmark still load-bearing.** Even with cross-validation on LongMemEval, the Sandbox Universe scores are by the author. Independent reproducibility requires either external lanes or a third-party run.

5. **No production-deployment evidence.** I use Ingrain in my own Hermes agent workflows daily, but I haven't captured a specific `ingrain why` example catching a real mistake on real production work. That single screenshot would be more credible than any benchmark.

## What I think this work demonstrates

For someone reading this as part of a portfolio:

1. **A real architectural pivot driven by external evidence.** Regex → LLM consolidator wasn't a refactor; it was a class change. The fact that the regex compiler was clean, fast, and "worked" on my own benchmark didn't save it when external data said otherwise.

2. **An honest statistical posture.** The sidecar-isolation bootstrap CI is in the report. The 7-3 sign test result that wasn't significant is in the report. The Oracle n=12 → n=50 result didn't change my framing; both are committed. The intermediate `ingrain-llm-sidecar` runs (the broken v1 with strict prompt, the still-broken v2 before sidecar fix) are preserved in git history.

3. **Cross-validation as a forcing function.** Sandbox Universe alone wasn't enough; running on LongMemEval was what forced the architectural pivot. The repos are structured so future memory systems get the same forcing function.

4. **A real systems contribution.** The `ingrain why` audit trail is something neither MemGPT, Letta, Mem0, nor Zep provide. The sidecar architecture is provably `≥ default` by construction. The Hermes plugin makes the whole thing work without any new API keys or SDK lock-in. These are claims that can be checked in the code.

## What's next

In order of expected leverage:

1. **One week of production use** with `ingrain why` snapshots captured and added to the README as a case study.
2. **External lane submissions** — invite MemGPT / Letta / Mem0 teams via the `CONTRIBUTING.md` lane-submission protocol. Even one external lane that doesn't win Ingrain validates the framework.
3. **Sandbox Universe v1 scorer** with the raw-dump cap fixed and a new `expected_synthesis` component that forces actual answer composition.
4. **Long-context consolidator improvements** — multi-pass for `longmemeval_s` style traces. Predict 0.074 → 0.15-0.20.
5. **A NeurIPS/ICLR workshop submission** if any of the above land cleanly.

## Receipts

- Ingrain: [github.com/benlloydg/ingrain](https://github.com/benlloydg/ingrain)
- Sandbox Universe (benchmarks + reports): [github.com/benlloydg/sandbox-universe](https://github.com/benlloydg/sandbox-universe)
- All committed runs (per-question raw outputs, answers, summaries): [`sandbox-universe/reports/INDEX.md`](https://github.com/benlloydg/sandbox-universe/blob/main/reports/INDEX.md)
- Sidecar isolation analysis (bootstrap CI, sign test): [`reports/v0/analysis/sidecar-isolation.md`](https://github.com/benlloydg/sandbox-universe/blob/main/reports/v0/analysis/sidecar-isolation.md)
- Failure walkthrough (scorer bug I found in my own benchmark): [`reports/v0/analysis/failure-walkthrough-repeated-work.md`](https://github.com/benlloydg/sandbox-universe/blob/main/reports/v0/analysis/failure-walkthrough-repeated-work.md)
- Public-readiness audit: [`AUDIT.md`](AUDIT.md)
