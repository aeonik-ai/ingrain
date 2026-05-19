# Evaluation Standards

Ingrain should not present a perfect local score as proof of broad memory quality.

## Current Standard

There is no single industry-standard benchmark for a learned-experience layer for coding and runner agents. The closest established benchmarks cover adjacent abilities:

| Benchmark or framework | What it tests | Relevance to Ingrain |
|---|---|---|
| LongMemEval | Long-term chat memory across information extraction, multi-session reasoning, temporal reasoning, knowledge updates, and abstention. | Useful external baseline for conversational memory, but not directly focused on execution lessons. |
| LoCoMo | Very long multi-session conversations, event summaries, QA, multimodal dialogue, temporal and causal reasoning. | Useful for long-horizon memory, less specific to runner-agent practice. |
| BEAM | Long-term memory at 100K to 10M-token scales with validated probing questions. | Strong stress test for retrieval at scale, especially where context stuffing is impossible. |
| LongMemEval-V2 | Agent experience in specialized web environments: state recall, dynamic state tracking, workflow knowledge, environment gotchas, and premise awareness. | Closest conceptual match: compact evidence from history trajectories for downstream agent performance. |
| EvoMemBench | Agent memory across in-episode vs cross-episode and knowledge-oriented vs execution-oriented tasks. | Strong framing for Ingrain because execution-oriented procedural memory is the product's real claim. |
| RAGAS-style RAG metrics | Context precision, context recall, response relevancy, faithfulness, answer accuracy, tool-call accuracy, and agent goal accuracy. | Useful secondary metrics for retrieval quality and grounded output, but not sufficient for learned experience by itself. |

Sources:

- LongMemEval: <https://arxiv.org/abs/2410.10813>
- LoCoMo: <https://arxiv.org/abs/2402.17753>
- BEAM: <https://arxiv.org/abs/2510.27246>
- LongMemEval-V2: <https://arxiv.org/abs/2605.12493>
- EvoMemBench: <https://arxiv.org/abs/2605.18421>
- Ragas metrics: <https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/>
- Karpathy LLM Wiki gist: <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>

## Public Claim Boundary

Use this language:

> Ingrain ships with local regression evals for learned-experience carry-forward, plus a live Hermes provider harness that records raw provider outputs and blockers.

Do not use this language:

> Ingrain scored 100/100, so it is better memory than Hindsight, OpenViking, or other memory systems.

## Eval Tiers

| Tier | Name | Purpose | Public interpretation |
|---|---|---|---|
| 0 | LES-Core | Small deterministic smoke test for the compiler, hydration, practice cards, and source evidence. | A 100/100 means the local regression gate passed. It is not a benchmark headline. |
| 1 | Deterministic learned-experience comparison | Local comparison across Hermes default, OpenViking-style retrieval, Hindsight-style synthesis, and Ingrain on preregistered universes. | Useful for engineering iteration. It is not evidence against live Hindsight or live OpenViking. |
| 2 | LES-Hard | Harder deterministic benchmark modeled after LongMemEval-V2/EvoMemBench themes: environment gotchas, premise awareness, stale intent, abstention, and execution-oriented memory. | Better public engineering evidence than LES-Core, but still not a live provider benchmark. |
| 3 | Live Hermes provider matrix | Real installed Hermes providers only; blocked providers are recorded as blocked with command logs. | Valid evidence about this machine and this configuration. |
| 4 | External memory benchmarks | LongMemEval, BEAM, LoCoMo, LongMemEval-V2, or EvoMemBench adapters where licensing and runtime allow. | The only tier suitable for broad comparative claims. |

## What A Karpathy-Safe Eval Should Look Like

- Preregister the universes before running providers.
- Keep raw traces, command logs, stderr, environment, and exact versions.
- Separate deterministic baselines from live provider runs.
- Treat provider errors and timeouts as failures, not as scored text.
- Include baselines that can win.
- Include abstention and stale-plan traps.
- Include enough difficulty that strong systems do not all score 100.
- Report latency, setup complexity, credentials, and cost when live providers are used.
- Make the repo useful even if the launch headline is modest.

## LES-Hard Direction

The best public-facing deterministic benchmark is **LES-Hard**, modeled after LongMemEval-V2 and EvoMemBench:

- environment gotchas
- workflow knowledge
- stale-plan and active-goal separation
- correction supersession
- premise awareness
- abstention when memory is insufficient
- completed outcome vs old todo conflicts
- compact evidence gathering under a token budget
- latency and cost alongside quality

LES-Hard now has enough scenarios that Ingrain lands below perfect. Current v0 result: `545/560` for Ingrain versus `536/560` for the deterministic Hindsight-style baseline. Treat this as engineering evidence with raw artifacts, not as proof that Ingrain beats live Hindsight.
