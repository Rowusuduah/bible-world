"""
chain-probe v0.1 — Core Implementation
Framework-agnostic fault isolation for multi-step LLM pipelines.

Biblical Foundation:
- Exodus 28:15-21 (Urim and Thummim — named step-gate oracle)
- Ezekiel 33:1-9 (Watchman — step-level sentinel with alarm)
- 1 Kings 18:30-39 (Elijah staged evidence — frozen-input step replay)

BibleWorld Cycle 017 | Pattern Commander
"""

from __future__ import annotations

import copy
import functools
import json
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Optional

# ---------------------------------------------------------------------------
# DATA MODELS
# ---------------------------------------------------------------------------

@dataclass
class StepRecord:
    """A single step's execution record within a ProbeSession."""
    session_id: str
    step_name: str
    step_index: int
    inputs_json: str          # JSON-serialized deep copy of inputs
    output_str: str           # str(output) for semantic analysis
    duration_ms: float
    token_count: int
    timestamp: str
    tags: dict = field(default_factory=dict)
    expected_keywords: list[str] = field(default_factory=list)
    forbidden_keywords: list[str] = field(default_factory=list)
    expected_output: Optional[str] = None
    # Set by FaultLocator:
    keyword_score: Optional[float] = None
    embedding_score: Optional[float] = None
    llm_score: Optional[float] = None
    semantic_score: Optional[float] = None
    fault_score: Optional[float] = None
    fault_type: Optional[str] = None  # PASS | ORIGIN | CASCADE


@dataclass
class FaultReport:
    """Output of FaultLocator.locate() — identifies which step caused the failure."""
    session_id: str
    fault_step: Optional[str]         # Name of ORIGIN step (None if all pass)
    fault_score: Optional[float]
    fault_confidence: Optional[str]   # HIGH | MEDIUM | LOW
    cascade_steps: list[str]
    recommendation: str
    step_summary: list[dict]          # [{step_name, fault_score, fault_type}]

    def summary(self) -> str:
        lines = []
        for s in self.step_summary:
            name = s["step_name"]
            fs = s.get("fault_score") or 0.0
            ft = s.get("fault_type") or "UNKNOWN"
            arrow = " ← ORIGIN FAULT" if ft == "ORIGIN" else (" (cascade)" if ft == "CASCADE" else "")
            lines.append(f"  Step [{name}]   fault_score={fs:.2f}  {ft}{arrow}")
        lines.append("")
        if self.fault_step:
            lines.append(f"FAULT LOCATED: {self.fault_step} (confidence: {self.fault_confidence})")
            lines.append(f"RECOMMENDATION: {self.recommendation}")
        else:
            lines.append("ALL STEPS PASS — no fault detected")
        return "\n".join(lines)


@dataclass
class ReplayResult:
    """Result of replaying a single step with modified parameters."""
    step_name: str
    session_id: str
    params: dict
    output_str: str
    original_semantic_score: float
    new_semantic_score: float
    score_delta: float
    verdict: str  # FAULT_MITIGATED | FAULT_CONFIRMED | FAULT_PARTIAL


# ---------------------------------------------------------------------------
# SESSION STORE (SQLite)
# ---------------------------------------------------------------------------

_DB_DEFAULT = Path.home() / ".chain_probe" / "sessions.db"

class SessionStore:
    """Persistent SQLite store for ProbeSession data."""

    def __init__(self, db_path: Path = _DB_DEFAULT):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    step_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'RUNNING',
                    fault_step TEXT,
                    fault_score REAL,
                    metadata TEXT
                );

                CREATE TABLE IF NOT EXISTS step_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    inputs_json TEXT NOT NULL,
                    output_str TEXT NOT NULL,
                    duration_ms REAL NOT NULL,
                    token_count INTEGER DEFAULT 0,
                    timestamp TEXT NOT NULL,
                    expected_keywords TEXT,
                    forbidden_keywords TEXT,
                    expected_output TEXT,
                    keyword_score REAL,
                    embedding_score REAL,
                    llm_score REAL,
                    semantic_score REAL,
                    fault_score REAL,
                    fault_type TEXT,
                    tags TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                );

                CREATE TABLE IF NOT EXISTS probe_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    fault_step TEXT,
                    fault_score REAL,
                    fault_confidence TEXT,
                    cascade_steps TEXT,
                    recommendation TEXT,
                    full_report TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                );
            """)

    def create_session(self, session_id: str, name: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO sessions (session_id, name, created_at) VALUES (?, ?, datetime('now'))",
                (session_id, name)
            )

    def save_step_record(self, record: StepRecord) -> None:
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO step_records (
                    session_id, step_name, step_index, inputs_json, output_str,
                    duration_ms, token_count, timestamp,
                    expected_keywords, forbidden_keywords, expected_output,
                    keyword_score, embedding_score, llm_score, semantic_score,
                    fault_score, fault_type, tags
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                record.session_id, record.step_name, record.step_index,
                record.inputs_json, record.output_str, record.duration_ms,
                record.token_count, record.timestamp,
                json.dumps(record.expected_keywords),
                json.dumps(record.forbidden_keywords),
                record.expected_output,
                record.keyword_score, record.embedding_score, record.llm_score,
                record.semantic_score, record.fault_score, record.fault_type,
                json.dumps(record.tags)
            ))
            conn.execute(
                "UPDATE sessions SET step_count = step_count + 1 WHERE session_id = ?",
                (record.session_id,)
            )

    def load_step_records(self, session_id: str) -> list[StepRecord]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM step_records WHERE session_id = ? ORDER BY step_index ASC",
                (session_id,)
            ).fetchall()
        records = []
        for row in rows:
            r = StepRecord(
                session_id=row["session_id"],
                step_name=row["step_name"],
                step_index=row["step_index"],
                inputs_json=row["inputs_json"],
                output_str=row["output_str"],
                duration_ms=row["duration_ms"],
                token_count=row["token_count"],
                timestamp=row["timestamp"],
                expected_keywords=json.loads(row["expected_keywords"] or "[]"),
                forbidden_keywords=json.loads(row["forbidden_keywords"] or "[]"),
                expected_output=row["expected_output"],
                keyword_score=row["keyword_score"],
                embedding_score=row["embedding_score"],
                llm_score=row["llm_score"],
                semantic_score=row["semantic_score"],
                fault_score=row["fault_score"],
                fault_type=row["fault_type"],
                tags=json.loads(row["tags"] or "{}"),
            )
            records.append(r)
        return records

    def update_fault_status(self, session_id: str, fault_step: Optional[str], fault_score: Optional[float]) -> None:
        status = "FAULT" if fault_step else "COMPLETE"
        with self._conn() as conn:
            conn.execute(
                "UPDATE sessions SET status=?, fault_step=?, fault_score=? WHERE session_id=?",
                (status, fault_step, fault_score, session_id)
            )

    def save_probe_report(self, report: FaultReport) -> None:
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO probe_reports (
                    session_id, created_at, fault_step, fault_score,
                    fault_confidence, cascade_steps, recommendation, full_report
                ) VALUES (?,datetime('now'),?,?,?,?,?,?)
            """, (
                report.session_id, report.fault_step, report.fault_score,
                report.fault_confidence, json.dumps(report.cascade_steps),
                report.recommendation, json.dumps(asdict(report))
            ))

    def list_sessions(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT session_id, name, created_at, step_count, status, fault_step, fault_score FROM sessions ORDER BY created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# PROBE SESSION (Context Manager)
# ---------------------------------------------------------------------------

_active_session: threading.local = threading.local()
_store = SessionStore()

class ProbeSession:
    """
    Context manager that groups step executions into a named session.

    Usage:
        with ProbeSession(name="my_pipeline_run") as session:
            result = my_pipeline(query="test")
    """

    def __init__(self, name: str, session_id: Optional[str] = None, db_path: Path = _DB_DEFAULT):
        self.name = name
        self.session_id = session_id or str(uuid.uuid4())
        self._step_records: list[StepRecord] = []
        self._step_index = 0
        self._store = SessionStore(db_path)

    def __enter__(self) -> "ProbeSession":
        self._store.create_session(self.session_id, self.name)
        _active_session.session = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        for record in self._step_records:
            self._store.save_step_record(record)
        _active_session.session = None
        return False  # Don't suppress exceptions

    def _add_step_record(self, record: StepRecord) -> None:
        self._step_records.append(record)

    def _next_step_index(self) -> int:
        idx = self._step_index
        self._step_index += 1
        return idx

    def get_step_records(self) -> list[StepRecord]:
        return list(self._step_records)

    @classmethod
    def load(cls, session_id: str, db_path: Path = _DB_DEFAULT) -> "ProbeSession":
        """Load a past session from the database for replay."""
        store = SessionStore(db_path)
        records = store.load_step_records(session_id)
        session = cls(name="loaded", session_id=session_id, db_path=db_path)
        session._step_records = records
        return session


def _get_active_session() -> Optional[ProbeSession]:
    return getattr(_active_session, "session", None)


def _serialize_inputs(args: tuple, kwargs: dict) -> str:
    """Serialize function inputs to JSON for frozen snapshot."""
    try:
        data = {"args": [_safe_serialize(a) for a in args], "kwargs": {k: _safe_serialize(v) for k, v in kwargs.items()}}
        return json.dumps(data, default=str)
    except Exception:
        return json.dumps({"args": [str(a) for a in args], "kwargs": {k: str(v) for k, v in kwargs.items()}})


def _safe_serialize(obj: Any) -> Any:
    """Best-effort serialization for input snapshotting."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, (list, tuple)):
        return [_safe_serialize(i) for i in obj]
    if isinstance(obj, dict):
        return {str(k): _safe_serialize(v) for k, v in obj.items()}
    # Pydantic v2
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    # Pydantic v1
    if hasattr(obj, "dict"):
        return obj.dict()
    return str(obj)


def _extract_token_count(output: Any) -> int:
    """Extract token count from LLM response objects or estimate from string."""
    # OpenAI response
    if hasattr(output, "usage") and hasattr(output.usage, "total_tokens"):
        return output.usage.total_tokens
    # Anthropic response
    if hasattr(output, "usage") and hasattr(output.usage, "input_tokens"):
        return (output.usage.input_tokens or 0) + (output.usage.output_tokens or 0)
    # Estimate from string
    return len(str(output).split())


# ---------------------------------------------------------------------------
# PROBE DECORATOR
# ---------------------------------------------------------------------------

def probe(
    name: str,
    expected_keywords: Optional[list[str]] = None,
    forbidden_keywords: Optional[list[str]] = None,
    expected_output: Optional[str] = None,
    halt_on_fault: bool = False,
    tags: Optional[dict] = None,
    llm_judge: Optional[Callable] = None,
):
    """
    Decorator that instruments a pipeline step for fault isolation.

    The Urim and Thummim pattern (Exodus 28:15-21): each step is a named decision gate.
    The Watchman pattern (Ezekiel 33:1-9): each step has a sentinel with alarm capability.

    Args:
        name: Step identifier (shown in fault reports)
        expected_keywords: Keywords that should appear in output (used by KeywordJudge)
        forbidden_keywords: Keywords that should NOT appear in output
        expected_output: Reference output for semantic similarity comparison
        halt_on_fault: If True, raise ProbeFaultHalt when fault_score > 0.5
        tags: Metadata dict attached to step record
        llm_judge: Optional callable(step_name, inputs, output, expected) → float [0,1]
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            session = _get_active_session()

            if session is None:
                # No active session — run transparently without instrumentation
                return func(*args, **kwargs)

            step_index = session._next_step_index()
            inputs_json = _serialize_inputs(args, kwargs)

            start = time.perf_counter()
            output = func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start) * 1000

            record = StepRecord(
                session_id=session.session_id,
                step_name=name,
                step_index=step_index,
                inputs_json=inputs_json,
                output_str=str(output),
                duration_ms=duration_ms,
                token_count=_extract_token_count(output),
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                expected_keywords=expected_keywords or [],
                forbidden_keywords=forbidden_keywords or [],
                expected_output=expected_output,
                tags=tags or {},
            )

            # Attach the original function reference for StepReplay
            if not hasattr(wrapper, "_probe_func"):
                wrapper._probe_func = func

            session._add_step_record(record)
            return output

        wrapper._probe_name = name
        wrapper._probe_func = func
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# FAULT LOCATOR
# ---------------------------------------------------------------------------

class KeywordJudge:
    """Level 1 semantic judge — keyword presence/absence check."""

    def score(self, record: StepRecord) -> float:
        if not record.expected_keywords and not record.forbidden_keywords:
            return 0.5  # Neutral when no keywords configured

        output_lower = record.output_str.lower()
        total_checks = len(record.expected_keywords) + len(record.forbidden_keywords)
        if total_checks == 0:
            return 0.5

        passed = 0
        for kw in record.expected_keywords:
            if kw.lower() in output_lower:
                passed += 1

        for kw in record.forbidden_keywords:
            if kw.lower() not in output_lower:
                passed += 1

        return passed / total_checks


class EmbeddingJudge:
    """Level 2 semantic judge — cosine similarity via sentence-transformers."""

    _model = None  # Lazy load

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                cls._model = SentenceTransformer("all-MiniLM-L6-v2")
            except ImportError:
                return None
        return cls._model

    def score(self, record: StepRecord) -> float:
        model = self._get_model()
        if model is None:
            return 0.5  # Neutral if sentence-transformers not installed

        reference = record.expected_output
        if not reference:
            # Use query/inputs as reference if no expected output
            try:
                inputs = json.loads(record.inputs_json)
                all_inputs = inputs.get("args", []) + list(inputs.get("kwargs", {}).values())
                reference = " ".join(str(i) for i in all_inputs if isinstance(i, str))
            except Exception:
                return 0.5

        if not reference or not record.output_str:
            return 0.5

        try:
            embeddings = model.encode([record.output_str, reference])
            # Cosine similarity
            a, b = embeddings[0], embeddings[1]
            norm_a = sum(x**2 for x in a) ** 0.5
            norm_b = sum(x**2 for x in b) ** 0.5
            if norm_a == 0 or norm_b == 0:
                return 0.5
            cosine = sum(a[i] * b[i] for i in range(len(a))) / (norm_a * norm_b)
            # Normalize from [-1, 1] to [0, 1]
            return (cosine + 1.0) / 2.0
        except Exception:
            return 0.5


class CascadeAnalyzer:
    """
    Distinguishes the ORIGIN fault from CASCADE faults.

    The Elijah pattern (1 Kings 18:30-39): staged evidence accumulation.
    Find the first step that exceeded the threshold — that is the ORIGIN.
    Downstream steps that also exceeded (at a lower threshold) are CASCADE.
    """

    def analyze(self, records: list[StepRecord], fault_threshold: float = 0.5) -> None:
        """Set fault_type on each record in-place."""
        origin_found = False
        origin_step = None

        for record in records:
            fs = record.fault_score or 0.0
            if not origin_found and fs > fault_threshold:
                record.fault_type = "ORIGIN"
                origin_found = True
                origin_step = record.step_name
            elif origin_found and fs > fault_threshold * 0.6:
                record.fault_type = "CASCADE"
            else:
                record.fault_type = "PASS"


class FaultLocator:
    """
    Main fault isolation engine.

    Implements the Urim and Thummim pattern (Exodus 28:15-21):
    interrogate each named step-gate and determine which one failed.
    """

    def __init__(
        self,
        session: ProbeSession,
        fault_threshold: float = 0.5,
        llm_judge: Optional[Callable] = None,
        keyword_weight: float = 0.3,
        embedding_weight: float = 0.7,
    ):
        self.session = session
        self.fault_threshold = fault_threshold
        self.llm_judge = llm_judge
        self.keyword_weight = keyword_weight
        self.embedding_weight = embedding_weight
        self._keyword_judge = KeywordJudge()
        self._embedding_judge = EmbeddingJudge()
        self._cascade_analyzer = CascadeAnalyzer()

    def locate(self) -> FaultReport:
        records = self.session.get_step_records()
        if not records:
            return FaultReport(
                session_id=self.session.session_id,
                fault_step=None,
                fault_score=None,
                fault_confidence=None,
                cascade_steps=[],
                recommendation="No steps recorded in session.",
                step_summary=[],
            )

        # Score each step
        for record in records:
            kw_score = self._keyword_judge.score(record)
            emb_score = self._embedding_judge.score(record)
            record.keyword_score = kw_score
            record.embedding_score = emb_score

            if self.llm_judge:
                try:
                    inputs = json.loads(record.inputs_json)
                    llm_score = self.llm_judge(
                        record.step_name, inputs, record.output_str, record.expected_output or ""
                    )
                    record.llm_score = float(llm_score)
                    # Recalculate with LLM weight
                    record.semantic_score = (
                        0.2 * kw_score + 0.5 * emb_score + 0.3 * record.llm_score
                    )
                except Exception:
                    record.llm_score = None
                    record.semantic_score = self.keyword_weight * kw_score + self.embedding_weight * emb_score
            else:
                record.semantic_score = self.keyword_weight * kw_score + self.embedding_weight * emb_score

            record.fault_score = max(0.0, min(1.0, 1.0 - record.semantic_score))

        # Cascade analysis
        self._cascade_analyzer.analyze(records, self.fault_threshold)

        # Build report
        origin_records = [r for r in records if r.fault_type == "ORIGIN"]
        cascade_records = [r for r in records if r.fault_type == "CASCADE"]

        fault_step = origin_records[0].step_name if origin_records else None
        fault_score = origin_records[0].fault_score if origin_records else None

        if fault_step:
            if fault_score and fault_score > 0.8:
                confidence = "HIGH"
            elif fault_score and fault_score > 0.6:
                confidence = "MEDIUM"
            else:
                confidence = "LOW"
            recommendation = self._generate_recommendation(origin_records[0])
        else:
            confidence = None
            recommendation = "All steps passed — no fault detected."

        step_summary = [
            {
                "step_name": r.step_name,
                "step_index": r.step_index,
                "fault_score": round(r.fault_score or 0.0, 4),
                "fault_type": r.fault_type,
                "keyword_score": round(r.keyword_score or 0.0, 4),
                "embedding_score": round(r.embedding_score or 0.0, 4),
                "duration_ms": round(r.duration_ms, 2),
                "token_count": r.token_count,
            }
            for r in records
        ]

        report = FaultReport(
            session_id=self.session.session_id,
            fault_step=fault_step,
            fault_score=round(fault_score, 4) if fault_score is not None else None,
            fault_confidence=confidence,
            cascade_steps=[r.step_name for r in cascade_records],
            recommendation=recommendation,
            step_summary=step_summary,
        )

        # Persist report
        _store.update_fault_status(self.session.session_id, fault_step, fault_score)
        _store.save_probe_report(report)

        return report

    def _generate_recommendation(self, record: StepRecord) -> str:
        """Generate human-readable recommendation from fault analysis."""
        parts = [f"Step '{record.step_name}' produced output with low semantic score."]
        if record.keyword_score is not None and record.keyword_score < 0.4:
            expected = record.expected_keywords
            found = [kw for kw in expected if kw.lower() in record.output_str.lower()]
            missing = [kw for kw in expected if kw.lower() not in record.output_str.lower()]
            if missing:
                parts.append(f"Missing expected keywords: {missing}.")
        if record.embedding_score is not None and record.embedding_score < 0.4:
            parts.append("Output is semantically distant from expected. Check prompt, model selection, or input quality.")
        parts.append("Use 'probe replay' to test this step in isolation with different parameters.")
        return " ".join(parts)


# ---------------------------------------------------------------------------
# STEP REPLAY ENGINE
# ---------------------------------------------------------------------------

class StepReplay:
    """
    Re-runs a specific step with frozen inputs from a recorded session.

    The Elijah pattern (1 Kings 18:30-39): pour water three times
    — each pour a deliberate parameter change — to build staged evidence
    about whether the failure is in THIS step or not.
    """

    def __init__(self, session: ProbeSession, step_name: str):
        self.session = session
        self.step_name = step_name
        self._record = self._find_record()

    def _find_record(self) -> StepRecord:
        records = self.session.get_step_records()
        for r in records:
            if r.step_name == self.step_name:
                return r
        raise ValueError(f"Step '{self.step_name}' not found in session {self.session.session_id}")

    def run(self, func: Optional[Callable] = None, **param_overrides) -> ReplayResult:
        """
        Replay the step with frozen inputs + optional parameter overrides.

        Args:
            func: Optional replacement function (if you want to test a different implementation)
            **param_overrides: Additional keyword arguments to inject into the step call
        """
        if func is None:
            raise ValueError(
                "Provide the step function to replay: StepReplay(session, 'step_name').run(func=my_step_func)"
            )

        # Restore frozen inputs
        try:
            inputs_data = json.loads(self._record.inputs_json)
            args = inputs_data.get("args", [])
            kwargs = inputs_data.get("kwargs", {})
        except Exception:
            args, kwargs = [], {}

        # Apply overrides
        kwargs.update(param_overrides)

        # Re-run
        start = time.perf_counter()
        output = func(*args, **kwargs)
        duration_ms = (time.perf_counter() - start) * 1000

        output_str = str(output)

        # Compute new semantic score
        temp_record = StepRecord(
            session_id=self.session.session_id,
            step_name=self.step_name,
            step_index=self._record.step_index,
            inputs_json=self._record.inputs_json,
            output_str=output_str,
            duration_ms=duration_ms,
            token_count=_extract_token_count(output),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            expected_keywords=self._record.expected_keywords,
            forbidden_keywords=self._record.forbidden_keywords,
            expected_output=self._record.expected_output,
        )

        kw_judge = KeywordJudge()
        emb_judge = EmbeddingJudge()
        kw_score = kw_judge.score(temp_record)
        emb_score = emb_judge.score(temp_record)
        new_semantic_score = 0.3 * kw_score + 0.7 * emb_score

        original_score = self._record.semantic_score or 0.5
        score_delta = new_semantic_score - original_score

        if score_delta > 0.1:
            verdict = "FAULT_MITIGATED"
        elif abs(score_delta) <= 0.1:
            verdict = "FAULT_CONFIRMED"
        else:
            verdict = "FAULT_WORSENED"

        return ReplayResult(
            step_name=self.step_name,
            session_id=self.session.session_id,
            params=param_overrides,
            output_str=output_str,
            original_semantic_score=round(original_score, 4),
            new_semantic_score=round(new_semantic_score, 4),
            score_delta=round(score_delta, 4),
            verdict=verdict,
        )

    def compare(self, results: list[ReplayResult]) -> dict:
        """Compare multiple replay results and identify the best parameters."""
        if not results:
            return {}
        best = max(results, key=lambda r: r.new_semantic_score)
        return {
            "best_params": best.params,
            "best_score": best.new_semantic_score,
            "best_verdict": best.verdict,
            "all_results": [
                {"params": r.params, "score": r.new_semantic_score, "delta": r.score_delta, "verdict": r.verdict}
                for r in sorted(results, key=lambda r: r.new_semantic_score, reverse=True)
            ]
        }


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

__all__ = [
    "probe",
    "ProbeSession",
    "FaultLocator",
    "StepReplay",
    "FaultReport",
    "StepRecord",
    "ReplayResult",
    "KeywordJudge",
    "EmbeddingJudge",
    "CascadeAnalyzer",
    "SessionStore",
]


# ---------------------------------------------------------------------------
# USAGE EXAMPLE
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Minimal demonstration without any LLM API
    print("chain-probe v0.1 — Demonstration")
    print("=" * 60)

    @probe(name="retrieve", expected_keywords=["document", "result"])
    def mock_retrieve(query: str) -> list[str]:
        # Simulating bad retrieval — returns empty results
        return []  # This will have a high fault_score

    @probe(name="synthesize", expected_keywords=["answer", "based on"])
    def mock_synthesize(docs: list[str], query: str) -> str:
        if not docs:
            return "I don't know."  # Cascade failure from bad retrieval
        return f"Based on the documents, the answer to '{query}' is: [answer here]."

    with ProbeSession(name="demo_run") as session:
        docs = mock_retrieve("What is chain-probe?")
        answer = mock_synthesize(docs, "What is chain-probe?")

    report = FaultLocator(session).locate()
    print(report.summary())
    print()
    print(f"Session ID: {session.session_id}")
    print("Run 'probe history' to see all past sessions.")
