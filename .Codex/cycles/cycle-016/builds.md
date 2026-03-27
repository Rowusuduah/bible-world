# BibleWorld Cycle 016 — Builds

**Cycle:** 016
**Date:** 2026-03-27
**Builds This Cycle:** 1

---

## Build 015: context-lens

**Type:** Software — Open-Source Python Library / Developer Tool
**Pattern Source:** PAT-051 (Ezekiel 37:1-10 — Valley of Dry Bones, positional completeness) + PAT-052 (Luke 15:4-6 — Lost Sheep, no acceptable loss) + PAT-053 (Hebrews 4:13 + 9:6-7 — Systematic position coverage)
**Problem Solved:** LLMs silently fail to retrieve information buried in the middle of long contexts (lost-in-the-middle problem). No open-source tool systematically tests whether a model retrieves information reliably at every context window position before deployment. Teams discover this failure from user complaints, not pre-deployment tests.
**Target User:** Senior ML engineers and AI platform engineers at companies using RAG pipelines, long-document analysis, or multi-turn agent workflows with long context windows. Specifically: engineers who get paged because "the LLM ignored the relevant part of the document."
**Core Features:**
- PositionHeatmap: places a needle at N positions across the context, runs the LLM at each, records RETRIEVED/MISSED per position
- FaultZone detection: identifies whether failures are middle-heavy (lost-in-the-middle), edge-heavy, or scattered
- Multi-needle audit: test multiple critical facts in one run (audit_multi)
- CI gate: context-lens ci --min-score 0.80 exits 1 on failure — blocks deployment of unreliable context configurations
- SQLite audit history: track retrieval scores over time as model versions change
- RELIABLE / CONDITIONAL / UNRELIABLE verdict: clear, actionable, deployable proof of context reliability
**Tech Stack:** Python 3.9+, SQLite (stdlib), dataclasses (stdlib), zero hard dependencies (provider SDKs optional)
**Pivot_Score:** 8.80
**Build Score:** 9.0/10 (feasibility 2.9 + impact 2.9 + completeness 1.9 + biblical fidelity 1.3)
**Files Created:**
- `.Codex/builds/context-lens/context_lens.py` (530+ lines — full implementation)
- `.Codex/builds/context-lens/README.md` (350+ lines — full documentation)
- `.Codex/builds/context-lens/examples/basic_usage.py` (130+ lines — working example)
- `.Codex/builds/context-lens/examples/rag_pipeline_audit.py` (160+ lines — RAG-specific example)
- `.Codex/builds/context-lens/pyproject.toml` (full packaging config)
**Key Differentiator:** The ONLY open-source tool that specifically tests LLM context window positional sensitivity — whether information at every position (not just edge positions) is reliably retrieved. Every other eval tool tests what the model says, not where in the context the model's attention fails. The PositionHeatmap is a novel artifact.
**Competitive Landscape:** Langfuse, LangSmith, Opik, DeepEval, Promptfoo — none test positional retrieval sensitivity. Redis context window management guides exist but are documentation, not a testing library. There is no pip-installable library that runs needle-at-position audits. GREEN.
**Acquisition Path:** Arize Phoenix (LLM observability — context position audit is a natural extension), Anthropic (trust mission — reliable context retrieval increases confidence in Claude for RAG), Databricks (LLM evaluation in data pipeline context), Confluent/Cohere (RAG pipeline quality assurance)
