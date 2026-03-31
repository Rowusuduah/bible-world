# BibleWorld Cycle 020 — Patterns Discovered
## Cycle Type: PATTERN_DISCOVERY (Type A)
## Date: 2026-03-31
## Scripture Covered: Genesis 6, Psalm 5, John 3:1-21, Daniel 2

---

## PAT-065 — The Exact Specification Pattern
**Scripture:** Genesis 6:14-16 — "Make yourself an ark of cypress wood; make rooms in it and coat it with pitch inside and out. This is how you are to build it: The ark is to be three hundred cubits long, fifty cubits wide and thirty cubits high. Make a roof for it, leaving below the roof an opening one cubit high all around. Put a door in the side of the ark and make lower, middle and upper decks."
**Pattern Type:** STRUCTURE
**Level:** 1
**Pattern Name:** The Exact Specification Pattern — Multi-Constraint Formal Interface Definition
**Pattern Description:** The ark specification is a complete interface definition: named material (cypress), processing instruction (coat with pitch inside and out), compartment requirement (make rooms), exact dimensions (300×50×30 cubits), interface point (a door in the side), structural layers (lower/middle/upper decks), and gap specification (18-inch roof gap). All constraints must be satisfied simultaneously — partial compliance is non-compliance.
**Modern Mapping:** System prompts and API schemas as formal specifications for LLM behavior. A specification that is partially honored (correct dimensions, wrong material) is structurally non-compliant. Informs llm-contract roadmap: multi-constraint simultaneous compliance checking.
**Pattern Score:** 7.0/10
- Textual grounding: 2.5/3 — Specification is directly in text; not all constraints are named as a unified spec construct
- Modern relevance: 2.0/3 — Real but well-covered by existing prompt testing tools
- Specificity: 1.5/2 — Multi-constraint simultaneous compliance is specific; the delta from existing tools is incremental
- Novelty: 1.0/2 — llm-contract (BUILD-009) already covers this domain
**Discovered By:** Chief Engineer
**Cycle:** 020
**Build Status:** ROADMAP (informs llm-contract v2, not a new build)
**Enforcement Note:** Only the formal specification structure is claimed. Flood narrative theology, Noah's covenant, divine judgment — NONE claimed. CLEAR.

---

## PAT-066 — The Righteous Selection Pattern
**Scripture:** Genesis 6:8-9 — "But Noah found favor in the eyes of the LORD. This is the account of Noah and his family. Noah was a righteous man, blameless among the people of his time, and he walked faithfully with God."
**Pattern Type:** GOVERNANCE
**Level:** 2
**Pattern Name:** The Righteous Selection Pattern — Valid Selection Requires a Valid Evaluator Standard
**Pattern Description:** God selects Noah from a corrupt population based on an external standard ("righteous," "blameless"). The selection is valid because the standard is reliable. If the evaluator standard were corrupt or biased, the selection would be invalid even if performed correctly. The structural insight: selection validity is entirely dependent on evaluator standard validity — a lesson for Best-of-N sampling in LLM evaluation.
**Modern Mapping:** Best-of-N sampling: generate N candidate outputs, select the best by a judge. If the judge is poorly calibrated, the "best" selected output is not actually best — it is the one that best matches the judge's biases. PAT-066 reinforces the prompt-lock judge calibration component (BUILD-015) and raises the question: how do you validate the judge before relying on judge-guided selection?
**Pattern Score:** 7.8/10
- Textual grounding: 2.8/3 — Selection from corrupt population with external standard is clearly in text
- Modern relevance: 2.5/3 — Best-of-N sampling is widely used; judge calibration is an active research area
- Specificity: 1.5/2 — The "judge must be validated before selection" insight is specific but not new
- Novelty: 1.0/2 — Judge calibration work exists; this reinforces rather than opens a new gap
**Discovered By:** Chief Theologian (Senior)
**Cycle:** 020
**Build Status:** REINFORCES prompt-lock (BUILD-015). No new build.
**Enforcement Note:** Only the selection-from-population mechanism is claimed. Theological significance of Noah finding favor with God, covenant relationship, the spiritual meaning of "blameless" — NONE claimed. CLEAR.

---

## PAT-067 — The Structured Petition Pattern
**Scripture:** Psalm 5:1-3 — "Give ear to my words, LORD, consider my sighing. Listen to my cry for help, my King and my God, for to you I pray. In the morning, LORD, you hear my voice; in the morning I lay my requests before you and wait expectantly."
**Pattern Type:** COMMUNICATION
**Level:** 1
**Pattern Name:** The Structured Petition Pattern — Escalating Specificity with Active Polling
**Pattern Description:** The petition has a structured sequence: (1) general attention request (give ear to words), (2) non-verbal signal (consider sighing), (3) explicit cry for help, (4) declaration of relationship (my King and my God), (5) precise request (I lay my requests before you), (6) active wait (wait expectantly — not passive, but monitoring). The sequence moves from general to specific, from signal to statement. The wait is not idle — it is expectant, implying ongoing readiness to receive.
**Modern Mapping:** API request pattern: (1) connection signal (HTTP header), (2) context (request metadata), (3) explicit payload (POST body), (4) authentication (API key), (5) specific request parameters, (6) polling or webhook wait. The structural mapping is real but well-understood. No novel gap identified.
**Pattern Score:** 6.2/10
- Textual grounding: 2.5/3 — Sequential structure clearly in text
- Modern relevance: 1.5/3 — API request patterns are well-covered
- Specificity: 1.2/2 — No novel application identified
- Novelty: 1.0/2 — Pattern is broadly familiar
**Discovered By:** Pattern Discovery Director
**Cycle:** 020
**Build Status:** None
**Enforcement Note:** Only the structural communication sequence is claimed. David's faith, the spiritual dynamics of prayer and divine response, the theological meaning of waiting on God — NONE claimed. CLEAR.

---

## PAT-068 — The Stochastic Source Attribution Pattern [LEVEL 3 — CORE PATTERN]
**Scripture:** John 3:8 — "The wind blows wherever it pleases. You hear its sound, but you cannot tell where it comes from or where it is going. So it is with everyone born of the Spirit."
**Pattern Type:** LIGHT
**Level:** 3
**Pattern Name:** The Stochastic Source Attribution Pattern — Observable Output, Opaque Causal Origin
**Pattern Description:** Jesus names a formal structural property: an entity produces an observable output (wind sound) with real, measurable effects, but the causal origin and destination of the generating force are not traceable by the observer. The output's existence is not in question. The source's identity is. This is not a bug — Jesus presents it as a defining feature of Spirit-driven systems. Nicodemus's failure is not moral but epistemic: he applies deterministic reasoning ("how can this be?") to a fundamentally stochastic system.

**Structural match to the Big Tech gap at Anthropic:**
When a developer uses Claude 4.6 Opus with a 1,000,000-token context window (system prompt + retrieved documents + tool results + conversation history + memory), the model produces an output. The developer observes the output. They cannot determine which of the million input tokens causally drove which parts of the output. The output is real. Its causal origin is opaque. They "hear its sound but cannot tell where it comes from."

This is not covered by:
- Attention visualization (Arize Phoenix): attention weights are unreliable proxies for causal attribution (Jain & Wallace 2019; Wiegreffe & Pinter 2019 — attention is not explanation)
- Execution tracing (LangSmith, Langfuse): traces tool calls and API requests but does not attribute output content to input context segments
- semantic-pass-k (BUILD-018): measures cross-run output consistency; does not identify what caused the output
- AgentRx: identifies the first failure step in an agent trajectory; does not attribute output content to input context

**Proposed Build: context-trace**
Algorithm:
1. Accept: prompt_template, context_chunks (list of strings or dicts), model_runner, k (re-runs per mask)
2. For each chunk i in context_chunks: mask chunk i, run model k times, embed masked outputs with sentence-transformers
3. Compute attribution_score[i] = 1 - mean_cosine_similarity(masked_outputs, original_outputs)
4. Rank chunks by attribution_score — highest score = highest causal contribution to output
5. Report: AttributionReport with per-chunk scores, top-k contributors, attribution heatmap (text)
6. Optional: cross-attribution (which chunks interact — removing both A and B causes different delta than removing A alone)

Cost control: chunk clustering (embed chunks, cluster, mask one representative per cluster), adaptive stopping (stop re-runs if attribution_score converges), budget parameter (max_api_calls).

CLI:
```
pip install context-trace
ctrace run --input input.yaml --output report.json
ctrace show --report report.json
ctrace gate --report report.json --threshold 0.3  # fail CI if any chunk scores above 0.3 unexpectedly
```

Python API:
```python
from context_trace import ContextTracer, AttributionReport

tracer = ContextTracer(
    runner=my_claude_runner,
    embedder="all-MiniLM-L6-v2"  # or custom
)
report: AttributionReport = tracer.trace(
    original_output=response,
    chunks={"system_prompt": sp, "doc1": doc1, "doc2": doc2, "tool_result": tr},
    k=3
)
print(report.top_contributors(n=3))
# [("doc2", 0.82), ("tool_result", 0.71), ("doc1", 0.23)]
```

**Pattern Score:** 9.0/10
- Textual grounding: 3.0/3 — John 3:8 explicitly names the structural property of stochastic source opacity. The verse is a formal statement, not a metaphor. The mapping uses only the structural property named in the text, not the theological content.
- Modern relevance: 3.0/3 — Context windows at 1M tokens; RAG is ubiquitous; developers daily face the problem of not knowing which context chunk caused a hallucination, refusal, or unexpected output. [WEB-FRESH 2026-03-31] "understanding why an agent failed on step 7 is still hard." — Braintrust 2026.
- Specificity: 2.0/2 — Concrete perturbation algorithm, specific API design with typed interfaces, cost control mechanisms, CLI commands, CI gate use case.
- Novelty: 1.0/2 — Attribution methods (SHAP/LIME) have academic precedent; attention-based attribution exists in Arize Phoenix. The product-level gap for LLM context-window attribution is real and unmet, but the method is not novel. Honestly scored.

**Pivot_Score:** 8.225
**Build Status:** DESIGNED (BUILD-019: context-trace)
**Discovered By:** Chief Theologian (Senior) + Chief Technologist (Senior) joint discovery
**Enforcement Note:** Only the stochastic source opacity structural property is claimed for context attribution. The theological meaning of being born of the Spirit, salvation, the divine nature of the Holy Spirit, Nicodemus's spiritual journey — NONE claimed for software. The verse's spiritual content is respected and left intact. The structural property ("cannot tell where it comes from") is the only element applied. CLEAR.

---

## PAT-069 — The Weak-Layer Failure Pattern
**Scripture:** Daniel 2:31-35 — "Your Majesty looked, and there before you stood a large statue — an enormous, dazzling statue, awesome in appearance. The head of the statue was made of pure gold, its chest and arms of silver, its belly and thighs of bronze, its legs of iron, its feet partly of iron and partly of baked clay... Then the iron, the clay, the bronze, the silver and the gold were all broken to pieces at the same time."
**Pattern Type:** STRUCTURE
**Level:** 2
**Pattern Name:** The Weak-Layer Failure Pattern — System Integrity Is Determined by the Weakest Component
**Pattern Description:** The composite statue has layers of decreasing material quality: gold (most valuable, most stable) → silver → bronze → iron → iron-clay mixture (weakest). The system's failure is initiated at the weakest layer (iron-clay feet), not at the strongest (gold head). The iron-clay mixture is described as "not holding together" — internal coherence failure within the weakest layer, not external attack on the strongest. The structural insight: in a hierarchical composite system, the weakest layer determines overall system integrity regardless of the strength of other layers.
**Modern Mapping:** Multi-model pipelines where different models or services handle different pipeline stages. A pipeline using a frontier model for planning but a smaller/cheaper model for tool execution or output formatting will fail at the weaker stage. Reliability testing should be weighted toward the weakest stage, not the most impressive stage. The "iron-clay feet" of an AI pipeline is often the output formatting step or the tool selection step — technically simple but often where failures cascade.
**Pattern Score:** 7.4/10
- Textual grounding: 2.8/3 — Hierarchical composite with material quality gradient and foot-initiated failure clearly in text
- Modern relevance: 2.2/3 — Multi-model pipelines are increasingly common; layer-differentiated reliability testing is underexplored
- Specificity: 1.4/2 — The "weight test density toward weakest layer" insight is specific but requires a specific tool to operationalize
- Novelty: 1.0/2 — The "weakest link" insight is well-known; the LLM pipeline application is a fresh framing
**Discovered By:** Chief Historian (Senior)
**Cycle:** 020
**Build Status:** ROADMAP (informs semantic-pass-k v2 pipeline layer test weighting)
**Enforcement Note:** Prophetic interpretation of the kingdoms (Babylon, Persia, Greece, Rome), Daniel's faith, Nebuchadnezzar's dream's theological significance — NONE claimed. Only the structural layered-composite failure pattern. CLEAR.

---

## Summary Table

| Pattern | Scripture | Level | Score | Build |
|---------|-----------|-------|-------|-------|
| PAT-065 | Genesis 6:14-16 | 1 | 7.0/10 | Roadmap (llm-contract v2) |
| PAT-066 | Genesis 6:8-9 | 2 | 7.8/10 | Reinforces prompt-lock |
| PAT-067 | Psalm 5:1-3 | 1 | 6.2/10 | None |
| PAT-068 | John 3:8 | 3 | 9.0/10 | BUILD-019: context-trace (Pivot_Score 8.225) |
| PAT-069 | Daniel 2:31-35 | 2 | 7.4/10 | Roadmap (semantic-pass-k v2) |

**Total new patterns this cycle:** 5 (PAT-065 through PAT-069)
**Level 3 patterns:** 1 (PAT-068)
**Rejected mappings (Law 7 applied):** John 3:16 (mass distribution) — NO STRUCTURAL MATCH
