# BibleWorld Cycle 023 — Builds
## BUILD Cycle | 2026-04-01

---

## BUILD-023: pressure-gauge

**Pattern Source:** PAT-078 (Daniel 5:5-6, 27 — The TEKEL Pressure Drift Pattern)
**Build Type:** SOFTWARE — Developer Testing Library (Python, pip-installable)
**Build Score:** 9.1/10
**Pivot_Score:** 8.65

---

### Problem Statement

Long-running LLM agents exhibit a documented behavioral change pattern as their context window fills — named "context anxiety" in 2026 developer literature. The behavior change includes:

1. **Premature wrapping:** Agent declares the task complete when it is not, to avoid continued operation near context limits
2. **Rushed steps:** Multi-step processes are compressed or skipped as fill level rises
3. **False completion signals:** Agent emits "done" markers prematurely
4. **Altered reasoning quality:** The model's reasoning becomes more superficial, less careful, more convergent as fill rises
5. **Behavioral inconsistency with baseline:** The same query, run at 80% fill, produces a structurally different response than the same query at 10% fill

**This is documented at production scale:**
- Inkeep.com (2026): "Context anxiety shows up as the context window fills up. The model does not just lose coherence. It changes behavior. It may start wrapping up prematurely. It may rush steps. It may declare that something is done when it is not." [WEB-FRESH 2026-04-01]
- Anthropic's Blueprint for Long-Running AI Agents (2026): identifies context window management as a primary reliability challenge; Anthropic SDK added auto-compaction but notes behavior still changes [WEB-FRESH 2026-04-01]
- agentic-patterns.com — "Context Window Anxiety Management" is listed as a named agentic design pattern in 2026 [WEB-FRESH 2026-04-01]
- Every AI agent experiences performance degradation after 35 minutes of human time; LLMs declare work done even when it is not [WEB-FRESH 2026-04-01]

**Why no existing tool measures this:**
- **Langfuse:** records what happened in each span — cannot compare behavior at 20% fill vs. 80% fill
- **Arize Phoenix:** scores individual output quality — cannot produce ContextPressureScore across fill levels
- **invariant-probe:** tests behavioral invariance under ENVIRONMENTAL perturbations (time shift, env var, latency) — NOT context fill progression (different dimension, different mechanism)
- **session-lens:** tests session memory fidelity — NOT whether the model's current-step behavior changes as fill rises
- **livelock-probe:** detects zero-progress across steps — NOT behavioral drift per se (a model in context anxiety is making progress but the QUALITY and CHARACTER of its behavior is drifting)
- **DeepEval, Braintrust:** score output quality per invocation — cannot produce fill-level comparative drift curves
- **W&B Weave:** experiment tracking — cannot run controlled fill-level sweep and compute drift

**The gap is structural:** No tool runs a controlled experiment: "Run the same agent task at 10%, 30%, 50%, 70%, 90% fill levels. Embed each output. Compute behavioral similarity to baseline (10% fill). Report where drift begins and how severe it gets." This is the ContextPressureScore and ContextDriftCurve that pressure-gauge produces.

**Documented gap:** Named by researchers, undressed by tools. This is the canonical definition of a GREEN competitive window.

---

### Core Innovation

**ContextPressureScore** — A scalar metric (0.0 to 1.0) measuring mean behavioral similarity of an agent's outputs at varying context fill levels relative to baseline behavior at low fill. High score = behavior stable under context pressure. Low score = significant behavioral drift as context fills.

**ContextDriftCurve** — A plot/report of cosine similarity at each fill level interval (10%, 20%, ..., 90%) showing the SHAPE of behavioral drift. Some models drift suddenly at 70%; others drift linearly from 30%. The drift curve reveals the pressure onset threshold.

**pressure_onset_token** — The context token count at which behavioral similarity drops below the configurable stability threshold. This is the "TEKEL moment" — where the model begins to fail its own standard.

---

### API Design

```python
from pressure_gauge import PressureGauge, PressureConfig, PressureReport, pressure_sweep

# === Core Classes ===

class PressureConfig:
    fill_levels: list[float] = [0.10, 0.30, 0.50, 0.70, 0.90]
    # Fill levels to test (fraction of max_context_tokens)
    max_context_tokens: int                     # model's max context (4096, 8192, 128000, etc.)
    baseline_fill: float = 0.10                 # low-fill baseline to compare against
    stability_threshold: float = 0.85           # min cosine similarity = stable behavior
    model: str = "all-MiniLM-L6-v2"            # sentence-transformer for embedding
    runs_per_level: int = 3                     # runs at each fill level (averaging)
    pad_strategy: Literal["repeat_text", "inject_history", "lorem_ipsum"] = "inject_history"
    # inject_history: pad with realistic conversation history (most ecologically valid)
    # repeat_text: pad with repeated neutral text (fast, less realistic)
    # lorem_ipsum: pad with Lorem Ipsum (fast, clearly artificial)
    task_prompt: str                            # the task to run at each fill level
    agent_fn: Callable[[str], str]              # function wrapping the agent call
    criticality: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = "HIGH"

class PressureReport:
    context_pressure_score: float               # 0.0 (no drift) to 1.0 (total drift)
    # NOTE: low score = HIGH drift; convention is inverted from invariant-probe
    # ContextPressureScore = 1.0 - mean cosine drift across fill levels
    # So 1.0 = perfectly stable, 0.0 = completely different behavior at high fill
    pressure_stability_score: float             # mean cosine similarity across levels (alias)
    pressure_onset_token: int | None            # token count where drift begins (None = no drift)
    pressure_onset_fill: float | None           # fill level fraction where drift begins
    drift_curve: list[DriftPoint]               # one DriftPoint per fill level
    passed: bool                                # True if pressure_stability_score >= stability_threshold
    baseline_fill: float                        # which fill level was used as baseline
    worst_fill_level: float                     # fill level with lowest similarity to baseline
    worst_similarity: float                     # cosine similarity at worst fill level
    summary: str                                # human-readable interpretation

class DriftPoint:
    fill_level: float                           # 0.10, 0.30, etc.
    fill_tokens: int                            # actual token count
    similarity_to_baseline: float              # cosine similarity vs. baseline outputs
    samples: int                               # how many runs averaged
    representative_output: str                 # truncated sample output at this fill level


# === Core Function ===

def pressure_sweep(
    config: PressureConfig
) -> PressureReport:
    """
    Run a controlled pressure sweep:
    1. For each fill_level in config.fill_levels:
       a. Pad context to fill_level * max_context_tokens using pad_strategy
       b. Append task_prompt
       c. Run agent_fn config.runs_per_level times
       d. Embed each output using sentence-transformer
       e. Average embeddings
    2. Compute cosine similarity of each fill_level's embedding vs. baseline_fill embedding
    3. Compute ContextPressureScore = mean of all similarities
    4. Compute pressure_onset_token = first token count where similarity < stability_threshold
    5. Return PressureReport
    """


# === Convenience Class ===

class PressureGauge:
    def __init__(self, config: PressureConfig): ...

    def sweep(self) -> PressureReport:
        """Run full pressure sweep. Equivalent to pressure_sweep(config)."""

    def quick_check(self, fill_levels: list[float] = [0.10, 0.90]) -> PressureReport:
        """Fast two-point check: baseline vs. worst case. Good for CI."""

    def onset_search(self, resolution: float = 0.10) -> tuple[float, int]:
        """Binary search for pressure_onset_fill. Returns (onset_fill, onset_token)."""


# === Decorator ===

def pressure_probe(
    fill_levels: list[float] = [0.10, 0.30, 0.50, 0.70, 0.90],
    stability_threshold: float = 0.85,
    max_context_tokens: int = 8192,
    criticality: str = "HIGH"
):
    """
    Decorator for agent functions. Auto-runs pressure sweep before first real call.
    Raises PressureDriftError if stability check fails.

    @pressure_probe(fill_levels=[0.10, 0.50, 0.90], stability_threshold=0.88)
    def my_agent(prompt: str) -> str:
        return client.messages.create(...).content[0].text
    """
```

---

### CLI Design

```bash
# Install
pip install pressure-gauge

# Run a pressure sweep
pgauge run \
    --agent "python my_agent.py" \
    --task "Summarize the status of the project and list next steps" \
    --max-tokens 8192 \
    --fill-levels 0.1,0.3,0.5,0.7,0.9 \
    --pad-strategy inject_history \
    --output report.json

# Display last report
pgauge show

# Gate for CI (exit code 1 if drift detected)
pgauge gate --min-pressure-stability 0.85

# Plot drift curve (saves PNG)
pgauge plot --output drift_curve.png

# Quick two-point check (baseline vs. 90% fill only)
pgauge quick --fill-low 0.1 --fill-high 0.9

# Onset search — find the fill level where drift begins
pgauge onset --resolution 0.05

# Estimate API cost before running full sweep
pgauge estimate --max-tokens 8192 --model claude-3-5-haiku --runs 3
```

---

### pytest Plugin

```python
# In conftest.py or test file:
import pytest
from pressure_gauge.pytest_plugin import pressure_stability

@pressure_stability(
    fill_levels=[0.10, 0.50, 0.90],
    min_stability=0.85,
    max_context_tokens=8192,
    task="Explain the current state of the system"
)
def test_agent_pressure_stability(agent_fn):
    """Agent should behave consistently regardless of context fill level."""
    # pressure_gauge auto-runs the sweep; test passes if stability >= 0.85
    pass


# Or use assert style:
def test_my_agent_stable_under_pressure():
    from pressure_gauge import PressureGauge, PressureConfig

    config = PressureConfig(
        max_context_tokens=8192,
        task_prompt="What is the current task status?",
        agent_fn=my_agent,
        stability_threshold=0.85
    )
    gauge = PressureGauge(config)
    report = gauge.quick_check()

    assert report.passed, (
        f"Agent failed pressure stability check. "
        f"Stability score: {report.pressure_stability_score:.3f} "
        f"(threshold: 0.85). "
        f"Drift onset at {report.pressure_onset_fill:.0%} fill "
        f"({report.pressure_onset_token:,} tokens)."
    )
```

---

### ContextPressureScore Algorithm

```
ALGORITHM: ContextPressureScore

INPUT:
  agent_fn: the agent to test
  fill_levels: [0.10, 0.30, 0.50, 0.70, 0.90] (or user-defined)
  baseline_fill: 0.10
  max_context_tokens: 8192
  runs_per_level: 3
  task_prompt: the test task
  embed_model: sentence-transformer model

STEP 1 — Baseline generation:
  pad_tokens = int(baseline_fill * max_context_tokens) - len(task_prompt_tokens)
  context = pad(pad_tokens) + task_prompt
  Run agent_fn(context) × runs_per_level
  baseline_embeddings = embed(outputs)
  baseline_vector = mean(baseline_embeddings)

STEP 2 — Fill level sweep:
  For each fill_level in fill_levels (excluding baseline_fill):
    pad_tokens = int(fill_level * max_context_tokens) - len(task_prompt_tokens)
    context = pad(pad_tokens) + task_prompt
    Run agent_fn(context) × runs_per_level
    level_embeddings = embed(outputs)
    level_vector = mean(level_embeddings)
    similarity[fill_level] = cosine_similarity(level_vector, baseline_vector)

STEP 3 — Score computation:
  pressure_stability_score = mean(similarity.values())
  context_pressure_score = 1 - pressure_stability_score  # drift magnitude

  # Onset detection:
  sorted_levels = sorted(fill_levels)
  pressure_onset_fill = first fill_level where similarity[fill_level] < stability_threshold
  pressure_onset_token = pressure_onset_fill * max_context_tokens

STEP 4 — Report:
  Return PressureReport with all fields populated

COST ESTIMATE:
  calls = len(fill_levels) × runs_per_level = 5 × 3 = 15 API calls per sweep
  tokens_per_call ≈ max_context_tokens × fill_level (average ~50% fill) ≈ 4,096 tokens
  total_tokens ≈ 15 × 4,096 = ~61,000 tokens per sweep
  cost at Claude 3.5 Haiku pricing ($0.80/$4.00 per MTok) ≈ $0.05 per sweep
  cost at GPT-4o mini pricing ($0.15/$0.60 per MTok) ≈ $0.01 per sweep

NOTE: Use pgauge estimate before running to get model-specific cost estimate.
```

---

### Padding Strategy Details

The quality of padding affects ecological validity. Three strategies:

**inject_history (RECOMMENDED):**
Generate a realistic conversation history of increasing length. For each fill level, inject `N` prior turns of synthetic conversation history matching the domain. This most closely simulates real long-running agent conditions (accumulated conversation history, prior tool calls, prior reasoning).
```python
# Example injected history (N turns based on required token count)
[
    {"role": "user", "content": "What is the status of step 1?"},
    {"role": "assistant", "content": "Step 1 is complete. The output is X."},
    {"role": "user", "content": "Proceed to step 2."},
    {"role": "assistant", "content": "Beginning step 2. Analyzing Y..."},
    ...  # as many turns as needed to reach fill_level
]
```

**repeat_text (FAST):**
Pad with repeated neutral text (e.g., "The system is operating normally." × N). Less ecologically valid but deterministic and fast for quick checks.

**lorem_ipsum (CONTROL):**
Pad with Latin filler text. Most clearly artificial. Useful as a control condition to distinguish genuine context-anxiety from injection-type effects.

---

### Interpreting Results

| pressure_stability_score | Interpretation | Action |
|--------------------------|---------------|--------|
| >= 0.95 | Excellent stability | No action needed |
| 0.90 – 0.95 | Good stability | Monitor; acceptable for most use cases |
| 0.85 – 0.90 | Moderate stability | Consider context management strategies |
| 0.75 – 0.85 | Significant drift | Implement context compaction; add sub-task checkpoints |
| < 0.75 | Severe context anxiety | Redesign agent for shorter context windows or add mid-task resets |

**Criticality-based thresholds:**
- CRITICAL (medical, legal, financial): min_stability >= 0.95
- HIGH (production agents): min_stability >= 0.88
- MEDIUM (development/testing): min_stability >= 0.80
- LOW (exploratory): min_stability >= 0.70

---

### Sprint Plan — 6 Weeks to pip-publishable v0.1

**Week 1: Core algorithm + CLI skeleton**
- Implement ContextPressureScore algorithm
- Implement three padding strategies
- Implement basic CLI: pgauge run / pgauge show
- Tests for algorithm correctness on mock outputs
- pyproject.toml, README.md with "tekel" framing removed (public API uses "context stability" language)

**Week 2: PressureReport + output formats**
- Full PressureReport class with all fields
- DriftPoint series
- JSON output
- Rich terminal table output (matching invariant-probe/livelock-probe style)
- pgauge gate command with configurable threshold

**Week 3: PressureGauge class + decorators**
- PressureGauge.sweep() and quick_check()
- onset_search() binary search
- @pressure_probe decorator
- Error handling: PressureDriftError, PressureConfigError

**Week 4: pytest plugin + drift curve plotting**
- pytest plugin (pressure_stability fixture)
- pgauge plot command (matplotlib curve, PNG export)
- pgauge estimate command (cost estimation before run)
- Integration tests with real Claude API calls

**Week 5: padding quality + documentation**
- inject_history padding with domain-aware generation
- Documentation: README, API reference, usage examples
- Comparison guide: pressure-gauge vs. invariant-probe vs. livelock-probe (clear differentiation)
- PyPI package preparation

**Week 6: hardening + publication**
- Edge cases: very short context windows, agents that refuse to answer at high fill, padding that affects task semantics
- CI/CD examples (GitHub Actions workflow)
- Version 0.1.0 release to PyPI
- HackerNews Show HN post
- Dev.to tutorial post

**Total: 6 weeks to pip-publishable v0.1**

---

### Known Unknowns (KU-064 through KU-067)

**KU-064:** Does the padding strategy (inject_history vs. repeat_text vs. lorem_ipsum) produce significantly different ContextPressureScore values for the same model? If inject_history and repeat_text give very different scores, which is the "true" measure of context anxiety? Study needed.

**KU-065:** Context auto-compaction (Anthropic SDK feature, 2026) reduces the effective fill level experienced by the model. How should pressure-gauge handle agents that use auto-compaction? Does compaction eliminate context anxiety, or does it change its character?

**KU-066:** Different models exhibit different context anxiety onset thresholds. At what fill_level does Sonnet 4.5 exhibit context anxiety vs. Opus 4.6 (1M context window, reportedly less anxiety)? Should pressure-gauge include a model baseline library?

**KU-067:** Task type affects context anxiety severity — summarization tasks may be less affected than multi-step planning tasks. How to design task prompts that are maximally diagnostic for context anxiety? What task types produce the most signal?

---

### Competitive Differentiation Matrix

| Tool | What It Measures | Perturbation Type | pressure-gauge's Difference |
|------|-----------------|-------------------|----------------------------|
| invariant-probe | Behavioral change under environmental perturbations | External (time, env vars, latency) | pressure-gauge measures internal context fill pressure, not external environment |
| livelock-probe | Progress toward goal (zero vs. non-zero) | N/A (structural analysis) | pressure-gauge measures behavioral CHARACTER change, not progress magnitude |
| session-lens | Session memory fidelity | N/A (recall accuracy) | pressure-gauge measures current-step behavioral drift, not historical recall accuracy |
| context-trace | Which context chunks drive which outputs | N/A (attribution) | pressure-gauge measures how behavior changes as context fills, not which chunks matter |
| Langfuse | Execution tracing | N/A | pressure-gauge requires controlled experiment; Langfuse records what happened |
| Arize Phoenix | Output quality scoring | N/A | pressure-gauge produces comparative fill-level drift, not absolute quality |
| DeepEval | Multi-metric evaluation | N/A | pressure-gauge produces fill-level comparative measurement, not metric scoring |

**One-sentence differentiation (no Bible required):** pressure-gauge is the first tool that measures how an AI agent's behavior changes as its context window fills — detecting the point where context pressure begins to alter the agent's outputs relative to its low-fill baseline.

---

### Why This Is Acquisition-Ready

1. **Anthropic acquired Humanloop** (evaluation/trust) and **Vercept** (computer-use agent reliability) — both in the reliability/evaluation space. pressure-gauge addresses a gap in the Claude Code and long-running agent ecosystem that Anthropic explicitly acknowledges in their 2026 documentation.

2. **Context anxiety is growing, not shrinking.** Even as context windows expand (Opus 4.6 at 1M tokens), long-running agents use more context. The problem scales with agent capability.

3. **YC RFS 2026 specifically calls out AI testing and debugging.** pressure-gauge is directly in the YC-funded zone.

4. **OpenAI acquired Promptfoo** (LLM security testing), **Neptune** (ML experiment tracking), **Astral** (developer tooling). The pattern: open-source developer tools with GitHub stars get acquired. pressure-gauge is designed for exactly this acquisition funnel.

5. **Solo-buildable in 6 weeks.** Zero capital required. Same dependency stack as invariant-probe and livelock-probe.

---

### Build Metadata

**pip name:** pressure-gauge
**PyPI command:** pip install pressure-gauge
**CLI name:** pgauge
**Core metric:** ContextPressureScore / pressure_stability_score
**Core innovation:** First tool to produce ContextDriftCurve and pressure_onset_token for LLM agents
**Capital required:** ZERO
**Dependencies:** sentence-transformers, anthropic/openai SDK, click, rich, numpy, matplotlib, pyyaml, pytest (optional)
**Sprint required:** 6 weeks to pip-publishable v0.1
**Agent responsible:** Chief Builder (Senior Agent)
**Competitive moat:** GREEN [WEB-FRESH 2026-04-01]
**Build score:** 9.1/10
**Pivot_Score:** 8.65/10
