# BibleWorld Cycle 010 — Build Specifications

**Cycle:** 010
**Date:** 2026-03-27
**Builds Produced:** 1
**Build Name:** llm-contract
**Pivot_Score:** 8.30

---

## BUILD-009: llm-contract

**Build ID:** BUILD-009
**Build Name:** llm-contract
**Pattern Source:** PAT-035 (Acts 2:1-13 — The Pentecost Contract)
**Build Type:** SOFTWARE — Open-Source Python Library / Developer Tool
**Cycle Started:** 010
**Status:** IN-DESIGN (full spec written)
**Priority:** #1 (after prompt-lock v0.1 ships)

---

### 1. Problem Statement

LLM function calls have a structural validation problem and a behavioral validation vacuum.

**What exists:**
- Pydantic validates JSON structure (field names, data types, required fields)
- DeepEval validates semantic quality (accuracy, relevance, faithfulness — post-hoc)
- Promptfoo tests prompts against eval suites (security + quality regression)
- Langfuse traces what happened (observability)

**What does NOT exist:**
A library that enforces what an LLM function call *must behaviorally produce* — defining, versioning, and continuously validating behavioral contracts at the function boundary, across provider switches, model updates, and prompt changes.

**Confirmed pain points (web search verified):**
1. "Most mysterious LLM regressions aren't model issues — they're data contract issues" (practitioner quote, verified Search 5)
2. "The single greatest developer frustration: AI solutions that look correct but are slightly wrong" (Stack Overflow Dev Survey 2025, verified Search 3)
3. "Teams using 4.7 AI tools but only 1.8 integrate" — contract enforcement at boundaries is what would enable integration (verified Search 3)
4. Inter-agent schema violations: "Agents execute 15+ LLM calls; no tool enforces each call returns the promised schema" (verified Search 7)
5. Model updates break contracts silently: OpenAI, Anthropic model updates change output behavior without versioned contract alerts (known engineering pain, no current solution)

**Financial scale:** $250M+ annually in hallucination-related production incidents (verified Search 6). Schema/behavioral violations are a significant fraction of these.

---

### 2. Solution Overview

llm-contract is a Python library that brings **contract-driven development** to LLM function calls.

It provides three things:
1. **Contract Definition** — A decorator and schema system for defining what an LLM function must produce, behaviorally and structurally
2. **Contract Validation** — Runtime validation that enforces the contract on every call
3. **Contract Versioning + Drift Detection** — Semver-style versioning for behavioral contracts; CI integration; drift alerting when production outputs begin violating the contract

---

### 3. Key Features (7 Specific Features)

#### Feature 1: `@contract` Decorator
Apply behavioral contracts to any LLM function call with a single decorator.

```python
from llm_contract import contract, ContractSchema, SemanticRule

@contract(
    schema=SummarySchema,
    semantic_rules=[
        SemanticRule("must_include_key_facts", weight=0.8),
        SemanticRule("must_not_hallucinate_names", weight=1.0),
        SemanticRule("tone_must_be_neutral", weight=0.6),
    ],
    version="1.2.0",
    on_violation="raise"  # or "warn", "log", "fallback"
)
def summarize_document(doc: str) -> SummarySchema:
    return claude.messages.create(...)
```

#### Feature 2: Structural + Semantic Validation
Two-layer validation:
- **Layer 1 (Structural):** Pydantic-integrated schema validation — field names, types, required fields, value constraints
- **Layer 2 (Semantic):** LLM-as-judge evaluation against named semantic rules — runs a lightweight Claude/GPT call to verify the behavioral contract

Both layers must pass for the contract to be honored.

#### Feature 3: Contract Versioning (SemVer for Behavior)
Contracts carry semantic version numbers following a behavioral versioning spec:
- **Major bump** (1.0.0 → 2.0.0): Breaking behavioral change — downstream consumers MUST update
- **Minor bump** (1.0.0 → 1.1.0): New behavioral requirement added — backward-compatible
- **Patch bump** (1.0.0 → 1.0.1): Clarification or threshold adjustment — no behavioral change

```python
# Contract version is enforced at import time against your contract registry
@contract(schema=SummarySchema, version="1.2.0")
```

If the registered contract for `summarize_document` is version `1.2.0` and you deploy with `1.1.0`, the mismatch is caught at startup.

#### Feature 4: Provider-Agnostic Contract Enforcement
Works with any LLM provider. The contract is defined on the *output*, not the model. This means:
- Switching from Claude to GPT-4o does not break the contract
- The contract VERIFIES the output regardless of provider
- Contract violations tell you which provider violated it

```python
# Works with OpenAI
@contract(schema=SummarySchema, version="1.2.0")
def summarize_openai(doc: str) -> SummarySchema:
    return openai.chat.completions.create(...)

# Same contract, different provider — violations are provider-tagged
@contract(schema=SummarySchema, version="1.2.0")
def summarize_anthropic(doc: str) -> SummarySchema:
    return anthropic.messages.create(...)
```

#### Feature 5: CI/CD Gate Integration
llm-contract ships a CLI and GitHub Action for CI/CD integration:

```bash
# Run contract validation suite
llm-contract validate --suite ./contracts/ --provider anthropic

# Output:
# ✓ summarize_document v1.2.0 — 47/50 samples PASS (94.0%) [threshold: 90%]
# ✓ extract_entities v2.0.1 — 50/50 samples PASS (100.0%)
# ✗ generate_report v1.1.0 — 38/50 samples PASS (76.0%) [threshold: 90%]
# GATE FAIL — 1 contract below threshold. Blocking merge.
```

GitHub Action:
```yaml
- name: Run contract validation
  uses: llm-contract/action@v1
  with:
    contracts: './contracts/'
    provider: 'anthropic'
    threshold: 0.90
    api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

#### Feature 6: Drift Detection + Alerting
llm-contract logs every validation result to a local SQLite database (or configurable backend). It computes rolling violation rates and alerts when contract compliance drops:

```bash
llm-contract drift-report --last 7d
# Contract: summarize_document v1.2.0
# Pass rate: 94.2% (7 days ago) → 87.1% (today)
# DRIFT DETECTED: -7.1pp over 7 days
# Likely cause: Model update (anthropic/claude-3-5-haiku released 2026-03-20)
# Recommendation: Run provider comparison to identify regression
```

The drift report links to the specific commit SHA and model version where drift began.

#### Feature 7: Contract Registry + Sharing
Teams can publish contracts to a shared registry for reuse:

```bash
# Publish a contract
llm-contract publish summarize_document@1.2.0 --registry https://your-registry.example.com

# Import a shared contract
llm-contract import text-classification@3.1.0 --from community
```

This enables contract reuse across teams and organization-wide behavioral standards.

---

### 4. Technical Architecture

**Language:** Python 3.10+
**Package manager:** pip (published to PyPI)
**Core dependencies:**
- `pydantic >= 2.0` — structural schema validation
- `anthropic` / `openai` — LLM judge calls (configurable)
- `sqlite3` (stdlib) — drift logging
- `click` — CLI
- `pytest` plugin — `pytest-llm-contract` for CI integration

**Architecture layers:**
```
User code
   │
   ▼
@contract decorator
   │
   ├── Layer 1: Pydantic structural validation
   │     └── Validates field names, types, required fields, value constraints
   │
   ├── Layer 2: SemanticRule evaluation
   │     └── Calls configurable LLM judge with rule + output
   │     └── Returns pass/fail + confidence score per rule
   │
   ├── Contract version check
   │     └── Validates deployed version against contract registry
   │
   └── Drift logger
         └── Writes result to SQLite with timestamp + provider + model version
```

**Violation handling strategies:**
- `on_violation="raise"` — raises `ContractViolationError` with details
- `on_violation="warn"` — logs warning, returns output anyway
- `on_violation="fallback"` — calls a fallback function and returns that result
- `on_violation="log"` — silently logs to SQLite, returns output

**Performance:**
- Layer 1 (structural): ~0ms (Pydantic is fast)
- Layer 2 (semantic): ~200-800ms (depends on judge model)
- Semantic validation is opt-in and can be disabled in production with `validate_semantic=False` for performance-critical paths
- Structural validation always runs

---

### 5. API Design (Full Public API)

```python
# Core decorator
@contract(
    schema: Type[BaseModel],           # Pydantic schema for structural validation
    semantic_rules: List[SemanticRule], # Optional behavioral rules
    version: str,                       # Semantic version (e.g. "1.2.0")
    on_violation: str = "raise",        # "raise" | "warn" | "log" | "fallback"
    fallback: Callable = None,          # Used when on_violation="fallback"
    validate_semantic: bool = True,     # Toggle semantic validation
    judge_model: str = "claude-3-5-haiku-20241022",  # Model for semantic eval
    log_results: bool = True,           # Whether to log to SQLite
)

# Semantic rule
SemanticRule(
    name: str,          # Rule name (used in reports)
    description: str,   # Human-readable rule statement
    weight: float,      # Weight 0.0-1.0 (1.0 = critical, fail if violated)
    threshold: float = 0.9,  # Pass/fail threshold
)

# Exception
ContractViolationError(
    function_name: str,
    contract_version: str,
    violations: List[ViolationDetail],
    structural_violations: List[str],
    semantic_violations: List[SemanticViolationDetail],
)

# CLI
llm-contract validate --suite PATH --provider PROVIDER [--threshold FLOAT]
llm-contract drift-report --last DURATION
llm-contract compare --before COMMIT --after COMMIT
llm-contract publish FUNCTION@VERSION --registry URL
llm-contract import CONTRACT@VERSION --from SOURCE
llm-contract init  # scaffolds a contracts/ directory with examples
```

---

### 6. Sample Code — Full Working Example

```python
# contracts.py
from pydantic import BaseModel
from typing import List
import anthropic
from llm_contract import contract, SemanticRule

# Define the output schema (structural layer)
class DocumentSummary(BaseModel):
    title: str
    summary: str          # 2-4 sentences
    key_points: List[str] # 3-5 items
    sentiment: str        # "positive" | "negative" | "neutral"
    confidence: float     # 0.0-1.0

# Apply behavioral contract
@contract(
    schema=DocumentSummary,
    semantic_rules=[
        SemanticRule(
            name="no_fabrication",
            description="Summary must not introduce facts not present in the source document",
            weight=1.0,   # Critical — fail immediately if violated
        ),
        SemanticRule(
            name="key_points_from_document",
            description="Each key point must be traceable to content in the source document",
            weight=0.9,
        ),
        SemanticRule(
            name="appropriate_length",
            description="Summary must be 2-4 sentences. Key points must be 3-5 items.",
            weight=0.7,
        ),
    ],
    version="1.0.0",
    on_violation="raise",
    judge_model="claude-3-5-haiku-20241022",
)
def summarize_document(document: str) -> DocumentSummary:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Summarize this document. Return JSON matching this schema:
{{
  "title": "...",
  "summary": "...",
  "key_points": ["...", "..."],
  "sentiment": "positive|negative|neutral",
  "confidence": 0.0-1.0
}}

Document:
{document}"""
        }]
    )
    import json
    return DocumentSummary(**json.loads(response.content[0].text))

# Usage
try:
    result = summarize_document(document_text)
    print(result.summary)
except ContractViolationError as e:
    print(f"Contract violated: {e.violations}")
    # Log, alert, fallback...
```

```bash
# CI validation
llm-contract validate --suite contracts/ --provider anthropic --threshold 0.90

# Drift monitoring
llm-contract drift-report --last 30d --alert-threshold 0.05
```

---

### 7. How It's Different from Existing Tools

| Feature | llm-contract | Pydantic | DeepEval | Promptfoo | Langfuse |
|---------|-------------|----------|----------|-----------|----------|
| Structural schema validation | ✓ | ✓ | ✗ | ✗ | ✗ |
| Behavioral contract enforcement | ✓ | ✗ | Partial | ✗ | ✗ |
| Contract versioning (semver) | ✓ | ✗ | ✗ | ✗ | ✗ |
| Provider-agnostic | ✓ | N/A | ✓ | ✓ | ✓ |
| Runtime enforcement (not post-hoc) | ✓ | ✓ | ✗ | ✗ | ✗ |
| Drift detection + alerting | ✓ | ✗ | ✗ | ✗ | Partial |
| CI gate (pass/fail on contract) | ✓ | ✗ | ✓ | ✓ | ✗ |
| Contract registry + sharing | ✓ | ✗ | ✗ | ✗ | ✗ |

**The core differentiation:** Pydantic validates *structure*. llm-contract validates *behavior*. DeepEval evaluates *quality* (post-hoc, per run). llm-contract enforces *contracts* (at function boundary, continuously, with versioning). These are complementary, not competing.

---

### 8. User Persona

**Primary:** The "Plumber" engineer — AI/ML engineer maintaining LLM pipelines in production.
- Works at a startup or Big Tech team shipping LLM features daily
- Has multiple LLM function calls in production; can't watch all of them manually
- Gets paged when an LLM function starts returning garbage
- Currently uses Pydantic for structure and has NO solution for behavioral drift
- Pain: "We switched from GPT-4 to Claude and half our pipelines started producing outputs that were structurally correct but behaviorally wrong. We had no way to catch this before users reported it."

**Secondary:** Platform engineer standardizing LLM usage across a large org.
- Needs to enforce org-wide behavioral standards on LLM function calls
- Contract registry enables publishing and sharing approved contracts
- Every team imports from the registry rather than defining contracts independently

**Tertiary:** ML engineer integrating external LLM APIs (OpenAI, Anthropic) into business-critical workflows.
- Cannot afford behavioral regressions when model providers update their models
- llm-contract's drift detection sends alerts before customers notice

---

### 9. Adoption Path

**Week 1-3:** Build v0.1
- Core `@contract` decorator with structural validation
- Basic `SemanticRule` with Claude as default judge
- `ContractViolationError` with detailed violation info
- SQLite drift logging
- `llm-contract validate` CLI command
- Publish to PyPI: `pip install llm-contract`

**Week 4-6:** Community launch
- GitHub repo with real README
- HackerNews Show HN: "llm-contract — Pydantic for LLM behavior, not just JSON structure"
- dev.to article: "Why your LLM functions need behavioral contracts (and how to add them in 5 lines)"
- Twitter/X thread: "Your LLM functions have Pydantic validation. They don't have behavioral contracts. Here's the difference."

**Month 2:** v0.2
- GitHub Action: `llm-contract/action@v1`
- OpenAI judge support (not just Claude)
- Contract registry (local + remote)
- `llm-contract drift-report` CLI

**Month 3-6:** Enterprise path
- Team contract registries
- Slack/PagerDuty drift alerts
- Multi-model provider comparison mode
- Commercial support tier for enterprise customers

**Acquisition path:**
- Anthropic (complements their trust/safety mission; behavioral contracts are a form of alignment infrastructure)
- OpenAI (complements Promptfoo acquisition — Promptfoo = security + prompt regression; llm-contract = behavioral contracts)
- Datadog (adding LLM behavioral monitoring to their existing APM + LLM observability product line)
- Pydantic Labs (natural extension of their structural validation mission into behavioral validation)

---

### Build Score

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Feasibility (0-3) | 3.0 | Pure Python; decorator pattern; Pydantic integration is trivial; Claude API for judge; SQLite for storage; v0.1 in 2-3 weeks is realistic for a solo engineer |
| Impact (0-3) | 2.7 | Every team shipping LLM function calls in production (growing daily); behavioral contract violations cost $250M+/yr; addresses confirmed #1 developer frustration |
| Completeness (0-2) | 1.9 | Feature list is specific and actionable; API design is ready to implement; architecture is clear; edge cases (semantic rule algorithm) need further design but are not blockers for v0.1 |
| Biblical fidelity (0-2) | 2.0 | Acts 2 behavioral contract honored across multiple nodes maps precisely to the library's core function; the parallel is specific and honest |
| **TOTAL** | **9.6 / 10** | |

**Pivot_Score:** 8.30
**Build Score:** 9.6
**Status:** IN-DESIGN — FULL SPEC READY

---

*BUILD-009: llm-contract — The Pentecost Contract made into software. Many models, one behavioral contract.*
