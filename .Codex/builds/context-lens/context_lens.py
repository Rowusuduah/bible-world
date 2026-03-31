"""
context-lens: Test whether your LLM actually uses information at every position in its context window.

The lost-in-the-middle problem: LLMs pay heavy attention to information at the start and end of
long contexts. Information buried in the middle is frequently ignored, silently. Traditional
eval suites don't test this — they test correctness on a single input, not positional sensitivity.

context-lens systematically places a "needle" (key fact or instruction) at every position
in the context window, runs the LLM against a question that requires the needle, and produces
a PositionHeatmap showing where your model is reliable vs. unreliable.

This is the missing pre-deployment gate for any RAG pipeline, long-document system, or
multi-turn agent that relies on information anywhere in a long context.

Usage:
    from context_lens import ContextLens, Needle, HaystackTemplate

    lens = ContextLens(model_fn=my_llm_call)
    result = lens.audit(needle=my_needle, haystack=my_haystack, positions=10)
    result.report()

CLI:
    context-lens audit --config my_audit.yaml
    context-lens ci --config my_audit.yaml --min-score 0.80
"""

from __future__ import annotations

import json
import math
import sqlite3
import textwrap
import time
from dataclasses import dataclass, field, asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Optional

__version__ = "0.1.0"
__author__ = "BibleWorld — context-lens"


# ---------------------------------------------------------------------------
# Core Data Structures
# ---------------------------------------------------------------------------

@dataclass
class Needle:
    """A key fact or instruction that must be found and used from within the context.

    Attributes:
        content: The exact text of the needle (the key fact/instruction to insert).
        question: The question the LLM must answer using the needle.
        expected_answer: What a correct, needle-aware answer looks like (for judge matching).
        answer_keywords: Keywords that MUST appear in the response to count as retrieved.
        label: Human-readable label for reports.
    """
    content: str
    question: str
    expected_answer: str
    answer_keywords: list[str]
    label: str = "needle"

    def validate(self) -> None:
        if not self.content.strip():
            raise ValueError("Needle.content must not be empty.")
        if not self.question.strip():
            raise ValueError("Needle.question must not be empty.")
        if not self.answer_keywords:
            raise ValueError("Needle.answer_keywords must not be empty — needed for retrieval check.")


@dataclass
class HaystackTemplate:
    """A template for the surrounding context (the 'haystack') into which the needle is inserted.

    Attributes:
        filler_text: A repeating unit of filler text. Will be repeated to fill context.
        target_tokens: Target approximate token count for the full haystack (default 4000).
        system_prompt: Optional system prompt to prepend.
        tokens_per_filler: Approximate token count of one filler_text repetition.
    """
    filler_text: str
    target_tokens: int = 4000
    system_prompt: str = ""
    tokens_per_filler: int = 50

    def build(self, needle_content: str, position_fraction: float) -> str:
        """
        Build a full context string with the needle inserted at position_fraction (0.0 = start, 1.0 = end).

        Args:
            needle_content: The needle text to insert.
            position_fraction: Float between 0.0 and 1.0 indicating where in the haystack to insert the needle.

        Returns:
            Full context string with needle at the specified position.
        """
        if not 0.0 <= position_fraction <= 1.0:
            raise ValueError(f"position_fraction must be between 0.0 and 1.0, got {position_fraction}")

        repetitions = max(1, self.target_tokens // self.tokens_per_filler)
        needle_index = int(position_fraction * repetitions)
        needle_index = max(0, min(needle_index, repetitions))

        parts: list[str] = []
        for i in range(repetitions):
            if i == needle_index:
                parts.append(f"\n\n[KEY INFORMATION]: {needle_content}\n\n")
            parts.append(self.filler_text)

        if needle_index >= repetitions:
            parts.append(f"\n\n[KEY INFORMATION]: {needle_content}\n\n")

        return "\n".join(parts)


@dataclass
class PositionResult:
    """Result for a single needle-at-position test.

    Attributes:
        position_fraction: Where in context the needle was placed (0.0 = start, 1.0 = end).
        position_label: Human-readable position label (e.g., "position 3/10").
        response: The raw LLM response.
        retrieved: Whether the LLM successfully used the needle (based on keyword check).
        keyword_hits: Which of the expected keywords appeared in the response.
        keyword_misses: Which keywords were absent.
        latency_ms: Time taken for the LLM call in milliseconds.
        error: Error message if the call failed.
    """
    position_fraction: float
    position_label: str
    response: str
    retrieved: bool
    keyword_hits: list[str]
    keyword_misses: list[str]
    latency_ms: float
    error: str = ""


@dataclass
class PositionHeatmap:
    """The complete result of a context-lens audit.

    Attributes:
        needle_label: Label of the tested needle.
        positions_tested: Number of positions tested.
        results: PositionResult for each position.
        retrieval_score: Fraction of positions where needle was retrieved (0.0–1.0).
        fault_zones: Positions (as fractions) where retrieval failed.
        fault_zone_label: Human-readable description of failure pattern.
        model_name: Name of the model under test (if provided).
        timestamp: When the audit ran.
        duration_seconds: Total audit duration.
        verdict: RELIABLE / CONDITIONAL / UNRELIABLE
    """
    needle_label: str
    positions_tested: int
    results: list[PositionResult]
    retrieval_score: float
    fault_zones: list[float]
    fault_zone_label: str
    model_name: str
    timestamp: str
    duration_seconds: float
    verdict: str  # RELIABLE | CONDITIONAL | UNRELIABLE

    # Thresholds used
    reliable_threshold: float = 0.90
    conditional_threshold: float = 0.70

    def to_dict(self) -> dict:
        return {
            "needle_label": self.needle_label,
            "positions_tested": self.positions_tested,
            "retrieval_score": round(self.retrieval_score, 4),
            "fault_zones": self.fault_zones,
            "fault_zone_label": self.fault_zone_label,
            "model_name": self.model_name,
            "timestamp": self.timestamp,
            "duration_seconds": round(self.duration_seconds, 2),
            "verdict": self.verdict,
            "reliable_threshold": self.reliable_threshold,
            "conditional_threshold": self.conditional_threshold,
            "results": [
                {
                    "position_fraction": r.position_fraction,
                    "position_label": r.position_label,
                    "retrieved": r.retrieved,
                    "keyword_hits": r.keyword_hits,
                    "keyword_misses": r.keyword_misses,
                    "latency_ms": round(r.latency_ms, 1),
                    "response_preview": r.response[:200] if r.response else "",
                    "error": r.error,
                }
                for r in self.results
            ]
        }

    def report(self, verbose: bool = True) -> str:
        """Generate a human-readable report of the audit results."""
        lines = [
            "",
            "=" * 72,
            "  context-lens Audit Report",
            "=" * 72,
            f"  Needle      : {self.needle_label}",
            f"  Model       : {self.model_name or 'unknown'}",
            f"  Positions   : {self.positions_tested}",
            f"  Score       : {self.retrieval_score:.1%}  ({self._score_bar()})",
            f"  Verdict     : {self._verdict_colored()}",
            f"  Timestamp   : {self.timestamp}",
            f"  Duration    : {self.duration_seconds:.1f}s",
            "-" * 72,
            "  Position Heatmap:",
            "",
        ]

        for r in self.results:
            icon = "[OK]" if r.retrieved else "[MISS]"
            bar = "##" if r.retrieved else ".."
            lines.append(f"    {r.position_label:20s}  {icon}  {bar}  {r.position_fraction:.2f}")

        if self.fault_zones:
            lines += [
                "",
                f"  Fault Zones ({len(self.fault_zones)}):",
                f"    {self.fault_zone_label}",
                f"    Positions: {[f'{z:.2f}' for z in self.fault_zones]}",
            ]
        else:
            lines += ["", "  No fault zones detected."]

        if verbose and self.results:
            lines += ["", "  Per-Position Details:", ""]
            for r in self.results:
                lines.append(f"    {r.position_label} | retrieved={r.retrieved} | "
                              f"hits={r.keyword_hits} | misses={r.keyword_misses} | "
                              f"latency={r.latency_ms:.0f}ms")
                if r.error:
                    lines.append(f"      ERROR: {r.error}")
                elif r.response:
                    preview = r.response[:120].replace("\n", " ")
                    lines.append(f"      Response: {preview}...")

        lines += [
            "",
            "=" * 72,
            "",
        ]

        text = "\n".join(lines)
        print(text)
        return text

    def _score_bar(self) -> str:
        filled = round(self.retrieval_score * 20)
        return "[" + "#" * filled + "." * (20 - filled) + "]"

    def _verdict_colored(self) -> str:
        if self.verdict == "RELIABLE":
            return f"RELIABLE  (>= {self.reliable_threshold:.0%} threshold passed)"
        elif self.verdict == "CONDITIONAL":
            return f"CONDITIONAL  (>= {self.conditional_threshold:.0%} but < {self.reliable_threshold:.0%})"
        else:
            return f"UNRELIABLE  (< {self.conditional_threshold:.0%} — DO NOT SHIP)"


# ---------------------------------------------------------------------------
# Judge: Keyword-Based Retrieval Checker
# ---------------------------------------------------------------------------

class KeywordJudge:
    """Checks whether LLM response contains the expected answer keywords.

    This is the v0.1 judge — zero-cost, deterministic, no API calls.
    v0.2 will add an optional LLM-as-judge for semantic matching.
    """

    def evaluate(self, response: str, needle: Needle) -> tuple[bool, list[str], list[str]]:
        """
        Returns:
            (retrieved, keyword_hits, keyword_misses)
        """
        response_lower = response.lower()
        hits = []
        misses = []
        for kw in needle.answer_keywords:
            if kw.lower() in response_lower:
                hits.append(kw)
            else:
                misses.append(kw)

        # Retrieved if at least 50% of keywords found (configurable in future)
        retrieved = len(hits) >= math.ceil(len(needle.answer_keywords) * 0.5)
        return retrieved, hits, misses


# ---------------------------------------------------------------------------
# Core Engine
# ---------------------------------------------------------------------------

class ContextLens:
    """Main context-lens engine.

    Args:
        model_fn: A callable that accepts a prompt string and returns a response string.
                  Signature: model_fn(prompt: str) -> str
                  This is your LLM call — any provider, any framework.
        model_name: Optional name for the model under test (for reports).
        reliable_threshold: Fraction of positions that must be retrieved to get RELIABLE verdict.
                           Default 0.90.
        conditional_threshold: Minimum fraction to avoid UNRELIABLE verdict. Default 0.70.
        db_path: Path to SQLite database for storing audit history. Default ".context_lens.db".
        judge: Judge instance for evaluating retrieval. Default: KeywordJudge.
    """

    def __init__(
        self,
        model_fn: Callable[[str], str],
        model_name: str = "",
        reliable_threshold: float = 0.90,
        conditional_threshold: float = 0.70,
        db_path: str = ".context_lens.db",
        judge: Optional[KeywordJudge] = None,
    ):
        self.model_fn = model_fn
        self.model_name = model_name
        self.reliable_threshold = reliable_threshold
        self.conditional_threshold = conditional_threshold
        self.db_path = db_path
        self.judge = judge or KeywordJudge()
        self._init_db()

    def audit(
        self,
        needle: Needle,
        haystack: HaystackTemplate,
        positions: int = 10,
        verbose: bool = True,
    ) -> PositionHeatmap:
        """
        Run a full context position audit.

        Places the needle at `positions` evenly-spaced positions across the context,
        calls the LLM at each position, and records whether it retrieved the needle.

        Args:
            needle: The Needle to test.
            haystack: The HaystackTemplate defining context structure.
            positions: Number of positions to test (default 10). More positions = more coverage.
            verbose: If True, prints a progress indicator.

        Returns:
            PositionHeatmap with full results.
        """
        needle.validate()

        if positions < 2:
            raise ValueError("positions must be >= 2 (at least start and end).")

        t_start = time.time()
        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        position_fractions = [i / (positions - 1) for i in range(positions)]
        results: list[PositionResult] = []

        for i, frac in enumerate(position_fractions):
            label = f"position {i + 1}/{positions}"
            if verbose:
                print(f"  [context-lens] Testing {label} (fraction={frac:.2f})...", end=" ", flush=True)

            context = haystack.build(needle.content, frac)
            prompt = self._build_prompt(context, needle.question, haystack.system_prompt)

            t_call = time.time()
            response = ""
            error = ""
            try:
                response = self.model_fn(prompt)
            except Exception as e:
                error = str(e)
                response = ""

            latency_ms = (time.time() - t_call) * 1000
            retrieved, hits, misses = self.judge.evaluate(response, needle)

            if verbose:
                status = "OK" if retrieved else "MISS"
                print(f"[{status}]")

            results.append(PositionResult(
                position_fraction=frac,
                position_label=label,
                response=response,
                retrieved=retrieved,
                keyword_hits=hits,
                keyword_misses=misses,
                latency_ms=latency_ms,
                error=error,
            ))

        duration = time.time() - t_start

        # Compute heatmap metrics
        retrieved_count = sum(1 for r in results if r.retrieved)
        retrieval_score = retrieved_count / len(results) if results else 0.0
        fault_zones = [r.position_fraction for r in results if not r.retrieved]

        fault_zone_label = self._describe_fault_zones(fault_zones, positions)

        if retrieval_score >= self.reliable_threshold:
            verdict = "RELIABLE"
        elif retrieval_score >= self.conditional_threshold:
            verdict = "CONDITIONAL"
        else:
            verdict = "UNRELIABLE"

        heatmap = PositionHeatmap(
            needle_label=needle.label,
            positions_tested=positions,
            results=results,
            retrieval_score=retrieval_score,
            fault_zones=fault_zones,
            fault_zone_label=fault_zone_label,
            model_name=self.model_name,
            timestamp=timestamp,
            duration_seconds=duration,
            verdict=verdict,
            reliable_threshold=self.reliable_threshold,
            conditional_threshold=self.conditional_threshold,
        )

        self._store_result(heatmap)
        return heatmap

    def audit_multi(
        self,
        needles: list[Needle],
        haystack: HaystackTemplate,
        positions: int = 10,
        verbose: bool = True,
    ) -> list[PositionHeatmap]:
        """
        Run a complete audit across multiple needles.

        Args:
            needles: List of needles to test — each tested at all positions.
            haystack: HaystackTemplate.
            positions: Number of positions per needle.
            verbose: Print progress.

        Returns:
            List of PositionHeatmaps, one per needle.
        """
        heatmaps = []
        for idx, needle in enumerate(needles):
            if verbose:
                print(f"\n[context-lens] Needle {idx + 1}/{len(needles)}: {needle.label}")
            hm = self.audit(needle, haystack, positions=positions, verbose=verbose)
            heatmaps.append(hm)

        return heatmaps

    def summary_report(self, heatmaps: list[PositionHeatmap]) -> dict:
        """
        Generate a multi-needle summary report.

        Returns a dict with aggregate statistics suitable for CI gate decisions.
        """
        if not heatmaps:
            return {}

        scores = [hm.retrieval_score for hm in heatmaps]
        verdicts = [hm.verdict for hm in heatmaps]

        overall_score = sum(scores) / len(scores)
        all_reliable = all(v == "RELIABLE" for v in verdicts)
        any_unreliable = any(v == "UNRELIABLE" for v in verdicts)

        return {
            "model_name": heatmaps[0].model_name,
            "needles_tested": len(heatmaps),
            "overall_score": round(overall_score, 4),
            "all_reliable": all_reliable,
            "any_unreliable": any_unreliable,
            "per_needle": [
                {
                    "label": hm.needle_label,
                    "score": round(hm.retrieval_score, 4),
                    "verdict": hm.verdict,
                    "fault_zones": hm.fault_zones,
                }
                for hm in heatmaps
            ],
            "overall_verdict": (
                "RELIABLE" if all_reliable else
                "UNRELIABLE" if any_unreliable else
                "CONDITIONAL"
            )
        }

    def ci_gate(
        self,
        heatmaps: list[PositionHeatmap],
        min_score: float = 0.80,
        fail_on_unreliable: bool = True,
    ) -> tuple[bool, str]:
        """
        CI gate check.

        Args:
            heatmaps: List of PositionHeatmaps from audit_multi.
            min_score: Minimum overall retrieval score to pass (default 0.80).
            fail_on_unreliable: If True, any UNRELIABLE needle verdict fails the gate.

        Returns:
            (passed: bool, message: str)
        """
        summary = self.summary_report(heatmaps)
        overall_score = summary.get("overall_score", 0.0)
        any_unreliable = summary.get("any_unreliable", False)

        if fail_on_unreliable and any_unreliable:
            unreliable = [n["label"] for n in summary["per_needle"] if n["verdict"] == "UNRELIABLE"]
            msg = f"CI GATE FAILED: UNRELIABLE verdict on needle(s): {unreliable}"
            return False, msg

        if overall_score < min_score:
            msg = (f"CI GATE FAILED: overall_score={overall_score:.1%} < min_score={min_score:.1%}. "
                   f"Model does not reliably retrieve information from all context positions.")
            return False, msg

        msg = f"CI GATE PASSED: overall_score={overall_score:.1%} >= min_score={min_score:.1%}. Verdict: {summary['overall_verdict']}."
        return True, msg

    def history(self, limit: int = 20) -> list[dict]:
        """Return recent audit history from SQLite store."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, needle_label, model_name, retrieval_score, verdict, timestamp "
                "FROM audits ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "needle_label": r[1],
                    "model_name": r[2],
                    "retrieval_score": r[3],
                    "verdict": r[4],
                    "timestamp": r[5],
                }
                for r in rows
            ]
        except Exception:
            return []
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_prompt(self, context: str, question: str, system_prompt: str) -> str:
        """Build the full prompt for the LLM call."""
        parts = []
        if system_prompt:
            parts.append(f"System: {system_prompt}\n\n")
        parts.append(f"Context:\n{context}\n\n")
        parts.append(f"Question: {question}\n\nAnswer:")
        return "".join(parts)

    def _describe_fault_zones(self, fault_zones: list[float], positions: int) -> str:
        """Produce a human-readable description of fault zone patterns."""
        if not fault_zones:
            return "No fault zones — full context reliability confirmed."

        # Check for middle-heavy failure (the classic lost-in-the-middle pattern)
        middle_faults = [z for z in fault_zones if 0.25 < z < 0.75]
        edge_faults = [z for z in fault_zones if z <= 0.25 or z >= 0.75]

        if len(middle_faults) > len(edge_faults) and middle_faults:
            return (
                f"MIDDLE-HEAVY FAILURE (lost-in-the-middle pattern detected): "
                f"{len(middle_faults)}/{positions} middle positions failed. "
                f"Information in the middle of this context is not reliably retrieved."
            )
        elif edge_faults and not middle_faults:
            return (
                f"EDGE FAILURE: {len(edge_faults)}/{positions} edge positions failed. "
                f"Information at context boundaries is not reliably retrieved."
            )
        else:
            return (
                f"SCATTERED FAILURES: {len(fault_zones)}/{positions} positions failed. "
                f"No clear pattern — general context retrieval degradation."
            )

    def _init_db(self) -> None:
        """Initialize SQLite database for audit history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                needle_label TEXT,
                model_name TEXT,
                positions_tested INTEGER,
                retrieval_score REAL,
                fault_zones TEXT,
                fault_zone_label TEXT,
                verdict TEXT,
                timestamp TEXT,
                duration_seconds REAL,
                full_result TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _store_result(self, heatmap: PositionHeatmap) -> None:
        """Store audit result to SQLite."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO audits
                (needle_label, model_name, positions_tested, retrieval_score,
                 fault_zones, fault_zone_label, verdict, timestamp, duration_seconds, full_result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                heatmap.needle_label,
                heatmap.model_name,
                heatmap.positions_tested,
                heatmap.retrieval_score,
                json.dumps(heatmap.fault_zones),
                heatmap.fault_zone_label,
                heatmap.verdict,
                heatmap.timestamp,
                heatmap.duration_seconds,
                json.dumps(heatmap.to_dict()),
            ))
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# YAML Config Loader
# ---------------------------------------------------------------------------

def load_config(config_path: str) -> dict:
    """Load an audit config from a YAML file.

    Returns a dict with:
        model_name, needles, haystack, positions, reliable_threshold, conditional_threshold

    Example YAML:
        model_name: gpt-4o
        positions: 10
        reliable_threshold: 0.90
        haystack:
          filler_text: "The quick brown fox jumps over the lazy dog."
          target_tokens: 4000
          tokens_per_filler: 10
        needles:
          - label: "API key location"
            content: "The API key for the payment service is PAY-SK-TEST-12345."
            question: "What is the API key for the payment service?"
            expected_answer: "PAY-SK-TEST-12345"
            answer_keywords: ["PAY-SK-TEST-12345"]
    """
    try:
        import yaml
        with open(config_path) as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback: try to read as JSON
        with open(config_path) as f:
            return json.load(f)


def build_from_config(config: dict, model_fn: Callable[[str], str]) -> tuple[ContextLens, list[Needle], HaystackTemplate, int]:
    """Build ContextLens, needles, and haystack from a config dict."""
    haystack_cfg = config.get("haystack", {})
    haystack = HaystackTemplate(
        filler_text=haystack_cfg.get("filler_text", "The following is background information. "),
        target_tokens=haystack_cfg.get("target_tokens", 4000),
        tokens_per_filler=haystack_cfg.get("tokens_per_filler", 10),
        system_prompt=haystack_cfg.get("system_prompt", ""),
    )

    needles = []
    for n in config.get("needles", []):
        needles.append(Needle(
            content=n["content"],
            question=n["question"],
            expected_answer=n["expected_answer"],
            answer_keywords=n["answer_keywords"],
            label=n.get("label", "needle"),
        ))

    lens = ContextLens(
        model_fn=model_fn,
        model_name=config.get("model_name", ""),
        reliable_threshold=config.get("reliable_threshold", 0.90),
        conditional_threshold=config.get("conditional_threshold", 0.70),
        db_path=config.get("db_path", ".context_lens.db"),
    )

    positions = config.get("positions", 10)
    return lens, needles, haystack, positions


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli_main() -> None:
    """CLI entry point for context-lens."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="context-lens",
        description="Test whether your LLM retrieves information from every position in its context window.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # audit command
    audit_parser = subparsers.add_parser("audit", help="Run a context position audit.")
    audit_parser.add_argument("--config", required=True, help="Path to YAML/JSON audit config file.")
    audit_parser.add_argument("--output", help="Write JSON result to this file.")
    audit_parser.add_argument("--quiet", action="store_true", help="Suppress verbose output.")

    # ci command
    ci_parser = subparsers.add_parser("ci", help="Run audit and exit with code 1 if gate fails.")
    ci_parser.add_argument("--config", required=True, help="Path to YAML/JSON audit config file.")
    ci_parser.add_argument("--min-score", type=float, default=0.80, help="Minimum retrieval score (default 0.80).")
    ci_parser.add_argument("--no-fail-unreliable", action="store_true", help="Don't fail on UNRELIABLE verdict.")

    # history command
    history_parser = subparsers.add_parser("history", help="Show audit history.")
    history_parser.add_argument("--db", default=".context_lens.db", help="SQLite database path.")
    history_parser.add_argument("--limit", type=int, default=10, help="Number of records to show.")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "history":
        lens = ContextLens(model_fn=lambda x: "", db_path=args.db)
        records = lens.history(limit=args.limit)
        if not records:
            print("No audit history found.")
        else:
            print(f"\n{'ID':4}  {'Needle':30}  {'Model':20}  {'Score':7}  {'Verdict':12}  Timestamp")
            print("-" * 100)
            for r in records:
                print(f"{r['id']:4}  {r['needle_label']:30}  {r['model_name']:20}  "
                      f"{r['retrieval_score']:.1%}  {r['verdict']:12}  {r['timestamp']}")
        sys.exit(0)

    # Load config for audit/ci commands
    config = load_config(args.config)

    # For CLI usage, we need a model_fn — look for API key environment variables
    model_fn = _build_cli_model_fn(config)

    lens, needles, haystack, positions = build_from_config(config, model_fn)

    if not needles:
        print("ERROR: No needles defined in config.")
        sys.exit(1)

    verbose = not getattr(args, "quiet", False)
    heatmaps = lens.audit_multi(needles, haystack, positions=positions, verbose=verbose)
    summary = lens.summary_report(heatmaps)

    if args.command == "audit":
        print(f"\n[context-lens] Summary:")
        print(f"  Needles tested    : {summary['needles_tested']}")
        print(f"  Overall score     : {summary['overall_score']:.1%}")
        print(f"  Overall verdict   : {summary['overall_verdict']}")
        for n in summary["per_needle"]:
            print(f"    {n['label']:30}  {n['score']:.1%}  {n['verdict']}")

        if getattr(args, "output", None):
            Path(args.output).write_text(json.dumps(summary, indent=2))
            print(f"\n[context-lens] Result written to {args.output}")

    elif args.command == "ci":
        min_score = args.min_score
        fail_on_unreliable = not args.no_fail_unreliable
        passed, message = lens.ci_gate(heatmaps, min_score=min_score, fail_on_unreliable=fail_on_unreliable)
        print(f"\n[context-lens] {message}")
        sys.exit(0 if passed else 1)


def _build_cli_model_fn(config: dict) -> Callable[[str], str]:
    """Build a model function from config for CLI use.

    Supports:
    - provider: "anthropic" with ANTHROPIC_API_KEY
    - provider: "openai" with OPENAI_API_KEY
    - provider: "mock" for testing (returns empty responses)
    """
    import os
    provider = config.get("provider", "anthropic").lower()
    model = config.get("model", "")

    if provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            print("WARNING: ANTHROPIC_API_KEY not set. Using mock responses.")
            return lambda prompt: ""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            model_id = model or "claude-3-5-haiku-20241022"
            def anthropic_fn(prompt: str) -> str:
                response = client.messages.create(
                    model=model_id,
                    max_tokens=256,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text
            return anthropic_fn
        except ImportError:
            print("WARNING: anthropic package not installed. Using mock responses.")
            return lambda prompt: ""

    elif provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            print("WARNING: OPENAI_API_KEY not set. Using mock responses.")
            return lambda prompt: ""
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            model_id = model or "gpt-4o-mini"
            def openai_fn(prompt: str) -> str:
                response = client.chat.completions.create(
                    model=model_id,
                    max_tokens=256,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content or ""
            return openai_fn
        except ImportError:
            print("WARNING: openai package not installed. Using mock responses.")
            return lambda prompt: ""

    else:
        # mock provider — for testing
        return lambda prompt: ""


if __name__ == "__main__":
    _cli_main()
