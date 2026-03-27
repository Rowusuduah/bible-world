# prompt-shield — Technical Specification
## v0.1 Implementation Spec

**Version:** 0.1.0
**Status:** IN-DESIGN
**Biblical Pattern:** PAT-048 (Daniel 5:25-28), PAT-049 (Matthew 7:24-27), PAT-050 (Proverbs 17:3)
**Pivot_Score:** 8.75
**Build Score:** 9.1/10

---

## 1. Core Data Models

```python
# prompt_shield/models.py

from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime
import hashlib
import json


BrittlenessVerdict = Literal["ROBUST", "CONDITIONAL", "BRITTLE"]
ParaphraseLevel = Literal["lexical", "syntactic", "semantic"]


@dataclass
class ParaphraseVariant:
    """A single semantically-equivalent variant of an original input."""
    original: str
    variant: str
    level: ParaphraseLevel
    similarity_score: float  # cosine similarity to original (0.0-1.0)
    validated: bool = False  # True if similarity_score >= min_similarity threshold


@dataclass
class VariantResult:
    """Output produced by the LLM function for a single variant."""
    variant: ParaphraseVariant
    output: str
    deviation_score: float   # 1 - cosine_similarity(canonical_output, variant_output)
    is_deviant: bool         # True if deviation_score > deviation_threshold


@dataclass
class FaultLine:
    """A specific paraphrase variant that causes brittleness."""
    level: ParaphraseLevel
    variant: str
    deviation_score: float
    canonical_fragment: str  # first 100 chars of canonical output
    actual_fragment: str     # first 100 chars of variant output
    recommendation: str


@dataclass
class LevelBreakdown:
    """Brittleness breakdown by paraphrase level."""
    level: ParaphraseLevel
    score: float
    variant_count: int
    deviant_count: int
    verdict: BrittlenessVerdict


@dataclass
class BrittleCertificate:
    """
    The crucible output — PAT-050 (Proverbs 17:3).
    Structured artifact proving the prompt passed (or failed) the brittleness audit.
    """
    certificate_id: str
    issued_at: datetime
    prompt_hash: str
    prompt_name: str
    verdict: BrittlenessVerdict
    brittleness_score: float
    threshold: float
    confidence_lower: float
    confidence_upper: float
    variant_count: int
    level_breakdown: list[LevelBreakdown]
    fault_lines: list[FaultLine]

    def to_json(self) -> str:
        data = {
            "certificate_id": self.certificate_id,
            "issued_at": self.issued_at.isoformat(),
            "prompt_hash": self.prompt_hash,
            "prompt_name": self.prompt_name,
            "verdict": self.verdict,
            "brittleness_score": round(self.brittleness_score, 4),
            "threshold": self.threshold,
            "confidence_interval": [
                round(self.confidence_lower, 4),
                round(self.confidence_upper, 4)
            ],
            "variant_count": self.variant_count,
            "level_breakdown": {
                b.level: {
                    "score": round(b.score, 4),
                    "variant_count": b.variant_count,
                    "deviant_count": b.deviant_count,
                    "verdict": b.verdict
                }
                for b in self.level_breakdown
            },
            "fault_lines": [
                {
                    "level": f.level,
                    "variant": f.variant,
                    "deviation_score": round(f.deviation_score, 4),
                    "recommendation": f.recommendation
                }
                for f in self.fault_lines
            ]
        }
        return json.dumps(data, indent=2)

    def to_markdown(self) -> str:
        verdict_emoji = {"ROBUST": "✅", "CONDITIONAL": "⚠️", "BRITTLE": "❌"}[self.verdict]
        lines = [
            f"# BrittleCertificate — {self.prompt_name}",
            f"",
            f"**Verdict:** {verdict_emoji} {self.verdict}",
            f"**BrittlenessScore:** {self.brittleness_score:.4f} (threshold: {self.threshold})",
            f"**Confidence Interval:** [{self.confidence_lower:.4f}, {self.confidence_upper:.4f}]",
            f"**Variants Tested:** {self.variant_count}",
            f"**Issued:** {self.issued_at.isoformat()}",
            f"**Certificate ID:** `{self.certificate_id}`",
            f"",
            f"## Level Breakdown",
            f"",
            f"| Level | Score | Deviant/Total | Verdict |",
            f"|-------|-------|---------------|---------|",
        ]
        for b in self.level_breakdown:
            v = {"ROBUST": "✅", "CONDITIONAL": "⚠️", "BRITTLE": "❌"}[b.verdict]
            lines.append(f"| {b.level} | {b.score:.4f} | {b.deviant_count}/{b.variant_count} | {v} {b.verdict} |")

        if self.fault_lines:
            lines.extend(["", "## Fault Lines", ""])
            for i, f in enumerate(self.fault_lines, 1):
                lines.extend([
                    f"### {i}. {f.level.capitalize()} brittleness",
                    f"**Variant:** `{f.variant}`",
                    f"**Deviation:** {f.deviation_score:.4f}",
                    f"**Recommendation:** {f.recommendation}",
                    ""
                ])

        return "\n".join(lines)


@dataclass
class BrittlenessResult:
    """Complete result of a brittleness check run."""
    score: float
    verdict: BrittlenessVerdict
    certificate: BrittleCertificate
    variant_results: list[VariantResult]
    test_input_count: int
    run_duration_seconds: float
```

---

## 2. BrittlenessEngine

```python
# prompt_shield/engine.py

import re
from typing import Callable
from .models import ParaphraseVariant, ParaphraseLevel


class BrittlenessEngine:
    """
    Generates and validates paraphrase variants for brittleness testing.

    PAT-049 (Matthew 7 — Two Builders): Three stress levels correspond to
    three storm vectors (rain/lexical, streams/syntactic, wind/semantic).
    All three must be applied for a complete stress test.
    """

    def __init__(
        self,
        variants_per_input: int = 8,
        levels: list[ParaphraseLevel] = None,
        min_similarity: float = 0.75,
        max_similarity: float = 0.98,  # reject near-duplicates
        paraphrase_model: str = "ramsrigouthamg/t5_paraphraser",
        similarity_model: str = "all-MiniLM-L6-v2",
    ):
        self.variants_per_input = variants_per_input
        self.levels = levels or ["lexical", "semantic"]
        self.min_similarity = min_similarity
        self.max_similarity = max_similarity
        self._paraphrase_model = None
        self._paraphrase_tokenizer = None
        self._similarity_model = None
        self._paraphrase_model_name = paraphrase_model
        self._similarity_model_name = similarity_model

    def _load_models(self):
        """Lazy load models on first use."""
        if self._similarity_model is None:
            from sentence_transformers import SentenceTransformer
            self._similarity_model = SentenceTransformer(self._similarity_model_name)

        if self._paraphrase_model is None and "t5" in self._paraphrase_model_name.lower():
            from transformers import T5ForConditionalGeneration, T5Tokenizer
            self._paraphrase_model = T5ForConditionalGeneration.from_pretrained(
                self._paraphrase_model_name
            )
            self._paraphrase_tokenizer = T5Tokenizer.from_pretrained(
                self._paraphrase_model_name
            )

    def generate_variants(self, text: str) -> list[ParaphraseVariant]:
        """Generate all requested paraphrase variants for a single input."""
        self._load_models()
        variants = []

        variants_per_level = max(1, self.variants_per_input // len(self.levels))

        for level in self.levels:
            if level == "lexical":
                raw = self._generate_lexical(text, variants_per_level)
            elif level == "syntactic":
                raw = self._generate_syntactic(text, variants_per_level)
            elif level == "semantic":
                raw = self._generate_semantic(text, variants_per_level)
            else:
                raw = []

            for candidate in raw:
                similarity = self._compute_similarity(text, candidate)
                if (self.min_similarity <= similarity <= self.max_similarity
                        and candidate.strip() != text.strip()):
                    variants.append(ParaphraseVariant(
                        original=text,
                        variant=candidate,
                        level=level,
                        similarity_score=similarity,
                        validated=True
                    ))

        return variants

    def _generate_semantic(self, text: str, n: int) -> list[str]:
        """
        Generate semantic paraphrases using T5 paraphraser.
        Highest quality, covers full meaning reformulation.
        Corresponds to the 'wind' stress vector in Matthew 7.
        """
        if self._paraphrase_model is None:
            return self._generate_semantic_fallback(text, n)

        import torch
        input_ids = self._paraphrase_tokenizer.encode(
            f"paraphrase: {text} </s>",
            return_tensors="pt",
            max_length=256,
            truncation=True
        )
        with torch.no_grad():
            outputs = self._paraphrase_model.generate(
                input_ids,
                max_length=256,
                num_beams=n * 2,
                num_return_sequences=n,
                temperature=1.5,
                early_stopping=True
            )
        return [
            self._paraphrase_tokenizer.decode(o, skip_special_tokens=True)
            for o in outputs
        ]

    def _generate_lexical(self, text: str, n: int) -> list[str]:
        """
        Generate lexical variants via synonym substitution.
        Corresponds to the 'rain' stress vector in Matthew 7.
        """
        try:
            import nltk
            from nltk.corpus import wordnet
            nltk.download("wordnet", quiet=True)
            nltk.download("averaged_perceptron_tagger", quiet=True)
        except ImportError:
            return []

        words = text.split()
        variants = []
        for _ in range(n):
            new_words = []
            for word in words:
                synsets = wordnet.synsets(word)
                synonyms = set()
                for syn in synsets:
                    for lemma in syn.lemmas():
                        synonym = lemma.name().replace("_", " ")
                        if synonym.lower() != word.lower():
                            synonyms.add(synonym)
                if synonyms and len(word) > 3:
                    import random
                    new_words.append(random.choice(list(synonyms)))
                else:
                    new_words.append(word)
            variants.append(" ".join(new_words))
        return list(set(variants))

    def _generate_syntactic(self, text: str, n: int) -> list[str]:
        """
        Generate syntactic variants via structural transformation.
        Corresponds to the 'streams' stress vector in Matthew 7.
        v0.1: Simple rule-based transformations. v0.2: dependency parsing.
        """
        variants = []
        # Contraction expansion/contraction
        contractions = {
            "what's": "what is", "what is": "what's",
            "i'm": "i am", "i am": "i'm",
            "can't": "cannot", "cannot": "can't",
            "don't": "do not", "do not": "don't",
            "how's": "how is", "isn't": "is not",
        }
        variant = text
        for k, v in contractions.items():
            if k.lower() in variant.lower():
                variant = re.sub(re.escape(k), v, variant, flags=re.IGNORECASE)
                break
        if variant != text:
            variants.append(variant)

        # Question restructuring (simple)
        if text.lower().startswith("what is"):
            variants.append(text.replace("What is", "Tell me", 1).replace("what is", "tell me", 1))
        if text.lower().startswith("how do i"):
            variants.append(text.replace("How do I", "What is the way to", 1)
                             .replace("how do i", "what is the way to", 1))

        # Pad to n
        while len(variants) < n:
            variants.append(text)  # will be filtered as near-duplicate
        return variants[:n]

    def _generate_semantic_fallback(self, text: str, n: int) -> list[str]:
        """Fallback: simple question starters for short texts."""
        starters = [
            "Could you tell me", "I'd like to know", "Can you show me",
            "Please tell me", "I need to know", "What would be"
        ]
        variants = []
        for starter in starters[:n]:
            if "?" in text:
                core = text.replace("What is ", "").replace("?", "").strip()
                variants.append(f"{starter} {core.lower()}?")
        return variants

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute semantic similarity between two texts."""
        from sentence_transformers import util
        embeddings = self._similarity_model.encode([text1, text2])
        return float(util.cos_sim(embeddings[0], embeddings[1]))
```

---

## 3. BrittlenessRunner

```python
# prompt_shield/runner.py

import time
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Callable
from .models import (
    BrittlenessResult, BrittleCertificate, BrittlenessVerdict,
    VariantResult, LevelBreakdown, FaultLine
)
from .engine import BrittlenessEngine
from .store import BrittlenessStore


class BrittlenessRunner:
    """
    Executes the brittleness audit.

    PAT-048 (Daniel 5 — TEKEL Audit):
    The runner is the independent evaluator — it uses the user's eval function
    as the measurement instrument, just as Daniel used the words themselves
    as the measurement instrument (not the king's interpreters).
    """

    ROBUST_THRESHOLD = 0.15
    BRITTLE_THRESHOLD = 0.30

    def __init__(
        self,
        llm_function: Callable[[str], str],
        engine: BrittlenessEngine = None,
        store_path: str = "./shield.db",
        deviation_threshold: float = 0.15,
        similarity_model: str = "all-MiniLM-L6-v2",
    ):
        self.llm_function = llm_function
        self.engine = engine or BrittlenessEngine()
        self.store = BrittlenessStore(store_path)
        self.deviation_threshold = deviation_threshold
        self._similarity_model = None
        self._similarity_model_name = similarity_model

    def _load_similarity_model(self):
        if self._similarity_model is None:
            from sentence_transformers import SentenceTransformer
            self._similarity_model = SentenceTransformer(self._similarity_model_name)

    def _compute_deviation(self, canonical: str, variant_output: str) -> float:
        """Compute output deviation (0.0 = identical, 1.0 = completely different)."""
        from sentence_transformers import util
        self._load_similarity_model()
        embs = self._similarity_model.encode([canonical, variant_output])
        similarity = float(util.cos_sim(embs[0], embs[1]))
        return 1.0 - similarity

    def _compute_confidence_interval(self, deviants: int, total: int) -> tuple[float, float]:
        """Wilson score interval for proportion of deviants."""
        import math
        if total == 0:
            return 0.0, 0.0
        n = total
        p = deviants / n
        z = 1.96  # 95% confidence
        center = (p + z**2/(2*n)) / (1 + z**2/n)
        margin = (z * math.sqrt(p*(1-p)/n + z**2/(4*n**2))) / (1 + z**2/n)
        return max(0.0, center - margin), min(1.0, center + margin)

    def _verdict(self, score: float, threshold: float) -> BrittlenessVerdict:
        if score <= self.ROBUST_THRESHOLD:
            return "ROBUST"
        elif score <= threshold:
            return "CONDITIONAL"
        else:
            return "BRITTLE"

    def run(
        self,
        test_inputs: list[str],
        threshold: float = 0.30,
        prompt_name: str = "unnamed_prompt",
    ) -> BrittlenessResult:
        """
        Run the TEKEL audit (PAT-048) — weigh the prompt on the scales.

        Args:
            test_inputs: List of test input strings to generate variants for
            threshold: BrittlenessScore above which verdict is BRITTLE
            prompt_name: Name for this prompt (used in certificate)

        Returns:
            BrittlenessResult with score, verdict, and BrittleCertificate
        """
        start_time = time.time()
        all_variant_results: list[VariantResult] = []
        level_stats: dict[str, dict] = {}

        for test_input in test_inputs:
            # Get canonical output (the reference)
            canonical_output = self.llm_function(test_input)

            # Generate variants
            variants = self.engine.generate_variants(test_input)

            for variant in variants:
                if not variant.validated:
                    continue

                # Run LLM function on variant
                variant_output = self.llm_function(variant.variant)

                # Compute deviation
                deviation = self._compute_deviation(canonical_output, variant_output)
                is_deviant = deviation > self.deviation_threshold

                vr = VariantResult(
                    variant=variant,
                    output=variant_output,
                    deviation_score=deviation,
                    is_deviant=is_deviant
                )
                all_variant_results.append(vr)

                # Track level stats
                level = variant.level
                if level not in level_stats:
                    level_stats[level] = {"total": 0, "deviant": 0}
                level_stats[level]["total"] += 1
                if is_deviant:
                    level_stats[level]["deviant"] += 1

        # Compute overall score
        total = len(all_variant_results)
        deviants = sum(1 for r in all_variant_results if r.is_deviant)
        score = deviants / total if total > 0 else 0.0
        verdict = self._verdict(score, threshold)

        # Level breakdown
        level_breakdowns = []
        for level, stats in level_stats.items():
            lv = stats["deviant"] / stats["total"] if stats["total"] > 0 else 0.0
            level_breakdowns.append(LevelBreakdown(
                level=level,
                score=lv,
                variant_count=stats["total"],
                deviant_count=stats["deviant"],
                verdict=self._verdict(lv, threshold)
            ))

        # Fault lines — top 5 most deviant variants
        fault_lines = []
        sorted_deviant = sorted(
            [r for r in all_variant_results if r.is_deviant],
            key=lambda r: r.deviation_score,
            reverse=True
        )[:5]
        for r in sorted_deviant:
            fault_lines.append(FaultLine(
                level=r.variant.level,
                variant=r.variant.variant,
                deviation_score=r.deviation_score,
                canonical_fragment="",  # filled by caller if needed
                actual_fragment=r.output[:100],
                recommendation=self._generate_recommendation(r)
            ))

        # Confidence interval
        ci_lower, ci_upper = self._compute_confidence_interval(deviants, total)

        # Build certificate (PAT-050 — Proverbs 17:3 — the crucible output)
        prompt_hash = hashlib.sha256(str(test_inputs).encode()).hexdigest()[:16]
        certificate = BrittleCertificate(
            certificate_id=f"shld_{secrets.token_hex(8)}",
            issued_at=datetime.now(timezone.utc),
            prompt_hash=f"sha256:{prompt_hash}",
            prompt_name=prompt_name,
            verdict=verdict,
            brittleness_score=score,
            threshold=threshold,
            confidence_lower=ci_lower,
            confidence_upper=ci_upper,
            variant_count=total,
            level_breakdown=level_breakdowns,
            fault_lines=fault_lines
        )

        duration = time.time() - start_time

        result = BrittlenessResult(
            score=score,
            verdict=verdict,
            certificate=certificate,
            variant_results=all_variant_results,
            test_input_count=len(test_inputs),
            run_duration_seconds=duration
        )

        # Persist to store
        self.store.log_run(result)

        return result

    def _generate_recommendation(self, result: VariantResult) -> str:
        """Generate actionable fix recommendation for a fault line."""
        level = result.variant.level
        if level == "lexical":
            return (
                "Prompt is brittle to word-level variation. "
                "Add few-shot examples with diverse vocabulary. "
                "Avoid relying on specific keyword triggers."
            )
        elif level == "syntactic":
            return (
                "Prompt is brittle to sentence structure changes. "
                "Test prompt with questions phrased as statements and vice versa. "
                "Add explicit instruction: 'The user may phrase their request in different ways.'"
            )
        elif level == "semantic":
            return (
                "Prompt is brittle to semantic rephrasing. "
                "The prompt relies on surface-form patterns, not semantic understanding. "
                "Add diverse few-shot examples covering multiple phrasings of the same intent."
            )
        return "Review prompt for surface-form dependency."
```

---

## 4. SQLite Store

```python
# prompt_shield/store.py

import sqlite3
import json
from pathlib import Path
from .models import BrittlenessResult


class BrittlenessStore:
    """
    SQLite trace log for all brittleness check runs.
    PAT-048 (Daniel 5): The writing on the wall is permanent.
    All verdicts are inscribed — not ephemeral.
    """

    CREATE_RUNS_TABLE = """
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_at TEXT NOT NULL,
        prompt_name TEXT NOT NULL,
        prompt_hash TEXT NOT NULL,
        test_input_count INTEGER NOT NULL,
        variant_count INTEGER NOT NULL,
        brittleness_score REAL NOT NULL,
        threshold REAL NOT NULL,
        verdict TEXT NOT NULL,
        confidence_lower REAL,
        confidence_upper REAL,
        certificate_json TEXT NOT NULL,
        run_duration_seconds REAL
    )
    """

    CREATE_BASELINES_TABLE = """
    CREATE TABLE IF NOT EXISTS baselines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prompt_name TEXT NOT NULL UNIQUE,
        registered_at TEXT NOT NULL,
        approved_score REAL NOT NULL,
        approved_verdict TEXT NOT NULL,
        certificate_id TEXT NOT NULL
    )
    """

    def __init__(self, store_path: str = "./shield.db"):
        self.path = Path(store_path)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.path) as conn:
            conn.execute(self.CREATE_RUNS_TABLE)
            conn.execute(self.CREATE_BASELINES_TABLE)
            conn.commit()

    def log_run(self, result: BrittlenessResult):
        with sqlite3.connect(self.path) as conn:
            conn.execute("""
                INSERT INTO runs (
                    run_at, prompt_name, prompt_hash, test_input_count,
                    variant_count, brittleness_score, threshold, verdict,
                    confidence_lower, confidence_upper, certificate_json,
                    run_duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.certificate.issued_at.isoformat(),
                result.certificate.prompt_name,
                result.certificate.prompt_hash,
                result.test_input_count,
                result.variant_count,
                result.score,
                result.certificate.threshold,
                result.verdict,
                result.certificate.confidence_lower,
                result.certificate.confidence_upper,
                result.certificate.to_json(),
                result.run_duration_seconds
            ))
            conn.commit()

    def register_baseline(
        self, prompt_name: str, score: float,
        verdict: str, certificate_id: str
    ):
        with sqlite3.connect(self.path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO baselines
                (prompt_name, registered_at, approved_score, approved_verdict, certificate_id)
                VALUES (?, datetime('now'), ?, ?, ?)
            """, (prompt_name, score, verdict, certificate_id))
            conn.commit()

    def get_baseline(self, prompt_name: str) -> dict | None:
        with sqlite3.connect(self.path) as conn:
            row = conn.execute(
                "SELECT * FROM baselines WHERE prompt_name = ?", (prompt_name,)
            ).fetchone()
        if row is None:
            return None
        cols = ["id", "prompt_name", "registered_at", "approved_score",
                "approved_verdict", "certificate_id"]
        return dict(zip(cols, row))
```

---

## 5. CLI

```python
# prompt_shield/cli.py

import sys
import json
import click
from pathlib import Path


@click.group()
def cli():
    """prompt-shield — Catch brittle prompts before production does."""
    pass


@cli.command()
@click.option("--config", default="shield.yaml", help="Config file path")
@click.option("--threshold", default=0.30, help="Brittleness threshold (0.0-1.0)")
@click.option("--output", default=None, help="Output certificate JSON path")
def run(config, threshold, output):
    """Run brittleness audit and display results."""
    from .config import load_config
    from .runner import BrittlenessRunner
    from .engine import BrittlenessEngine

    cfg = load_config(config)

    for prompt_cfg in cfg.get("prompts", []):
        engine = BrittlenessEngine(
            variants_per_input=prompt_cfg.get("variants_per_input", 8),
            levels=prompt_cfg.get("levels", ["lexical", "semantic"])
        )
        llm_function = _load_function(prompt_cfg["function"])
        runner = BrittlenessRunner(llm_function=llm_function, engine=engine)

        result = runner.run(
            test_inputs=prompt_cfg["test_inputs"],
            threshold=prompt_cfg.get("threshold", threshold),
            prompt_name=prompt_cfg["name"]
        )

        click.echo(f"\n{'='*50}")
        click.echo(f"Prompt: {prompt_cfg['name']}")
        click.echo(f"BrittlenessScore: {result.score:.4f}")
        click.echo(f"Verdict: {result.verdict}")
        click.echo(f"Variants tested: {result.certificate.variant_count}")

        if output or cfg.get("output", {}).get("certificate"):
            cert_path = output or cfg["output"]["certificate"]
            Path(cert_path).write_text(result.certificate.to_json())
            click.echo(f"Certificate written to: {cert_path}")


@cli.command()
@click.option("--config", default="shield.yaml", help="Config file path")
@click.option("--threshold", default=0.30, help="Brittleness threshold")
def ci(config, threshold):
    """
    CI gate — exits 0 if ROBUST/CONDITIONAL, 1 if BRITTLE.
    The TEKEL test (PAT-048): weigh on the scales. Exit code is the verdict.
    """
    from .config import load_config
    from .runner import BrittlenessRunner
    from .engine import BrittlenessEngine
    from pathlib import Path

    cfg = load_config(config)
    any_brittle = False

    for prompt_cfg in cfg.get("prompts", []):
        engine = BrittlenessEngine(
            variants_per_input=prompt_cfg.get("variants_per_input", 8),
            levels=prompt_cfg.get("levels", ["lexical", "semantic"])
        )
        llm_function = _load_function(prompt_cfg["function"])
        runner = BrittlenessRunner(llm_function=llm_function, engine=engine)

        result = runner.run(
            test_inputs=prompt_cfg["test_inputs"],
            threshold=prompt_cfg.get("threshold", threshold),
            prompt_name=prompt_cfg["name"]
        )

        verdict_symbol = {"ROBUST": "✅", "CONDITIONAL": "⚠️", "BRITTLE": "❌"}[result.verdict]
        click.echo(f"{verdict_symbol} {prompt_cfg['name']}: {result.score:.4f} ({result.verdict})")

        if result.verdict == "BRITTLE":
            any_brittle = True
            click.echo("  Fault lines:")
            for fl in result.certificate.fault_lines[:3]:
                click.echo(f"    [{fl.level}] '{fl.variant}' → deviation {fl.deviation_score:.4f}")
                click.echo(f"    Fix: {fl.recommendation}")

        # Write outputs
        outputs = cfg.get("output", {})
        if outputs.get("certificate"):
            Path(outputs["certificate"]).write_text(result.certificate.to_json())

    if any_brittle:
        click.echo("\n❌ BRITTLENESS DETECTED — deployment blocked.")
        sys.exit(1)
    else:
        click.echo("\n✅ All prompts passed the brittleness audit.")
        sys.exit(0)


@cli.command()
@click.option("--store", default="./shield.db", help="Store database path")
@click.option("--prompt", default=None, help="Filter by prompt name")
def report(store, prompt):
    """Show brittleness history from the SQLite store."""
    import sqlite3
    with sqlite3.connect(store) as conn:
        if prompt:
            rows = conn.execute(
                "SELECT run_at, prompt_name, brittleness_score, verdict FROM runs "
                "WHERE prompt_name = ? ORDER BY run_at DESC LIMIT 20", (prompt,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT run_at, prompt_name, brittleness_score, verdict FROM runs "
                "ORDER BY run_at DESC LIMIT 20"
            ).fetchall()

    click.echo(f"\n{'Timestamp':<30} {'Prompt':<30} {'Score':<10} Verdict")
    click.echo("-" * 80)
    for row in rows:
        click.echo(f"{row[0]:<30} {row[1]:<30} {row[2]:<10.4f} {row[3]}")


def _load_function(function_path: str):
    """Load a Python function from a dotted path string."""
    module_path, func_name = function_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, func_name)
```

---

## 6. Decorator API

```python
# prompt_shield/decorators.py

import functools
from typing import Callable
from .engine import BrittlenessEngine
from .runner import BrittlenessRunner


class BrittlePromptError(Exception):
    """Raised when a decorated function's prompt exceeds the brittleness threshold."""
    def __init__(self, score: float, threshold: float, verdict: str, certificate):
        self.score = score
        self.threshold = threshold
        self.verdict = verdict
        self.certificate = certificate
        super().__init__(
            f"BrittlePromptError: score={score:.4f} > threshold={threshold} ({verdict})"
        )


def brittle_check(
    threshold: float = 0.30,
    variants: int = 8,
    levels: list = None,
    test_inputs: list[str] = None,
    raise_on_brittle: bool = True,
    store_path: str = "./shield.db",
):
    """
    Decorator that runs a brittleness audit when the test suite executes.

    Usage:
        @brittle_check(threshold=0.25, variants=10, levels=["lexical", "semantic"])
        def my_llm_function(user_input: str) -> str:
            ...

    The decorator:
    1. Detects when running in test mode (pytest, or SHIELD_CHECK=true env var)
    2. Generates `variants` paraphrase variants per test input
    3. Runs the wrapped function on each variant
    4. Computes BrittlenessScore
    5. Raises BrittlePromptError if score > threshold and raise_on_brittle=True
    """
    import os

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Only run brittleness check in test/CI mode
            in_test_mode = (
                os.environ.get("SHIELD_CHECK", "").lower() == "true"
                or os.environ.get("PYTEST_CURRENT_TEST") is not None
            )

            if not in_test_mode:
                return func(*args, **kwargs)

            # Determine test inputs
            inputs = test_inputs or (list(args[:1]) if args else [])
            if not inputs:
                return func(*args, **kwargs)

            engine = BrittlenessEngine(
                variants_per_input=variants,
                levels=levels or ["lexical", "semantic"]
            )

            def wrapped_func(text: str) -> str:
                new_args = (text,) + args[1:]
                return func(*new_args, **kwargs)

            runner = BrittlenessRunner(
                llm_function=wrapped_func,
                engine=engine,
                store_path=store_path
            )
            result = runner.run(
                test_inputs=inputs,
                threshold=threshold,
                prompt_name=func.__name__
            )

            if raise_on_brittle and result.verdict == "BRITTLE":
                raise BrittlePromptError(
                    score=result.score,
                    threshold=threshold,
                    verdict=result.verdict,
                    certificate=result.certificate
                )

            # Attach result to function for inspection
            wrapper._last_shield_result = result
            return func(*args, **kwargs)

        wrapper._shield_config = {
            "threshold": threshold,
            "variants": variants,
            "levels": levels,
        }
        return wrapper

    return decorator
```

---

## 7. pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "prompt-shield"
version = "0.1.0"
description = "Catch brittle prompts before production does — brittleness score and CI gate for LLM prompts"
readme = "README.md"
license = { file = "LICENSE" }
requires-python = ">=3.9"
dependencies = [
    "sentence-transformers>=2.7.0",
    "click>=8.1.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
t5 = [
    "transformers>=4.40.0",
    "torch>=2.0.0",
]
llm = [
    "anthropic>=0.25.0",
]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio",
    "ruff",
    "mypy",
]

[project.scripts]
shield = "prompt_shield.cli:cli"

[project.entry-points."pytest11"]
shield = "prompt_shield.pytest_plugin"

[tool.ruff]
line-length = 100
target-version = "py39"
```

---

## 8. Known Unknowns (for backlog)

| ID | Question | Priority | Notes |
|----|---------|----------|-------|
| KU-027 | Optimal paraphrase quality threshold (min_similarity=0.75 — too high? too low?) | HIGH | Need calibration study across 5+ prompt types |
| KU-028 | What brittleness thresholds are appropriate for different domains (medical, legal, financial)? | HIGH | Default 0.30 may be too loose for high-stakes domains |
| KU-029 | How many variants (N) are needed for statistically valid BrittlenessScore at 95% confidence? | HIGH | Wilson interval math gives N≥20 for tight CI, but CI cost is high |
| KU-030 | LLM-generated paraphrase quality vs T5 quality tradeoff | MEDIUM | Claude generates higher-quality paraphrases but adds API cost |
| KU-031 | Syntactic transformer v0.2 — dependency parsing vs rule-based | MEDIUM | spaCy dependency parsing for true syntactic transformation |
| KU-032 | Cached paraphrase sets — when to regenerate vs reuse? | MEDIUM | Cache invalidation based on input hash + model version |
