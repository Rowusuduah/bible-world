"""
EvalGate — AI Agent Output Evaluation Middleware
Source Pattern: PAT-010 (Genesis 1:2-3 — Logical separation before physical output)
Build ID: BUILD-001
BibleWorld Cycle: 001

The Principle:
"Let there be light" (Genesis 1:3) — logical infrastructure established before luminaries.
An AI agent can produce output before that output is reliable.
EvalGate inserts the evaluation layer between capability and production.

Architecture:
  Agent output → EvalGate intercept → Test suite → Grade → Pass/Fail → Production / Quarantine

Usage:
    gate = EvalGate(threshold=0.8)
    gate.add_suite(FactualAccuracyTests())
    gate.add_suite(SafetyTests())

    result = gate.evaluate(agent_output="The capital of Ghana is Accra.")
    if result.passes:
        deploy(result.output)
    else:
        quarantine(result.output, result.failures)
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class EvalResult:
    """Result of a single evaluation check."""
    check_name: str
    passed: bool
    score: float          # 0.0 to 1.0
    reason: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class GateVerdict:
    """Final verdict from EvalGate after running all suites."""
    output: str
    passes: bool
    overall_score: float  # weighted average across all checks
    results: list[EvalResult] = field(default_factory=list)
    failures: list[EvalResult] = field(default_factory=list)

    def __post_init__(self):
        self.failures = [r for r in self.results if not r.passed]

    def summary(self) -> str:
        status = "PASS" if self.passes else "FAIL"
        return (
            f"EvalGate [{status}] score={self.overall_score:.2f} "
            f"checks={len(self.results)} failures={len(self.failures)}"
        )


class BaseTestSuite:
    """
    Abstract base for test suites. Subclass this to build domain-specific checks.
    Each suite runs a list of named checks against an agent output string.
    """

    def __init__(self, name: str):
        self.name = name
        self._checks: list[tuple[str, Callable[[str], EvalResult]]] = []

    def add_check(self, name: str, fn: Callable[[str], EvalResult]):
        self._checks.append((name, fn))

    def run(self, output: str) -> list[EvalResult]:
        results = []
        for check_name, fn in self._checks:
            try:
                result = fn(output)
                result.check_name = f"{self.name}::{check_name}"
                results.append(result)
            except Exception as e:
                results.append(EvalResult(
                    check_name=f"{self.name}::{check_name}",
                    passed=False,
                    score=0.0,
                    reason=f"Check raised exception: {e}"
                ))
        return results


class LengthCheck(BaseTestSuite):
    """Simple suite: checks minimum and maximum output length."""

    def __init__(self, min_chars: int = 10, max_chars: int = 10000):
        super().__init__("LengthCheck")
        self.add_check("min_length", lambda o: EvalResult(
            check_name="min_length",
            passed=len(o) >= min_chars,
            score=1.0 if len(o) >= min_chars else 0.0,
            reason=f"len={len(o)}, required>={min_chars}"
        ))
        self.add_check("max_length", lambda o: EvalResult(
            check_name="max_length",
            passed=len(o) <= max_chars,
            score=1.0 if len(o) <= max_chars else 0.0,
            reason=f"len={len(o)}, required<={max_chars}"
        ))


class SafetyCheck(BaseTestSuite):
    """
    Basic safety suite: flags outputs containing known dangerous patterns.
    Extend this with domain-specific forbidden phrases for production use.
    """

    DEFAULT_BLOCKED = [
        r"\bpassword\b",
        r"\bapi[_\s]?key\b",
        r"\bsecret\b",
        r"\bcredit\s*card\b",
    ]

    def __init__(self, blocked_patterns: Optional[list[str]] = None):
        super().__init__("SafetyCheck")
        patterns = blocked_patterns or self.DEFAULT_BLOCKED
        for p in patterns:
            captured_p = p
            self.add_check(
                f"blocked:{p[:20]}",
                lambda o, pat=captured_p: EvalResult(
                    check_name=f"blocked:{pat[:20]}",
                    passed=not bool(re.search(pat, o, re.IGNORECASE)),
                    score=0.0 if re.search(pat, o, re.IGNORECASE) else 1.0,
                    reason=f"Pattern '{pat}' {'found' if re.search(pat, o, re.IGNORECASE) else 'not found'}"
                )
            )


class JsonStructureCheck(BaseTestSuite):
    """Verifies that the output is valid JSON and optionally contains required keys."""

    def __init__(self, required_keys: Optional[list[str]] = None):
        super().__init__("JsonStructureCheck")
        self.required_keys = required_keys or []

        def is_valid_json(output: str) -> EvalResult:
            try:
                data = json.loads(output)
                missing = [k for k in self.required_keys if k not in data]
                if missing:
                    return EvalResult(
                        check_name="valid_json",
                        passed=False,
                        score=0.5,
                        reason=f"Valid JSON but missing keys: {missing}"
                    )
                return EvalResult(check_name="valid_json", passed=True, score=1.0)
            except json.JSONDecodeError as e:
                return EvalResult(
                    check_name="valid_json",
                    passed=False,
                    score=0.0,
                    reason=f"Invalid JSON: {e}"
                )

        self.add_check("valid_json_structure", is_valid_json)


class EvalGate:
    """
    The main evaluation gate.

    Configure with a pass threshold (default 0.8) and attach test suites.
    Call evaluate(output) to get a GateVerdict.
    """

    def __init__(self, threshold: float = 0.8):
        assert 0.0 <= threshold <= 1.0, "Threshold must be between 0.0 and 1.0"
        self.threshold = threshold
        self._suites: list[BaseTestSuite] = []

    def add_suite(self, suite: BaseTestSuite) -> "EvalGate":
        self._suites.append(suite)
        return self  # fluent interface

    def evaluate(self, output: str) -> GateVerdict:
        all_results: list[EvalResult] = []
        for suite in self._suites:
            all_results.extend(suite.run(output))

        if not all_results:
            # No suites configured — pass by default with warning
            return GateVerdict(
                output=output,
                passes=True,
                overall_score=1.0,
                results=[],
            )

        overall_score = sum(r.score for r in all_results) / len(all_results)
        passes = overall_score >= self.threshold

        verdict = GateVerdict(
            output=output,
            passes=passes,
            overall_score=overall_score,
            results=all_results,
        )
        return verdict


# ---------------------------------------------------------------------------
# Quick-start example
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    gate = (
        EvalGate(threshold=0.8)
        .add_suite(LengthCheck(min_chars=5, max_chars=500))
        .add_suite(SafetyCheck())
    )

    test_outputs = [
        "The capital of Ghana is Accra. Population approximately 2.5 million.",
        "Short",
        "My password is abc123 and my API_KEY is secret.",
    ]

    for output in test_outputs:
        verdict = gate.evaluate(output)
        print(verdict.summary())
        for f in verdict.failures:
            print(f"  FAIL: {f.check_name} — {f.reason}")
        print()
