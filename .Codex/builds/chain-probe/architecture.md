# chain-probe — Architecture Document

**Version:** 0.1
**Date:** 2026-03-27
**BibleWorld Cycle:** 017
**Pattern Source:** PAT-054 (Exodus 28 — Urim/Thummim) + PAT-055 (Ezekiel 33 — Watchman) + PAT-056 (1 Kings 18 — Elijah Staged Evidence)

---

## System Overview

chain-probe is a pure Python library that wraps multi-step LLM pipeline functions with zero-config instrumentation, detects which step introduced a semantic failure, and enables step-level replay for debugging.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER'S PIPELINE                              │
│  (LangChain / LlamaIndex / raw API / any Python — doesn't matter)  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
             ┌───────────────▼───────────────┐
             │        @probe decorator        │
             │   (wraps any step function)    │
             │                               │
             │  • Pre-call: snapshot inputs   │
             │  • Post-call: capture output   │
             │  • Emit StepRecord to session  │
             └───────────────┬───────────────┘
                             │
             ┌───────────────▼───────────────┐
             │         ProbeSession           │
             │  (context manager per run)     │
             │                               │
             │  • Groups steps into a run     │
             │  • Assigns session_id (UUID)   │
             │  • Writes to SQLite on exit    │
             └───────────────┬───────────────┘
                             │
          ┌──────────────────┴──────────────────┐
          │                                     │
┌─────────▼──────────┐             ┌────────────▼──────────┐
│   SessionStore     │             │   FaultLocator         │
│   (SQLite)         │             │                        │
│                    │             │  Three-level cascade:  │
│ • sessions table   │             │  1. KeywordJudge       │
│ • step_records     │             │  2. EmbeddingJudge     │
│ • probe_reports    │             │  3. LLMJudge (opt.)    │
│                    │             │                        │
│ Persistent across  │             │  • fault_score/step    │
│ runs — replay any  │             │  • CascadeAnalyzer     │
│ past session       │             │  • FaultReport output  │
└─────────┬──────────┘             └────────────┬──────────┘
          │                                     │
          └──────────────┬──────────────────────┘
                         │
            ┌────────────▼────────────┐
            │     StepReplay Engine   │
            │                        │
            │  • Load frozen inputs   │
            │  • Inject step mocks    │
            │  • Re-run step in ISO   │
            │  • Compare scores       │
            │  • Emit ReplayReport    │
            └────────────┬────────────┘
                         │
            ┌────────────▼────────────┐
            │   Output Layer          │
            │                        │
            │  • ProbeReport (JSON)   │
            │  • ProbeMap (HTML/JSON) │
            │  • CLI (click + rich)   │
            │  • pytest plugin        │
            └─────────────────────────┘
```

---

## Component Specifications

### 1. @probe Decorator

**Location:** `chain_probe/decorator.py`

```
ProbeDecorator
├── __init__(name, expected_keywords, expected_output, halt_on_fault, tags, llm_judge)
├── __call__(func) → wrapped_func
└── wrapped_func(*args, **kwargs)
    ├── _snapshot_inputs(args, kwargs) → dict (deep copy, serializable)
    ├── _call_original(func, args, kwargs) → (output, duration_ms, token_count)
    ├── _emit_step_record(session, step_record)
    └── (optional) _check_halt_condition(fault_score) → raise ProbeFaultHalt
```

**Input snapshotting strategy:**
- Primitive types: direct copy
- Pydantic models: `.model_dump()`
- Dictionaries/lists: `json.loads(json.dumps(obj, default=str))` (handles most types)
- LangChain objects: `str(obj)` fallback with warning
- Token counting: detect if output is OpenAI/Anthropic response object, extract `usage.total_tokens`; else `len(str(output).split())`

### 2. ProbeSession

**Location:** `chain_probe/session.py`

```
ProbeSession
├── __init__(name, session_id=None, db_path=None)
├── __enter__() → self (sets active session thread-local)
├── __exit__() → commit all step records to SQLite
├── add_step_record(StepRecord)
├── get_step_records() → list[StepRecord]
└── load(session_id, db_path) → ProbeSession (class method — load past session)
```

**Thread safety:** Uses `threading.local()` for active session context. One active session per thread.

### 3. StepRecord (Data Model)

```python
@dataclass
class StepRecord:
    session_id: str
    step_name: str
    step_index: int
    inputs: dict           # frozen deep copy of inputs
    output: Any            # raw output from step function
    output_str: str        # str(output) for semantic analysis
    duration_ms: float
    token_count: int
    timestamp: str         # ISO 8601
    tags: dict
    # Set by FaultLocator:
    keyword_score: float = None
    embedding_score: float = None
    llm_score: float = None
    semantic_score: float = None
    fault_score: float = None
    fault_type: str = None  # "PASS" | "ORIGIN" | "CASCADE"
```

### 4. SessionStore (SQLite Schema)

```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    step_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'RUNNING',  -- RUNNING | COMPLETE | FAULT
    fault_step TEXT,
    fault_score REAL,
    metadata TEXT  -- JSON
);

CREATE TABLE step_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    step_name TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    inputs TEXT NOT NULL,         -- JSON
    output_str TEXT NOT NULL,
    duration_ms REAL NOT NULL,
    token_count INTEGER DEFAULT 0,
    timestamp TEXT NOT NULL,
    keyword_score REAL,
    embedding_score REAL,
    llm_score REAL,
    semantic_score REAL,
    fault_score REAL,
    fault_type TEXT,
    tags TEXT,                    -- JSON
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE probe_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    fault_step TEXT,
    fault_score REAL,
    fault_confidence TEXT,        -- HIGH | MEDIUM | LOW
    cascade_steps TEXT,           -- JSON list
    recommendation TEXT,
    full_report TEXT,             -- JSON
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);
```

**Default DB path:** `~/.chain_probe/sessions.db`

### 5. FaultLocator

**Location:** `chain_probe/fault_locator.py`

**Algorithm:**

```
FaultLocator.locate(session) → FaultReport:

1. Load all StepRecords for session
2. For each step in order:
   a. Run KeywordJudge(step_record) → keyword_score ∈ [0.0, 1.0]
   b. Run EmbeddingJudge(step_record) → embedding_score ∈ [0.0, 1.0]
   c. If llm_judge provided: Run LLMJudge(step_record) → llm_score ∈ [0.0, 1.0]
   d. Compute semantic_score (weighted average)
   e. Compute fault_score = 1.0 - semantic_score
   f. Store scores on StepRecord

3. CascadeAnalyzer.analyze(step_records, fault_threshold=0.5):
   a. Find first step N where fault_score > fault_threshold
   b. Mark N as ORIGIN
   c. For all steps M > N where fault_score > fault_threshold * 0.6:
      Mark M as CASCADE (with origin=N)
   d. All remaining steps: PASS

4. Build FaultReport:
   - fault_step: name of ORIGIN step (or None if all PASS)
   - fault_score: fault_score of ORIGIN step
   - fault_confidence: HIGH if fault_score > 0.8, MEDIUM if > 0.6, LOW otherwise
   - cascade_steps: list of CASCADE step names
   - recommendation: generated from fault_step + keyword/embedding analysis
   - step_summary: list of (step_name, fault_score, fault_type) tuples
```

**KeywordJudge:**
```
keyword_score:
  - If expected_keywords not set: return 0.5 (neutral)
  - For each required keyword: +1 if present in output
  - For each forbidden keyword: -1 if present in output
  - Normalize to [0.0, 1.0]
```

**EmbeddingJudge:**
```
embedding_score:
  - Model: sentence-transformers/all-MiniLM-L6-v2 (local, 22MB)
  - If expected_output not set: use step inputs as reference
  - score = cosine_similarity(embed(output), embed(reference))
  - score ∈ [-1, 1] → normalize to [0.0, 1.0]
```

### 6. StepReplay Engine

**Location:** `chain_probe/replay.py`

```
StepReplay(session, step_name)
├── run(**param_overrides) → ReplayResult
│   ├── Load frozen inputs for step_name from session
│   ├── Load original function reference (via __qualname__ registry)
│   ├── Apply param_overrides to call signature
│   ├── Execute step function with frozen inputs + overrides
│   ├── Compute new semantic_score
│   └── Return ReplayResult(params, output, semantic_score, score_delta, verdict)
│
└── compare(runs: list[ReplayResult]) → ComparisonReport
    ├── Rank runs by semantic_score
    └── Identify best-performing parameter combination
```

**Verdict logic:**
```
if new_semantic_score > original_semantic_score + 0.1:
    verdict = "FAULT_MITIGATED"   # Override helped
elif abs(new_semantic_score - original_semantic_score) < 0.1:
    verdict = "FAULT_CONFIRMED"   # Same failure regardless of override
else:
    verdict = "FAULT_PARTIAL"     # Some improvement but not resolved
```

### 7. ProbeMap Generator

**Location:** `chain_probe/probe_map.py`

Generates an HTML report showing:
- All steps with probes (covered)
- Any steps called without a probe decorator (dark zones — detected by comparing call stack to step registry)
- Per-step fault scores and types
- Timeline visualization

### 8. CLI

**Location:** `chain_probe/cli.py`

Commands:
- `probe run <command> --session <name>` — runs command with probe active
- `probe report --session <id>` — displays FaultReport for session
- `probe replay --session <id> --step <name> [--param k=v ...]` — replays step
- `probe map --session <id> --output <file>` — generates ProbeMap
- `probe ci --session <id> --threshold <float>` — CI gate
- `probe history` — lists all sessions with fault status

### 9. pytest Plugin

**Location:** `chain_probe/pytest_plugin.py`

```python
# conftest.py (auto-discovered if chain_probe installed)
@pytest.fixture
def probe_session(request):
    with ProbeSession(name=request.node.name) as session:
        yield session
```

```python
# test_pipeline.py
def test_rag_pipeline(probe_session):
    with probe_session:
        result = run_pipeline(query="test query")
    report = FaultLocator(probe_session).locate()
    assert report.fault_step is None, f"Step failed: {report.fault_step}"
```

---

## File Structure

```
chain_probe/
├── __init__.py              # Public API: probe, ProbeSession, FaultLocator, StepReplay
├── decorator.py             # @probe decorator implementation
├── session.py               # ProbeSession context manager
├── models.py                # StepRecord, FaultReport, ReplayResult dataclasses
├── store.py                 # SessionStore (SQLite operations)
├── fault_locator.py         # FaultLocator, CascadeAnalyzer
├── judges/
│   ├── __init__.py
│   ├── keyword_judge.py     # KeywordJudge
│   ├── embedding_judge.py   # EmbeddingJudge (sentence-transformers)
│   └── llm_judge.py         # LLMJudge (user-provided model_fn)
├── replay.py                # StepReplay engine
├── probe_map.py             # ProbeMap HTML generator
├── cli.py                   # CLI commands (click)
└── pytest_plugin.py         # pytest fixture plugin

tests/
├── test_decorator.py
├── test_fault_locator.py
├── test_cascade_analysis.py
├── test_step_replay.py
└── test_cli.py

examples/
├── basic_usage.py
├── rag_pipeline_probe.py
└── multi_step_agent.py

pyproject.toml
README.md
```

---

## Dependencies

```toml
[project]
name = "chain-probe"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = [
    "sentence-transformers>=2.2.0",
    "click>=8.0.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio", "mypy", "ruff"]

[project.entry-points."pytest11"]
chain_probe = "chain_probe.pytest_plugin"

[project.scripts]
probe = "chain_probe.cli:main"
```

---

## Known Unknowns (Open Research Questions)

| ID | Question | Impact | Priority |
|----|---------|--------|----------|
| KU-036 | Embedding model choice for EmbeddingJudge — all-MiniLM-L6-v2 is the default; domain-specific models (legal, medical) may need fine-tuned embeddings for accurate fault scores | Medium | Medium |
| KU-037 | fault_score threshold calibration — 0.5 default proposed; needs empirical validation across pipeline types (RAG, agent, sequential chain) | High | High |
| KU-038 | Cascade fault detection edge cases — if Step 1 fails catastrophically, all downstream steps will also fail; distinguishing "cascade from Step 1" from "independent failures at each step" requires more signals | Medium | Medium |
| KU-039 | Non-determinism in LLMJudge — temperature=0 required for reproducible judge scores; still not fully deterministic across API providers; median-of-3 runs proposed | Medium | Low |
