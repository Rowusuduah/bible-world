# prompt-lock

**Git-native prompt regression testing with judge calibration and trace-linked eval scoring for any LLM CI/CD pipeline.**

> "I stationed some of the people behind the lowest points of the wall at the exposed places, posting them by families, with their swords, spears and bows." — Nehemiah 4:13

Every prompt change is a gap in the wall. prompt-lock stations a calibrated eval guard at every gap. No regression passes undetected.

---

## The Problem

You are shipping LLM features fast. Prompts change 5-10 times a week. But:

- You have **no automated detection** when a prompt change causes quality to drop.
- Your **LLM-as-judge might be miscalibrated** — it could be passing bad outputs and blocking good ones.
- When quality drops in production, you **cannot trace which change caused it**.
- Every evaluation tool you have tried is **locked to one framework** (LangChain) or one purpose (security red-teaming).

Gartner found that only 18% of software engineering teams use AI evaluation platforms in 2025. The other 82% are testing LLMs less rigorously than their login forms.

prompt-lock fixes this.

---

## What prompt-lock Does

1. **Detects prompt changes** in every PR using git diff
2. **Calibrates your LLM judge** before trusting it as a CI gate (requires >80% agreement with your human-labeled examples)
3. **Runs your eval suite** on changed prompts only (keeps CI costs low)
4. **Logs every run** with commit SHA, prompt hash, model version, and scores to a local SQLite ledger
5. **Fails the build** if quality drops below your configured threshold
6. Works with **any LLM framework** — not just LangChain, not just OpenAI

---

## Quick Start

### Install

```bash
pip install prompt-lock
```

### Initialize

```bash
prompt-lock init
```

This creates `.prompt-lock/config.yaml` with sensible defaults.

### Add Your First Eval

```yaml
# .prompt-lock/config.yaml
version: 1

prompts:
  - path: prompts/summarize.txt
    name: summarize
    model: anthropic/claude-3-5-haiku
    evals:
      - type: llm_judge
        judge_model: anthropic/claude-3-5-haiku
        criteria: "Is the summary accurate, concise, and complete?"
        calibration:
          dataset: evals/calibration/summarize_labels.jsonl
          min_agreement: 0.80
        threshold: 0.75

gate:
  mode: regression
  regression_threshold: 0.05

tracer:
  backend: sqlite
  db_path: .prompt-lock/traces.db
```

### Calibrate Your Judge

```bash
prompt-lock calibrate --judge claude-3-5-haiku --dataset evals/calibration/summarize_labels.jsonl
```

Output:
```
Judge Calibration Report
========================
Judge:          claude-3-5-haiku
Dataset:        20 human-labeled examples
Agreement:      87.5%  [PASS — threshold: 80%]
Correlation:    Spearman r=0.91  [STRONG]
Bias:           +0.03 (slight positive bias — judge scores slightly generous)
Status:         CALIBRATED — safe to use as CI gate
```

### Run Checks

```bash
prompt-lock check
```

Output:
```
prompt-lock v0.1.0
==================
Detecting changed prompts... 1 found
  - prompts/summarize.txt (modified)

Running eval suite for: summarize
  - llm_judge (claude-3-5-haiku): 0.82  [PASS — threshold: 0.75]
  - semantic_similarity:          0.79  [PASS — threshold: 0.70]

Baseline comparison:
  - Previous score: 0.85
  - Current score:  0.82
  - Regression:     -3.5%  [PASS — threshold: 5%]

Trace logged: .prompt-lock/traces.db
  Commit: a3f7b92
  Prompt hash: sha256:9d4c2a...
  Model: claude-3-5-haiku-20241022

Result: PASS
```

### GitHub Actions

```yaml
# .github/workflows/prompt-lock.yml
name: Prompt Regression Check
on: [pull_request]
jobs:
  prompt-lock:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: prompt-lock/action@v1
        with:
          config: .prompt-lock/config.yaml
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          fail-on-regression: true
```

---

## Judge Calibration (The Feature No One Else Has)

Before you trust an LLM to evaluate your LLM, you need to know if it agrees with humans.

Research shows: an LLM judge that achieves less than 80% agreement with human evaluators on your specific task is not reliable enough for automated CI gate decisions.

prompt-lock measures this before you ever use the judge in CI.

**Calibration dataset format** (20+ examples, JSONL):

```jsonl
{"input": "Summarize: [text]", "output": "The summary...", "human_score": 0.9}
{"input": "Summarize: [text 2]", "output": "The summary 2...", "human_score": 0.3}
```

You label 20 examples once. prompt-lock validates that your chosen judge agrees with you on those examples. If it does not (agreement < 80%), prompt-lock refuses to use that judge as a CI gate and tells you why.

This is the guard being trained before being stationed at the wall.

---

## Traceability

Every eval run is logged to `.prompt-lock/traces.db` with:

- Prompt file path and content hash
- Git commit SHA
- Model version and parameters
- Scores per metric
- Pass/fail result
- Timestamp

Query your trace history:

```bash
# Show all eval runs for a prompt in the last 30 days
prompt-lock traces show --prompt prompts/summarize.txt --last 30d

# Find the commit that caused a quality drop
prompt-lock traces diff --before 2026-03-15 --after 2026-03-15

# Export to JSON for your observability platform
prompt-lock traces export --format json --output traces.json
```

When quality drops in production, you know exactly which commit caused it.

---

## Comparison

| | prompt-lock | Promptfoo | LangSmith | DeepEval |
|---|---|---|---|---|
| Prompt change detection | YES | NO | NO | NO |
| Judge calibration | YES | NO | NO | NO |
| Framework-agnostic | YES | YES | NO (LangChain) | YES |
| Git-native versioning | YES | NO | NO | NO |
| Trace ledger with commit SHA | YES | NO | PARTIAL | NO |
| CI gate out of box | YES | YES | YES | NO |
| Open source | YES | YES | NO (SaaS) | YES |

---

## Supported Eval Types

| Type | Description |
|------|-------------|
| `llm_judge` | LLM evaluates output against a criteria string |
| `exact_match` | Exact string match against expected output |
| `semantic_similarity` | Cosine similarity using sentence-transformers (offline) |
| `regex` | Regular expression match |
| `custom` | Python function scorer |

---

## Supported LLM Providers

Via LiteLLM:
- Anthropic (Claude)
- OpenAI (GPT-4, o-series)
- Google (Gemini)
- Local models (Ollama)
- Any OpenAI-compatible API

---

## The Biblical Design Principle

prompt-lock was designed around a 2,500-year-old construction management insight:

Nehemiah was rebuilding the walls of Jerusalem under threat of attack. He did not stop building — but he stationed guards specifically at the lowest points and exposed places (the gaps), while workers kept building with tools in one hand and weapons in the other.

Every prompt change is a gap in the wall. Enemies of quality (regression, hallucination, degradation) always enter through the gaps — the points of change — not through the stable, finished sections.

The design decisions derived from this pattern:
- **Only eval changed prompts** (guards at gaps, not everywhere — keeps CI costs low)
- **Calibrate before guarding** (Nehemiah would not station an untrained guard)
- **Workers keep building** (non-blocking background runs for soft-fail mode)
- **The gate does not retreat** (hard-fail blocks merge — Nehemiah refused to abandon the wall)

---

## Contributing

```bash
git clone https://github.com/prompt-lock/prompt-lock
cd prompt-lock
pip install -e ".[dev]"
pytest tests/
```

PRs welcome. Issues welcome. Stars encouraged.

---

## License

MIT

---

*Built by BibleWorld. Grounded in Nehemiah 4:13-14.*
