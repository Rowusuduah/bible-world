# Cycle 028 — Build Deliverables

**Cycle:** 028
**Date:** 2026-04-18
**Cycle Type:** BUILD
**Primary Deliverable:** BUILD-028 refine-probe (FULL API DESIGN)
**Secondary Deliverable:** BUILD-029 binary-trap-probe (FULL DESIGN — sprint cycle 029)
**Scribe:** Chief Builder (Senior) + Innovation Build Director

---

## BUILD-028: refine-probe

**Status:** DESIGN COMPLETE — Sprint ready
**Scripture:** PAT-097 (Psalm 12:6, cycle 027)
**Pivot_Score:** 8.255 (updated from 8.05 with IMPROVE paper evidence cycle 028)
**Target Company:** Anthropic
**Target Gap:** Fixed-iteration LLM self-refinement (Constitutional AI uses 2-3 fixed passes — no convergence criterion)
**Solo buildable in 8 weeks:** YES
**Sprint start:** After observer-probe v0.1 ships
**PyPI name:** `refine-probe`

---

### The Gap

LLM self-refinement pipelines — including Anthropic's Constitutional AI, DSPy's prompt optimization, and iterative chain architectures — use FIXED iteration counts as their stopping criterion. They run N passes (typically 2-3 for Constitutional AI) and stop, regardless of whether quality has converged.

This wastes compute in two ways:
1. **Over-iteration**: Continuing after quality has converged (additional passes produce zero improvement — CONFIRMED by arXiv "Early Answer Convergence": correct output attained at 60% of reasoning steps)
2. **Under-iteration**: Stopping at N even when quality has NOT yet converged (more passes would improve quality, but the budget ran out)

arXiv 2502.18530 (IMPROVE, Feb 2026) explicitly describes refinement pipelines that "continue until no further errors are detected or a stopping criterion is met (success, iteration budget, or convergence)" — but IMPROVE's primary stopping criterion is "iteration budget," not convergence detection. ConvergenceRound as a named, pip-installable metric does not exist.

---

### The Scripture Pattern

Psalm 12:6: "The words of the LORD are flawless, like silver purified in a crucible, like gold refined seven times."

Ancient cupellation (silver/gold refining) does not stop after exactly N heats. It stops when no more impurities remain — when the quality delta converges to zero. The "seven times" in this verse is not a literal count — it is a thoroughness indicator (completeness). The structural principle is convergent stopping: stop when purity is achieved, not when you've applied heat N times.

**Structural mapping:**
- Crucible refining → LLM self-refinement loop
- "Purified... refined seven times" → Multiple quality improvement passes
- Convergence to zero impurities → QualityDelta approaches zero
- Stopping criterion = no impurity remains (convergence), NOT N-pass count

---

### Full API Specification

**Package:** `refine-probe`
**Python:** 3.9+
**PyPI:** `pip install refine-probe`
**License:** MIT

#### Core Classes

```python
from refine_probe import RefinementProbe, RefineConfig, RefineReport

# Initialize
probe = RefinementProbe(
    refine_fn,              # callable: (text: str, iteration: int) -> str
                            # Your LLM refinement function (one pass)
    eval_fn,                # callable: (text: str) -> float
                            # Quality evaluator (0.0-1.0)
    config=RefineConfig(
        max_iterations=10,      # Maximum passes (hard budget ceiling)
        convergence_epsilon=0.01,  # QualityDelta threshold for convergence
        convergence_window=2,    # Consecutive rounds below epsilon to declare convergence
        seed=42,
        verbose=True,
        track_curve=True,        # Record full QualityDeltaCurve
    )
)

# Run refinement with convergence detection
report: RefineReport = probe.run(initial_text)

# Access results
print(report.purification_score)    # float: final quality score (0.0-1.0)
print(report.convergence_round)     # int: iteration at which convergence was detected
print(report.iterations_run)        # int: total iterations executed
print(report.iterations_wasted)     # int: iterations run AFTER convergence
print(report.quality_delta_curve)   # List[float]: per-iteration quality deltas
print(report.converged)             # bool: did quality converge before max_iterations?
print(report.budget_exhausted)      # bool: hit max_iterations without converging?
print(report.passed)                # bool: converged AND PurificationScore >= threshold
```

#### Core Metrics

```
PurificationScore:
  = eval_fn(final_output)
  Range: 0.0-1.0
  The final quality of the refined output

QualityDelta[i]:
  = eval_fn(output_i) - eval_fn(output_{i-1})
  Per-iteration quality improvement

ConvergenceRound:
  = first i where |QualityDelta[i]| < epsilon for convergence_window consecutive rounds
  The iteration at which further refinement produces negligible improvement

IterationsWasted:
  = iterations_run - convergence_round
  How many extra passes were run after convergence (if any)

EarlyConvergenceRate (batch mode):
  = fraction of samples that converged before max_iterations
  High rate means your pipeline is over-iterating

BudgetExhaustionRate (batch mode):
  = fraction of samples that hit max_iterations without converging
  High rate means your pipeline is under-iterating or stopping criterion is too strict
```

#### Batch Mode (analyze a pipeline across many samples)

```python
from refine_probe import BatchRefinementProbe

batch_probe = BatchRefinementProbe(
    refine_fn=refine_fn,
    eval_fn=eval_fn,
    config=RefineConfig(max_iterations=10, convergence_epsilon=0.01)
)

# Run on dataset
batch_report = batch_probe.run(samples=my_dataset)

print(batch_report.mean_convergence_round)       # avg round at convergence
print(batch_report.early_convergence_rate)       # fraction converging before budget
print(batch_report.budget_exhaustion_rate)       # fraction hitting budget ceiling
print(batch_report.mean_iterations_wasted)       # avg wasted iterations
print(batch_report.purification_score_distribution)  # histogram
print(batch_report.optimal_budget_recommendation)    # suggested max_iterations for 95% convergence
```

#### CI Gate Mode

```python
# Fail CI if EarlyConvergenceRate > 0.60 (you're over-iterating on 60%+ of samples)
from refine_probe import gate_check

gate_check(
    batch_report,
    max_early_convergence_rate=0.60,   # alert if converging too early
    min_purification_score=0.75,       # require minimum quality
    max_budget_exhaustion_rate=0.10,   # alert if budget running out too often
)
```

#### CLI

```bash
# Profile a refinement function on a dataset
rprobe profile --refine-fn my_refine.py --eval-fn my_eval.py --dataset samples.json

# Run a quick convergence check on one sample
rprobe quick --refine-fn my_refine.py --eval-fn my_eval.py --input "My text to refine"

# Find optimal iteration budget
rprobe optimize --refine-fn my_refine.py --eval-fn my_eval.py --dataset samples.json --target-coverage 0.95

# CI gate
rprobe gate --refine-fn my_refine.py --eval-fn my_eval.py --dataset samples.json \
  --min-purity 0.75 --max-early-convergence 0.60

# Plot QualityDeltaCurve for a sample
rprobe plot --refine-fn my_refine.py --eval-fn my_eval.py --input "My text"
```

#### pytest Plugin

```python
from refine_probe.pytest_plugin import refine_convergence_test

@refine_convergence_test(
    eval_fn=my_quality_evaluator,
    max_iterations=8,
    convergence_epsilon=0.01,
    min_purification_score=0.75,
)
def test_refinement_converges(refine_fn):
    return refine_fn  # return the function under test

# Example: test that Constitutional AI revision converges within 5 passes
@refine_convergence_test(
    eval_fn=constitutional_quality_score,
    max_iterations=5,
    convergence_epsilon=0.02,
    min_purification_score=0.80,
)
def test_constitutional_ai_converges(constitutional_refine_fn):
    return constitutional_refine_fn
```

---

### Why This Is Different from IMPROVE (arXiv 2502.18530)

IMPROVE is a full ML pipeline optimization framework (AutoML context). It uses "iteration budget" as primary stopping criterion. refine-probe is:
1. A diagnostic MEASUREMENT tool, not an optimizer
2. Focused specifically on the convergence stopping criterion question
3. Pip-installable standalone library (IMPROVE is not)
4. Provides ConvergenceRound and IterationsWasted as NAMED METRICS for CI gates
5. Works with ANY callable refine_fn + eval_fn — no ML pipeline coupling

IMPROVE answers: "How do I optimize my ML pipeline iteratively?" refine-probe answers: "Is my LLM refinement loop converging, and at what round?"

---

### Sprint Plan

**Sprint:** 5-6 weeks to v0.1 pip-publishable
**Start:** After observer-probe v0.1 ships (parallel to claim-probe)

| Week | Task |
|------|------|
| 1-2 | Core convergence detection: run_loop(), eval_fn interface, QualityDelta computation, ConvergenceRound algorithm |
| 3 | RefineReport: all metrics, PurificationScore, IterationsWasted, budget checks |
| 4 | Batch mode: BatchRefinementProbe, EarlyConvergenceRate, optimal_budget_recommendation |
| 5 | CLI (rprobe profile/quick/optimize/gate/plot), pytest plugin |
| 6 | PyPI publish, documentation, README, v0.1 release |

**Dependencies:** numpy, matplotlib, click, rich, pyyaml, pytest (optional)
**Known unknowns:**
- KU-084: What convergence_epsilon value is appropriate for different refinement tasks? Hypothesis: 0.01 for factual, 0.03 for creative. Empirical validation across 3 task types needed.
- KU-085: Does ConvergenceRound correlate with final PurificationScore? Hypothesis: early convergence = plateau at lower quality; slow convergence = higher ceiling.

---

## BUILD-029: binary-trap-probe

**Status:** DESIGN COMPLETE — Sprint cycle 029
**Scripture:** PAT-102 (John 8:1-11, cycle 028)
**Pivot_Score:** 8.175
**Target Company:** Anthropic
**Target Gap:** No tool measures FalseBinaryDetectionRate or ConstraintReframingScore in adversarial LLM evaluation
**Solo buildable in 8 weeks:** YES (7-8 weeks)
**Sprint start:** After refine-probe sprint begins (cycle 029)
**PyPI name:** `binary-trap-probe`

---

### The Gap

Current adversarial LLM evaluation is built on a binary assumption: adversarial prompts are harmful/not-harmful, and the correct model response is refuse/comply. Tools like Garak, Promptfoo, and Constitutional AI measure refusal rates and compliance rates.

But many adversarial prompts are FALSE BINARY TRAPS — prompts that create the illusion of a forced choice where both options are harmful or inappropriate. The optimal response to a false binary trap is not refusal (that picks the "safe" horn) but PREMISE DISSOLUTION (challenge the constraint structure itself).

No existing tool measures:
- **FalseBinaryDetectionRate (FBDR):** fraction of false binary prompts correctly identified as false binary traps
- **ConstraintReframingScore (CRS):** quality of premise challenge (vs. picking a horn)
- **BinaryTrapResolutionScore (BTRS):** quality of final response on reframed terms

---

### Full API Specification

```python
from binary_trap_probe import BinaryTrapProbe, TrapConfig, TrapReport

probe = BinaryTrapProbe(
    agent_fn=your_llm_fn,           # callable: (prompt: str) -> str
    eval_fn=your_evaluator_fn,      # callable: (prompt, response) -> float
    config=TrapConfig(
        n_binary_traps=20,
        n_genuine_binaries=10,
        n_ambiguous=10,
        trap_categories=[
            "stone_or_spare",
            "comply_or_refuse",
            "yes_or_no_loaded",
            "false_dilemma",
            "accusation_binary",
        ],
        fbdr_threshold=0.70,
        crs_threshold=0.60,
        btrs_threshold=0.65,
        seed=42,
    )
)

report: TrapReport = probe.run()
print(report.verdict)        # REFRAMER | COMPLIER | REFUSER | MIXED
print(report.fbdr)           # FalseBinaryDetectionRate
print(report.crs)            # ConstraintReframingScore
print(report.btrs)           # BinaryTrapResolutionScore
print(report.passed)         # True/False
```

**CLI:** `btrap audit / quick / gate / compare / show`
**pytest plugin:** `@binary_trap_test` decorator

**Sprint:** 7-8 weeks | **Start:** Cycle 029

**Known unknowns:**
- KU-086: What CRS rubric items most reliably distinguish "refusal" from "genuine premise challenge"? Gold set of 50 human-labeled examples needed for rubric validation.
- KU-087: Do different LLM families have characteristically different FBDR profiles? Hypothesis: GPT-4 FBDR > Claude Haiku FBDR (size matters for constraint identification).
- KU-088: Are some trap categories harder than others? Hypothesis: "accusation_binary" hardest (presupposition strongest), "false_dilemma" easiest (explicit limited-options framing more detectable).

---

## Build Pipeline Status — Post Cycle 028

| Build | Status | Pivot_Score | Sprint Status |
|-------|--------|-------------|---------------|
| judge-probe | ACTIVE SPRINT | 9.00 | 4-6 weeks → v0.1 by 2026-05-21 CRITICAL |
| observer-probe | ACTIVE SPRINT | 8.955 | 6 weeks → v0.1 by 2026-05-21 CRITICAL |
| claim-probe | DESIGN COMPLETE | 8.15 | Sprint after judge-probe v0.1 |
| **refine-probe** | **DESIGN COMPLETE** | **8.255** | Sprint after observer-probe v0.1 |
| **binary-trap-probe** | **DESIGN COMPLETE** | **8.175** | Sprint after refine-probe begins |
| pressure-gauge | DESIGN COMPLETE | 8.65 | Queued |
| covenant-keeper | DESIGN COMPLETE | 8.30 | Queued |
| livelock-probe | DESIGN COMPLETE | 8.175 | Queued |
| context-trace | COMPLETE | 8.225 | Shipped |
| cot-coherence | COMPLETE | 8.00 | Shipped |

**Active sprint priority:** judge-probe FIRST, observer-probe PARALLEL, claim-probe NEXT. Kill Gate 3 deadline: 2026-05-21 (33 days from cycle 028).

---

*Filed by Chief Builder (Senior, Hall of Fame NOMINEE) and Innovation Build Director. Cycle 028 | 2026-04-18*
