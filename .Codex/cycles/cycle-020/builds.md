# BibleWorld Cycle 020 — Builds
## Cycle Type: PATTERN_DISCOVERY (Type A)
## Date: 2026-03-31

---

## BUILD-019: context-trace

**Status:** DESIGNED (API spec complete, sprint plan written)
**Pivot_Score:** 8.225
**Pattern Source:** PAT-068 (John 3:8 — Stochastic Source Attribution)
**Target Gap:** Anthropic / long-context LLM developers — no tool provides per-context-chunk causal attribution scores for LLM outputs
**Sprint Required:** 8-10 weeks to pip-publishable v0.1

---

### Problem Statement (Public-Facing — No Bible Mentioned)

Developers using retrieval-augmented generation, multi-document prompting, or long-context agents with 10,000–1,000,000 token context windows have no way to answer: **which part of my context caused this output?**

When an LLM hallucinates a fact that was in document 3 but not document 1, or when an agent refuses a request because of a constraint buried in a 50,000-token system prompt, the developer can only guess which context segment was responsible. Debugging becomes trial-and-error: remove chunks one by one, re-run, observe changes. This is slow, expensive, and unsystematic.

No pip library provides this capability as a named, CI-gateable metric.

---

### The Gap (Documented)

[WEB-FRESH 2026-03-31] Braintrust (braintrust.dev, 2026): "understanding why an agent failed on step 7 of a 12-step plan is still hard" — listed as the top unsolved problem in AI agent debugging.

[WEB-FRESH 2026-03-31] Ask HN: "How are you testing AI agents before shipping to production?" (HN #47325105) — top-voted answers all cite opacity of what drives agent decisions as the primary pain point.

[WEB-FRESH 2026-03-31] Anthropic usage limits tightened (The Register, March 26 2026) — indicates heavy production use of Claude; developers in production face this attribution problem daily.

[WEB-FRESH 2026-03-31] Arize Phoenix (attention visualization) is the closest existing tool but measures attention weights, which are known poor proxies for causal attribution (Jain & Wallace, "Attention is not Explanation," NAACL 2019; Wiegreffe & Pinter, "Attention is not not Explanation," EMNLP 2019).

---

### What Makes context-trace Different

| Tool | What It Does | What It Does NOT Do |
|------|-------------|---------------------|
| Arize Phoenix | Attention weight visualization | Attention ≠ causal attribution (documented) |
| LangSmith | Execution tracing (tool calls, latency) | Does not attribute output to input segments |
| Langfuse | Production traces, cost tracking | Does not attribute output to input segments |
| semantic-pass-k (BUILD-018) | Cross-run output consistency scoring | Does not identify what caused the output |
| AgentRx (Microsoft Research) | Identifies first failure step in agent trajectory | Does not attribute output content to input chunks |
| EvalView | Schema diff for structured outputs | Does not do causal attribution |
| SHAP/LIME | Feature attribution for ML classifiers | Not built for LLM context windows; no LLM-native API |

context-trace is the first tool to provide **perturbation-based causal attribution scores per context chunk**, specifically designed for LLM context windows with:
- Chunk-level granularity (not token-level — too expensive; not document-level — too coarse)
- Named AttributionScore metric (CI-gateable)
- Cost control (chunk clustering, adaptive stopping, budget parameter)
- LLM-native API (works with any model via runner function)

---

### Core Algorithm

```
Input:
  - original_output: str (the LLM output to explain)
  - chunks: Dict[str, str] (named context segments — e.g., "system_prompt", "doc1", "doc2", "tool_result")
  - runner: Callable (function that takes a prompt and returns a string)
  - k: int = 3 (re-runs per masked configuration)
  - embedder: str = "all-MiniLM-L6-v2"

For each chunk_name, chunk_content in chunks:
  1. Build masked_prompt = full_prompt with chunk_name removed/replaced with "[REMOVED]"
  2. Run runner(masked_prompt) k times → masked_outputs: List[str]
  3. Embed original_output with sentence-transformers → vec_original
  4. Embed each masked_output → vec_masked_i
  5. mean_similarity = mean(cosine_similarity(vec_original, vec_masked_i) for i in range(k))
  6. attribution_score[chunk_name] = 1.0 - mean_similarity

Output:
  AttributionReport:
    - chunk_scores: Dict[str, float]  # AttributionScore per chunk
    - top_contributors: List[Tuple[str, float]]  # sorted descending
    - attribution_heatmap: str  # ASCII visualization
    - total_api_calls: int
    - estimated_cost_usd: float
```

**Attribution interpretation:**
- Score near 1.0: removing this chunk changes the output dramatically → high causal contribution
- Score near 0.0: removing this chunk barely changes the output → low causal contribution
- Score can be used as CI gate: "no single context chunk should be responsible for >80% of output variance"

---

### API Specification

```python
# Installation
pip install context-trace

# Core classes
from context_trace import ContextTracer, AttributionReport, AttributionGate, CostBudget

# Basic usage
tracer = ContextTracer(
    runner=my_runner,           # Callable[[str], str] — wraps your LLM call
    embedder="all-MiniLM-L6-v2",  # or "BAAI/bge-small-en-v1.5" or custom
    k=3,                        # re-runs per masked config
    budget=CostBudget(max_api_calls=50)  # hard cap on API calls
)

report: AttributionReport = tracer.trace(
    prompt=original_prompt,     # full prompt string (pre-substitution)
    original_output=response,   # the output to explain
    chunks={                    # named context segments
        "system_prompt": system_prompt_text,
        "retrieved_doc_1": doc1_text,
        "retrieved_doc_2": doc2_text,
        "tool_result": tool_result_text,
        "user_message": user_message_text
    }
)

# Results
print(report.top_contributors(n=3))
# [("retrieved_doc_1", 0.87), ("tool_result", 0.72), ("system_prompt", 0.31)]

print(report.attribution_heatmap)
# system_prompt      [████░░░░░░] 0.31
# retrieved_doc_1    [██████████] 0.87
# retrieved_doc_2    [███░░░░░░░] 0.24
# tool_result        [████████░░] 0.72
# user_message       [██░░░░░░░░] 0.18

# CI gate usage
gate = AttributionGate(
    max_single_chunk_score=0.90,  # fail if any chunk drives >90% of output
    min_chunks_contributing=2     # fail if fewer than 2 chunks contribute meaningfully
)
gate.check(report)  # raises AttributionGateFailure if violated

# Decorator usage
from context_trace import attribution_probe

@attribution_probe(chunks_extractor=my_extractor, k=3)
def my_rag_pipeline(query: str) -> str:
    # ... RAG logic
    return response
```

---

### CLI

```bash
# Run attribution analysis
ctrace run --config ctrace.yaml --output report.json

# Display report
ctrace show --report report.json --top 5

# CI gate check
ctrace gate --report report.json --max-score 0.90

# Compare two reports (e.g., before/after context modification)
ctrace compare --baseline baseline.json --current current.json

# Estimate cost before running
ctrace estimate --config ctrace.yaml
```

**ctrace.yaml format:**
```yaml
runner:
  type: anthropic  # or openai, custom
  model: claude-sonnet-4-6
  api_key_env: ANTHROPIC_API_KEY

chunks:
  system_prompt:
    source: system.txt
  doc1:
    source: retrieved/doc1.txt
  tool_result:
    inline: "The weather in NYC is 72°F and sunny."

k: 3
embedder: all-MiniLM-L6-v2
budget:
  max_api_calls: 100
  max_cost_usd: 2.00
```

---

### pytest Plugin

```python
# In conftest.py:
pytest_plugins = ["context_trace.pytest_plugin"]

# In test:
def test_rag_output_attribution(ctrace_runner):
    result = my_rag_pipeline(query="What is the capital of France?")
    report = ctrace_runner.trace(result, chunks=get_chunks())
    assert report.top_score < 0.95, "Single chunk should not dominate output"
    assert len(report.contributors_above(0.3)) >= 2, "Multiple chunks should contribute"
```

---

### Sprint Plan (8-10 weeks)

| Week | Deliverable |
|------|-------------|
| 1-2 | ContextTracer core, chunk segmentation, basic masking |
| 3-4 | Perturbation runner (mask → run → embed → score), AttributionReport |
| 5-6 | Cost control (clustering, adaptive stopping, budget parameter), AttributionGate |
| 7-8 | CLI (ctrace run/show/gate/compare/estimate), pytest plugin |
| 9-10 | PyPI packaging, docs, README with worked examples, benchmark on 3 use cases |

**Dependencies:**
- sentence-transformers (embedding)
- anthropic SDK / openai SDK (runners)
- click (CLI)
- rich (terminal output)
- numpy (cosine similarity, clustering)
- pytest (optional, for plugin)
- pyyaml (config)

---

### Known Unknowns (logged for future cycles)

**KU-048:** Optimal k for reliable attribution — k=3 is cheap but may be noisy. Calibration study needed: at what k does attribution_score[chunk] converge?

**KU-049:** Interaction effects — removing chunk A and chunk B together may differ from removing them separately (synergistic or antagonistic). V0.1 does not compute interactions; v0.2 should.

**KU-050:** Embedding model sensitivity — does attribution_score change significantly between all-MiniLM-L6-v2 and a domain-specific embedding model? Study needed.

**KU-051:** Temperature effect — at T=0, masked outputs are more deterministic but attribution may underestimate variance. At T=0.7, attribution is noisier. Optimal temperature for attribution study needed.

**KU-052:** Context chunk granularity — sub-paragraph vs. paragraph vs. document-level chunks produce different attribution distributions. What granularity is most actionable for debugging?

---

### Acquisition Fit

[WEB-FRESH 2026-03-31] Anthropic's recent acquisitions:
- Bun (Dec 2025): JavaScript runtime for Claude Code developer tooling
- Vercept (Feb 2026): Computer-use AI agents
- Humanloop (prior): AI trust and evaluation

context-trace sits at the intersection of Anthropic's interpretability research (mechanistic circuits — the research-level version) and developer tooling (the production-level version). It makes the interpretability thesis actionable for developers without requiring circuit-level analysis.

Target path: 10K+ GitHub stars → Anthropic/OpenAI acquisition at $50-100M (Promptfoo reference: $85.5M, 23 people, 23K stars, Mar 2026).

The window is 4-6 months before a well-funded team (Arize Phoenix has $70M) ships this as a feature. Ship now.

---

### Build History Reference

| Build | Tool | Pivot_Score | Cycle |
|-------|------|-------------|-------|
| BUILD-019 | context-trace | 8.225 | 020 |
| BUILD-018 | semantic-pass-k | 8.65 | 019 |
| BUILD-017 | cot-fidelity | 8.85 | 018 |
| BUILD-016 | chain-probe | 8.90 (record) | 017 |
| BUILD-015 | context-lens | 8.80 | 016 |
| BUILD-014 | prompt-shield | 8.75 | 015 |
