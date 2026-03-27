# context-lens

**Test whether your LLM actually retrieves information from every position in its context window — before it silently fails in production.**

Your LLM passes all your evals. You ship it. Users start complaining that it ignores half their documents. You check the logs — technically successful calls, no errors. The bug is invisible. This is the lost-in-the-middle problem, and context-lens is the missing test gate.

---

## The Problem

Research confirmed what production engineers already knew: LLMs pay heavy attention to information at the **start** and **end** of long contexts, and silently drop information **buried in the middle**.

```
Context position:  [start] ====== [middle] ====== [end]
LLM attention:     HIGH               LOW           HIGH
```

This breaks:
- **RAG pipelines** — retrieved chunks in positions 3-7 of 10 may be ignored
- **Long document analysis** — key clauses in the middle of contracts get missed
- **Multi-turn agents** — prior tool outputs buried in conversation history get lost
- **System prompts with long instructions** — middle constraints are violated silently

**The failure mode is always the same:** traditional evals test correctness on a single input. They do not test whether the model is reliable *at every position* in the context window.

context-lens fills this gap.

---

## What context-lens Does

context-lens places a "needle" (a key fact or instruction) at every position across your context window, runs your LLM, and produces a **PositionHeatmap** — a complete picture of where your model is reliable and where it fails.

```
position 1/10  (fraction=0.00)  [OK]  ##
position 2/10  (fraction=0.11)  [OK]  ##
position 3/10  (fraction=0.22)  [OK]  ##
position 4/10  (fraction=0.33)  [MISS]  ..    ← FAULT ZONE
position 5/10  (fraction=0.44)  [MISS]  ..    ← FAULT ZONE
position 6/10  (fraction=0.56)  [MISS]  ..    ← FAULT ZONE
position 7/10  (fraction=0.67)  [OK]  ##
position 8/10  (fraction=0.78)  [OK]  ##
position 9/10  (fraction=0.89)  [OK]  ##
position 10/10 (fraction=1.00)  [OK]  ##

Retrieval Score: 70%  — CONDITIONAL
Fault zones: MIDDLE-HEAVY FAILURE (lost-in-the-middle pattern detected)
```

Then it gives you a **CI gate** that fails your pipeline if the score drops below your threshold.

---

## Installation

```bash
pip install context-lens

# With Anthropic support:
pip install "context-lens[anthropic]"

# With OpenAI support:
pip install "context-lens[openai]"

# With YAML config support:
pip install "context-lens[yaml]"

# Everything:
pip install "context-lens[all]"
```

---

## Quick Start

```python
from context_lens import ContextLens, Needle, HaystackTemplate
import anthropic

# 1. Wrap your LLM in a str -> str function
client = anthropic.Anthropic()
def my_llm(prompt: str) -> str:
    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text

# 2. Define what must be found (the "needle")
needle = Needle(
    label="API rate limit",
    content="The API rate limit is 1000 requests per minute per key.",
    question="What is the API rate limit?",
    expected_answer="1000 requests per minute",
    answer_keywords=["1000", "per minute"],
)

# 3. Define the surrounding context (the "haystack")
haystack = HaystackTemplate(
    filler_text="This document describes the system API. All endpoints require authentication. ",
    target_tokens=4000,
    tokens_per_filler=15,
)

# 4. Run the audit
lens = ContextLens(model_fn=my_llm, model_name="claude-3-5-haiku")
heatmap = lens.audit(needle=needle, haystack=haystack, positions=10)

# 5. Read the result
heatmap.report()
print(f"Score: {heatmap.retrieval_score:.1%}")
print(f"Verdict: {heatmap.verdict}")
print(f"Fault zones: {heatmap.fault_zones}")
```

---

## Multi-Needle Audit

Test multiple pieces of critical information in one run:

```python
needles = [
    Needle(
        label="Rate limit",
        content="Rate limit: 1000 req/min.",
        question="What is the rate limit?",
        expected_answer="1000 req/min",
        answer_keywords=["1000"],
    ),
    Needle(
        label="Retry policy",
        content="On 429 errors, use exponential backoff starting at 2 seconds.",
        question="How should you handle 429 errors?",
        expected_answer="exponential backoff, 2 seconds",
        answer_keywords=["exponential backoff", "2 seconds"],
    ),
    Needle(
        label="Token expiry",
        content="Session tokens expire after 24 hours.",
        question="When do session tokens expire?",
        expected_answer="24 hours",
        answer_keywords=["24 hours"],
    ),
]

heatmaps = lens.audit_multi(needles, haystack, positions=10)
summary = lens.summary_report(heatmaps)
print(f"Overall score: {summary['overall_score']:.1%}")
print(f"Overall verdict: {summary['overall_verdict']}")
```

---

## CI Gate

Block deployment if context retrieval is unreliable:

```python
heatmaps = lens.audit_multi(needles, haystack, positions=10)
passed, message = lens.ci_gate(heatmaps, min_score=0.80)
print(message)
# Exit with code 1 if gate fails:
import sys
sys.exit(0 if passed else 1)
```

---

## CLI Usage

### Run an audit from config file:

```bash
context-lens audit --config my_audit.yaml
context-lens audit --config my_audit.yaml --output results.json
```

### CI gate (exits 1 on failure):

```bash
context-lens ci --config my_audit.yaml --min-score 0.85
```

### View audit history:

```bash
context-lens history --limit 10
```

---

## Config File Format (YAML)

```yaml
# my_audit.yaml
model_name: claude-3-5-haiku-20241022
provider: anthropic     # anthropic | openai | mock
model: claude-3-5-haiku-20241022
positions: 10
reliable_threshold: 0.90
conditional_threshold: 0.70

haystack:
  filler_text: "This document contains system documentation. "
  target_tokens: 4000
  tokens_per_filler: 10
  system_prompt: "Answer questions using only the provided context."

needles:
  - label: "Database connection string"
    content: "The database connection string is db://prod-server:5432/myapp"
    question: "What is the database connection string?"
    expected_answer: "db://prod-server:5432/myapp"
    answer_keywords: ["prod-server", "5432"]

  - label: "Retry limit"
    content: "The maximum retry count is 3 attempts with 5-second intervals."
    question: "How many retries are allowed and at what interval?"
    expected_answer: "3 retries, 5-second intervals"
    answer_keywords: ["3", "5-second"]
```

---

## GitHub Actions Integration

```yaml
# .github/workflows/context-lens.yml
name: Context Window Audit

on: [push, pull_request]

jobs:
  context-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install context-lens
        run: pip install "context-lens[all]"

      - name: Run context position audit
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          context-lens ci --config .context_lens.yaml --min-score 0.80

      - name: Upload audit results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: context-lens-results
          path: .context_lens.db
```

---

## Verdicts Explained

| Verdict | Score Range | Meaning |
|---------|-------------|---------|
| **RELIABLE** | >= 90% | LLM consistently retrieves information from all context positions. Safe to ship. |
| **CONDITIONAL** | 70–89% | LLM has some positional failures. Review fault zones before shipping. |
| **UNRELIABLE** | < 70% | LLM has significant positional failures. Do not ship this configuration. |

---

## Fault Zone Patterns

context-lens identifies three failure patterns:

### 1. Middle-Heavy Failure (Lost-in-the-Middle)
```
Positions: [OK] [OK] [MISS] [MISS] [MISS] [OK] [OK]
```
Information in the middle of the context is not retrieved. Classic LLM attention pattern.
**Fix:** Reorder retrieved chunks to put critical info first/last. Reduce total context size.

### 2. Edge Failure
```
Positions: [MISS] [OK] [OK] [OK] [OK] [OK] [MISS]
```
Rare — usually indicates prompt structure issues.

### 3. Scattered Failures
```
Positions: [OK] [MISS] [OK] [MISS] [OK] [MISS] [OK]
```
General degradation. Often indicates context is too long for the model's reliable attention window.

---

## Programmatic API

### `ContextLens`

```python
lens = ContextLens(
    model_fn=my_llm,                  # str -> str callable
    model_name="my-model",            # for reports
    reliable_threshold=0.90,          # >= this -> RELIABLE
    conditional_threshold=0.70,       # >= this -> CONDITIONAL, else UNRELIABLE
    db_path=".context_lens.db",       # SQLite history store
)

# Single needle audit
heatmap: PositionHeatmap = lens.audit(needle, haystack, positions=10)

# Multi-needle audit
heatmaps: list[PositionHeatmap] = lens.audit_multi(needles, haystack, positions=10)

# Summary across all needles
summary: dict = lens.summary_report(heatmaps)

# CI gate
passed: bool, message: str = lens.ci_gate(heatmaps, min_score=0.80)

# Audit history
records: list[dict] = lens.history(limit=20)
```

### `Needle`

```python
needle = Needle(
    label="my needle",                        # for reports
    content="The API key is sk-12345.",        # text to place in context
    question="What is the API key?",           # question to ask the LLM
    expected_answer="sk-12345",                # what a correct answer looks like
    answer_keywords=["sk-12345"],              # MUST appear in response to count as retrieved
)
```

### `HaystackTemplate`

```python
haystack = HaystackTemplate(
    filler_text="Filler text that repeats. ",  # repeating context filler
    target_tokens=4000,                        # approximate context size
    tokens_per_filler=10,                      # tokens in one filler_text repetition
    system_prompt="You are a helpful assistant.",  # optional system prompt
)
```

### `PositionHeatmap`

```python
heatmap.retrieval_score   # float: fraction of positions retrieved (0.0–1.0)
heatmap.verdict           # str: RELIABLE | CONDITIONAL | UNRELIABLE
heatmap.fault_zones       # list[float]: position fractions where retrieval failed
heatmap.fault_zone_label  # str: human-readable fault pattern description
heatmap.results           # list[PositionResult]: per-position details
heatmap.report()          # prints full report, returns str
heatmap.to_dict()         # dict for JSON serialization
```

---

## Why context-lens?

| Tool | What it tests |
|------|---------------|
| DeepEval, Promptfoo | Whether specific inputs produce correct outputs |
| prompt-shield | Whether outputs are stable across paraphrase variants |
| drift-guard | Whether PR code matches PR intent |
| **context-lens** | **Whether the LLM retrieves information from all context positions** |

The problem these tools solve is different. context-lens tests a specific failure mode that is invisible to all of them: positional sensitivity in the context window.

---

## Roadmap

- **v0.1** (current): KeywordJudge, PositionHeatmap, CLI, SQLite history, CI gate, GitHub Action
- **v0.2**: LLM-as-judge for semantic retrieval checking (beyond keyword matching)
- **v0.3**: Automatic fault zone diagnosis with remediation suggestions
- **v0.4**: Token-precise position control (place needle at exact token offset)
- **v0.5**: Multi-model comparison (which model is more position-robust?)
- **v1.0**: pytest plugin, pre-commit hook

---

## Contributing

Issues and PRs welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a PR.

---

## License

MIT License. Copyright 2026 BibleWorld.
