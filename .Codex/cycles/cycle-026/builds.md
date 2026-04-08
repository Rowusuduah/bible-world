# BibleWorld Cycle 026 — Builds
## BUILD Cycle | Target: Anthropic | 2026-04-08

**Cycle:** 026
**Cycle Type:** BUILD (B)
**Primary Build:** BUILD-026: judge-probe (Pivot_Score: 9.00)
**Sprint Parallel:** observer-probe sprint kickoff documentation (BUILD-025 continues)

---

## BUILD-026: judge-probe

**Pattern Source:** PAT-094 (John 7:24 — The Surface-Semantic Evaluation Gap)
**Build Type:** SOFTWARE — Developer Testing Library (Python, pip-installable)
**Pip Name:** `judge-probe`
**CLI Command:** `jprobe`
**Version Target:** v0.1 (pip-publishable)
**Sprint Estimate:** 4–6 weeks

---

### THE PROBLEM

LLM-as-a-judge is the dominant evaluation paradigm in 2026. Virtually every production AI evaluation pipeline uses an LLM judge to score agent outputs: DeepEval uses GPT-4o as judge, Braintrust uses LLM judges natively, prompt-lock uses LLM judges for regression testing, covenant-keeper uses LLM judges for adversarial scoring. The judge is upstream of everything.

**The documented failure mode:**
Multiple published studies in 2025-2026 confirm LLM judges exhibit systematic biases based on SURFACE FEATURES of responses, not their semantic content:
- **Verbosity bias:** Longer responses score higher even at equal semantic quality
- **Politeness bias:** Responses with confident, polite openers ("Certainly! Here's...") score higher
- **Formatting bias:** Bullet points score higher than paragraphs on the same content
- **Position bias:** In pairwise comparison, the first response scores higher than the second
- **Confidence language bias:** "I am confident that..." scores higher than "I think..."

**Why this is catastrophic:**
If your LLM judge is surface-biased, then:
- Your evaluation results are noise-corrupted at the source
- You can't trust invariant-probe, covenant-keeper, or pressure-gauge results that use judge scoring
- Your prompt engineering will optimize for presentation, not quality
- Your A/B testing of model versions will pick the more verbose model, not the better model

**What exists today:**
- NO pip library produces JudgeSurfaceBias as a named, standalone metric
- NO tool generates controlled surface variants to isolate judge bias
- DeepEval, Braintrust, Langfuse, Arize: all USE judges but do not AUDIT them
- Anthropic's Petri (Nov 2025): measures sycophancy (judge agrees with incorrect statements) — ADJACENT but sycophancy ≠ surface bias. Petri = "does the judge agree with wrong human opinions?" judge-probe = "does the judge respond to formatting instead of content?" These are structurally distinct failure modes.
- G-Eval paper (Wang et al.): measures CoT scoring consistency of a specific judge protocol — DIFFERENT (CoT consistency ≠ surface presentation bias as independent variable)
- Braintrust judge calibration: compares LLM judge to human annotations on CONTENT quality — DIFFERENT (human-vs-LLM calibration ≠ surface-feature isolation test)

**Competitive Status:** GREEN — 8 tools audited (DeepEval, Braintrust, Promptfoo/OpenAI, Langfuse, Arize Phoenix, LangSmith, Anthropic Petri, G-Eval) — NONE implement JudgeSurfaceBias. Window: 4–6 months.

---

### THE BIBLICAL INSIGHT

John 7:24 is an EXPLICIT INSTRUCTION: "Stop judging by mere appearances, and instead judge correctly."

The structural context: the crowd judges circumcision on the Sabbath as lawful but healing on the Sabbath as unlawful. Both are purposeful bodily interventions on a human being on the Sabbath — structurally equivalent. The crowd is applying SURFACE CATEGORY ("sacred ritual" vs. "work") as the judgment criterion, which produces an INCONSISTENT verdict on structurally equivalent inputs.

Jesus names the failure mode precisely: judging by appearances (surface category / surface features) rather than correct judgment (structural equivalence / underlying principle).

This is exactly what LLM judge surface bias is: the judge assigns different verdicts to the same semantic content when it is presented with different surface features. The judge is responding to appearance, not substance.

The instruction provides the TEST DESIGN: hold semantic content constant, vary surface presentation, measure whether verdicts change. If they do — the judge is evaluating by appearances, not correctly.

**Why a Big Tech engineer would say "I never thought of it that way":**
"I've been using LLM judges as a black box to measure output quality. I never thought to TEST the judge itself for surface bias. The idea of holding semantic content constant and varying the presentation to isolate the judge's surface sensitivity — that's a completely new axis of measurement that I hadn't considered."

---

### THE API SPECIFICATION

#### Core Classes

```python
from judge_probe import JudgeProbe, JudgeConfig, JudgeReport

class JudgeConfig:
    judge_fn: Callable[[str, str], str]        # LLM judge function: (prompt, response) -> verdict
    n_variants_per_response: int = 5           # surface variants generated per response
    variant_strategies: List[str] = [          # which surface dimensions to vary
        "verbosity",     # compress/expand while preserving meaning
        "structure",     # bullet <-> paragraph
        "politeness",    # formal/confident opener vs. hedged opener
        "position",      # for pairwise: flip response order
        "confidence",    # "I am sure" vs. "I think" vs. "It may be"
    ]
    response_pairs: List[Tuple[str, str]]       # (prompt, gold_response) pairs to audit
    variant_model: str = "claude-3-haiku"       # LLM for variant generation
    embed_model: str = "all-MiniLM-L6-v2"     # for semantic similarity verification
    semantic_preservation_threshold: float = 0.85  # minimum cosine similarity to accept variant

class JudgeReport:
    judge_surface_bias: float                  # PRIMARY METRIC: variance in verdicts across surface variants (0-1)
    verdict_distribution: Dict[str, float]     # distribution of verdicts per variant type
    highest_bias_features: List[str]           # which surface features drive most variance
    semantic_preservation_verified: bool       # all variants passed semantic similarity check
    verdict: str                               # CALIBRATED | SURFACE_BIASED | HIGHLY_BIASED
    passed: bool                               # True if judge_surface_bias < threshold
    bias_heatmap: Dict[str, Dict]             # per-strategy bias scores
    sample_verdicts: List[Dict]               # examples of divergent verdicts for inspection
```

#### Primary Interface

```python
probe = JudgeProbe(config)
report = probe.audit(response_pairs)

# Full audit: generates variants, submits to judge, computes JudgeSurfaceBias
# Returns JudgeReport with all metrics
```

#### Key Methods

```python
# JudgeProbe methods
probe.audit(response_pairs) -> JudgeReport          # full audit
probe.quick_audit(prompt, response) -> float         # single-response quick check
probe.identify_bias_sources() -> Dict[str, float]   # which strategies drive most bias
probe.compare_judges(judge_a, judge_b) -> Dict      # compare surface bias between two judges
probe.generate_variants(response) -> List[str]       # expose variant generator for inspection

# SurfaceVariantGenerator (internal, also exposable)
generator.expand_verbosity(text) -> str
generator.compress_verbosity(text) -> str
generator.convert_to_bullets(text) -> str
generator.convert_to_paragraphs(text) -> str
generator.add_confident_opener(text) -> str
generator.add_hedged_opener(text) -> str
generator.flip_pairwise_order(response_a, response_b) -> Tuple[str, str]

# SemanticPreservationChecker (internal)
checker.verify(original, variant, threshold) -> bool  # cosine similarity gate
```

#### CLI Commands

```bash
# Full audit: test your LLM judge for surface bias
jprobe audit --judge claude-3-5-sonnet --responses responses.json

# Quick check: single response
jprobe quick --judge gpt-4o --prompt "What is X?" --response "X is Y..."

# CI gate: fail pipeline if judge_surface_bias > threshold
jprobe gate --judge claude-3-5-sonnet --responses responses.json --max-bias 0.15

# Compare two judges on same inputs
jprobe compare --judge-a claude-3-5-sonnet --judge-b gpt-4o --responses responses.json

# Show bias sources: which surface features drive the most variance
jprobe sources --judge claude-3-5-sonnet --responses responses.json

# Plot: bias heatmap by surface feature
jprobe plot --report report.json --output bias_heatmap.png
```

#### pytest Plugin

```python
# In conftest.py or test file
from judge_probe.pytest_plugin import probe_judge

def test_judge_not_surface_biased(judge_fn, response_pairs):
    @probe_judge(judge_fn, max_bias=0.15)
    def my_evaluation():
        return response_pairs

    my_evaluation()  # fails if JudgeSurfaceBias > 0.15
```

---

### THE ALGORITHM — JudgeSurfaceBias Computation

```
STEP 1: INPUT VALIDATION
  For each (prompt, response) in response_pairs:
    Verify response is non-empty and evaluable

STEP 2: VARIANT GENERATION
  For each strategy in variant_strategies:
    variant_response = SurfaceVariantGenerator.apply(strategy, response)
    semantic_sim = cosine_similarity(embed(response), embed(variant_response))
    if semantic_sim < semantic_preservation_threshold:
      REJECT variant (surface change altered meaning — regenerate)
    else:
      ACCEPT variant

STEP 3: JUDGE SUBMISSION
  For each accepted variant:
    verdict = judge_fn(prompt, variant_response)
    record: (strategy, variant_response, verdict)

STEP 4: BIAS COMPUTATION
  For each strategy:
    strategy_verdicts = [verdict for verdict in records where strategy == s]
    strategy_bias = variance(normalize_verdict(v) for v in strategy_verdicts)
  
  JudgeSurfaceBias = mean(strategy_bias for all strategies)
  
  Verdict thresholds:
    JudgeSurfaceBias < 0.10  → CALIBRATED
    0.10 <= bias < 0.20       → SURFACE_BIASED (warning)
    bias >= 0.20              → HIGHLY_BIASED (fail)

STEP 5: FEATURE ATTRIBUTION
  highest_bias_features = sorted strategies by strategy_bias, descending
  Report: which feature drives the most surface sensitivity

STEP 6: SEMANTIC PRESERVATION AUDIT
  Report whether ALL variants passed semantic similarity check
  If some variants rejected: flag as partial audit
```

**Key Design Principle:**
The semantic preservation check is critical — it ensures that variant generation did not accidentally change the meaning of the response (which would make verdict changes appropriate, not biased). By verifying cosine similarity >= threshold before including a variant, judge-probe guarantees: VARIANT MEANING ≈ ORIGINAL MEANING. Therefore: any verdict change = SURFACE BIAS.

---

### DIFFERENTIATION MATRIX

| Tool | What It Measures | judge-probe vs. |
|------|-----------------|-----------------|
| DeepEval | Output quality (50+ metrics, per-invocation) | USES judge but doesn't audit it — ORTHOGONAL |
| Braintrust | LLM-vs-human calibration on CONTENT quality | Content calibration ≠ surface bias isolation — COMPLEMENTARY |
| Anthropic Petri | Sycophancy (agrees with incorrect statements) | Sycophancy = agreeing-with-wrong-humans ≠ surface presentation bias — COMPLEMENTARY |
| G-Eval | CoT scoring consistency for NLG evaluation | CoT consistency ≠ surface feature isolation — DIFFERENT |
| Promptfoo/OpenAI | Security/adversarial testing (offense-focused) | Offense testing ≠ judge auditing — DIFFERENT |
| LangSmith | Tracing + human annotation on execution | Execution tracing ≠ judge behavior audit — DIFFERENT |
| Arize Phoenix | Output quality scoring + monitoring | Monitoring ≠ judge surface audit — DIFFERENT |
| Langfuse | Observability + tracing + prompt management | Observability ≠ judge surface audit — DIFFERENT |

**One-Sentence Differentiation (without mentioning Bible):**
judge-probe is the only tool that audits whether your LLM judge is responding to surface presentation features — length, formatting, politeness, position — rather than actual content quality.

---

### KNOWN UNKNOWNS (KU-076 through KU-079)

**KU-076:** How many response pairs are needed for stable JudgeSurfaceBias estimates? Preliminary estimate: 10-20 pairs per judge audit for 95% CI stability. Needs empirical validation.

**KU-077:** Do different LLM judges have characteristically different surface bias profiles? Hypothesis: larger models = lower surface bias. GPT-4o vs. Claude-3-Haiku bias comparison needed.

**KU-078:** Can judge-probe surface variants be generated reliably enough? Semantic preservation threshold = 0.85 may reject too many variants if model generates poor variants. Empirical testing needed.

**KU-079:** Does JudgeSurfaceBias compound when judges are chained? (Judge A's output used as input to Judge B's evaluation.) Chained judge bias may be multiplicative, not additive. Needs investigation.

---

### SPRINT PLAN — 6 WEEKS TO PIP-PUBLISHABLE v0.1

**Week 1:** Core variant generator (verbosity + structure variants). SemanticPreservationChecker. Unit tests for variant generation quality.

**Week 2:** JudgeRunner — submit variants to LLM judge, collect verdicts. Verdict normalization (map free-text verdicts to scalar scores). Core JudgeSurfaceBias computation algorithm.

**Week 3:** JudgeProbe class. JudgeConfig + JudgeReport dataclasses. Position bias test (pairwise flip). Confidence language variants. Full algorithm integration.

**Week 4:** CLI implementation (jprobe audit/quick/gate/compare/sources/plot). Matplotlib bias heatmap. pytest plugin.

**Week 5:** Integration testing against real judges (GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro). Threshold calibration. Known unknown KU-076 (sample size stability) empirical validation.

**Week 6:** README + documentation. PyPI packaging (setup.py / pyproject.toml). pip install judge-probe test. GitHub release. Hacker News Show HN post.

**Dependencies:** sentence-transformers, anthropic SDK, openai SDK (optional), click, rich, numpy, matplotlib, pyyaml, pytest (optional)
**Capital Required:** ZERO

---

### observer-probe SPRINT WEEK 1 STATUS (BUILD-025 — Parallel Track)

**Status:** Sprint initiated this cycle. Following the 6-week plan documented in BUILD-025.

Week 1 deliverable: ProbeRunner core + BiasScorer foundation.
- ProbeRunner: executes agent task prompts under eval-evident and production-evident system context templates
- BiasScorer: computes pairwise cosine similarity of eval-mode vs. prod-mode outputs, returns ObservabilityBias = 1 - mean(cosine_similarity)
- ContextTemplateLibrary stub: 3 eval-evident templates + 3 production-evident templates documented

**Concurrent sprint design:** Both judge-probe (new, 6 weeks) and observer-probe (continuing, weeks 1-2 of 6) can be run simultaneously by a solo builder. Different focus areas: judge-probe = judge auditing; observer-probe = agent context-mode sensitivity. No code overlap. Total sprint load: 2 parallel 6-week sprints = feasible for solo builder at 20hrs/week each.

---

*Filed by: Chief Builder (Senior) | Innovation Build Director | Chief Engineer*
*Cycle: 026 | Date: 2026-04-08*
