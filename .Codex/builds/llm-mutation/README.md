# llm-mutation
## Mutation Testing for LLM Prompts

**Tagline:** "Find the gaps in your eval suite before production does."
**Version:** 0.1.0 (planned)
**License:** MIT
**Install:** `pip install llm-mutation`
**Pattern Source:** PAT-045 (Judges 6:36-40 — The Gideon Fleece Inversion Pattern)
**Pivot_Score:** 8.65
**Build Score:** 9.0/10
**Cycle:** 014

---

## The Problem

You have an eval suite for your LLM feature. It has 50 test cases. They all pass. You ship.

Two days later, production is broken. Users are getting wrong outputs. Your test suite gave you false confidence.

**Why?** Your eval suite was testing 50 specific cases you wrote. It was never tested itself. It cannot tell you whether it would catch a bug if a key constraint in your prompt was removed, a clause was dropped, or a scope was changed.

This is the fundamental gap in LLM testing: **teams test prompts but never test whether their tests are any good.**

### The Numbers
- **45%** of developers say their #1 frustration is AI solutions that are "almost right, but not quite" *(Stack Overflow Developer Survey 2025)*
- **66%** spend MORE time debugging AI-generated code than writing from scratch *(Stack Overflow 2025)*
- "These metrics are often worse than useless because teams can't determine what differentiates a score of 3 from 4" *(The Pragmatic Engineer, 2025)*

The root cause: eval suites are written by the same people who wrote the prompts, against the same inputs they expected. They don't catch subtle semantic regressions.

---

## The Solution: Mutation Testing

In software engineering, **mutation testing** solves this by introducing deliberate bugs into source code and checking whether the test suite catches them. Tools: Pitest (Java), Stryker (JavaScript), Mutahunter (Python).

**llm-mutation brings this to LLM prompts.**

It generates deliberate semantic mutations of your prompt — negating a constraint, dropping a clause, expanding scope — then runs your existing eval suite against each mutated variant. If your eval suite fails to detect a mutation, it has a gap. The **mutation score** (% of mutations killed) tells you how strong your eval suite is.

### Concrete Example

```
Original prompt:
"You are a customer service agent for AcmeCorp.
Answer questions about software products only.
Never discuss competitor products.
Always respond in formal English.
Direct pricing questions to sales@acmecorp.com."

Mutation: Remove "Never discuss competitor products."
→ Your eval suite should score this LOWER — competitor questions now pass.
→ If your eval suite scores both prompts the same, it has a gap.
→ llm-mutation identifies this and recommends: "Add test case: user asks to compare you to CompetitorX"
```

---

## Quickstart

```bash
pip install llm-mutation
export ANTHROPIC_API_KEY=sk-ant-...

# Run mutation test
mutate run \
  --prompt prompts/customer_service.txt \
  --eval evals/test_customer_service.py \
  --output reports/mutation_report.json

# View report
mutate report --input reports/mutation_report.json

# CI gate (exits 1 if score < 80%)
mutate ci --input reports/mutation_report.json --min-score 0.80
```

---

## How It Works

### Step 1: MutationEngine generates semantic mutations

```python
from llm_mutation import MutationEngine

engine = MutationEngine(operators=["NegateConstraint", "DropClause", "ScopeExpand"])
mutations = engine.generate(prompt="prompts/customer_service.txt")
# Returns: [Mutation(...), Mutation(...), ...]
```

Six built-in operators (all deterministic — no LLM needed for generation):

| Operator | What it does | Example |
|----------|--------------|---------|
| `NegateConstraint` | Removes or negates a prohibitive clause | "Never X" → removes line |
| `DropClause` | Removes a requirement clause entirely | "Always respond formally" → removed |
| `ScopeExpand` | Widens a scope restriction | "software only" → "products and services" |
| `ScopeNarrow` | Narrows a permission | "any topic" → "general topics only" |
| `ConditionInvert` | Inverts a conditional behavior | "if angry, de-escalate" → "if calm, proceed" |
| `PhraseSwap` | Substitutes key style/behavior phrase | "concise" → "comprehensive" |

### Step 2: MutantRunner executes your eval suite against each mutant

```python
from llm_mutation import MutantRunner

runner = MutantRunner(
    eval_fn=my_eval_function,    # (prompt: str, cases: list) -> float
    test_cases=my_test_cases,
    delta_threshold=0.15,         # minimum score drop to count as KILLED
    runs_per_mutant=3,            # runs for median averaging
)
results = runner.run(mutations)
```

A mutant is **KILLED** if your eval suite scores it at least `delta_threshold` lower than the original.
A mutant **SURVIVES** if your eval suite scores it the same — meaning your suite has a gap.

### Step 3: MutationReport shows your gaps

```python
from llm_mutation import MutationReport

report = MutationReport.from_results(results)
print(report.summary())
```

```
MUTATION SCORE: 71% (5/7 mutations killed)

KILLED MUTATIONS:
  ✓ NegateConstraint — "Never discuss competitor products." removed
    Score: 0.91 → 0.42 (delta: 0.49) ✓ KILLED

  ✓ DropClause — "Always respond in formal English." removed
    Score: 0.91 → 0.55 (delta: 0.36) ✓ KILLED

SURVIVING MUTATIONS:
  ✗ DropClause — "Direct pricing questions to sales@acmecorp.com." removed
    Score: 0.91 → 0.89 (delta: 0.02) ✗ SURVIVED
    → ADD TEST CASE: "User asks 'What does the enterprise plan cost?'"
    → EXPECTED: Response mentions sales@acmecorp.com

  ✗ ScopeExpand — "software products only" → "products and services"
    Score: 0.91 → 0.88 (delta: 0.03) ✗ SURVIVED
    → ADD TEST CASE: "User asks about AcmeCorp's consulting services"
    → EXPECTED: Agent redirects to software-only scope

WARNING: Mutation score 71% is below recommended threshold of 80%.
Your eval suite may miss bugs in pricing-redirect and scope-enforcement areas.
```

---

## API Reference

### MutationEngine

```python
class MutationEngine:
    def __init__(
        self,
        operators: list[str] = None,  # default: all 6 operators
        max_mutations: int = 20,       # cap to prevent combinatorial explosion
        prompt_format: str = "auto",   # "string", "messages", "jinja2", "auto"
    ): ...

    def generate(
        self,
        prompt: str | list | Path,     # prompt content or path to file
    ) -> list[Mutation]: ...
```

### MutantRunner

```python
class MutantRunner:
    def __init__(
        self,
        eval_fn: Callable,             # (prompt: str, cases: list) -> float
        test_cases: list,
        delta_threshold: float = 0.15, # minimum delta to count as KILLED
        runs_per_mutant: int = 3,      # runs for median averaging (non-determinism)
        timeout_per_run: int = 60,     # seconds per eval run
        parallel: bool = True,         # run mutations in parallel
        max_workers: int = 4,
    ): ...

    def run(self, mutations: list[Mutation]) -> list[MutantResult]: ...
```

### MutationReport

```python
class MutationReport:
    mutation_score: float      # 0.0 - 1.0
    total_mutations: int
    killed: int
    survived: int
    skipped: int
    recommendations: list[str]
    results: list[MutantResult]

    @classmethod
    def from_results(cls, results: list[MutantResult]) -> "MutationReport": ...

    def summary(self, format: str = "text") -> str: ...  # "text", "json", "markdown"
    def to_json(self, path: Path) -> None: ...
```

### CLI

```bash
# Run full mutation test
mutate run [OPTIONS]
  --prompt PATH       Prompt file to mutate (required)
  --eval PATH         Eval function file (required)
  --output PATH       Output report path (default: mutation_report.json)
  --operators TEXT    Comma-separated operators (default: all)
  --max-mutations INT Cap on total mutations (default: 20)
  --delta FLOAT       Score delta threshold (default: 0.15)
  --runs INT          Runs per mutant for averaging (default: 3)

# Generate human-readable report
mutate report [OPTIONS]
  --input PATH        Report JSON file (required)
  --format TEXT       Output format: text, markdown, html (default: text)

# CI gate
mutate ci [OPTIONS]
  --input PATH        Report JSON file (required)
  --min-score FLOAT   Minimum mutation score (default: 0.80)
  # Exit code 0 = passed, 1 = failed

# Calibrate eval suite against known-broken mutations
mutate calibrate [OPTIONS]
  --prompt PATH       Prompt file (required)
  --eval PATH         Eval function file (required)
  # Runs known-severity mutations and reports calibration score

# Verify judge consistency
mutate verify-judge [OPTIONS]
  --prompt PATH       Prompt file (required)
  --eval PATH         Eval function file (required)
  --judges PATH       YAML file with multiple judge configurations
  # Reports inter-judge agreement score
```

---

## Integrations

### pytest Plugin

```python
# pip install llm-mutation[pytest]
# In conftest.py or test file:

import pytest
from llm_mutation.pytest_plugin import mutation_test

@mutation_test(
    prompt="prompts/customer_service.txt",
    eval_fn="evals.customer_service:eval_fn",
    test_cases="evals.customer_service:TEST_CASES",
    min_score=0.80,
)
def test_customer_service_mutation_score():
    """Fails if mutation score < 80%"""
    pass
```

### DeepEval Integration

```python
from llm_mutation import MutantRunner
from llm_mutation.integrations import deepeval_runner

# Use DeepEval metrics as eval function
runner = MutantRunner(
    eval_fn=deepeval_runner(
        metrics=["answer_relevancy", "faithfulness", "contextual_precision"],
        test_cases=deepeval_test_cases,
    ),
    test_cases=deepeval_test_cases,
)
```

### Promptfoo Integration

```yaml
# mutation_config.yaml
prompt: prompts/customer_service.txt
eval_backend: promptfoo
promptfoo_config: evals/promptfoo.yaml
min_mutation_score: 0.80
```

---

## GitHub Action

```yaml
# .github/workflows/llm-mutation.yml
name: LLM Prompt Mutation Test
on:
  pull_request:
    paths:
      - 'prompts/**'
      - 'evals/**'

jobs:
  mutation-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install llm-mutation
      - name: Run mutation tests
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          mutate run \
            --prompt prompts/customer_service.txt \
            --eval evals/test_customer_service.py \
            --output mutation_report.json
          mutate ci \
            --input mutation_report.json \
            --min-score 0.80
      - name: Upload mutation report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: mutation-report
          path: mutation_report.json
```

---

## Understanding Mutation Score

| Score | Interpretation | Action |
|-------|---------------|--------|
| >= 90% | Excellent — eval suite is comprehensive | Maintain; add tests for new prompt clauses |
| 80-89% | Good — eval suite is adequate for CI gate | Add the recommended test cases |
| 70-79% | Marginal — eval suite has meaningful gaps | Add recommended tests before shipping |
| 60-69% | Weak — eval suite is likely missing important behaviors | Significant eval suite work needed |
| < 60% | Dangerous — eval suite is not fit for purpose | Rebuild eval suite before trusting it |

**Recommended minimum for production CI gate: 80%**

---

## Calibration and Judge Verification

### `mutate calibrate` — Berean Null Test
Before trusting your mutation score, verify that your eval suite can actually detect known-broken mutations:

```bash
mutate calibrate \
  --prompt prompts/customer_service.txt \
  --eval evals/test_customer_service.py
```

```
CALIBRATION RESULTS:
Tested 5 known-severity mutations against your eval suite.
  ✓ Severity: HIGH — complete system prompt removal — Caught (score: 0.91 → 0.12)
  ✓ Severity: HIGH — "Never X" negated to "Always X" — Caught (score: 0.91 → 0.08)
  ✓ Severity: MEDIUM — all constraints removed — Caught (score: 0.91 → 0.31)
  ✗ Severity: MEDIUM — tone instruction removed — Missed (score: 0.91 → 0.87)
  ✓ Severity: LOW — single clause dropped — Caught (score: 0.91 → 0.71)

Calibration score: 80% (4/5 known-severity mutations caught)
WARNING: Eval suite missed MEDIUM severity tone mutation. Your tone-testing coverage may be insufficient.
Recommend: Add test cases specifically targeting formal vs. informal response style.
```

### `mutate verify-judge` — Twelve Spies Protocol
If you use LLM-as-judge in your eval function, verify that your judge is consistent:

```yaml
# judges.yaml
judges:
  - name: claude-haiku
    model: claude-3-5-haiku-20241022
    prompt: evals/judge_prompt_v1.txt
  - name: claude-sonnet
    model: claude-3-5-sonnet-20241022
    prompt: evals/judge_prompt_v1.txt
  - name: gpt-4o-mini
    model: gpt-4o-mini
    prompt: evals/judge_prompt_v1.txt
```

```bash
mutate verify-judge \
  --prompt prompts/customer_service.txt \
  --eval evals/test_customer_service.py \
  --judges judges.yaml
```

```
JUDGE CONSISTENCY RESULTS:
Agreement on mutation verdicts:
  claude-haiku vs claude-sonnet: 92% agreement ✓
  claude-haiku vs gpt-4o-mini:   78% agreement ⚠
  claude-sonnet vs gpt-4o-mini:  80% agreement ⚠

Recommendation: If using gpt-4o-mini as judge, align judge prompts with claude-sonnet results.
The 22% disagreement rate on GPT-4o-mini suggests different calibration — do not mix judges across CI runs.
```

---

## Biblical Foundation

This tool is grounded in PAT-045 (Judges 6:36-40 — The Gideon Fleece Inversion Pattern).

Gideon did not simply ask for a sign. He designed a **two-condition invertible test**:
1. Fleece wet, ground dry
2. Fleece dry, ground wet (exact inversion of condition 1)

He was not testing whether God would respond. He was testing whether his testing mechanism was reliable — could it discriminate between coincidence and genuine signal? The inversion was deliberate: a coincidental result could pass one condition; it could not pass both inversions without being genuine.

**This is the structure of mutation testing:**
- Introduce deliberate inversions (mutations) into your prompt
- If your eval suite detects the mutation — KILLED — the suite is calibrated
- If your eval suite misses the mutation — SURVIVED — the suite has a gap
- The mutation score (% killed) is your bowlful-of-water measurement: concrete, quantitative, not vibes

Supporting patterns:
- PAT-046 (Acts 17:11 — Berean Null Test): calibrate your evaluation mechanism before trusting it → `mutate calibrate`
- PAT-047 (Numbers 13:25-33 — Twelve Spies Divergence): evaluator consensus is not a substitute for calibration → `mutate verify-judge`

---

## Roadmap

### v0.1 (Target: 30 days)
- 6 mutation operators (deterministic)
- MutantRunner with DeepEval + pytest integrations
- MutationReport (JSON + text)
- CLI: `mutate run`, `mutate report`, `mutate ci`
- GitHub Action template
- `mutate calibrate`
- SQLite result store
- PyPI release

### v0.2 (Target: 60 days)
- `mutate verify-judge` command
- Promptfoo YAML integration
- LLM-generated mutation operators (KU-026: auto-generate mutations from prompt using LLM)
- Mutation score trend tracking (track mutation score over commits)
- HTML report with per-clause coverage visualization

### v0.3 (Target: 90 days)
- Mutation score as a metric in observability dashboards (OpenTelemetry export)
- Custom operator plugin API
- Multi-prompt project support (test an entire `prompts/` directory)
- Integration with LangSmith, Braintrust dataset formats

---

## Competitive Landscape

| Tool | Tests prompts | Tests eval suite quality |
|------|--------------|--------------------------|
| Promptfoo | Yes | No |
| DeepEval | Yes | No |
| LangSmith | Yes (via datasets) | No |
| Braintrust | Yes | No |
| PromptBench | Academic benchmarks only | No |
| **llm-mutation** | Yes (as baseline) | **Yes — this is the differentiator** |

**The gap:** Every existing tool tests whether your prompt produces good output. llm-mutation tests whether your eval suite would notice if it didn't.

---

*Built by BibleWorld — Cycle 014*
*Pattern: PAT-045 (Judges 6:36-40 — The Gideon Fleece Inversion Pattern)*
*"The crucible for silver and the furnace for gold, but people are tested by their praise." — Proverbs 27:21*
