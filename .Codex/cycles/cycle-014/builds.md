# BibleWorld Cycle 014 — Build Specification
## llm-mutation: Semantic Mutation Testing for LLM Prompts

**Cycle:** 014
**Date:** 2026-03-27
**Build ID:** BUILD-013
**Tool Name:** llm-mutation
**Pivot_Score:** 8.65
**Build Score:** 9.0/10
**Pattern Source:** PAT-045 (Judges 6:36-40) + PAT-046 (Acts 17:11 variant) + PAT-047 (Numbers 13:25-33)

---

## THE PROBLEM

### Pain Statement
You have written 50 test cases for your LLM-powered feature. They all pass. You ship. Two days later, production is on fire: users are getting wildly wrong outputs on inputs that never appeared in your test cases.

What went wrong? Your eval suite was not actually testing what you thought it was testing. It was testing 50 specific input-output pairs — but it had no ability to tell you whether it would catch a bug if someone subtly changed the prompt. Your eval suite gave you confidence. Your eval suite lied to you.

This is not a hypothetical. It is the documented reality of LLM engineering:
- **45% of developers** report their #1 frustration is AI solutions that are "almost right, but not quite" (Stack Overflow Developer Survey 2025)
- **66% of developers** spend MORE time debugging AI-generated code than writing from scratch
- "These metrics are often worse than useless because teams can't determine what differentiates a score of 3 from a 4" — Pragmatic Engineer, 2025

The root cause is clear: **eval suites are commonly written to pass, not to fail.** They are written by the same people who wrote the prompts, against the same inputs the authors expected. They do not catch the subtle semantic bugs that a slightly different input or a slightly degraded prompt would expose.

### The Mutation Testing Solution
In software engineering, **mutation testing** solves this problem. Tools like Pitest (Java), Stryker (JavaScript), and Mutahunter (Python) introduce deliberate bugs into your source code — then run your test suite against the buggy code. If your test suite passes despite the bug, the test suite has a gap. The mutation "survived." A good test suite "kills" most mutations.

This principle is directly applicable to LLM prompts:
- A prompt has constraints, clauses, scopes, and conditions — exactly like code
- Introducing deliberate semantic mutations (negate a constraint, drop a clause, expand scope) should cause your eval suite to fail
- If your eval suite passes after a critical constraint is removed, the eval suite has a gap
- The mutation score (% of mutations killed) tells you how strong your eval suite is

**llm-mutation is Mutahunter for LLM prompts.**

### Concrete Example
```
Original prompt:
"You are a helpful customer service agent for AcmeCorp.
Answer questions about our software products only.
Never discuss competitor products.
Always respond in formal English.
If the user asks about pricing, direct them to sales@acmecorp.com."

Mutation 1 (NegateConstraint): Remove "Never discuss competitor products."
→ Your eval suite should score this prompt differently: competitor questions now pass.
→ If your eval suite scores both prompts equally, it has a gap.

Mutation 2 (DropClause): Remove "Always respond in formal English."
→ Responses may now be casual, slangy, or inconsistent in register.
→ If your eval suite doesn't catch the tone shift, it's not testing tone.

Mutation 3 (ScopeExpand): Change "software products only" to "products and services."
→ Scope has widened. Non-software support questions now receive answers.
→ If your eval suite doesn't test boundary cases, this mutation survives.
```

If all three mutations score the same as the original prompt in your eval suite, your eval suite is measuring something other than what your prompt specifies.

---

## THE SOLUTION: llm-mutation

**Tool name:** llm-mutation
**Tagline:** "Mutation testing for LLM prompts. Find the gaps in your eval suite before production does."
**Install:** `pip install llm-mutation`
**License:** MIT
**Language:** Python 3.9+

---

## CORE FEATURES (MVP — v0.1)

### Feature 1: MutationEngine (6 Semantic Mutation Operators)

The MutationEngine takes a prompt (string, Jinja2 template, or OpenAI messages list) and generates a set of semantically mutated variants.

**Operator 1: NegateConstraint**
Removes or negates a constraint clause.
- Input: "Never discuss competitor products."
- Output: "You may discuss competitor products." OR simply removes the line.
- Targets: clauses beginning with "never", "do not", "avoid", "must not", "always refuse"

**Operator 2: DropClause**
Removes a semantically meaningful clause entirely.
- Input: "Always respond in formal English."
- Output: [clause removed — prompt continues without it]
- Targets: clauses beginning with "always", "ensure", "make sure to", "remember to"

**Operator 3: ScopeExpand**
Widens the scope of a restriction.
- Input: "Answer questions about software products only."
- Output: "Answer questions about products and services."
- Targets: clauses with "only", "exclusively", "limited to", "restricted to"

**Operator 4: ScopeNarrow**
Narrows the scope of a permission.
- Input: "Answer questions about any topic."
- Output: "Answer questions about general topics only."
- Targets: broad scope clauses, open-ended permission statements

**Operator 5: ConditionInvert**
Inverts a conditional statement.
- Input: "If the user is angry, de-escalate before answering."
- Output: "If the user is calm, proceed directly to answering."
- Targets: "if" / "when" / "unless" clauses with behavioral consequence

**Operator 6: PhraseSwap**
Substitutes a key phrase with a semantically adjacent but behaviorally distinct alternative.
- Input: "Provide a concise answer."
- Output: "Provide a comprehensive answer."
- Targets: adjectives and adverbs that constrain output style/length/depth

**Implementation note:** All operators are deterministic. They use regex pattern matching and rule-based transformations — no LLM needed for mutation generation. This ensures reproducibility: the same prompt always produces the same set of mutations.

### Feature 2: MutantRunner

MutantRunner executes your eval suite against each mutated prompt variant and collects scores.

**Supported eval suite formats:**
- **pytest-style:** any function decorated with `@pytest.mark.eval` that returns a score (0.0-1.0) or PASS/FAIL
- **DeepEval:** via `deepeval.test_run` integration
- **Promptfoo YAML:** via `promptfoo eval --config` subprocess invocation
- **Custom:** any Python callable `fn(prompt: str, test_cases: list) -> float`

**Execution:**
For each mutant M generated from original prompt P:
1. Substitute P with M in your eval function
2. Run all N eval test cases against M
3. Collect per-test-case scores
4. A mutant is KILLED if the score for M is statistically lower than for P (using configurable delta threshold, default 0.15)
5. A mutant SURVIVES if the score for M is within delta of the score for P

**Non-determinism handling (KU-024):**
By default, each test case is run 3 times against both P and M, and median scores are used. Configurable via `--runs N`. Delta threshold (default 0.15) accounts for natural LLM variance.

### Feature 3: MutationReport

MutationReport generates a structured report showing:

```
MUTATION SCORE: 71% (5/7 mutations killed)

KILLED MUTATIONS (eval suite detected):
  ✓ NegateConstraint: "Never discuss competitor products." removed
    - Eval score: 0.42 (vs original 0.91) — delta: 0.49 ✓ KILLED
  ✓ DropClause: "Always respond in formal English." removed
    - Eval score: 0.55 (vs original 0.91) — delta: 0.36 ✓ KILLED
  ✓ ScopeExpand: "software products only" → "products and services"
    - Eval score: 0.61 (vs original 0.91) — delta: 0.30 ✓ KILLED
  ✓ ConditionInvert: "if angry, de-escalate" → "if calm, proceed"
    - Eval score: 0.44 (vs original 0.91) — delta: 0.47 ✓ KILLED
  ✓ PhraseSwap: "formal" → "casual"
    - Eval score: 0.38 (vs original 0.91) — delta: 0.53 ✓ KILLED

SURVIVING MUTATIONS (eval suite did NOT detect):
  ✗ DropClause: "If the user asks about pricing, direct to sales@acmecorp.com." removed
    - Eval score: 0.89 (vs original 0.91) — delta: 0.02 ✗ SURVIVED
    → RECOMMENDATION: Add test case: "User asks 'what is the price of Plan X?'"
    → EXPECTED: Response must mention sales@acmecorp.com

  ✗ ScopeNarrow: "AcmeCorp" scope narrowed — product line restriction added
    - Eval score: 0.88 (vs original 0.91) — delta: 0.03 ✗ SURVIVED
    → RECOMMENDATION: Add test case: "User asks about product from full catalog range"
    → EXPECTED: Agent answers without artificial restriction

MUTATION SCORE: 71% (adequate threshold: 80%)
WARNING: 2 mutations survived. Your eval suite may miss bugs in these constraint areas.
Add the recommended test cases to improve coverage.
```

### Feature 4: CLI Interface

```bash
# Run mutation testing against an eval suite
mutate run \
  --prompt prompts/customer-service.txt \
  --eval evals/customer_service_eval.py \
  --output reports/mutation-report.json

# Generate human-readable report
mutate report --input reports/mutation-report.json

# CI gate: fail if mutation score below threshold
mutate ci \
  --input reports/mutation-report.json \
  --min-score 0.80

# Calibrate: verify eval suite catches known-broken mutations
mutate calibrate \
  --prompt prompts/customer-service.txt \
  --eval evals/customer_service_eval.py

# Verify judge consistency across multiple LLM judge configurations
mutate verify-judge \
  --prompt prompts/customer-service.txt \
  --eval evals/customer_service_eval.py \
  --judges configs/judges.yaml
```

### Feature 5: GitHub Action Template

```yaml
# .github/workflows/mutation-test.yml
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
            --prompt prompts/customer-service.txt \
            --eval evals/customer_service_eval.py \
            --output reports/mutation-report.json
          mutate ci \
            --input reports/mutation-report.json \
            --min-score 0.80
```

### Feature 6: pytest Plugin

```python
# Install: pip install llm-mutation[pytest]
# Usage in conftest.py:

from llm_mutation import pytest_plugin  # auto-detected by pytest

# In your test file:
@pytest.mark.mutation(
    prompt_file="prompts/customer_service.txt",
    min_mutation_score=0.80
)
def test_customer_service_mutation():
    """This test fails if mutation score < 80%"""
    pass  # llm-mutation runs automatically via plugin
```

---

## TECHNICAL ARCHITECTURE

### Module Structure

```
llm_mutation/
├── __init__.py
├── operators/
│   ├── __init__.py
│   ├── base.py              # MutationOperator ABC
│   ├── negate_constraint.py  # NegateConstraint operator
│   ├── drop_clause.py        # DropClause operator
│   ├── scope_expand.py       # ScopeExpand operator
│   ├── scope_narrow.py       # ScopeNarrow operator
│   ├── condition_invert.py   # ConditionInvert operator
│   └── phrase_swap.py        # PhraseSwap operator
├── engine.py               # MutationEngine — applies operators to prompts
├── runner.py               # MutantRunner — executes eval suite against mutants
├── report.py               # MutationReport — aggregates results
├── calibrator.py           # Calibration module (PAT-046 — Berean Null Test)
├── judge_verifier.py       # Judge consistency checker (PAT-047)
├── store.py                # SQLite result persistence
├── cli.py                  # Click-based CLI
└── pytest_plugin.py        # pytest integration
```

### Data Structures

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class MutantVerdict(Enum):
    KILLED = "killed"      # eval suite detected the mutation
    SURVIVED = "survived"  # eval suite failed to detect
    SKIP = "skip"          # could not evaluate (timeout/error)

@dataclass
class Mutation:
    id: str                      # e.g. "mut-001"
    operator: str                # e.g. "NegateConstraint"
    original_clause: str         # the clause that was modified
    mutated_clause: str          # the modified version
    original_prompt: str         # full original prompt
    mutated_prompt: str          # full mutated prompt

@dataclass
class MutantResult:
    mutation: Mutation
    original_score: float        # eval suite score for original prompt
    mutated_score: float         # eval suite score for mutated prompt
    score_delta: float           # original_score - mutated_score
    verdict: MutantVerdict       # KILLED, SURVIVED, or SKIP
    recommendation: Optional[str]  # suggested test case to add (if SURVIVED)
    runs: int                    # number of runs used for averaging

@dataclass
class MutationReport:
    prompt_file: str
    eval_file: str
    timestamp: str
    total_mutations: int
    killed: int
    survived: int
    skipped: int
    mutation_score: float        # killed / (total - skipped)
    results: list[MutantResult]
    calibration_passed: Optional[bool]
    judge_agreement: Optional[float]
    recommendations: list[str]   # synthesized test case recommendations
```

### SQLite Schema

```sql
CREATE TABLE mutation_runs (
    id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL,
    prompt_file TEXT NOT NULL,
    eval_file TEXT NOT NULL,
    commit_sha TEXT,
    timestamp TEXT NOT NULL,
    mutation_score REAL NOT NULL,
    total_mutations INTEGER NOT NULL,
    killed INTEGER NOT NULL,
    survived INTEGER NOT NULL,
    min_score_threshold REAL,
    ci_passed BOOLEAN
);

CREATE TABLE mutant_results (
    id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL,
    mutation_id TEXT NOT NULL,
    operator TEXT NOT NULL,
    original_clause TEXT NOT NULL,
    mutated_clause TEXT NOT NULL,
    original_score REAL NOT NULL,
    mutated_score REAL NOT NULL,
    score_delta REAL NOT NULL,
    verdict TEXT NOT NULL,
    recommendation TEXT,
    FOREIGN KEY (run_id) REFERENCES mutation_runs(run_id)
);

CREATE TABLE calibration_results (
    id INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL,
    calibration_score REAL NOT NULL,
    known_broken_caught INTEGER NOT NULL,
    known_broken_total INTEGER NOT NULL,
    calibration_passed BOOLEAN NOT NULL,
    FOREIGN KEY (run_id) REFERENCES mutation_runs(run_id)
);
```

### Prompt Formats Supported

```python
# Format 1: Plain string
prompt = "You are a helpful assistant. Answer only questions about software."

# Format 2: OpenAI messages list
prompt = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "{user_input}"}
]

# Format 3: Jinja2 template file
# prompt_template.j2:
# You are {{ agent_name }}.
# Answer questions about {{ topic }} only.
# Never discuss {{ forbidden }}.

# All formats: mutation operators applied to the system message or main instruction text
```

### API Design

```python
from llm_mutation import MutationEngine, MutantRunner, MutationReport

# 1. Generate mutations
engine = MutationEngine(
    operators=["NegateConstraint", "DropClause", "ScopeExpand"],  # select operators
    max_mutations=20  # cap total mutations generated
)
mutations = engine.generate(prompt="path/to/prompt.txt")
print(f"Generated {len(mutations)} mutations")

# 2. Run eval suite against each mutation
runner = MutantRunner(
    eval_fn=my_eval_function,  # callable: (prompt: str, cases: list) -> float
    test_cases=my_test_cases,
    delta_threshold=0.15,      # minimum score difference to count as KILLED
    runs_per_mutant=3,         # runs for median averaging (KU-024 solution)
)
results = runner.run(mutations)

# 3. Generate report
report = MutationReport.from_results(results)
print(f"Mutation score: {report.mutation_score:.0%}")
print(f"Surviving mutations: {report.survived}")
for rec in report.recommendations:
    print(f"  Recommendation: {rec}")

# 4. CI gate
if report.mutation_score < 0.80:
    raise SystemExit(f"Mutation score {report.mutation_score:.0%} below threshold 80%")
```

---

## QUICKSTART

```bash
# Install
pip install llm-mutation

# Set your LLM API key (for eval judge)
export ANTHROPIC_API_KEY=sk-ant-...

# Create a prompt file
cat > my_prompt.txt << 'EOF'
You are a helpful customer service agent for AcmeCorp.
Answer questions about our software products only.
Never discuss competitor products.
Always respond in formal English.
If the user asks about pricing, direct them to sales@acmecorp.com.
EOF

# Create an eval file (simple example)
cat > my_eval.py << 'EOF'
import anthropic

client = anthropic.Anthropic()

TEST_CASES = [
    {"input": "What products does AcmeCorp offer?", "expected_behavior": "lists products"},
    {"input": "How does your software compare to CompetitorX?", "expected_behavior": "declines competitor comparison"},
    {"input": "What is the price of your enterprise plan?", "expected_behavior": "directs to sales email"},
    {"input": "yo wtf is wrong with ur app lol", "expected_behavior": "formal response despite casual input"},
]

def eval_prompt(prompt: str, test_cases: list) -> float:
    """Returns 0.0-1.0 score for how well prompt handles test cases."""
    scores = []
    for case in test_cases:
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=200,
            system=prompt,
            messages=[{"role": "user", "content": case["input"]}]
        )
        # Simple heuristic scoring (in production: use llm-as-judge)
        output = response.content[0].text.lower()
        if case["expected_behavior"] == "declines competitor comparison":
            scores.append(1.0 if "competitor" not in output or "i can't discuss" in output else 0.0)
        elif case["expected_behavior"] == "directs to sales email":
            scores.append(1.0 if "sales@acmecorp.com" in output else 0.0)
        else:
            scores.append(0.8)  # generic pass
    return sum(scores) / len(scores)
EOF

# Run mutation test
mutate run \
  --prompt my_prompt.txt \
  --eval my_eval.py \
  --output mutation_report.json

# View report
mutate report --input mutation_report.json

# CI gate (exit code 1 if score < 80%)
mutate ci --input mutation_report.json --min-score 0.80
```

---

## GO-TO-MARKET: OPEN-SOURCE STRATEGY

### Positioning
**"Mutahunter for LLM prompts."**

Every senior engineer who has used mutation testing for code immediately understands what llm-mutation does. The concept requires zero explanation to the target audience. The gap is obvious once pointed out: "You'd never ship code without mutation testing your test suite. Why are you shipping prompts without mutation-testing your eval suite?"

### Target Users (in order of adoption priority)
1. **Senior ML engineers** at companies with >5 prompts in production — they already have eval suites, they already feel the false-confidence problem
2. **AI platform teams** standardizing LLM quality gates organization-wide — they need a mutation score as a required CI metric
3. **AI-assisted coding teams** — 76% increase in code volume means 76% more AI-generated code with no increase in test suite quality; mutation testing fills the gap
4. **OSS LLM framework maintainers** — LangChain, LlamaIndex, AutoGen maintainers will integrate llm-mutation as their quality standard for example prompts and templates

### Distribution
1. **PyPI** — `pip install llm-mutation` — primary distribution
2. **GitHub** — MIT license, comprehensive README, examples directory
3. **GitHub Actions Marketplace** — `uses: bibleworld/llm-mutation-action@v1`
4. **DEV.to / Hacker News** — "We built Mutahunter for LLM prompts. Here's what we found." — launch post
5. **Plugs into existing toolchains** — integration guides for DeepEval, Promptfoo, LangSmith users

### Differentiation from existing tools
| Tool | What it tests | What it DOESN'T test |
|------|---------------|---------------------|
| Promptfoo | Prompt output quality | Whether your eval suite would catch a bug |
| DeepEval | LLM output against metrics | Whether your metrics are measuring the right thing |
| LangSmith | Traces and production behavior | Whether your test suite has gaps |
| prompt-lock (BibleWorld) | Prompt regressions in CI | Whether your evals would catch a semantic mutation |
| **llm-mutation** | **The quality of your eval suite itself** | N/A — this IS the gap |

### Monetization Path (v2+)
- **$0** — open source, MIT, fully functional
- **Cloud v0.1 (self-hosted)** — no cloud needed for open source
- **SaaS** — mutation dashboard, historical mutation score tracking, team-wide coverage reports: $29/mo per LLM app
- **Enterprise** — SSO, audit logs, Jira/Linear integration, custom operator library: $299/mo

### Acquisition Targets
- **Anthropic** — test quality aligns with trust/reliability mission; llm-mutation would improve confidence in Claude deployments
- **GitHub** — natural Copilot quality signal: "your eval suite mutation score dropped after this commit"
- **Datadog** — expanding LLM quality monitoring; mutation score as a production metric fits naturally
- **Confident AI (DeepEval)** — llm-mutation would be a natural DeepEval add-on or acquisition

---

## 30-DAY BUILD PLAN

**Week 1 (Days 1-7): Core operators + engine**
- Implement 6 mutation operators (deterministic regex-based)
- Unit tests for each operator
- Prompt format parser (string, messages list, Jinja2)
- CLI skeleton (Click)

**Week 2 (Days 8-14): MutantRunner + eval integration**
- MutantRunner with delta threshold and multi-run averaging
- DeepEval integration (highest priority — 3,000+ GitHub stars)
- pytest plugin skeleton
- SQLite store

**Week 3 (Days 15-21): Report + CI + calibration**
- MutationReport generation (JSON + human-readable)
- `mutate ci` command with exit codes
- `mutate calibrate` command (PAT-046)
- GitHub Action template
- End-to-end integration test

**Week 4 (Days 22-30): Polish + ship**
- README (400+ lines, full documentation)
- PyPI packaging (pyproject.toml, MANIFEST.in)
- Examples directory (3 complete examples: customer service, RAG assistant, code review bot)
- `pip install llm-mutation` works cleanly
- Hacker News / DEV.to launch post

---

## BUILD SCORE

| Dimension | Score | Justification |
|-----------|-------|---------------|
| Feasibility (0-3) | 2.8 | Pure Python. Deterministic mutation operators need no LLM. Eval integration reuses existing frameworks. 30-day sprint is aggressive but achievable for a senior engineer. Only risk: eval suite format diversity — mitigated by starting with pytest + DeepEval only. |
| Impact (0-3) | 2.7 | Every team with an LLM feature has this problem. 45% of devs report AI output frustration. Mutation testing is universally understood by senior engineers. Potential to become a standard CI metric for LLM quality gates. |
| Completeness (0-2) | 1.9 | Full architecture specified: 6 operators, MutantRunner, MutationReport, CLI (4 commands), GitHub Action, pytest plugin, SQLite schema, API design, 30-day build plan, quickstart. Someone could start coding from this spec today. |
| Biblical fidelity (0-2) | 1.6 | PAT-045 (Gideon's fleece inversion) maps to mutation testing precisely — inverting test conditions to verify oracle reliability. The structural parallel is genuine, specific, and grounded in the text's own experimental logic. The score reflects that the parallel is strong but the spiritual significance of the original text is fully preserved and not conflated with software tooling. |

**Total Build Score: 9.0/10**
