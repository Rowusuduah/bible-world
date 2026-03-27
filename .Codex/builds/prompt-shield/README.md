# prompt-shield

**Catch brittle prompts before production does.**

[![PyPI version](https://badge.fury.io/py/prompt-shield.svg)](https://badge.fury.io/py/prompt-shield)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## The Problem

You crafted a prompt. You ran evals on 200 test cases. All pass. You ship.

72 hours later, support tickets flood in. Users who phrase their requests slightly differently are getting wrong answers. "Show me my balance" works. "What's my current account balance?" breaks. Same semantic intent. Different surface form. Same broken prompt.

**Your prompt is brittle.** It's built on sand.

Standard eval suites test whether *specific inputs* produce *correct outputs*. They do not test whether your prompt produces *consistent outputs across equivalent phrasings*. That gap is where production failures live.

prompt-shield closes the gap.

---

## What It Does

prompt-shield generates semantically-equivalent paraphrase variants of your test inputs and measures whether your prompt produces consistent outputs across all of them.

A **BrittlenessScore** of 0.0 means all variants produce equivalent output — your prompt is semantically robust, built on rock.

A score near 1.0 means your outputs change dramatically across paraphrases — you're building on sand. The storm (real users) will find this.

The **BrittleCertificate** is your deployment artifact: a structured, machine-readable certification that your prompt passed the brittleness audit at a specified confidence level.

---

## Install

```bash
pip install prompt-shield
```

---

## Quick Start

```python
from prompt_shield import BrittlenessRunner, BrittlenessEngine
import anthropic

# 1. Define your LLM function
def my_llm_call(user_input: str) -> str:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=512,
        system="You are a helpful customer service assistant.",
        messages=[{"role": "user", "content": user_input}]
    )
    return response.content[0].text

# 2. Run brittleness check
engine = BrittlenessEngine(variants_per_input=8, levels=["lexical", "semantic"])
runner = BrittlenessRunner(llm_function=my_llm_call, engine=engine)

result = runner.run(
    test_inputs=["What is my account balance?"],
    threshold=0.30
)

# 3. Read the verdict
print(f"BrittlenessScore: {result.score:.3f}")  # 0.0 (robust) to 1.0 (brittle)
print(f"Verdict: {result.verdict}")             # ROBUST | CONDITIONAL | BRITTLE
print(f"Certificate: {result.certificate.to_json()}")
```

---

## Decorator API

```python
from prompt_shield import brittle_check

@brittle_check(threshold=0.25, variants=10, levels=["lexical", "syntactic", "semantic"])
def summarize_document(document: str) -> str:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        system="Summarize the following document in 3 bullet points.",
        messages=[{"role": "user", "content": document}]
    )
    return response.content[0].text

# In your test suite, @brittle_check automatically:
# 1. Generates 10 paraphrase variants of each input
# 2. Runs summarize_document on each variant
# 3. Computes BrittlenessScore
# 4. Raises BrittlePromptError if score > 0.25
```

---

## CI Gate

```bash
# Run from command line or CI/CD
shield ci --config shield.yaml --threshold 0.30

# Exit code 0 = ROBUST (deploy)
# Exit code 1 = BRITTLE (block deployment)
```

```yaml
# shield.yaml
prompts:
  - name: customer_service_assistant
    function: myapp.prompts.customer_service_handler
    test_inputs:
      - "What is my balance?"
      - "How do I reset my password?"
      - "I need to dispute a charge"
    threshold: 0.25
    levels: [lexical, semantic]
    variants_per_input: 8

output:
  certificate: shield-certificate.json
  report: shield-report.md
  store: ./shield.db
```

---

## GitHub Action

```yaml
# .github/workflows/shield.yml
name: Prompt Brittleness Check
on: [push, pull_request]

jobs:
  shield:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: pip install prompt-shield
      - name: Run brittleness audit
        run: shield ci --config shield.yaml --threshold 0.30
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - name: Upload certificate
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: brittle-certificate
          path: shield-certificate.json
```

---

## Understanding the BrittleCertificate

```json
{
  "certificate_id": "shld_01HQXYZ789",
  "issued_at": "2026-03-27T14:32:17Z",
  "prompt_hash": "sha256:a4f2b1...",
  "verdict": "CONDITIONAL",
  "brittleness_score": 0.22,
  "threshold": 0.25,
  "confidence_interval": [0.14, 0.31],
  "variant_count": 40,
  "level_breakdown": {
    "lexical": {"score": 0.08, "verdict": "ROBUST"},
    "syntactic": {"score": 0.15, "verdict": "ROBUST"},
    "semantic": {"score": 0.42, "verdict": "BRITTLE"}
  },
  "fault_lines": [
    {
      "level": "semantic",
      "variant": "Could you tell me the current balance on my account?",
      "deviation_score": 0.67,
      "recommendation": "Prompt relies on 'What is' question structure. Add few-shot examples with diverse phrasings."
    }
  ]
}
```

---

## Fault Line Analysis

When your prompt is brittle, prompt-shield tells you WHERE and WHY:

```python
from prompt_shield import FaultLineAnalyzer

if result.verdict == "BRITTLE":
    analyzer = FaultLineAnalyzer(result)
    fault_lines = analyzer.identify()

    for fault in fault_lines:
        print(f"Level: {fault.level}")
        print(f"Brittle variant: '{fault.variant}'")
        print(f"Deviation score: {fault.deviation_score:.3f}")
        print(f"Fix recommendation: {fault.recommendation}")
```

---

## Paraphrase Levels

| Level | What It Tests | Example |
|-------|--------------|---------|
| `lexical` | Word-level substitution | "What is my balance?" → "What's my account funds?" |
| `syntactic` | Sentence structure | "What is my balance?" → "My balance — what is it?" |
| `semantic` | Full rephrasing | "What is my balance?" → "Could you tell me how much money I have?" |

Start with `["lexical", "semantic"]` for v0.1. Add `syntactic` for thorough production audits.

---

## Scoring

```
BrittlenessScore = (variants with deviation > threshold) / (total variants)

deviation = 1 - cosine_similarity(canonical_output_embedding, variant_output_embedding)

Verdict:
  score < 0.15  → ROBUST     (certified for deployment)
  0.15–0.30     → CONDITIONAL (deploy with monitoring)
  score > 0.30  → BRITTLE    (block deployment, fix required)
```

---

## Baseline Registry

```python
from prompt_shield import BaselineRegistry

registry = BaselineRegistry(store_path="./shield.db")

# Register the current brittleness score as the approved baseline
registry.register(
    prompt_name="customer_service_v1",
    score=0.18,
    certificate=result.certificate
)

# Future runs compare against baseline
future_result = runner.run(test_inputs=[...], threshold=0.30)
regression = registry.check_regression(
    prompt_name="customer_service_v1",
    current_score=future_result.score,
    max_regression=0.05   # alert if score worsened by > 0.05
)

if regression.detected:
    print(f"BRITTLENESS REGRESSION: {regression.previous:.3f} → {regression.current:.3f}")
```

---

## Why prompt-shield? How This Is Different

| Tool | What It Tests | Brittleness? |
|------|--------------|-------------|
| DeepEval | Accuracy, relevance, hallucination on specific inputs | No |
| Promptfoo | Whether specific inputs still produce correct outputs | No |
| PromptBench | Academic robustness research (adversarial attacks) | Research only |
| spec-drift | Semantic specification compliance in production | No |
| **prompt-shield** | **Output consistency across semantically-equivalent paraphrases** | **Yes — only tool** |

---

## Architecture

```
BrittlenessEngine
├── ParaphraseGenerator
│   ├── LexicalParaphraser      (WordNet + PPDB synonym substitution)
│   ├── SyntacticTransformer    (clause reordering, active/passive)
│   └── SemanticParaphraser     (T5-paraphrase model / LLM-generated)
├── ParaphraseValidator         (semantic similarity gate, rejects low-quality variants)
└── VariantSet                  (validated paraphrases per test input)

BrittlenessRunner
├── VariantRunner               (executes LLM function on each variant)
├── OutputCollector             (canonical + variant outputs)
└── BrittlenessScorer           (computes score, confidence interval, level breakdown)

BrittleCertificate              (structured output artifact — JSON + Markdown)

FaultLineAnalyzer               (identifies which variants cause brittleness, why)

BaselineRegistry (SQLite)       (stores approved scores, detects regression)
```

---

## Biblical Foundation

prompt-shield is rooted in three biblical patterns from BibleWorld:

**Daniel 5:25-28 — The TEKEL Audit:** King Belshazzar's interpretation systems saw the same words on the wall but could not read them consistently. Daniel's independent audit revealed the truth: "TEKEL — weighed on the scales and found wanting." The BrittlenessScore is the TEKEL measurement — a calibrated audit of whether the prompt's output is determined by semantic understanding (the meaning) or surface-form pattern matching (the letters). The BrittleCertificate is the written wall — permanent, authoritative, not disputable.

**Matthew 7:24-27 — Two Builders:** Two houses stand indistinguishable in fair weather. The storm (rain, streams, wind — three independent stress vectors) reveals the foundation: rock or sand. The three-level paraphrase stress test (lexical, syntactic, semantic) IS the storm. A brittle prompt is built on sand — it performs in fair weather (standard test inputs) and falls when real users phrase their requests naturally. prompt-shield applies the storm before production.

**Proverbs 17:3 — The Crucible:** "The crucible for silver and the furnace for gold." The crucible doesn't destroy silver — it certifies it. The BrittleCertificate is the crucible's output: proof that the prompt passed the heat, that its quality is verified, not asserted. Ship with the certificate or fix the dross.

---

## Known Limitations

1. **Paraphrase quality dependency:** Low-quality paraphrases (not truly semantically equivalent) will produce false brittleness scores. The ParaphraseValidator (min_similarity=0.75) mitigates this but does not eliminate it. For critical prompts, review generated paraphrases manually before establishing baselines.

2. **CI latency:** Running N variants × M test inputs adds latency to CI. Mitigated by: cached paraphrase sets (same variants per run unless explicitly regenerated), configurable N, and the option to run lexical-only (fast) vs all three levels.

3. **Calibration:** Brittleness thresholds (0.15 ROBUST, 0.30 BRITTLE) are defaults based on initial calibration. Domain-specific prompts (legal, medical, financial) may require different thresholds. Use `shield calibrate` to tune for your domain.

4. **Semantic similarity metric:** v0.1 uses sentence-transformers cosine similarity for deviation detection. This will miss subtle semantic drift where surface forms diverge but meanings are preserved. v0.2 adds LLM-as-judge deviation scoring for higher fidelity.

---

## Roadmap

| Version | Timeline | Features |
|---------|----------|---------|
| v0.1 | Weeks 1-4 | Core engine, T5 paraphrase, BrittlenessScore, BrittleCertificate, CLI, GitHub Action |
| v0.2 | Month 2 | LLM-generated paraphrases, LLM-judge deviation, FaultLineAnalyzer, BaselineRegistry |
| v0.3 | Month 3 | Trend analysis dashboard, CI report artifacts, Slack/PagerDuty integration, enterprise config |

---

## License

MIT — free to use, modify, and distribute.

---

*Catch brittle prompts before production does.*
*The TEKEL test runs before the wall.*
*Build on rock.*
