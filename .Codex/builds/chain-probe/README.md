# chain-probe

**Framework-agnostic fault isolation for multi-step LLM pipelines.**

> You have a 5-step RAG pipeline. The final answer is wrong. Is it retrieval? Re-ranking? Context assembly? LLM synthesis? Output parsing? You don't know. You spend 4 hours bisecting logs. chain-probe tells you in seconds.

[![PyPI](https://img.shields.io/pypi/v/chain-probe)](https://pypi.org/project/chain-probe/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)

---

## The Problem

Multi-step LLM pipelines fail silently. Your pipeline runs. It returns HTTP 200. The answer is wrong. You don't know which step failed.

Existing tools don't help:
- **Langfuse / LangSmith**: show you traces of what happened — not which step caused the failure
- **DeepEval / Promptfoo**: evaluate the final output — not individual steps
- **LangGraph time travel**: step replay, but locked to LangGraph — won't work on LlamaIndex, raw API calls, or custom pipelines
- **Arize Phoenix**: infrastructure observability — monitors latency and token counts, not semantic correctness per step

**There is no framework-agnostic library that:**
1. Automatically detects which step introduced a semantic failure
2. Distinguishes the origin fault from downstream cascade failures
3. Replays any step in isolation with frozen inputs for debugging

Until now.

---

## Installation

```bash
pip install chain-probe
```

**Dependencies:**
- `sentence-transformers` — local embedding judge (free, offline)
- `click` — CLI
- `rich` — terminal output
- Python standard library: `sqlite3`, `functools`, `copy`, `json`

No LLM API required for basic usage. No framework dependencies.

---

## Quickstart

```python
from chain_probe import probe, ProbeSession, FaultLocator

# Wrap each step with @probe
@probe(name="retrieve", expected_keywords=["relevant", "document", "found"])
def retrieve(query: str) -> list[str]:
    return vector_db.search(query, top_k=5)

@probe(name="rank", expected_keywords=["score", "ranked"])
def rank(docs: list[str], query: str) -> list[str]:
    return reranker.rank(docs, query)

@probe(name="synthesize")
def synthesize(context: list[str], query: str) -> str:
    return llm.complete(f"Context: {context}\n\nAnswer: {query}")

# Run with a ProbeSession
with ProbeSession(name="pipeline_run_001") as session:
    docs = retrieve("What is retrieval-augmented generation?")
    ranked = rank(docs, "What is retrieval-augmented generation?")
    answer = synthesize(ranked, "What is retrieval-augmented generation?")

# Locate the fault
report = FaultLocator(session).locate()
print(report.summary())
# Step 1 [retrieve]    fault_score=0.82  ← ORIGIN FAULT
# Step 2 [rank]        fault_score=0.65  CASCADE (from retrieve)
# Step 3 [synthesize]  fault_score=0.14  PASS
#
# FAULT LOCATED: retrieve (confidence: HIGH)
# RECOMMENDATION: Retrieval returned low-relevance documents.
#                 Check vector DB query, embedding model, or top_k parameter.
```

---

## CLI

```bash
# Run a pipeline with probe instrumentation
probe run python pipeline.py --session my_run_001

# Generate fault report
probe report --session my_run_001

# Replay a specific step with different parameters
probe replay --session my_run_001 --step retrieve --param top_k=10
probe replay --session my_run_001 --step synthesize --temperature 0.0

# Generate ProbeMap (HTML coverage visualization)
probe map --session my_run_001 --output probe_map.html

# CI mode (exits non-zero if fault detected)
probe ci --session my_run_001 --threshold 0.5

# List all sessions
probe history
```

---

## Core Concepts

### @probe decorator
Wraps any callable. Records inputs, outputs, duration, and semantic score. Zero config — just add `@probe(name="step_name")` to any function.

```python
@probe(
    name="my_step",                          # Required: step identifier
    expected_keywords=["expected", "words"], # Optional: keyword check
    expected_output="The answer is...",      # Optional: semantic comparison
    halt_on_fault=False,                     # Optional: stop chain on fault
    tags={"env": "prod", "model": "gpt-4"}, # Optional: metadata
)
def my_step(input_data):
    ...
```

### FaultLocator
Runs a three-level semantic judge cascade on each step's output:

| Judge | Method | Cost |
|-------|--------|------|
| KeywordJudge | Required/forbidden keyword regex | Free |
| EmbeddingJudge | Cosine similarity via sentence-transformers | Free (local) |
| LLMJudge | User-provided model_fn (optional) | Per your LLM API |

**Fault Score Formula:**
```
fault_score = 1.0 - semantic_score
semantic_score = (0.3 × keyword_score) + (0.7 × embedding_score)   # no LLM judge
semantic_score = (0.2 × keyword_score) + (0.5 × embedding_score) + (0.3 × llm_score)  # with LLM judge
```

### Cascade Analysis
Distinguishes the step that CAUSED the failure from steps that INHERITED bad inputs:

```
Step 1 [retrieve]    fault_score=0.82  → ORIGIN (first step above threshold)
Step 2 [rank]        fault_score=0.65  → CASCADE (downstream of ORIGIN)
Step 3 [synthesize]  fault_score=0.14  → PASS
```

Without cascade analysis, you'd blame Step 3 (the last step you can see). With chain-probe, you know it was Step 1.

### StepReplay
Re-runs any step in isolation using frozen inputs from the recorded session:

```python
from chain_probe import StepReplay

replay = StepReplay(session, step_name="retrieve")

# Run with different parameters
r1 = replay.run(temperature=0.0)          # Deterministic run
r2 = replay.run(top_k=10)                 # More documents
r3 = replay.run(prompt_variant="Be specific and find exact facts about: {query}")

# Compare
for r in [r1, r2, r3]:
    print(f"Params: {r.params} | Score: {r.semantic_score:.3f} | Verdict: {r.verdict}")
```

### ProbeMap
Generates an HTML/JSON coverage map showing which steps have probes and which are unmonitored:

```
Pipeline Coverage Report
========================
✓ retrieve       [probed] fault_score: 0.82 ORIGIN
✓ rank           [probed] fault_score: 0.65 CASCADE
✓ synthesize     [probed] fault_score: 0.14 PASS
✗ format_output  [DARK]   No probe assigned — blind spot
✗ validate       [DARK]   No probe assigned — blind spot

Coverage: 3/5 steps (60%) — 2 dark zones detected
```

---

## ProbeSession Storage

Sessions are stored in a local SQLite database (`~/.chain_probe/sessions.db`). Each session stores:
- Session metadata (name, timestamp, pipeline version)
- Per-step records (frozen inputs, outputs, duration, token count, fault scores)
- Fault report (origin step, cascade steps, confidence level)

Sessions are persistent — you can replay and re-analyze any past run.

---

## CI/CD Integration

```yaml
# .github/workflows/probe.yml
- name: Run pipeline with chain-probe
  run: |
    probe run python src/pipeline.py --session ci_run_${{ github.sha }}
    probe ci --session ci_run_${{ github.sha }} --threshold 0.5
```

Returns exit code 1 if any step has fault_score > threshold. Integrates with any CI system.

---

## With LLM Judge

```python
import anthropic

client = anthropic.Anthropic()

def my_llm_judge(step_name: str, inputs: dict, output: str, expected: str) -> float:
    """Returns a score 0.0-1.0 (1.0 = correct, 0.0 = wrong)."""
    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": f"Rate how well this output answers the query on a scale of 0-10.\nQuery: {inputs.get('query', '')}\nOutput: {output}\n\nRespond with ONLY a number 0-10."
        }]
    )
    score_text = response.content[0].text.strip()
    return float(score_text) / 10.0

@probe(name="synthesize", llm_judge=my_llm_judge)
def synthesize(context, query):
    ...
```

---

## Comparison

| | chain-probe | LangGraph time travel | DeepEval | Langfuse | Promptfoo |
|--|-------------|----------------------|----------|----------|-----------|
| Framework-agnostic | ✓ | ✗ (LangGraph only) | ✓ | ✓ | ✓ |
| Step-level fault isolation | ✓ | partial | ✗ | ✗ | ✗ |
| Cascade fault analysis | ✓ | ✗ | ✗ | ✗ | ✗ |
| Step replay with frozen inputs | ✓ | ✓ (LG only) | ✗ | ✗ | ✗ |
| Coverage map (dark zones) | ✓ | ✗ | ✗ | ✗ | ✗ |
| Local / zero cloud dependency | ✓ | ✓ | ✓ | optional | ✓ |
| pip install | ✓ | N/A | ✓ | ✓ | ✓ |

---

## Biblical Foundation

chain-probe is built on three Scripture patterns discovered in BibleWorld Cycle 017:

- **Exodus 28:15-21 (Urim and Thummim)** — The High Priest's breastpiece had twelve stones, each a named decision gate. When consulted, the oracle gave a step-specific answer: not a final verdict, but a gate-by-gate response. chain-probe's `@probe` decorator is the Urim and Thummim: twelve named stones, each interrogable.
- **Ezekiel 33:1-9 (The Watchman)** — The watchman is assigned to a specific post and sounds the alarm at HIS position. Each step in a chain needs its own watchman. chain-probe's ProbeAlert is the watchman's trumpet.
- **1 Kings 18:30-39 (Elijah's Staged Evidence)** — Elijah poured water on the altar THREE TIMES, each pour a deliberate parameter change that built evidence. StepReplay is Elijah's protocol: three runs, three conditions, evidence accumulated.

---

## License

MIT. Free to use, fork, and build upon.

---

## BibleWorld

Built in [BibleWorld](https://github.com/bibleworld) — a multi-agent system that mines Scripture for patterns and applies them to real software problems.

> "Fashion a breastpiece for making decisions... There are to be twelve stones, one for each of the names of the sons of Israel, each engraved like a seal with the name of one of the twelve tribes." — Exodus 28:15-21
