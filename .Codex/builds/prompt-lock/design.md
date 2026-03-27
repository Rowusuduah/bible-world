# prompt-lock — Full Design Document

**Version:** 0.1 Design
**Date:** 2026-03-27
**Author:** BibleWorld Cycle 009 — Chief Technologist + Chief Builder
**Build ID:** BUILD-008
**Pivot_Score:** 8.70
**Build Score:** 9.5

---

## 1. PROBLEM STATEMENT (Precise)

### 1.1 The Core Gap

In 2026, there is no framework-agnostic, open-source tool that:

1. Detects when a prompt file changes in a git commit/PR
2. Runs an eval suite specifically for that changed prompt
3. Calibrates the LLM judge BEFORE using it as a CI gate
4. Logs every eval run linked to the exact commit SHA for trace-back debugging
5. Fails the CI build if quality regression is detected

Each of these capabilities exists in isolation across different tools, but no single tool combines all five for a drop-in CI/CD experience.

### 1.2 Evidence of Pain (from web research, 2026-03-27)

| Source | Finding |
|--------|---------|
| contextqa.com (2026) | "Most engineering teams shipping LLM features in 2026 are testing them less rigorously than they test their login forms." |
| Gartner (2025) | Only 18% of software engineering teams use AI evaluation platforms |
| futureagi.substack.com (2026) | Traceability (score → prompt version → model → dataset) explicitly named as the 2026 top priority — not yet solved |
| contextqa.com (2026) | "A judge achieving less than 80% agreement with human evaluators on your specific task type is not reliable enough for automated blocking decisions" — calibration problem named, no tool solves it |
| Industry data (2026) | $500-2,000 burned per agent failure from untested prompt changes |

### 1.3 Why Existing Tools Do Not Solve This

- **Promptfoo** (acquired by OpenAI): Security red-teaming and vulnerability scanning. Different problem. Does not track quality regression. Does not detect prompt file changes in git.
- **LangSmith**: LangChain-specific. If you are not using LangChain, you cannot use LangSmith CI integration without significant custom work.
- **DeepEval**: Excellent eval metrics library. But does not detect prompt changes in git, does not calibrate judges, and requires custom CI wiring.
- **RAGAS**: RAG-specific. Not applicable to general prompt workflows.
- **Evidently GitHub Actions**: LLM unit testing in CI, but limited metrics and no judge calibration or commit-linked traceability.

### 1.4 The Calibration Problem (Why This Is Uniquely Important)

Research explicitly states: using an LLM as a CI gate without measuring its agreement with human evaluators on your specific task type produces unreliable CI behavior. The judge might have:
- **Systematic positive bias** — scores everything generous, passes regressions
- **Systematic negative bias** — scores everything strict, blocks correct improvements
- **Task misalignment** — good at general evaluation but poor at your specific domain

Without calibration, a CI gate is a gate guarded by an untrained person who may let enemies through or block allies arbitrarily. This destroys trust in the CI system and leads teams to disable the gate entirely.

prompt-lock requires calibration before a judge can be used as a CI gate. This is the core differentiator.

---

## 2. DESIGN PRINCIPLES

### Principle 1: Guards at Gaps (Nehemiah 4:13)
Only run evals on prompts that changed in the current commit/PR. Do not run the full eval suite on every commit. This keeps CI costs proportional to the actual risk.

**Implication:** The git diff detector is not optional. It is architecturally central.

### Principle 2: Calibrate Before Guarding
A judge that is not calibrated to your task cannot be trusted as a CI gate. prompt-lock refuses to use an uncalibrated judge in a hard-fail CI gate.

**Implication:** Calibration is a first-class workflow step, not an optional feature.

### Principle 3: Trace Everything
Every eval run is a historical record. When quality drops in production, the ledger is the first tool you reach for.

**Implication:** Traceability is not a reporting feature. It is a first-class concern from v0.1.

### Principle 4: Zero Framework Lock-In
Works with any Python codebase. Does not require LangChain, LlamaIndex, or any specific framework. Uses LiteLLM for multi-provider LLM access.

**Implication:** Dependencies are minimal and generic. The eval runner is framework-agnostic.

### Principle 5: 5-Minute Setup
An engineer should be able to add prompt-lock to an existing project, configure a basic eval, run it, and see a pass/fail result in under 5 minutes.

**Implication:** The CLI, config format, and GitHub Action must all be designed for minimal friction.

---

## 3. ARCHITECTURE

### 3.1 Module Map

```
promptlock/
├── cli.py              # Entry point — click CLI
├── config.py           # Config loading and validation (pydantic)
├── detector.py         # Git diff-based prompt change detection
├── runner.py           # Framework-agnostic eval suite runner
├── gate.py             # CI gate logic (pass/fail/warn/regression)
├── baseline.py         # Golden baseline management
├── judge/
│   ├── calibrate.py    # Judge calibration scoring
│   ├── llm_judge.py    # LLM-as-judge scorer
│   ├── exact_match.py  # Exact match scorer
│   └── semantic.py     # Semantic similarity scorer
└── tracer/
    ├── ledger.py       # SQLite trace storage
    └── query.py        # CLI query interface
```

### 3.2 Data Flow

```
Git PR/Commit
     │
     ▼
detector.py
(git diff → find changed prompt files)
     │
     ▼
config.py
(load eval config for changed prompts)
     │
     ▼
judge/calibrate.py (if not already calibrated)
(compare judge vs. human labels → calibration score)
     │
     ▼
runner.py
(run eval suite on each changed prompt)
     │
     ├──► judge/llm_judge.py
     ├──► judge/exact_match.py
     ├──► judge/semantic.py
     └──► (custom scorer)
     │
     ▼
tracer/ledger.py
(log run: commit SHA, prompt hash, model, scores, timestamp)
     │
     ▼
gate.py
(compare scores vs. thresholds and baseline)
     │
     ▼
exit(0) [PASS] or exit(1) [FAIL]
```

### 3.3 Config Schema (Pydantic)

```python
class JudgeCalibrationConfig(BaseModel):
    dataset: str                    # path to JSONL human-labeled examples
    min_agreement: float = 0.80    # minimum agreement ratio

class EvalConfig(BaseModel):
    type: Literal["llm_judge", "exact_match", "semantic_similarity", "regex", "custom"]
    judge_model: Optional[str]      # for llm_judge
    criteria: Optional[str]         # for llm_judge
    calibration: Optional[JudgeCalibrationConfig]
    reference_dataset: Optional[str]  # for semantic_similarity
    threshold: float                # pass/fail threshold (0.0-1.0)

class PromptConfig(BaseModel):
    path: str
    name: str
    model: str
    evals: List[EvalConfig]

class GateConfig(BaseModel):
    mode: Literal["hard", "soft", "regression"] = "regression"
    regression_threshold: float = 0.05  # fail if drops >5%

class TracerConfig(BaseModel):
    backend: Literal["sqlite", "postgres"] = "sqlite"
    db_path: str = ".prompt-lock/traces.db"

class PromptLockConfig(BaseModel):
    version: int
    prompts: List[PromptConfig]
    gate: GateConfig = GateConfig()
    tracer: TracerConfig = TracerConfig()
```

### 3.4 Trace Ledger Schema (SQLite)

```sql
CREATE TABLE eval_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL,
    commit_sha  TEXT NOT NULL,
    prompt_path TEXT NOT NULL,
    prompt_hash TEXT NOT NULL,    -- sha256 of prompt content
    model       TEXT NOT NULL,
    eval_type   TEXT NOT NULL,
    score       REAL NOT NULL,
    threshold   REAL NOT NULL,
    passed      INTEGER NOT NULL,  -- 0 or 1
    metadata    TEXT              -- JSON blob for extra fields
);

CREATE TABLE calibration_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT NOT NULL,
    judge_model     TEXT NOT NULL,
    dataset_path    TEXT NOT NULL,
    dataset_hash    TEXT NOT NULL,
    agreement_rate  REAL NOT NULL,
    spearman_r      REAL NOT NULL,
    bias            REAL NOT NULL,    -- mean(judge_score - human_score)
    passed          INTEGER NOT NULL,
    min_agreement   REAL NOT NULL
);
```

### 3.5 Judge Calibration Algorithm

```python
def calibrate_judge(judge_model, dataset_path, min_agreement=0.80):
    examples = load_jsonl(dataset_path)  # list of {input, output, human_score}

    judge_scores = []
    for ex in examples:
        prompt = build_judge_prompt(ex["input"], ex["output"], criteria)
        raw = llm_call(judge_model, prompt)
        judge_scores.append(extract_score(raw))  # normalize to 0-1

    human_scores = [ex["human_score"] for ex in examples]

    # Agreement: proportion where |judge - human| < 0.2 (configurable)
    agreements = [abs(j - h) < 0.2 for j, h in zip(judge_scores, human_scores)]
    agreement_rate = sum(agreements) / len(agreements)

    # Spearman rank correlation
    spearman_r = spearmanr(judge_scores, human_scores).correlation

    # Systematic bias
    bias = mean([j - h for j, h in zip(judge_scores, human_scores)])

    passed = agreement_rate >= min_agreement

    return CalibrationResult(
        agreement_rate=agreement_rate,
        spearman_r=spearman_r,
        bias=bias,
        passed=passed
    )
```

### 3.6 Git Diff Prompt Detector

```python
def detect_changed_prompts(config: PromptLockConfig, base_ref="HEAD~1") -> List[str]:
    repo = git.Repo(".")
    diff = repo.head.commit.diff(base_ref)

    changed_files = {item.a_path for item in diff}

    # Match against configured prompt paths
    changed_prompts = []
    for prompt_config in config.prompts:
        if prompt_config.path in changed_files:
            changed_prompts.append(prompt_config)

    return changed_prompts
```

### 3.7 Regression Gate Logic

```python
def evaluate_gate(results: List[EvalResult], baseline: Dict, config: GateConfig) -> GateDecision:
    if config.mode == "hard":
        # Fail if any score below threshold
        for r in results:
            if r.score < r.threshold:
                return GateDecision(passed=False, reason=f"{r.eval_type} score {r.score:.2f} < threshold {r.threshold:.2f}")

    elif config.mode == "regression":
        # Fail if score drops more than regression_threshold from baseline
        for r in results:
            baseline_score = baseline.get(r.prompt_name, {}).get(r.eval_type)
            if baseline_score and (baseline_score - r.score) > config.regression_threshold:
                return GateDecision(
                    passed=False,
                    reason=f"{r.eval_type} regressed {baseline_score - r.score:.1%} (threshold: {config.regression_threshold:.1%})"
                )

    elif config.mode == "soft":
        # Always pass, but log warnings
        return GateDecision(passed=True, warnings=[...])

    return GateDecision(passed=True)
```

---

## 4. EVAL TYPES — DETAILED DESIGN

### 4.1 LLM Judge (llm_judge)

Uses a LiteLLM-abstracted LLM to evaluate the output against a natural language criteria string.

**Judge prompt template:**
```
You are an evaluation judge. Your job is to score an AI-generated output on a scale from 0.0 to 1.0.

CRITERIA: {criteria}

INPUT: {input}
OUTPUT: {output}

Respond with ONLY a JSON object in this format:
{"score": 0.85, "reasoning": "The output addresses the main points but misses X."}

Score 0.0 = completely fails the criteria
Score 1.0 = perfectly satisfies the criteria
```

**Score extraction:** JSON parsing with fallback regex `score[:\s]+(0\.\d+|1\.0|0|1)`

### 4.2 Semantic Similarity (semantic_similarity)

Uses `sentence-transformers` (offline, no API cost) to compute cosine similarity between the model output and reference outputs.

**Algorithm:**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")  # 80MB, fast, offline

def semantic_score(output, references):
    output_emb = model.encode(output)
    ref_embs = model.encode(references)
    similarities = cosine_similarity([output_emb], ref_embs)[0]
    return float(max(similarities))  # best match among references
```

**Advantage:** Zero API cost per eval run once model is cached.

### 4.3 Exact Match (exact_match)

Direct string comparison with optional normalization (case, whitespace, punctuation).

### 4.4 Custom Scorer (custom)

Users provide a Python function path. prompt-lock calls it with `(input: str, output: str) -> float`.

```yaml
evals:
  - type: custom
    scorer: myapp.evals.check_json_validity
    threshold: 1.0
```

---

## 5. CLI DESIGN (FULL)

### `prompt-lock init`
Creates `.prompt-lock/config.yaml` with template. Creates `.prompt-lock/` directory.

### `prompt-lock check`
Main command. Detects changed prompts, runs evals, gates, returns exit code.

Options:
- `--all-prompts`: Ignore git diff, run evals for all configured prompts
- `--prompt <path>`: Run evals for a specific prompt only
- `--dry-run`: Run evals but do not gate (always exit 0)
- `--config <path>`: Override config file location

### `prompt-lock calibrate`
Run judge calibration for a specific judge.

Options:
- `--judge <model>`: Model to calibrate
- `--dataset <path>`: JSONL human-labeled dataset
- `--min-agreement <float>`: Override minimum agreement threshold

### `prompt-lock baseline update`
Update the baseline to current eval scores.

Options:
- `--prompt <path>`: Update baseline for specific prompt only
- `--force`: Skip confirmation prompt

### `prompt-lock traces show`
Query trace history.

Options:
- `--prompt <path>`: Filter by prompt
- `--last <duration>`: e.g., `30d`, `7d`, `1w`
- `--format <table|json|csv>`: Output format

### `prompt-lock traces diff`
Show score changes around a date.

Options:
- `--before <date>`
- `--after <date>`

### `prompt-lock report`
Generate HTML report of recent eval history.

Options:
- `--output <path>`: Output file (default: stdout)

---

## 6. GITHUB ACTIONS DESIGN

### Action Inputs

```yaml
inputs:
  config:
    description: "Path to prompt-lock config file"
    default: ".prompt-lock/config.yaml"
  anthropic-api-key:
    required: false
  openai-api-key:
    required: false
  fail-on-regression:
    description: "Fail the build if regression detected"
    default: "true"
  all-prompts:
    description: "Run evals for all prompts, not just changed ones"
    default: "false"
```

### Action Outputs

```yaml
outputs:
  result:
    description: "pass or fail"
  changed-prompts:
    description: "Comma-separated list of changed prompt files"
  scores:
    description: "JSON object of prompt -> score mappings"
```

### Action PR Comment

On every PR, the action posts a comment with the eval results table:

```
## prompt-lock Results

| Prompt | Eval Type | Score | Threshold | Baseline | Change | Status |
|--------|-----------|-------|-----------|----------|--------|--------|
| summarize.txt | llm_judge | 0.82 | 0.75 | 0.85 | -3.5% | PASS |
| classify.txt | semantic_sim | 0.91 | 0.80 | 0.89 | +2.2% | PASS |

All evals PASSED. Safe to merge.
```

---

## 7. DIFFERENTIATION MATRIX (Detailed)

| Capability | prompt-lock | Promptfoo | LangSmith | DeepEval | RAGAS | Evidently |
|-----------|-------------|-----------|-----------|----------|-------|-----------|
| Prompt file change detection (git diff) | YES | NO | NO | NO | NO | NO |
| Judge calibration scoring | YES | NO | NO | NO | NO | NO |
| Human-agreement measurement | YES | NO | NO | NO | NO | NO |
| Framework-agnostic | YES | YES | NO | YES | NO | YES |
| Git commit SHA in trace | YES | NO | YES | NO | NO | NO |
| Prompt hash in trace | YES | NO | NO | NO | NO | NO |
| SQLite trace ledger | YES | NO | NO | NO | NO | NO |
| Regression gate (not just threshold) | YES | NO | NO | NO | NO | NO |
| GitHub Actions native | YES | YES | YES | NO | NO | YES |
| Offline semantic similarity | YES | NO | NO | NO | YES | NO |
| Open source (MIT) | YES | YES | NO (SaaS) | YES | YES | YES |
| PyPI installable | YES | YES | NO | YES | YES | YES |

---

## 8. ACQUISITION THESIS

### Primary Path: OpenAI
OpenAI acquired Promptfoo for LLM security red-teaming. They now need the quality regression complement. prompt-lock is that complement. The narrative is clean: "We have the security evaluator. Now we need the quality regression evaluator."

### Secondary Path: Anthropic
Anthropic acquired Humanloop for AI trust and evaluation. prompt-lock's judge calibration module is directly aligned with Anthropic's trust-in-AI mandate. Anthropic's own research documented the CoT faithfulness decay problem. prompt-lock's architecture extends naturally to detecting that decay.

### Tertiary Path: Microsoft
Microsoft is building AI evaluation tools for Copilot. Only 5% of enterprise Copilot deployments went from pilot to production (Gartner). The gap is quality validation. prompt-lock solves quality validation at the prompt level — a natural fit for Microsoft's AI evaluation investment thesis.

---

## 9. RISKS AND MITIGATIONS

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| LangSmith expands to be framework-agnostic | MEDIUM | Move fast. Get to 500+ GitHub stars before they notice. |
| OpenAI expands Promptfoo into quality regression | MEDIUM | First-mover + judge calibration is the moat. |
| Judge calibration not worth the friction for small teams | LOW | Make it optional (soft-fail mode). Required only for hard-fail gates. |
| API costs for eval runs deter adoption | LOW | Semantic similarity scorer is offline (zero API cost). Promote this. |
| CI runs too slow for large prompt suites | LOW | Only eval changed prompts (the core architectural decision). |

---

## 10. BIBLICAL FIDELITY CHECK

Per BibleWorld Law 2 (Integrity Law): verify the Nehemiah mapping is genuine, not forced.

**What Nehemiah 4:13-14 actually describes:**
- A rebuild project (Jerusalem's walls) that is at risk
- The risk enters through specific points: the low, exposed places (shefalim)
- Response: station guards specifically at those exposed points
- Workers continue building simultaneously (both hands: tool and weapon)
- The goal is to complete the rebuild while preventing regression

**What prompt-lock actually does:**
- An LLM application that is being actively developed (a rebuild in progress)
- Quality regression risk enters through specific points: prompt changes (the gaps)
- Response: station eval guards specifically at the changed prompt files
- Developers continue shipping simultaneously (background runs or soft-fail mode)
- The goal is to enable continuous shipping while preventing quality regression

**Verdict:** Mapping is structural, not metaphorical. The core design decision (guard at gaps, not everywhere) is directly derived from the biblical text, not imposed on it. The pattern is genuine.

No Law 2 violation. Pattern integrity confirmed.

---

*Design document complete. Ready for v0.1 sprint.*
