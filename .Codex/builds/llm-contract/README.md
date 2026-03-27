# llm-contract

**Define, version, and enforce behavioral contracts on LLM function calls.**

> Pydantic validates structure. llm-contract validates behavior. Together they make LLM function calls trustworthy.

[![PyPI version](https://badge.fury.io/py/llm-contract.svg)](https://badge.fury.io/py/llm-contract)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/llm-contract/llm-contract/workflows/CI/badge.svg)](https://github.com/llm-contract/llm-contract/actions)

---

## The Problem

Your LLM functions have Pydantic validation. They don't have behavioral contracts.

Here's what that means in practice:

```python
# Pydantic catches this: ✓
{"title": 123, "summary": "..."}   # Wrong type — field validation fails

# Pydantic does NOT catch this: ✗
{"title": "Q3 Report", "summary": "Revenue was $12.4B (invented fact not in source doc)"}
# Structurally valid. Behaviorally wrong. Pydantic approves it. Your users see it.
```

This is the gap. And it costs teams — in bugs found by users, not tests.

**Real pain points this solves:**

- You switch from GPT-4o to Claude. Output structure looks correct. Behavior silently regressed. You find out when a customer complains.
- Your model provider updates their model. Your `summarize_document` function starts producing 8-bullet summaries instead of the 3-5 you designed for. No alert. Downstream breakage.
- You have 23 LLM functions in production. You cannot watch all of them manually for behavioral drift.
- Your team has three engineers. Each defines their own informal "should produce X" expectations in comments. No enforcement. No versioning. No shared standard.

**llm-contract fixes all of this.**

---

## The Solution

llm-contract brings **contract-driven development** to LLM function calls.

Three things:
1. **Contract Definition** — Declare what your LLM function must produce, behaviorally and structurally
2. **Contract Enforcement** — Runtime validation at the function boundary, on every call
3. **Contract Versioning + Drift Detection** — Semver for behavior; CI gates; drift alerts

---

## Quick Start

```bash
pip install llm-contract
```

```python
from pydantic import BaseModel
from typing import List
from llm_contract import contract, SemanticRule
import anthropic

# 1. Define the output schema (structure — Pydantic handles this)
class DocumentSummary(BaseModel):
    title: str
    summary: str
    key_points: List[str]
    sentiment: str   # "positive" | "negative" | "neutral"

# 2. Apply the behavioral contract
@contract(
    schema=DocumentSummary,
    semantic_rules=[
        SemanticRule(
            name="no_fabrication",
            description="Summary must not introduce facts not present in the source document",
            weight=1.0,  # Critical — fail if violated
        ),
        SemanticRule(
            name="key_points_count",
            description="Must include 3-5 key points, no more, no less",
            weight=0.8,
        ),
    ],
    version="1.0.0",
    on_violation="raise",
)
def summarize_document(document: str) -> DocumentSummary:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": f"Summarize: {document}"}]
    )
    import json
    return DocumentSummary(**json.loads(response.content[0].text))

# 3. Call it — violations raise ContractViolationError
result = summarize_document(my_document)
print(result.summary)  # Guaranteed to meet your behavioral contract
```

That's it. Three steps. Your LLM function now has a behavioral contract.

---

## Features

### Structural + Semantic Validation (Two Layers)

```python
@contract(
    schema=MyOutputSchema,          # Layer 1: Pydantic structural validation
    semantic_rules=[...],           # Layer 2: LLM-judge behavioral validation
    version="2.0.0",
    on_violation="raise",
)
```

**Layer 1** catches: wrong field types, missing required fields, invalid enum values, value out of range. Zero latency — Pydantic is fast.

**Layer 2** catches: fabricated facts, wrong tone, missing required content, semantic inconsistency. ~200-500ms via configurable LLM judge.

---

### Contract Versioning (SemVer for Behavior)

```python
@contract(schema=SummarySchema, version="2.1.0")
def summarize_document(doc: str) -> SummarySchema: ...
```

Behavioral versioning follows semantic versioning rules:
- **Major** (1.x.x → 2.0.0): Breaking behavioral change — downstream consumers must update
- **Minor** (x.1.x → x.2.0): New behavioral requirement — backward compatible
- **Patch** (x.x.1 → x.x.2): Threshold adjustment, no behavioral change

Version mismatches are caught at startup. Deploy with the wrong contract version, get an error before your first request.

---

### Provider-Agnostic Enforcement

Same contract, any provider:

```python
@contract(schema=SummarySchema, version="1.0.0")
def summarize_anthropic(doc: str) -> SummarySchema:
    # Uses Anthropic
    ...

@contract(schema=SummarySchema, version="1.0.0")
def summarize_openai(doc: str) -> SummarySchema:
    # Uses OpenAI
    ...
```

Switching providers doesn't break the contract. Violations are tagged with the provider that caused them.

---

### CI/CD Gate

```bash
# Validate all contracts in your suite
llm-contract validate --suite ./contracts/ --provider anthropic --threshold 0.90

# Output:
# ✓ summarize_document v1.0.0 — 47/50 PASS (94.0%) [threshold: 90%]
# ✓ extract_entities v2.1.0  — 50/50 PASS (100.0%)
# ✗ generate_report v1.0.0   — 38/50 PASS (76.0%) [threshold: 90%]
# GATE FAIL — 1 contract below threshold.
```

GitHub Action:
```yaml
- name: Validate LLM contracts
  uses: llm-contract/action@v1
  with:
    contracts: './contracts/'
    threshold: '0.90'
    provider: 'anthropic'
    api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

---

### Drift Detection

```bash
# Check for behavioral drift in the last 30 days
llm-contract drift-report --last 30d

# Output:
# Contract: summarize_document v1.0.0
# Pass rate: 95.2% (30 days ago) → 87.1% (today)
# DRIFT DETECTED: -8.1pp over 30 days
# Likely cause: anthropic/claude-3-5-sonnet model update (2026-03-20)
# Recommendation: run 'llm-contract compare' to isolate regression
```

All validation results are logged to a local SQLite database with timestamps, provider info, and model version. You own your data.

---

### Violation Handling Strategies

```python
@contract(..., on_violation="raise")    # Default — raise ContractViolationError
@contract(..., on_violation="warn")     # Log warning, return output anyway
@contract(..., on_violation="log")      # Silently log to SQLite
@contract(..., on_violation="fallback", fallback=my_fallback_fn)  # Call fallback
```

---

## How It Works

```
Your LLM function call
        │
        ▼
@contract decorator intercepts return value
        │
        ├── Layer 1: Pydantic structural validation
        │       └── Field names, types, required fields → pass/fail (0ms)
        │
        ├── Layer 2: SemanticRule evaluation (if enabled)
        │       └── For each rule: calls LLM judge with rule + output
        │       └── Aggregates weighted pass/fail scores
        │       └── Overall pass if weighted score > threshold
        │
        ├── Contract version check
        │       └── Validates deployed version matches contract registry
        │
        └── Drift logger
                └── Writes result to SQLite (timestamp, provider, model, pass/fail)
                │
                ▼
        Contract honored → return output to caller
        Contract violated → on_violation strategy executed
```

The LLM judge (default: `claude-3-5-haiku-20241022`) is called once per SemanticRule. It receives the rule description and the output to evaluate, and returns a binary pass/fail with a confidence score.

Semantic validation is opt-in and can be disabled in performance-critical paths:
```python
@contract(schema=MySchema, version="1.0.0", validate_semantic=False)
```

---

## Configuration

```python
# Global configuration
import llm_contract

llm_contract.configure(
    default_judge_model="claude-3-5-haiku-20241022",  # Default LLM judge
    default_judge_provider="anthropic",               # "anthropic" | "openai" | "local"
    db_path="./llm_contract_logs.db",                 # SQLite path
    log_all_results=True,                             # Log pass AND fail (not just fail)
    default_threshold=0.90,                           # Default pass threshold
)
```

Environment variables:
```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
LLM_CONTRACT_DB_PATH=./logs/contracts.db
LLM_CONTRACT_JUDGE_MODEL=claude-3-5-haiku-20241022
```

---

## Installation

```bash
# Basic install
pip install llm-contract

# With OpenAI judge support
pip install llm-contract[openai]

# With all providers
pip install llm-contract[all]

# pytest plugin
pip install llm-contract[pytest]
```

---

## pytest Integration

```python
# test_contracts.py
from llm_contract.pytest_plugin import ContractSuite

def test_summarize_document_contract(contract_suite):
    suite = ContractSuite(
        function=summarize_document,
        test_cases=[
            {
                "input": "Tesla reports record Q3 earnings of $25B...",
                "expected_pass": True,
            },
            {
                "input": "Short article: The sky is blue.",
                "expected_pass": True,
            },
        ],
        threshold=0.90,
    )
    suite.run_and_assert()
```

```bash
pytest tests/ -v
# test_summarize_document_contract PASSED
# Contract: summarize_document v1.0.0 — 2/2 PASS
```

---

## Comparison

| | llm-contract | Pydantic | DeepEval | Promptfoo |
|--|--|--|--|--|
| Structural validation | ✓ | ✓ | ✗ | ✗ |
| Behavioral contracts | ✓ | ✗ | Partial | ✗ |
| Contract versioning | ✓ | ✗ | ✗ | ✗ |
| Runtime enforcement | ✓ | ✓ | ✗ | ✗ |
| Drift detection | ✓ | ✗ | ✗ | ✗ |
| CI gate | ✓ | ✗ | ✓ | ✓ |
| Provider-agnostic | ✓ | N/A | ✓ | ✓ |
| pip install | ✓ | ✓ | ✓ | ✗ (npm) |

llm-contract works best alongside Pydantic (structure), DeepEval (quality benchmarking), and Langfuse (observability). It fills the behavioral contract gap that none of them address.

---

## Roadmap

**v0.1 (current)**
- `@contract` decorator with structural + semantic validation
- `ContractViolationError` with detailed violation details
- SQLite drift logging
- `llm-contract validate` CLI
- Claude and OpenAI judge support

**v0.2**
- GitHub Action: `llm-contract/action@v1`
- Contract registry (local + team-shared)
- `llm-contract drift-report` with trend visualization
- `llm-contract compare --before COMMIT --after COMMIT`

**v0.3**
- Multi-model provider comparison mode
- Contract inheritance (child extends parent)
- Slack / PagerDuty drift alerts
- Contract import/export

---

## Contributing

We welcome contributions. See [CONTRIBUTING.md](CONTRIBUTING.md).

Key areas where help is most valuable:
- Additional LLM judge implementations (Mistral, local models via Ollama)
- More SemanticRule templates (common patterns for summarization, extraction, classification)
- IDE integrations (VS Code extension for contract autocomplete)
- Performance optimization for high-throughput production use

```bash
git clone https://github.com/llm-contract/llm-contract
cd llm-contract
pip install -e ".[dev]"
pytest tests/
```

---

## License

MIT License. See [LICENSE](LICENSE).

---

## Why "llm-contract"?

Contracts are promises. A function decorated with `@contract` makes a promise to its callers: whatever model, whatever provider, whatever day of the week — this function will honor the behavioral specification. That promise is enforced at runtime, tested in CI, and monitored for drift in production.

LLM functions are powerful. Uncontracted LLM functions are expensive: expensive when they fail, expensive to debug, expensive to trust.

Give your LLM functions contracts. Make them trustworthy by construction.

---

*Built by engineers who got paged one too many times because an LLM function changed its behavior after a model update.*
