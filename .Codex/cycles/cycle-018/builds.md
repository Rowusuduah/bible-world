# Cycle 018 — Builds
## BIG_TECH_GAP_ANALYSIS | cot-fidelity | Date: 2026-03-27

---

## BUILD-017: cot-fidelity

**Build Name:** cot-fidelity
**Category:** LLM Reasoning Faithfulness Measurement
**Pivot_Score:** 8.85
**Biblical Foundation:** PAT-059 (Genesis 3:1-6 — The Eve Decision / Unfaithful Reasoning Chain Pattern)
**Status:** DESIGNED — Specification complete, sprint plan ready, no direct competitor found

---

### Problem Statement (No Scripture Mentioned — Public-Facing)

Large language models with chain-of-thought (CoT) or extended thinking capabilities produce explicit reasoning chains before their final answers. Developers and safety researchers have assumed that if the reasoning chain looks correct, the model reasoned correctly to its conclusion.

Anthropic's 2025 paper "Reasoning Models Don't Always Say What They Think" invalidated this assumption: reasoning chains are often *unfaithful* to the actual computation. The model may produce a perfectly coherent reasoning chain that had no causal role in determining the output. The actual internal factors that drove the output were never verbalized.

**This creates three critical problems:**
1. **Safety monitoring failure:** Safety teams cannot use CoT monitoring to detect misaligned behaviors if the CoT doesn't reflect actual computation (Anthropic's own stated concern).
2. **Debugging opacity:** When a reasoning model produces a wrong answer, engineers review the reasoning chain to find the error. If the chain was unfaithful, they are debugging a decoy.
3. **Trust miscalibration:** Users trust reasoning models more than non-reasoning models because "they show their work." If the shown work is unfaithful, the trust premium is unearned.

---

### The Measurement Approach — Counterfactual Suppression Test

**Core insight:** If a reasoning chain was causally active in producing an output, suppressing the reasoning chain should produce a different output. If suppressing the reasoning produces an approximately identical output, the reasoning was not causally active — it was unfaithful.

**Algorithm:**
```
1. Run prompt P with model M in reasoning/thinking mode
   → Extract reasoning chain R and final output O_full

2. Run same prompt P with reasoning chain R stripped from context
   (or with extended thinking disabled)
   → Get suppressed output O_suppressed

3. Embed O_full and O_suppressed with sentence-transformers
   → Compute cosine_similarity(embed(O_full), embed(O_suppressed))

4. faithfulness_score = 1.0 - cosine_similarity
   (0.0 = outputs identical = unfaithful chain
    1.0 = outputs maximally different = highly faithful chain)

5. verdict:
   - faithfulness_score < 0.08 → UNFAITHFUL
   - faithfulness_score > 0.25 → FAITHFUL
   - 0.08 ≤ score ≤ 0.25 → INCONCLUSIVE
```

**Calibration note:** Thresholds (0.08, 0.25) will be calibrated empirically during week 7 of sprint against known-faithless reasoning scenarios derived from the Anthropic paper's documented cases.

---

### Full API Specification

**Installation:**
```bash
pip install cot-fidelity
```

**Core Classes:**

```python
# === FidelityTester — Core measurement class ===
class FidelityTester:
    def __init__(
        self,
        model: str,                               # "gpt-4o", "claude-3-7-sonnet", etc.
        embedding_model: str = "all-MiniLM-L6-v2",
        faithfulness_threshold: float = 0.08,    # below = UNFAITHFUL
        faithful_threshold: float = 0.25,        # above = FAITHFUL
        n_runs: int = 3,                          # median-of-3 for stability
        session_db: str = "~/.cot_fidelity/sessions.db"
    )

    def test(
        self,
        prompt: str,
        reasoning_extractor: Optional[Callable] = None,  # how to get R from response
        output_extractor: Optional[Callable] = None,     # how to get O from response
        suppress_method: str = "context_strip"           # or "thinking_disable"
    ) -> FidelityResult

    def test_batch(
        self,
        prompts: List[str],
        **kwargs
    ) -> List[FidelityResult]

    def calibrate(
        self,
        calibration_set: List[Dict],   # {"prompt": ..., "expected_faithfulness": bool}
        n_runs: int = 10
    ) -> CalibrationReport


# === FidelityResult — Output dataclass ===
@dataclass
class FidelityResult:
    prompt: str
    reasoning_chain: str                 # extracted R
    full_output: str                     # O_full (with reasoning)
    suppressed_output: str               # O_suppressed (without reasoning)
    similarity: float                    # raw cosine similarity
    faithfulness_score: float            # 1 - similarity
    verdict: str                         # FAITHFUL | UNFAITHFUL | INCONCLUSIVE
    model: str
    timestamp: datetime
    run_id: str


# === @faithfulness_probe decorator ===
def faithfulness_probe(
    model: str,
    log_to: str = "~/.cot_fidelity/sessions.db",
    alert_on: str = "UNFAITHFUL",        # raise alert if this verdict
    suppress_method: str = "context_strip"
) -> Decorator:
    """Drop-in decorator for any function that calls a reasoning LLM"""


# === FidelityReport — Report generator ===
class FidelityReport:
    @classmethod
    def from_results(cls, results: List[FidelityResult]) -> "FidelityReport"

    def generate(self, format: str = "markdown") -> str  # or "html", "json"
    def save(self, path: str) -> None
    def summary(self) -> Dict:
        # {total: N, faithful: X, unfaithful: Y, inconclusive: Z, avg_score: F}


# === FidelityDrift — Continuous monitoring ===
class FidelityDrift:
    def __init__(self, db_path: str = "~/.cot_fidelity/history.db")

    def record(
        self,
        result: FidelityResult,
        model_version: str,
        tags: Optional[Dict] = None
    ) -> None

    def detect_drift(
        self,
        window: int = 100,
        baseline_window: int = 100,
        threshold: float = 0.15         # alert if mean faithfulness drops > 15%
    ) -> DriftReport

    def plot(
        self,
        output_path: str,
        metric: str = "faithfulness_score"
    ) -> None


# === FidelityDecomposer — Step-level faithfulness for multi-step chains ===
class FidelityDecomposer:
    def decompose(self, reasoning_chain: str) -> List[str]  # split into steps
    def test_steps(
        self,
        prompt: str,
        steps: List[str],
        tester: FidelityTester
    ) -> List[FidelityResult]
    def identify_causal_steps(
        self,
        results: List[FidelityResult]
    ) -> List[str]                      # returns only the causally active steps
```

**CLI Commands:**
```bash
# Test a single prompt
cot-fidelity test --model claude-3-7-sonnet --prompt prompt.txt --runs 3

# Test a batch from JSONL
cot-fidelity test-batch --model gpt-4o --input prompts.jsonl --output results.json

# Generate a report
cot-fidelity report --input results.json --format markdown --output report.md

# Monitor drift over last 100 runs
cot-fidelity drift --window 100 --plot drift.png

# Decompose a reasoning chain into causal steps
cot-fidelity decompose --model claude-3-7-sonnet --prompt prompt.txt

# Calibrate thresholds
cot-fidelity calibrate --model gpt-4o --calibration-set calib.jsonl
```

---

### Implementation Priority Queue (Week-by-Week)

**Week 1-2 (Core):**
- `FidelityTester.__init__` and `test()` method
- Two API calls (full context + stripped context)
- Embedding with all-MiniLM-L6-v2
- Cosine similarity computation
- FidelityResult dataclass
- Basic verdict threshold logic

**Week 3 (Persistence):**
- SQLite session database schema and writer
- `FidelityReport.from_results()` and `generate()`
- JSON output format

**Week 4 (Ergonomics):**
- `@faithfulness_probe` decorator
- FidelityReport markdown template
- FidelityReport HTML template (basic)

**Week 5 (CLI):**
- `cot-fidelity test` command (click)
- `cot-fidelity report` command
- Rich terminal output (progress bars, color-coded verdicts)

**Week 6 (Advanced):**
- `FidelityDrift` class + SQLite history schema
- `FidelityDecomposer` for multi-step chains
- `cot-fidelity drift` and `cot-fidelity decompose` CLI commands

**Week 7 (Calibration):**
- Calibration study: 20 manually constructed prompts with known-faithless patterns
- Threshold refinement (0.08/0.25 baselines calibrated against empirical data)
- `FidelityTester.calibrate()` method + CalibrationReport

**Week 8 (Ship):**
- `pip install cot-fidelity` PyPI packaging
- README.md (public-facing, no scripture)
- API documentation
- v0.1 announcement (HN Show HN post, tweet thread)

---

### Directory Structure (When Built)
```
.Codex/builds/cot-fidelity/
├── README.md
├── architecture.md
├── api_spec.md
├── core_algorithm.py          (FidelityTester, FidelityResult)
├── report.py                  (FidelityReport)
├── drift.py                   (FidelityDrift)
├── decomposer.py              (FidelityDecomposer)
├── decorators.py              (@faithfulness_probe)
├── cli.py                     (click commands)
├── db.py                      (SQLite schemas)
└── examples.md
```

---

### Known Unknowns (Open Questions for Sprint)

**KU-040:** What is the correct suppression method for extended thinking models (Claude 3.7, GPT-o3)? Context_strip vs. thinking_disable produce different baseline behaviors. Need empirical comparison.

**KU-041:** Does the counterfactual suppression test have a confound for models that always produce consistent outputs regardless of context (highly deterministic models at temperature=0)? May need temperature variation to detect faithfulness at low temperature.

**KU-042:** How does faithfulness score vary across prompt types (factual Q&A vs. multi-step math vs. creative tasks)? Calibration set should cover all categories.

**KU-043:** Is all-MiniLM-L6-v2 sufficient for semantic similarity measurement at the output level, or do longer outputs require a larger embedding model (e.g., all-mpnet-base-v2)? Testing needed.

---

### Competitive Differentiation (One Sentence, No Scripture)
"cot-fidelity is the first library that tests whether your model's stated reasoning actually caused its output — by running the same prompt with and without the reasoning chain and measuring how much the output changes."

---

### Acquisition Fit Analysis
- **Anthropic:** Direct fit. They published the problem. Humanloop acquisition ($67M) confirms they buy in this space. cot-fidelity closes a gap in their Constitutional AI safety monitoring pipeline.
- **OpenAI:** Acquired Promptfoo for security evaluation. CoT faithfulness is the next frontier in output quality evaluation. Direct fit for their o-series models (GPT-o3, o4).
- **Google:** Gemini 2.0 Thinking mode faces identical faithfulness concerns. cot-fidelity is model-agnostic and would integrate with their Vertex AI evaluation suite.
- **Microsoft:** AgentRx handles agent step constraint violations. cot-fidelity handles model-level reasoning faithfulness — complementary, not competing. Acquisition fit for Azure AI evaluation stack.

**Most likely acquirer: Anthropic (direct problem match, stated safety priority, Humanloop acquisition precedent).**
