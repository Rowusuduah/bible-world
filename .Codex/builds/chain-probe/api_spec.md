# chain-probe API Specification

**Version:** 0.1
**Date:** 2026-03-27

---

## Python API

### `probe` (decorator)

```python
@probe(
    name: str,                                    # Required. Step identifier.
    expected_keywords: list[str] | None = None,   # Keywords that SHOULD appear in output.
    forbidden_keywords: list[str] | None = None,  # Keywords that should NOT appear.
    expected_output: str | None = None,           # Reference output for semantic comparison.
    halt_on_fault: bool = False,                  # Raise ProbeFaultHalt if fault detected.
    tags: dict | None = None,                     # Metadata attached to step record.
    llm_judge: Callable | None = None,            # Optional LLM judge fn(step, inputs, output, expected) → float.
)
```

**Behavior:**
- When called inside a `ProbeSession` context: instruments the step, captures inputs/outputs, emits StepRecord.
- When called outside a `ProbeSession` context: runs transparently with zero overhead.

---

### `ProbeSession` (context manager)

```python
ProbeSession(
    name: str,                        # Human-readable name for this run.
    session_id: str | None = None,    # Optional. Auto-generated UUID if not provided.
    db_path: Path = ~/.chain_probe/sessions.db,
)
```

**Methods:**
- `get_step_records() → list[StepRecord]` — Returns all step records collected so far.
- `ProbeSession.load(session_id: str) → ProbeSession` — Class method. Load a past session for replay.

---

### `FaultLocator`

```python
FaultLocator(
    session: ProbeSession,
    fault_threshold: float = 0.5,     # fault_score above this → fault detected.
    llm_judge: Callable | None = None, # Optional LLM judge for Level 3 scoring.
    keyword_weight: float = 0.3,      # Weight of KeywordJudge in semantic_score.
    embedding_weight: float = 0.7,    # Weight of EmbeddingJudge in semantic_score.
)

.locate() → FaultReport
```

---

### `FaultReport` (dataclass)

```python
@dataclass
class FaultReport:
    session_id: str
    fault_step: str | None            # Name of ORIGIN step. None if all steps pass.
    fault_score: float | None         # fault_score of the ORIGIN step.
    fault_confidence: str | None      # "HIGH" | "MEDIUM" | "LOW"
    cascade_steps: list[str]          # Steps that failed due to cascade from ORIGIN.
    recommendation: str               # Human-readable debugging guidance.
    step_summary: list[dict]          # Per-step scores and fault types.

    .summary() → str                  # Pretty-printed fault report.
```

---

### `StepReplay`

```python
StepReplay(
    session: ProbeSession,
    step_name: str,
)

.run(
    func: Callable,          # The step function to re-run (required).
    **param_overrides,       # Additional kwargs to inject into the call.
) → ReplayResult

.compare(results: list[ReplayResult]) → dict   # Rank replay results, identify best params.
```

---

### `ReplayResult` (dataclass)

```python
@dataclass
class ReplayResult:
    step_name: str
    session_id: str
    params: dict                      # Parameters used in this replay run.
    output_str: str
    original_semantic_score: float
    new_semantic_score: float
    score_delta: float                # new - original. Positive = improvement.
    verdict: str                      # "FAULT_MITIGATED" | "FAULT_CONFIRMED" | "FAULT_WORSENED"
```

---

## CLI API

```
probe run <command> [OPTIONS]
    --session TEXT        Session name (default: auto-generated)
    --db PATH             Database path (default: ~/.chain_probe/sessions.db)

probe report [OPTIONS]
    --session TEXT        Session ID or name (required)
    --format TEXT         "text" | "json" (default: text)
    --output PATH         Write report to file instead of stdout

probe replay [OPTIONS]
    --session TEXT        Session ID (required)
    --step TEXT           Step name to replay (required)
    --func TEXT           Python dotted path to function (e.g. "mymodule.my_step")
    --param TEXT          key=value param overrides (repeatable)
    --runs INTEGER        Number of replay runs (default: 1)

probe map [OPTIONS]
    --session TEXT        Session ID (required)
    --output PATH         Output file for HTML/JSON map (required)
    --format TEXT         "html" | "json" (default: html)

probe ci [OPTIONS]
    --session TEXT        Session ID (required)
    --threshold FLOAT     Fault threshold (default: 0.5)
    Exit code: 0 = all steps pass, 1 = fault detected

probe history [OPTIONS]
    --limit INTEGER       Number of sessions to show (default: 20)
    --format TEXT         "table" | "json" (default: table)
    --db PATH             Database path
```

---

## Exit Codes (CLI)

| Code | Meaning |
|------|---------|
| 0 | All steps PASS (no fault detected) |
| 1 | FAULT detected (at least one ORIGIN step above threshold) |
| 2 | Configuration error (invalid session, missing step) |
| 3 | Internal error |

---

## ProbeMap Output (HTML)

The ProbeMap HTML report contains:

1. **Coverage Summary**: Total steps / probed steps / dark zones
2. **Step Table**: Each step with probe status, fault_score, fault_type, duration
3. **Fault Timeline**: Visual bar chart of fault_scores per step
4. **Cascade Graph**: Arrow diagram showing ORIGIN → CASCADE relationships
5. **Dark Zone Warning**: List of steps called without probe decoration

---

## Exceptions

```python
class ProbeFaultHalt(Exception):
    """Raised when halt_on_fault=True and fault_score > threshold."""
    step_name: str
    fault_score: float

class ProbeSessionNotFound(Exception):
    """Raised when loading a session that doesn't exist in the database."""
    session_id: str

class ProbeStepNotFound(Exception):
    """Raised when StepReplay cannot find the specified step in the session."""
    step_name: str
    session_id: str
```

---

## Configuration File (Optional)

`~/.chain_probe/config.json`:
```json
{
    "db_path": "~/.chain_probe/sessions.db",
    "default_fault_threshold": 0.5,
    "embedding_model": "all-MiniLM-L6-v2",
    "keyword_weight": 0.3,
    "embedding_weight": 0.7,
    "auto_probe_map": false,
    "ci_exit_on_fault": true
}
```
