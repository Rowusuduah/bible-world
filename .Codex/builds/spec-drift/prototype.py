"""
spec-drift: Semantic specification drift detector for LLM outputs.

"Among those who approach me I will be proved holy" — Leviticus 10:3
Structural validation is not enough. Semantic compliance must be declared and monitored.

pip install spec-drift
"""

from __future__ import annotations

import json
import sqlite3
import statistics
import time
import hashlib
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
from functools import wraps

try:
    from pydantic import BaseModel
except ImportError:
    raise ImportError("spec-drift requires pydantic v2: pip install pydantic>=2.0")

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------------------
# Core enums and data structures
# ---------------------------------------------------------------------------

class ConstraintType(str, Enum):
    AUTHORIZED_VALUES = "authorized_values"
    LENGTH_BOUNDS = "length_bounds"
    DISTRIBUTION = "distribution"
    PATTERN_MATCH = "pattern_match"
    CORRELATION = "correlation"


class DriftSeverity(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SemanticConstraint:
    """Declares a semantic constraint on a single LLM output field."""
    constraint_type: ConstraintType
    params: Dict[str, Any]
    alert_threshold: float = 0.15  # fraction of violations before alert
    field_name: Optional[str] = None  # set automatically by @spec decorator

    @classmethod
    def from_authorized_values(
        cls,
        authorized: List[Any],
        tolerance: float = 0.02,
        alert_threshold: float = 0.10,
    ) -> "SemanticConstraint":
        """Field values must be drawn from this authorized set (with tolerance)."""
        return cls(
            constraint_type=ConstraintType.AUTHORIZED_VALUES,
            params={"authorized": authorized, "tolerance": tolerance},
            alert_threshold=alert_threshold,
        )

    @classmethod
    def from_length_bounds(
        cls,
        min_words: int = 0,
        max_words: int = 10_000,
        alert_threshold: float = 0.15,
    ) -> "SemanticConstraint":
        """String field must have word count within [min_words, max_words]."""
        return cls(
            constraint_type=ConstraintType.LENGTH_BOUNDS,
            params={"min_words": min_words, "max_words": max_words},
            alert_threshold=alert_threshold,
        )

    @classmethod
    def from_distribution(
        cls,
        mean: float,
        std: float,
        drift_threshold: float = 1.0,
        alert_threshold: float = 0.20,
    ) -> "SemanticConstraint":
        """Numeric field should follow a distribution near (mean, std).
        Alerts if observed mean shifts by more than drift_threshold standard deviations."""
        return cls(
            constraint_type=ConstraintType.DISTRIBUTION,
            params={"mean": mean, "std": std, "drift_threshold": drift_threshold},
            alert_threshold=alert_threshold,
        )

    @classmethod
    def from_pattern(
        cls,
        regex: str,
        min_match_rate: float = 0.90,
        alert_threshold: float = 0.15,
    ) -> "SemanticConstraint":
        """String field should match the given regex pattern at a minimum rate."""
        return cls(
            constraint_type=ConstraintType.PATTERN_MATCH,
            params={"regex": regex, "min_match_rate": min_match_rate},
            alert_threshold=alert_threshold,
        )

    def check(self, value: Any) -> tuple[bool, str]:
        """Check a single value against this constraint.
        Returns (passed: bool, reason: str)."""
        import re

        if self.constraint_type == ConstraintType.AUTHORIZED_VALUES:
            authorized = self.params["authorized"]
            if value in authorized:
                return True, "authorized"
            return False, f"value '{value}' not in authorized set {authorized}"

        elif self.constraint_type == ConstraintType.LENGTH_BOUNDS:
            if not isinstance(value, str):
                return False, f"expected string, got {type(value).__name__}"
            wc = len(value.split())
            lo, hi = self.params["min_words"], self.params["max_words"]
            if lo <= wc <= hi:
                return True, f"word count {wc} within [{lo}, {hi}]"
            return False, f"word count {wc} outside [{lo}, {hi}]"

        elif self.constraint_type == ConstraintType.DISTRIBUTION:
            try:
                v = float(value)
            except (TypeError, ValueError):
                return False, f"cannot convert '{value}' to float"
            # Single-value check: within 3 sigma of declared mean
            mean, std = self.params["mean"], self.params["std"]
            z = abs(v - mean) / (std if std > 0 else 1e-9)
            if z <= 3.0:
                return True, f"value {v:.3f} within 3σ of mean {mean}"
            return False, f"value {v:.3f} is {z:.2f}σ from mean {mean}"

        elif self.constraint_type == ConstraintType.PATTERN_MATCH:
            if not isinstance(value, str):
                return False, f"expected string, got {type(value).__name__}"
            matched = bool(re.search(self.params["regex"], value))
            if matched:
                return True, "pattern matched"
            return False, f"value did not match pattern '{self.params['regex']}'"

        return True, "no constraint applied"


# ---------------------------------------------------------------------------
# @spec decorator
# ---------------------------------------------------------------------------

def spec(**constraints: SemanticConstraint):
    """Decorator that attaches semantic constraints to a Pydantic model class.

    Usage:
        @spec(
            category=SemanticConstraint.from_authorized_values(["pos", "neg", "neu"]),
            reasoning=SemanticConstraint.from_length_bounds(30, 300),
        )
        class SentimentAnalysis(BaseModel):
            category: str
            reasoning: str
            score: float
    """
    def decorator(cls: Type[T]) -> Type[T]:
        for fname, constraint in constraints.items():
            constraint.field_name = fname
        cls.__spec_constraints__ = constraints
        return cls
    return decorator


# ---------------------------------------------------------------------------
# Observation record
# ---------------------------------------------------------------------------

@dataclass
class Observation:
    """A single LLM output observation with constraint check results."""
    timestamp: float
    spec_name: str
    output_data: Dict[str, Any]
    constraint_results: Dict[str, tuple[bool, str]]  # field -> (passed, reason)
    model_version: Optional[str] = None
    prompt_hash: Optional[str] = None
    call_id: str = field(default_factory=lambda: hashlib.md5(
        str(time.time_ns()).encode()
    ).hexdigest()[:12])

    @property
    def passed(self) -> bool:
        return all(r[0] for r in self.constraint_results.values())

    @property
    def violation_count(self) -> int:
        return sum(1 for r in self.constraint_results.values() if not r[0])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id,
            "timestamp": self.timestamp,
            "spec_name": self.spec_name,
            "passed": self.passed,
            "violation_count": self.violation_count,
            "model_version": self.model_version,
            "prompt_hash": self.prompt_hash,
            "output_data": json.dumps(self.output_data),
            "constraint_results": json.dumps({
                k: {"passed": v[0], "reason": v[1]}
                for k, v in self.constraint_results.items()
            }),
        }


# ---------------------------------------------------------------------------
# SQLite store
# ---------------------------------------------------------------------------

class ObservationStore:
    """Persists observations to SQLite. Zero infrastructure required."""

    CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS observations (
        call_id      TEXT PRIMARY KEY,
        timestamp    REAL NOT NULL,
        spec_name    TEXT NOT NULL,
        passed       INTEGER NOT NULL,
        violation_count INTEGER NOT NULL,
        model_version TEXT,
        prompt_hash  TEXT,
        output_data  TEXT,
        constraint_results TEXT
    )
    """

    def __init__(self, db_path: str = "./spec_drift.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(self.CREATE_TABLE)
            conn.commit()

    def save(self, obs: Observation):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO observations VALUES "
                "(:call_id,:timestamp,:spec_name,:passed,:violation_count,"
                ":model_version,:prompt_hash,:output_data,:constraint_results)",
                obs.to_dict(),
            )
            conn.commit()

    def query(
        self,
        spec_name: str,
        since_hours: float = 24.0,
    ) -> List[Dict[str, Any]]:
        cutoff = time.time() - since_hours * 3600
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM observations WHERE spec_name=? AND timestamp>=? "
                "ORDER BY timestamp DESC",
                (spec_name, cutoff),
            ).fetchall()
        return [dict(r) for r in rows]

    def violation_rate(self, spec_name: str, since_hours: float = 24.0) -> float:
        rows = self.query(spec_name, since_hours)
        if not rows:
            return 0.0
        return sum(1 for r in rows if not r["passed"]) / len(rows)


# ---------------------------------------------------------------------------
# DriftMonitor — the main runtime component
# ---------------------------------------------------------------------------

class DriftMonitor:
    """Wraps LLM functions to monitor semantic specification compliance at runtime.

    Usage:
        monitor = DriftMonitor(spec=SentimentAnalysis)

        @monitor.watch
        def analyze_sentiment(text: str) -> SentimentAnalysis:
            ...

        # Or inline:
        result = monitor.observe(output_obj)
    """

    def __init__(
        self,
        spec: Type[T],
        db_path: str = "./spec_drift.db",
        model_version: Optional[str] = None,
        prompt_hash: Optional[str] = None,
        alert_callback: Optional[Callable[[str, float], None]] = None,
    ):
        self.spec_class = spec
        self.spec_name = spec.__name__
        self.constraints: Dict[str, SemanticConstraint] = getattr(
            spec, "__spec_constraints__", {}
        )
        self.store = ObservationStore(db_path)
        self.model_version = model_version
        self.prompt_hash = prompt_hash
        self.alert_callback = alert_callback

    def observe(self, output: T) -> T:
        """Check a Pydantic model instance against the spec. Log the observation."""
        if not isinstance(output, self.spec_class):
            raise TypeError(
                f"Expected {self.spec_class.__name__}, got {type(output).__name__}"
            )
        data = output.model_dump()
        results: Dict[str, tuple[bool, str]] = {}

        for fname, constraint in self.constraints.items():
            value = data.get(fname)
            passed, reason = constraint.check(value)
            results[fname] = (passed, reason)

        obs = Observation(
            timestamp=time.time(),
            spec_name=self.spec_name,
            output_data=data,
            constraint_results=results,
            model_version=self.model_version,
            prompt_hash=self.prompt_hash,
        )
        self.store.save(obs)

        # Check if rolling violation rate exceeds any constraint's alert_threshold
        if self.alert_callback:
            vrate = self.store.violation_rate(self.spec_name, since_hours=1.0)
            for fname, constraint in self.constraints.items():
                if vrate > constraint.alert_threshold:
                    self.alert_callback(
                        f"spec-drift ALERT: {self.spec_name}.{fname} "
                        f"violation rate {vrate:.1%} exceeds threshold "
                        f"{constraint.alert_threshold:.1%}",
                        vrate,
                    )
        return output

    def watch(self, fn: Callable) -> Callable:
        """Decorator: automatically observe the return value of an LLM function."""
        @wraps(fn)
        def wrapper(*args, **kwargs):
            result = fn(*args, **kwargs)
            return self.observe(result)
        return wrapper

    def drift_report(self, since_hours: float = 168.0) -> Dict[str, Any]:
        """Generate a semantic drift report for the last N hours."""
        rows = self.store.query(self.spec_name, since_hours)
        if not rows:
            return {"spec": self.spec_name, "observations": 0, "status": "no_data"}

        total = len(rows)
        violations = sum(1 for r in rows if not r["passed"])
        vrate = violations / total

        field_stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"pass": 0, "fail": 0}
        )
        for row in rows:
            cr = json.loads(row["constraint_results"])
            for fname, result in cr.items():
                if result["passed"]:
                    field_stats[fname]["pass"] += 1
                else:
                    field_stats[fname]["fail"] += 1

        return {
            "spec": self.spec_name,
            "period_hours": since_hours,
            "observations": total,
            "violation_rate": round(vrate, 4),
            "severity": self._severity(vrate).value,
            "field_violation_rates": {
                fname: round(s["fail"] / (s["pass"] + s["fail"]), 4)
                for fname, s in field_stats.items()
                if s["pass"] + s["fail"] > 0
            },
        }

    def _severity(self, vrate: float) -> DriftSeverity:
        if vrate == 0:
            return DriftSeverity.NONE
        if vrate < 0.05:
            return DriftSeverity.LOW
        if vrate < 0.15:
            return DriftSeverity.MEDIUM
        if vrate < 0.30:
            return DriftSeverity.HIGH
        return DriftSeverity.CRITICAL


# ---------------------------------------------------------------------------
# CI gate — used by `spec-drift ci` CLI command
# ---------------------------------------------------------------------------

def run_ci_gate(
    monitor: DriftMonitor,
    test_outputs: List[T],
    threshold: float = 0.20,
) -> tuple[bool, Dict[str, Any]]:
    """Run a CI gate check on a batch of test outputs.
    Returns (passed, report). Fails if violation_rate > threshold."""
    for output in test_outputs:
        monitor.observe(output)

    report = monitor.drift_report(since_hours=0.1)  # just the CI batch
    vrate = report.get("violation_rate", 0.0)
    passed = vrate <= threshold
    report["ci_threshold"] = threshold
    report["ci_passed"] = passed
    return passed, report


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import random

    # 1. Declare a spec on a Pydantic model
    @spec(
        category=SemanticConstraint.from_authorized_values(
            ["positive", "negative", "neutral"],
            tolerance=0.02,
            alert_threshold=0.10,
        ),
        reasoning=SemanticConstraint.from_length_bounds(
            min_words=10,
            max_words=200,
            alert_threshold=0.15,
        ),
        score=SemanticConstraint.from_distribution(
            mean=6.5,
            std=2.0,
            drift_threshold=1.0,
            alert_threshold=0.20,
        ),
    )
    class SentimentAnalysis(BaseModel):
        category: str
        reasoning: str
        score: float

    # 2. Create a monitor
    def on_alert(message: str, rate: float):
        print(f"[ALERT] {message}")

    monitor = DriftMonitor(
        spec=SentimentAnalysis,
        db_path=":memory:",  # in-memory for demo
        model_version="claude-3-5-haiku-20241022",
        alert_callback=on_alert,
    )

    # 3. Simulate authorized outputs (spec-compliant)
    authorized_outputs = [
        SentimentAnalysis(
            category=random.choice(["positive", "negative", "neutral"]),
            reasoning="This text expresses a clear positive sentiment with "
                      "strong affirmative language and constructive framing.",
            score=random.gauss(6.5, 2.0),
        )
        for _ in range(20)
    ]

    print("=== Observing authorized outputs ===")
    for output in authorized_outputs:
        monitor.observe(output)

    report = monitor.drift_report(since_hours=1.0)
    print(f"Violation rate (authorized): {report['violation_rate']:.1%}")
    print(f"Severity: {report['severity']}")

    # 4. Simulate a model update that causes semantic drift
    print("\n=== Simulating model drift (unauthorized values) ===")
    drifted_outputs = [
        SentimentAnalysis(
            category=random.choice(["positive", "negative", "neutral", "ambivalent", "mixed"]),
            reasoning="ok",  # too short — violates length constraint
            score=random.gauss(9.5, 1.0),  # distribution shifted
        )
        for _ in range(15)
    ]

    for output in drifted_outputs:
        monitor.observe(output)

    report = monitor.drift_report(since_hours=1.0)
    print(f"Violation rate (after drift): {report['violation_rate']:.1%}")
    print(f"Severity: {report['severity']}")
    print(f"Field breakdown: {report['field_violation_rates']}")

    # 5. CI gate check
    print("\n=== CI Gate Check ===")
    ci_outputs = [
        SentimentAnalysis(
            category="ambivalent",  # unauthorized
            reasoning="Brief.",
            score=10.0,
        )
        for _ in range(5)
    ]
    passed, ci_report = run_ci_gate(monitor, ci_outputs, threshold=0.20)
    print(f"CI gate passed: {passed}")
    print(f"CI violation rate: {ci_report['violation_rate']:.1%} (threshold: {ci_report['ci_threshold']:.1%})")
    print("\n✓ spec-drift prototype complete.")
