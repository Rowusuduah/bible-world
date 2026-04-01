# BibleWorld Cycle 022 — Builds
## PATTERN_DISCOVERY | 2026-04-01

---

## BUILD-022: livelock-probe

**Pattern Source:** PAT-075 (John 5:5-9 — The 38-Year Stuck State Pattern)
**Build Type:** SOFTWARE — Developer Testing Library (Python, pip-installable)
**Build Score:** 9.0/10
**Pivot_Score:** 8.175

---

### Problem Statement

AI agents deployed in production enter STRUCTURALLY STUCK states where they are actively working but making zero net progress. These livelock states are invisible to standard monitoring: no error is thrown, no timeout fires, spans complete "successfully," and the agent appears healthy. The only signal is: token budget consumed without task completion, or indefinite wall-clock time without result.

**Concrete instances documented:**
1. **Claude Code quota exhaustion (The Register, 2026-03-31):** Anthropic acknowledged "people are hitting usage limits in Claude Code way faster than expected." The most common cause is retry loops — agents in livelock consuming tokens without making progress.
2. **RAG retrieval livelock:** Agent receives retrieval results below its quality threshold. Retries. Gets similar results below threshold. Retries indefinitely. Each retrieval call "succeeds" (HTTP 200). No error.
3. **Multi-agent coordination livelock:** Agent A waits for Agent B's output. Agent B waits for Agent A's confirmation. Neither proceeds.
4. **Evaluation loop livelock:** Agent self-evaluates output against criteria. Output passes some criteria, fails others. Agent revises. New output passes different criteria, fails others. Loop until context window exhaustion.
5. **Tool rate-limit livelock:** Agent retries a rate-limited tool call with exponential backoff. Higher-priority requests always beat it. Agent retries indefinitely (active, consuming tokens, making zero progress).

**What makes this a STRUCTURALLY STUCK state vs. slowness:**
- Slow: progress vector > 0 (agent is advancing toward goal, just slowly)
- Stuck: progress vector ≈ 0 for k consecutive steps (agent is active but not advancing)

**Current tools miss this entirely:**
- Langfuse: records that a span occurred — cannot detect whether the span sequence has net progress
- Arize Phoenix: scores individual outputs — cannot detect whether k consecutive outputs represent zero progress toward goal
- AgentRx (Microsoft Research, March 2026): detects FIRST UNRECOVERABLE step — different problem (livelock steps are recoverable-looking)
- Braintrust: evaluates output quality — cannot detect whether quality-passing outputs still constitute zero goal progress
- LangSmith: traces execution paths — cannot detect livelock pattern in traced paths

---

### API Design

```python
from livelock_probe import LivelockSuite, ProgressConfig, LivelockReport, livelock_probe

# === Core Classes ===

class ProgressConfig:
    goal_embedding: str | list[float]   # goal description or pre-computed embedding
    k: int = 5                          # minimum consecutive stuck steps to trigger
    epsilon: float = 0.05               # progress threshold (below = stuck)
    model: str = "all-MiniLM-L6-v2"    # sentence-transformer model
    budget_steps: int = 100             # max steps before forced termination
    criticality: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = "HIGH"
    # Criticality thresholds: CRITICAL: max_livelock_score=0.05, HIGH: 0.15, MEDIUM: 0.30, LOW: 0.50

class LivelockReport:
    livelock_score: float               # 0.0 (progressing) to 1.0 (completely stuck)
    livelock_detected: bool
    stuck_window_start: int | None      # step index where livelock began
    stuck_window_end: int | None        # step index where livelock ended (or None if ongoing)
    total_steps: int
    progress_vector: list[float]        # per-step progress delta
    mean_progress: float                # average progress per step
    max_consecutive_stuck: int          # longest consecutive stuck run
    gate_passed: bool                   # True if livelock_score <= criticality threshold
    steps: list[StepRecord]             # full trace with embeddings
    recommendation: str                 # human-readable summary

class LivelockSuite:
    def __init__(self, config: ProgressConfig): ...

    def instrument(self, agent_fn: Callable) -> Callable:
        """Wrap an agent function to capture step outputs for livelock analysis."""
        ...

    def record_step(self, step_output: str, step_id: int = None) -> None:
        """Manually record a step output (for custom agent frameworks)."""
        ...

    def compute(self) -> LivelockReport:
        """Compute LivelockScore from recorded steps."""
        ...

    def gate(self) -> bool:
        """Return True if livelock score passes threshold for configured criticality."""
        ...

    def reset(self) -> None:
        """Reset recorded steps for new agent run."""
        ...

# === Decorator API ===

@livelock_probe(goal="complete the customer support ticket", k=5, criticality="HIGH")
def my_agent(ticket: dict) -> str:
    # Agent implementation — livelock_probe instruments each output
    ...

# === Usage Example ===

suite = LivelockSuite(ProgressConfig(
    goal_embedding="resolve the user's database connection issue",
    k=5,
    epsilon=0.05,
    criticality="HIGH"
))

# Option 1: Manual instrumentation
for step in range(max_steps):
    output = agent.run_step(context)
    suite.record_step(output, step_id=step)
    if suite.gate() is False:
        break

report = suite.compute()
print(f"LivelockScore: {report.livelock_score:.3f}")
print(f"Detected: {report.livelock_detected}")
if report.livelock_detected:
    print(f"Stuck from step {report.stuck_window_start}")

# Option 2: Decorator
@livelock_probe(goal="resolve the user's issue", k=5)
def support_agent(ticket):
    return run_agent_loop(ticket)
```

---

### CLI Design

```bash
# Run livelock detection against an agent
lprobe run --agent my_agent.py --goal "resolve customer ticket" --k 5 --criticality HIGH

# Show livelock report from last run
lprobe show

# Gate: exit code 1 if livelock detected above threshold
lprobe gate --max-livelock-score 0.15

# Report: generate HTML/JSON report
lprobe report --format json --output livelock-report.json

# Estimate budget: how many steps before livelock detection fires?
lprobe estimate --k 5 --epsilon 0.05

# Replay: re-run livelock analysis from saved step trace
lprobe replay --trace-file steps.json --goal "resolve customer ticket"
```

---

### Algorithm: LivelockScore

```python
def compute_livelock_score(
    steps: list[str],
    goal: str,
    k: int,
    epsilon: float,
    model: str
) -> LivelockReport:

    # 1. Embed goal and all steps
    embedder = SentenceTransformer(model)
    goal_vec = embedder.encode(goal, normalize_embeddings=True)
    step_vecs = embedder.encode(steps, normalize_embeddings=True, batch_size=32)

    # 2. Compute progress vector: cosine similarity to goal at each step
    progress_to_goal = cosine_similarity(step_vecs, goal_vec.reshape(1, -1)).flatten()
    # progress_to_goal[i] = how similar step i's output is to the goal state

    # 3. Compute step-wise progress delta
    progress_deltas = np.diff(progress_to_goal, prepend=progress_to_goal[0])
    # Positive delta = moving toward goal. Near-zero delta = stuck.

    # 4. Detect stuck windows: k consecutive steps with |progress_delta| < epsilon
    stuck_mask = np.abs(progress_deltas) < epsilon
    consecutive_stuck = find_max_consecutive_true(stuck_mask)
    livelock_detected = consecutive_stuck >= k

    # 5. Compute LivelockScore
    stuck_fraction = np.sum(stuck_mask) / len(steps)
    livelock_score = stuck_fraction  # 0.0 = all steps progressing; 1.0 = all steps stuck

    return LivelockReport(
        livelock_score=livelock_score,
        livelock_detected=livelock_detected,
        progress_vector=progress_deltas.tolist(),
        mean_progress=float(np.mean(progress_deltas)),
        max_consecutive_stuck=consecutive_stuck,
        ...
    )
```

---

### pytest Plugin

```python
# conftest.py (auto-loaded)
# Adds livelock_probe fixture

def test_support_agent_no_livelock(livelock_probe):
    probe = livelock_probe(
        goal="resolve customer support ticket",
        k=5,
        criticality="HIGH"
    )
    with probe.instrument():
        result = support_agent.run(sample_ticket)

    report = probe.compute()
    assert report.gate_passed, (
        f"Agent entered livelock state: LivelockScore={report.livelock_score:.3f}, "
        f"stuck from step {report.stuck_window_start}"
    )
```

---

### Differentiation Matrix

| Tool | Detects Livelock | LivelockScore | Progress Vector | CI Gate | Framework-Agnostic |
|------|-----------------|---------------|-----------------|---------|-------------------|
| **livelock-probe** | ✅ YES | ✅ YES | ✅ YES | ✅ YES | ✅ YES |
| Langfuse | ❌ (tracing) | ❌ | ❌ | ❌ | ✅ |
| Arize Phoenix | ❌ (observability) | ❌ | ❌ | ❌ | ✅ |
| AgentRx (MS Research) | ❌ (first unrecoverable step — different) | ❌ | ❌ | ❌ | ❌ |
| Braintrust | ❌ (evaluation) | ❌ | ❌ | ❌ | ✅ |
| LangSmith | ❌ (tracing) | ❌ | ❌ | ❌ | ❌ (LangChain) |

**One-sentence differentiation:** livelock-probe is the only tool that detects when an AI agent is making zero net progress toward its goal despite being active — distinguishing structurally stuck states from slowness, deadlock, or explicit errors.

---

### Sprint Plan (8 weeks, solo builder)

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 1-2 | Core algorithm | ProgressConfig, step recorder, embedding computation, progress vector |
| 3-4 | LivelockScore + calibration | LivelockScore algorithm, k/epsilon calibration against known stuck patterns |
| 5 | LivelockReport + gate | Full report output, CI gate logic, criticality tier thresholds |
| 6 | CLI | `lprobe run/show/gate/report/estimate/replay` |
| 7 | pytest plugin + decorator | `@livelock_probe` decorator, `livelock_probe` pytest fixture |
| 8 | Ship | README (350+ lines), PyPI packaging, HN post |

**Capital required:** ZERO
**Stack:** sentence-transformers + anthropic/openai SDK + click + rich + numpy + pyyaml

---

### Known Unknowns

- KU-060: Optimal epsilon threshold for livelock detection — needs empirical calibration against real agent traces. Default 0.05 is a hypothesis.
- KU-061: Progress vector computation assumes single goal description. Multi-goal agents (sub-goal trees) require hierarchical progress tracking — not yet designed.
- KU-062: Livelock vs. deliberate iteration — some agent patterns intentionally refine output across many steps (writing assistant revising drafts). Need "intentional iteration mode" where progress is measured against final quality rather than goal embedding proximity per step.
- KU-063: How to handle embedding model mismatch between goal encoding and step output encoding when outputs are highly technical (code, SQL) vs. natural language goal descriptions.

---

### Build Score: 9.0/10
- Feasibility: 3/3 (sentence-transformers, all standard pip packages, zero GPU required, 8-week solo sprint)
- Impact: 3/3 (every enterprise agent team faces this; Claude Code, LangChain, CrewAI, AutoGen all affected)
- Completeness: 2/2 (API design complete, algorithm specified, CLI designed, pytest plugin specified)
- Biblical fidelity: 1/2 (38-year stuck state → livelock is structurally precise, but "external bypass" aspect not fully implemented — livelock-probe detects, it does not bypass)

**Note on Biblical fidelity score:** The miracle includes the bypass (Jesus does not fix the pool, he bypasses it). livelock-probe only detects the stuck state; it does not provide the bypass command. A future build could add "forced termination with bypass command injection" — but that is scope expansion. Detection is the first-order need.
