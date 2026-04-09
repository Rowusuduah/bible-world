# BibleWorld Cycle 027 — Builds
## BIG_TECH_GAP_ANALYSIS | Target: Anthropic | 2026-04-09

**Cycle:** 027
**Date:** 2026-04-09
**Primary Build:** BUILD-027 — claim-probe (Pivot_Score 8.15)
**Secondary Build Identified:** refine-probe (Pivot_Score 8.05 — design target cycle 028)
**Build Status:** claim-probe IN-DESIGN (full spec below)

---

## BUILD-027: claim-probe [PIVOT-PHASE CYCLE 027]

### Overview
**Pattern Source:** PAT-095 (Daniel 7:8,11 — The Boastful Horn Pattern) + Matthew 21:28-32 (Parable of Two Sons — independent validation)
**Build Type:** SOFTWARE — Developer Testing Library (Python, pip-installable)
**Pivot_Score:** 8.15/10 — PASSES 7.0 THRESHOLD

---

### The Problem

AI agents in production routinely self-report their output quality, completion status, and confidence level. In multi-agent orchestration systems (Anthropic Three-Agent Harness, LangGraph, AutoGen), sub-agents communicate their completion state to orchestrators via self-reports. These self-reports are trusted at face value.

**The documented gap:** No tool measures whether an agent's self-report is calibrated against its actual quality. Anthropic's Three-Agent Harness documentation (InfoQ April 2026) explicitly lists "premature task termination" as a design challenge — this is ClaimFidelityScore failure in its most operationally costly form. An agent declares "done" before it is actually done, and the orchestrator proceeds on false information.

**Evidence from multiple independent sources:**
1. Anthropic Three-Agent Harness (InfoQ April 2026): "premature task termination"
2. PYMNTS April 2026: agents running $1-5K of compute unmonitored on $200 plans — self-reports are the only completion signal
3. arXiv 2601.23045: incoherence scales with reasoning length — longer agents = worse self-report calibration
4. Towardsdatascience "Prompt Fidelity" (2026): agents operate on 75% unverified inference but report it all as equivalent quality
5. Parable of Two Sons (Matthew 21:28-32): commitment-action gap is the mechanism; verbal compliance ≠ behavioral compliance

---

### How claim-probe Works

**Core Algorithm:**
```python
ClaimFidelityScore = independent_eval_score - agent_self_report_score
```

**Step 1:** Run agent on task_prompt → get agent_output
**Step 2:** Ask agent to self-rate its output: "Rate the quality of your previous response on a scale of 0-10. Reply with only a number." → get self_report_score
**Step 3:** Run independent evaluator (LLM judge or human) on (agent_output, task_prompt) → get eval_score
**Step 4:** ClaimFidelityScore = eval_score - self_report_score
- ClaimFidelityScore > 0.2: OVERCONFIDENT (claims exceed actual quality)
- ClaimFidelityScore < -0.2: UNDERCONFIDENT (claims below actual quality)
- -0.2 ≤ ClaimFidelityScore ≤ 0.2: CALIBRATED

**Aggregate across N samples:** ClaimFidelityDistribution, CalibrationError = mean(|ClaimFidelityScore|)

---

### API Specification

```python
from claim_probe import ClaimProbe, ClaimConfig, ClaimReport

# Initialize
config = ClaimConfig(
    agent_fn=my_agent,          # callable: prompt -> str
    eval_fn=my_evaluator,       # callable: (output, prompt) -> float [0-10]
    n_samples=20,               # number of task prompts to test
    overconfidence_threshold=0.2,
    underconfidence_threshold=-0.2,
    self_report_prompt="Rate the quality of your previous response (0-10, number only):",
)

probe = ClaimProbe(config)
report: ClaimReport = probe.measure(task_prompts)

# Report fields
report.claim_fidelity_score        # float: mean gap
report.calibration_error           # float: mean absolute gap
report.verdict                     # "CALIBRATED" | "OVERCONFIDENT" | "UNDERCONFIDENT"
report.passed                      # bool: True if |claim_fidelity_score| <= threshold
report.fidelity_distribution       # list[float]: per-sample gaps
report.top_overconfident_samples   # list[dict]: worst overconfidence examples
report.top_underconfident_samples  # list[dict]: worst underconfidence examples
report.calibration_curve           # list[dict]: binned reliability plot data
```

---

### CLI Specification

```bash
# Full audit
cprobe audit --agent my_agent.py --eval my_eval.py --tasks tasks.json

# Quick single task
cprobe quick --agent my_agent.py --eval my_eval.py --prompt "Summarize this document"

# CI gate (returns exit code 0/1)
cprobe gate --max-overconfidence 0.2 --max-calibration-error 0.15

# Compare two agents' calibration
cprobe compare --agent-a agentA.py --agent-b agentB.py --tasks tasks.json

# Plot calibration curve
cprobe plot --report report.json --output calibration_curve.png

# Show current metrics
cprobe show --report report.json
```

---

### pytest Plugin

```python
from claim_probe.pytest_plugin import claim_test

@claim_test(
    agent_fn=my_agent,
    eval_fn=my_evaluator,
    task_prompts=TASK_PROMPTS,
    max_overconfidence=0.2,
    max_calibration_error=0.15,
)
def test_agent_claim_calibration():
    pass  # claim_test decorator handles execution and assertion
```

---

### Competitive Differentiation Matrix

| Tool | What it measures | claim-probe gap |
|------|-----------------|-----------------|
| AgentRx (Microsoft Research) | Root cause of agent crash (post-hoc) | Different: claim-probe measures calibration continuously, not post-crash |
| SkillFortify (HN Feb 2026) | Formal verification of agent skills | Different: skill correctness ≠ self-report calibration |
| DashClaw (HN Mar 2026) | Intercept agent decisions before execution | Different: authorization/governance layer, not self-report measurement |
| Agent Arena (HN Feb 2026) | Manipulation-proofness of agent | Different: adversarial robustness ≠ calibration |
| Langfuse | Execution tracing and logging | Different: tracing infrastructure, not calibration scoring |
| DeepEval | Output quality evaluation | Different: evaluates output quality; claim-probe measures gap between self-report and that evaluation |
| Braintrust | LLM evaluation and comparison | Different: human-vs-LLM calibration on CONTENT; claim-probe measures agent SELF-REPORT vs. evaluation |
| Anthropic Petri | Sycophancy measurement | Different: Petri = agreeing with incorrect statements; claim-probe = self-report calibration gap |

**ClaimFidelityScore is unoccupied.** No PyPI package, no research paper with that exact metric name, no tool measuring it. **GREEN.**

---

### Sprint Plan

**Week 1-2: Core algorithm + data collection**
- Implement ClaimProbe.measure() with basic agent_fn + eval_fn interface
- Self-report extraction (simple prompt injection: "Rate your response 0-10")
- ClaimFidelityScore computation (single sample)
- Basic ClaimReport dataclass

**Week 3: Multi-sample aggregation + statistics**
- CalibrationError (mean absolute gap)
- ClaimFidelityDistribution (full sample distribution)
- CALIBRATED / OVERCONFIDENT / UNDERCONFIDENT verdict logic
- CalibrationCurve (binned reliability plot, like meteorological calibration plots)

**Week 4: CLI + CI gate**
- `cprobe audit` / `quick` / `gate` / `compare` / `plot` / `show`
- Exit code 0/1 for CI integration
- JSON report output

**Week 5: pytest plugin + polish**
- `@claim_test` decorator
- README with Claude Code use case example
- PyPI publishing

**Total Sprint:** 4-5 weeks to pip-publishable v0.1
**Kill Gate 3 Feasibility:** YES (42 days remaining as of 2026-04-09, 4-5 weeks = 28-35 days — within window)

---

### Capital Required
ZERO
- anthropic / openai SDK (optional — any callable agent_fn works)
- sentence-transformers (optional — for semantic self-report extraction)
- click (CLI)
- rich (terminal output)
- numpy (statistics)
- matplotlib (calibration curve plotting)
- pyyaml (config)
- pytest (optional plugin)

---

### Known Unknowns (KU-080 through KU-083)

**KU-080:** What self-report prompt formulation produces the most stable and honest self-reports? Hypothesis: simple direct ("Rate your output 0-10") outperforms complex ("On a scale from poor to excellent..."). Empirical validation needed across 3 formulations.

**KU-081:** Do agents show characteristically different ClaimFidelityScore profiles by task type? Hypothesis: agents are more overconfident on creative tasks and better calibrated on factual tasks. Empirical validation needed across 4 task categories (factual, creative, reasoning, code).

**KU-082:** Does ClaimFidelityScore compound in multi-agent chains? If Agent A has ClaimFidelityScore +0.2 (overconfident) and passes to Agent B which also has +0.2, does the orchestrator receive a compounded false signal? Hypothesis: YES — each link compounds. Design implication: claim-probe should be run per-agent, not only on final output.

**KU-083:** Do larger models (Opus) have better self-report calibration than smaller models (Haiku)? Hypothesis: YES — larger models are more calibrated. Empirical test: run ClaimFidelityScore across Haiku/Sonnet/Opus on identical tasks. Expected finding: Haiku most overconfident, Opus most calibrated.

---

### Acquisition Target Analysis

**Primary:** Anthropic
- Humanloop acquisition thesis: "AI trust and evaluation" — claim-probe extends to agent self-report trust
- Vercept acquisition: computer-use agent capabilities — claim-probe needed upstream of any deployed agent
- Three-Agent Harness documentation explicitly names "premature task termination" as design challenge
- claim-probe solves it with a named metric and CI gate

**Secondary:** Google
- DeepMind multi-agent research (Windsurf acqui-hire shows agent investment)
- Google evaluation toolchain growing rapidly (Constitutional AI equivalent)

**Tertiary:** Microsoft
- AgentRx is post-crash; claim-probe is pre-crash — complementary, not competing
- Agent Governance Toolkit (April 2026) shows Microsoft actively building agent reliability tools

---

## BUILD PIPELINE STATUS — POST CYCLE 027

| Build | Pattern | Pivot_Score | Sprint | Status |
|-------|---------|-------------|--------|--------|
| judge-probe | PAT-094 (John 7:24) | 9.00 | 4-6 wks | ACTIVE SPRINT |
| observer-probe | PAT-086 (Psalm 10) | 8.955 | 6 wks | ACTIVE SPRINT |
| pressure-gauge | PAT-078 (Daniel 5) | 8.65 | 6 wks | IN-DESIGN |
| cot-fidelity | PAT-059 (Genesis 3) | 8.85 | 8 wks | IN-DESIGN |
| semantic-pass-k | PAT-062 (Numbers 23) | 8.65 | 6 wks | IN-DESIGN |
| covenant-keeper | PAT-082 (Daniel 6) | 8.30 | 6 wks | IN-DESIGN |
| context-trace | PAT-068 (John 3) | 8.225 | 6 wks | IN-DESIGN |
| livelock-probe | PAT-075 (John 5) | 8.175 | 5 wks | IN-DESIGN |
| invariant-probe | PAT-070 (Genesis 7) | 8.175 | 6 wks | IN-DESIGN |
| session-lens | PAT-071 (John 4) | 7.90 | 5 wks | IN-DESIGN |
| **claim-probe** | **PAT-095 (Daniel 7)** | **8.15** | **4-5 wks** | **DESIGNED this cycle** |
| refine-probe | PAT-097 (Psalm 12:6) | 8.05 | 4-5 wks | CYCLE 028 DESIGN TARGET |
| internal-spring | PAT-098 (John 7:37) | 7.475 | 6 wks | CYCLE 029 WATCH |

**SPRINT PRIORITY:** judge-probe (4-6 weeks, Kill Gate 3 feasible). observer-probe parallel. claim-probe and refine-probe queued after.
