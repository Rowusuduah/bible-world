# Builds — Cycle 021
**Cycle Type:** BIG_TECH_GAP_ANALYSIS (Type H)
**Date:** 2026-03-31
**Target:** Anthropic

---

## BUILD-020: invariant-probe

**Build Type:** Python open-source pip library
**Status:** DESIGNED — Sprint plan written
**Pivot_Score:** 8.175
**Biblical Pattern:** PAT-070 (Genesis 7 — The Sealed Invariance Pattern)
**Anthropic Gap:** AI agents are not tested for behavioral invariance under irrelevant environmental perturbations. The Claude Code database deletion incident (March 2026) is the canonical failure mode: agent behavior was NOT invariant to a connection string change. No pip library implements systematic behavioral invariance testing for AI agents.
**Competitive Status:** GREEN — No direct competitor identified

### Problem It Solves

Developers deploying AI agents to production have no way to systematically verify that their agent's core behavior is INVARIANT to environmental changes that should not affect it. When you change the system time, inject API latency, rotate environment variables, or modify tool availability — does your agent still behave the same way? Today: no tool answers this question. You find out in production.

### How It Works

1. Define a task for your agent (e.g., "analyze and summarize this document")
2. Define an EnvironmentMatrix: the set of environmental perturbations to test (time shifts, latency, env var mutations, tool availability changes, temperature variations)
3. Run the agent across the full perturbation matrix
4. Embed all outputs using sentence-transformers
5. Compute InvarianceScore = mean cosine similarity between all perturbed outputs and the baseline output
6. Report which perturbations caused behavioral drift (InvarianceScore < threshold)
7. Flag dangerous_pairs: perturbations that caused destructive behavior (tool calls with irreversible side effects under perturbation)

### API Design

```python
from invariant_probe import InvariantSuite, EnvironmentMatrix, InvarianceReport

suite = InvariantSuite(
    agent_fn=my_agent,          # callable: (task: str, env: dict) -> str
    task="analyze and summarize document X",
    baseline_env={}             # default environment
)

matrix = EnvironmentMatrix(
    perturbations=[
        TimeShift(hours=[0, 6, 12, 24]),
        TemperatureShift(values=[0.0, 0.3, 0.7, 1.0]),
        LatencyInjection(ms=[0, 100, 500, 2000]),
        EnvVarMutation(vars=["DEBUG", "LOG_LEVEL", "REGION", "API_VERSION"]),
        ToolAvailabilityChange(remove=["search_tool", "read_tool"]),
        ConnectionStringMutation(target="db_url", variant="test_db")
    ]
)

report: InvarianceReport = suite.run(matrix=matrix)

# Results
print(report.invariance_score)    # float 0.0-1.0 (1.0 = perfectly invariant)
print(report.drift_map)           # dict: perturbation -> cosine_delta
print(report.dangerous_pairs)     # list of (perturbation, side_effect) tuples
print(report.gate_passed)         # bool: invariance_score >= threshold

# Post-task attestation mode (PAT-073: Furnace Attestation Protocol)
attest_report = suite.attest(
    task_completed=True,
    surfaces=["db_row_count", "file_count_dir", "api_call_count"],
    expected_state=before_state
)
print(attest_report.zero_damage_certified)  # bool
print(attest_report.surface_report)         # per-surface: modified/unmodified
```

### CLI Design

```bash
# Run invariance test
iprobe run --agent my_agent.py --task "summarize document" --matrix matrix.yaml

# Show drift map
iprobe show --report last

# Gate on invariance score
iprobe gate --threshold 0.85  # exits with non-zero if invariance_score < 0.85

# Post-task attestation (Daniel 3 mode)
iprobe attest --before-state before.json --after-state after.json --surfaces db,files,api

# Estimate cost
iprobe estimate --matrix matrix.yaml --model claude-3-5-sonnet
```

### Pytest Plugin

```python
# conftest.py
import pytest
from invariant_probe.pytest_plugin import InvariantProbePlugin

@pytest.mark.invariant(threshold=0.85, perturbations=["time", "latency", "env"])
def test_agent_summarizes_document():
    result = my_agent("summarize document X")
    assert len(result) > 100
```

### Sprint Plan (8 Weeks)

| Week | Deliverable |
|------|-------------|
| 1-2 | Core InvariantSuite, EnvironmentMatrix, perturbation injection layer (TimeShift, LatencyInjection, EnvVarMutation) |
| 3-4 | Output comparison layer (sentence-transformers embedding, cosine similarity, InvarianceReport) |
| 5 | CLI (iprobe run/show/gate), dangerous_pairs detection |
| 6 | Post-task attestation mode (`iprobe attest`, AttestationReport) |
| 7 | Pytest plugin, CI integration (GitHub Actions example) |
| 8 | PyPI packaging (pyproject.toml, build, publish), README, docs, examples |

**Solo Buildability:** YES — 8 weeks, one developer, no GPU required

### Dependencies

```
sentence-transformers>=2.0
anthropic>=0.20.0
openai>=1.0.0  # optional
click>=8.0
rich>=13.0
numpy>=1.24
pyyaml>=6.0
pytest>=7.0  # optional for plugin
```

### Known Unknowns

- **KU-053:** Optimal similarity threshold for InvarianceScore — at what threshold does behavioral drift become a reliability concern? Study needed.
- **KU-054:** Interaction effects in the perturbation matrix — does applying latency + env var mutation simultaneously produce different results than each alone? V0.1 tests independently; v0.2 should implement pairwise matrix.
- **KU-055:** Embedding model sensitivity for InvarianceScore — does invariance_score change significantly across embedding models? Same question as KU-050 for context-trace.
- **KU-056:** Temperature = 0 invariance behavior — at T=0, agents are deterministic. What does invariance testing add? Study needed for deterministic vs. stochastic modes.

### Acquisition Fit

- **Anthropic:** Trust mission + Vercept (computer-use agents) acquisition = direct fit. Enterprises need invariance certification before deploying computer-use Claude agents. invariant-probe provides the certification layer.
- **OpenAI:** Pattern of acquiring developer tools (Astral, Promptfoo). invariant-probe follows the same profile: open-source, pip-installable, fills a specific gap in their ecosystem.
- **GitHub/Microsoft:** Enterprise AI Copilot deployments need behavioral invariance certification. GitHub Actions integration is day-1 feature.

---

## BUILD-021: session-lens

**Build Type:** Python open-source pip library
**Status:** DESIGNED — Sprint plan written
**Pivot_Score:** 7.90
**Biblical Pattern:** PAT-071 (John 4:16-18 — The Hidden History Verification Pattern)
**Anthropic Gap:** Long-session AI agents accumulate history in their context window, but no tool verifies that the agent's recalled history matches the ground truth at the event level. Anthropic's cache bug (March 2026) produced 10-20x cost inflation precisely because session memory integrity failed — the agent behaved as if prior context was missing.
**Competitive Status:** GREEN (adjacent to RAGAS/DeepEval groundedness, but session-level multi-turn memory fidelity is distinct)

### Problem It Solves

When an AI agent operates over a long session (100+ turns), it accumulates history in its context window or memory store. This history drives its current behavior. If the history is incorrect (cache miss, retrieval error, context truncation, hallucinated recall), the agent's behavior degrades in ways that are hard to diagnose. You don't know WHICH historical events the agent is recalling incorrectly.

session-lens provides SessionMemoryFidelity scoring: the fraction of ground truth historical events that the agent accurately recalls, correctly attributes, and places in the right sequence.

### API Design

```python
from session_lens import SessionLens, HistoryProbe, MemoryReport

# Create probe from ground truth history
history = HistoryProbe.from_transcript("session_transcript.json")

# Auto-generate probe questions from history
probes = history.generate_probes(
    n=20,                    # number of probe questions
    types=["recall", "ordering", "attribution", "negation"]
)

# Run session-lens
lens = SessionLens(
    agent_fn=my_agent,       # callable: (question: str, context: str) -> str
    model="claude-3-5-sonnet-20241022"
)

report: MemoryReport = lens.run(
    probes=probes,
    session_context=history.to_context_window()
)

# Results
print(report.session_memory_fidelity)  # float 0.0-1.0
print(report.cache_miss_events)        # list: events agent failed to recall
print(report.hallucinated_events)      # list: events agent stated that didn't happen
print(report.ordering_errors)          # list: events recalled in wrong sequence
print(report.gate_passed)             # bool: fidelity >= threshold

# Detailed breakdown
for event in report.failed_events:
    print(f"{event.event_id}: {event.failure_type} — expected: {event.expected}, got: {event.actual}")
```

### CLI Design

```bash
# Run session memory fidelity test
slens run --agent my_agent.py --history session.json --probes 20

# Show memory report
slens show --report last

# Gate on fidelity score
slens gate --threshold 0.90  # exits non-zero if fidelity < 0.90

# Export probe questions for manual inspection
slens export-probes --history session.json --output probes.json
```

### Sprint Plan (6-7 Weeks)

| Week | Deliverable |
|------|-------------|
| 1-2 | HistoryProbe (transcript parser, auto-probe generation: recall/ordering/attribution/negation question types) |
| 3-4 | SessionLens runner (agent fn wrapper, probe injection, answer comparison) |
| 5 | MemoryReport (fidelity scoring, cache miss detection, hallucination detection, ordering errors) |
| 6 | CLI (slens run/show/gate/export-probes), pytest plugin |
| 6-7 | PyPI packaging, README, docs, examples |

**Solo Buildability:** YES — 6-7 weeks, one developer, no GPU required

### Dependencies

```
anthropic>=0.20.0
openai>=1.0.0  # optional
sentence-transformers>=2.0
click>=8.0
rich>=13.0
numpy>=1.24
pyyaml>=6.0
pytest>=7.0  # optional
```

### Known Unknowns

- **KU-057:** How to distinguish cache miss events from actual non-recall (agent genuinely doesn't process that history segment) vs. model limitation. Study needed.
- **KU-058:** Optimal probe question generation — what mix of recall/ordering/attribution/negation maximizes diagnostic coverage?
- **KU-059:** Multi-document history — when session history spans multiple documents, how to handle cross-document attribution correctly?

### Acquisition Fit

- **Anthropic:** Cache bug (March 2026) is a session memory integrity problem. session-lens provides the diagnostic layer. Humanloop acquisition (trust/evaluation) = exact fit for an evaluation tool that measures session memory integrity.
- **OpenAI:** Long-context API (128K+) creates session memory integrity challenges. Developer tool that validates long-context agent memory = acquisition target.
