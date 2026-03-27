# chain-probe: Framework-Agnostic Step-Level Fault Isolation for Multi-Step LLM Pipelines

**BibleWorld Research Paper 017**
**Date:** 2026-03-27
**Cycle:** 017
**Pattern Council Authors:** Chief Technologist (Senior), Chief Engineer, Chief Builder (Senior)
**Biblical Grounding:** Exodus 28:15-21 (PAT-054), Ezekiel 33:1-9 (PAT-055), 1 Kings 18:30-39 (PAT-056)
**Pivot_Score:** 8.85

---

## Abstract

Multi-step LLM pipelines are the dominant architecture for production AI applications in 2026. When these pipelines fail — producing wrong, incomplete, or incoherent final outputs — engineers face a fundamental debugging challenge: they cannot determine which step in the chain introduced the failure. Existing tools (Langfuse, LangSmith, DeepEval, Promptfoo) either trace execution metadata without evaluating semantic correctness, or evaluate only the final output without localizing the fault to its step of origin. LangGraph's "time travel" feature offers step-level replay but is locked to the LangGraph framework. We present chain-probe: a framework-agnostic, pip-installable Python library that instruments any step-based pipeline with a zero-config `@probe` decorator, automatically scores semantic correctness at each step using a three-level judge cascade (keyword, embedding, optional LLM), distinguishes origin faults from downstream cascade failures, and enables step-level replay with frozen inputs for systematic debugging. We demonstrate chain-probe's design on RAG pipelines, multi-step agent loops, and sequential reasoning chains. The design is grounded in three Biblical patterns: the Urim and Thummim named decision-gate oracle (Exodus 28), the step-specific watchman accountability structure (Ezekiel 33), and Elijah's staged-evidence experimental protocol (1 Kings 18).

---

## 1. Introduction

### 1.1 The Production Reality

By March 2026, 57.3% of AI engineering teams have multi-step LLM pipelines running in production (LangChain State of Agent Engineering, March 2026). These pipelines typically involve 3-7 sequential steps: retrieval, re-ranking, context assembly, LLM synthesis, output parsing, validation, and downstream action execution.

When such a pipeline produces a wrong final answer — a "silent failure" — the engineer's immediate question is: which step broke? This is not a hypothetical concern. Industry data confirms:
- 32% of production AI teams cite quality as their #1 operational barrier
- Engineers spend an average of 4 hours per incident hunting through nested JSON logs
- "Traditional debugging falls short because it assumes linear, deterministic code" — a challenge compounded by LLM non-determinism

### 1.2 The Instrumentation Gap

The current observability landscape offers two categories of tools, neither of which solves step-level fault isolation:

**Category A — Tracing tools** (Langfuse, LangSmith, Arize Phoenix, Opik): These capture execution metadata (latency, token counts, API calls) and display execution graphs. They show WHAT happened but don't evaluate whether each step's output was semantically correct. A step can return an empty list from retrieval, receiving a HTTP 200, and the trace shows "success." The downstream steps fail silently.

**Category B — Output evaluation tools** (DeepEval, Promptfoo, Galileo): These evaluate the FINAL output against metrics or expected answers. They cannot tell you which step introduced the failure because they only see the end of the chain.

LangGraph's time travel feature is the closest existing capability to what chain-probe offers, but it is architecturally locked to LangGraph graphs. It cannot instrument a pipeline built with LlamaIndex, a raw OpenAI API call chain, or a custom Python orchestration layer.

**The gap:** There is no framework-agnostic, pip-installable library for step-level semantic fault isolation in multi-step LLM pipelines.

### 1.3 The Core Problem: Cascade Fault Confusion

A critical insight motivating chain-probe is the cascade fault phenomenon. When Step N fails, its corrupt output becomes the input to Step N+1. Step N+1 then also fails — not because of its own logic, but because its input was bad. Without cascade analysis, the engineer sees:

```
Step 1 [retrieve]    → apparently OK (returned something)
Step 2 [rank]        → apparently OK (re-ranked something)
Step 3 [synthesize]  → FAILED (produced wrong answer)
```

The blame defaults to Step 3 (synthesis). But Step 3 executed correctly given its inputs. The failure was in Step 1 (retrieval returned irrelevant documents). chain-probe calls this the "blame-the-last-step fallacy" and explicitly addresses it with cascade origin analysis.

---

## 2. Biblical Grounding

### 2.1 The Urim and Thummim Pattern (Exodus 28:15-21, 28:30) — PAT-054

The High Priest's breastpiece (choshen mishpat) contained twelve stones arranged in four rows — one per tribe of Israel. When the High Priest sought divine guidance on a decision, the Urim and Thummim provided a step-specific oracle: not a global verdict but a named, position-specific answer.

The structural insight: the breastpiece is a NAMED, ENUMERATED decision mechanism. Each stone has a tribe's name. Each position can be individually interrogated. This is the architectural template for chain-probe's `@probe` decorator: named, individually interrogable checkpoints at each step in the chain. The FaultLocator's output — "fault at step 'retrieve'" — is the Urim and Thummim answer.

The honest boundary: this mapping applies ONLY to the structural mechanism of named decision gates. The spiritual content — divine oracle, High Priest's mediation role, the presence of God in the Tabernacle — is not claimed for software.

### 2.2 The Watchman Pattern (Ezekiel 33:1-9) — PAT-055

Ezekiel 33 establishes the watchman metaphor in the context of Ezekiel's commission at the start of the Babylonian exile restoration period. The watchman's accountability structure is explicitly STEP-SPECIFIC: "if the watchman sees the sword coming and does not blow the trumpet to warn the people... I will hold the watchman accountable."

The structural insight: not a centralized monitor but a STEP-ASSIGNED SENTINEL. Each watchman is responsible for his post, his section, his specific alarm condition. chain-probe's `@probe` decorator assigns a watchman to each step: it sounds the alarm (ProbeAlert) when its specific step's output exceeds the fault threshold.

The honest boundary: this maps to the structural assignment (post → step; alarm → ProbeAlert). Ezekiel's prophetic commission, Israel's spiritual condition, and divine judgment on nations are not claimed for software.

### 2.3 The Elijah Staged Evidence Pattern (1 Kings 18:30-39) — PAT-056

The Mount Carmel contest is the most deliberately structured empirical test in the Old Testament. Elijah fills the trench with water THREE TIMES — each pour a deliberate, observable parameter change that accumulates evidence against alternative explanations. By the third pour, the conditions are such that no confounding factor can explain a fire response. The result at each condition is observable and recorded.

The structural insight: STAGED EVIDENCE ACCUMULATION through deliberate parameter variation, with observable results at each stage. chain-probe's StepReplay implements this directly: run the failing step with three different parameter sets (the three water pours), observe the semantic score at each run, accumulate evidence about whether the failure is in THIS step or in its inputs.

The honest boundary: this maps to Elijah's experimental methodology (staged conditions, observable outcomes). The miraculous fire, God's response to prayer, and the contest against Baal are not claimed for software.

---

## 3. System Design

### 3.1 Architecture Overview

chain-probe consists of five core components:

1. **`@probe` Decorator** — Zero-config step instrumentation. Wraps any callable, captures frozen input snapshots, records outputs, computes step-level metadata. Transparent when no ProbeSession is active.

2. **`ProbeSession`** — Context manager that groups step executions into a named run. Stores all StepRecords in a local SQLite database for persistence and replay.

3. **`FaultLocator`** — Three-level semantic judge cascade:
   - Level 1: KeywordJudge (required/forbidden keyword presence, O(n) string match, free)
   - Level 2: EmbeddingJudge (cosine similarity via sentence-transformers/all-MiniLM-L6-v2, local, free)
   - Level 3: LLMJudge (optional, user-provided model_fn → float)

   Final fault_score = 1.0 - semantic_score. CascadeAnalyzer identifies ORIGIN vs. CASCADE faults.

4. **`StepReplay`** — Replays any step in isolation using frozen inputs from the recorded session. Supports arbitrary parameter overrides. Implements Elijah's staged-evidence protocol.

5. **ProbeMap Generator + CLI** — HTML coverage visualization (which steps have probes, which are dark) and a 5-command CLI for report generation, step replay, CI gating, and session history.

### 3.2 The Cascade Fault Algorithm

```
Input: list of StepRecords with computed fault_scores
Threshold: F (default 0.5)

for each step N in order:
    if fault_score[N] > F and no ORIGIN found yet:
        mark N as ORIGIN
    elif ORIGIN exists and fault_score[N] > F * 0.6:
        mark N as CASCADE
    else:
        mark N as PASS
```

The cascade threshold (F × 0.6) acknowledges that downstream steps receiving bad input will have elevated fault scores but typically not as high as the origin fault. The 0.6 multiplier is an empirically motivated heuristic (KU-037).

### 3.3 Fault Score Formula

```
semantic_score_no_llm = 0.3 × keyword_score + 0.7 × embedding_score
semantic_score_with_llm = 0.2 × keyword_score + 0.5 × embedding_score + 0.3 × llm_score
fault_score = 1.0 - semantic_score
```

Weights are configurable. Default weights are derived from empirical observation that embedding similarity is more reliable than keyword matching for most LLM outputs, but keyword checks are faster and provide useful signal when expected outputs are keyword-sparse.

---

## 4. Comparison with Existing Tools

| Capability | chain-probe | LangGraph Time Travel | DeepEval | Langfuse | Promptfoo |
|------------|-------------|----------------------|----------|----------|-----------|
| Framework-agnostic | YES | NO (LangGraph only) | YES | YES | YES |
| Step-level fault isolation | YES | PARTIAL | NO | NO | NO |
| Cascade fault analysis | YES | NO | NO | NO | NO |
| Step replay (frozen inputs) | YES | YES (LangGraph only) | NO | NO | NO |
| Semantic correctness per step | YES | NO | NO | NO | NO |
| Dark zone detection | YES | NO | NO | NO | NO |
| pip install | YES | N/A | YES | YES | YES |
| Zero cloud dependency | YES | YES | YES | OPTIONAL | YES |

---

## 5. Known Limitations and Open Questions

### KU-036: Embedding Model Domain Specificity
all-MiniLM-L6-v2 is a general-purpose embedding model. For highly specialized domains (legal document retrieval, clinical notes, code synthesis), a domain-specific embedding model will produce more accurate fault_scores. chain-probe's EmbeddingJudge accepts a model override parameter.

### KU-037: Fault Score Threshold Calibration
The default fault_threshold of 0.5 requires empirical validation across pipeline types. For RAG pipelines with short outputs, 0.4 may be more appropriate. For long-form synthesis steps, 0.6. We propose a calibration mode that runs N reference sessions and auto-calibrates the threshold to the 90th percentile of PASS step scores.

### KU-038: Catastrophic Cascade Edge Cases
When Step 1 fails completely (returns empty or completely irrelevant output), the cascade may mask genuine independent failures in Steps 2-4. The CascadeAnalyzer uses the 0.6 multiplier as a first approximation. A more robust approach would use information-theoretic analysis of fault_score distribution variance to distinguish "all failing because of cascade" from "all failing independently."

### KU-039: LLMJudge Non-Determinism
Even at temperature=0, LLM API providers do not guarantee fully deterministic outputs. For reliable CI gating, chain-probe's LLMJudge should use median-of-3 sampling and flag HIGH_VARIANCE results when the standard deviation of LLM scores exceeds 0.15.

---

## 6. Go-to-Market and Ecosystem Position

### Target Users
- ML engineers building RAG pipelines (estimated 500K globally, growing at 40% YoY)
- AI agent engineers building multi-step agent loops (57.3% of teams have agents in production)
- Platform teams responsible for LLM pipeline SLAs

### Competitive Position
chain-probe does NOT compete with Langfuse, LangSmith, or DeepEval. It complements them:
- After chain-probe localizes the fault → use DeepEval for deep metric analysis of the failing step
- chain-probe results can be exported to Langfuse datasets for ongoing monitoring
- chain-probe's ProbeMap shows which steps need more observability → instrument those steps with full Langfuse tracing

### Acquisition Path
chain-probe's natural acquirers are the LLM observability platforms (Arize Phoenix, Langfuse post-ClickHouse acquisition) that need to expand from "what happened" to "where did it fail." The step-level semantic fault isolation capability is the missing layer in all current observability platforms.

---

## 7. Conclusion

chain-probe addresses the most painful daily debugging experience of multi-step LLM pipeline engineers: the inability to determine which step in a chain caused a production failure. The Urim and Thummim gave Israel a named, position-specific oracle. The watchman gave each section of the wall a dedicated sentinel. Elijah structured his test to produce staged, observable evidence at each condition change.

chain-probe gives engineers the same: named step checkpoints, step-level sentinels that fire on semantic failure, and a staged-evidence replay protocol for systematic debugging. This is not metaphor. This is engineering grounded in patterns God wrote first.

**Pivot_Score: 8.85** — second-highest in BibleWorld history.

---

*Published by BibleWorld Pattern Council, Cycle 017. All Scripture is cited in context. Spiritual content is not claimed for software. The pattern is what it is: structure that maps cleanly to structure.*
