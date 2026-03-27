# BibleWorld Cycle 012 — Builds

**Cycle:** 012
**Date:** 2026-03-27
**Build Winner:** spec-drift (BUILD-011)
**Pivot_Score:** 8.63
**Biblical Pattern:** PAT-037 (Leviticus 10:1-3 — The Authorized Fire Pattern)

---

## BUILD-011: spec-drift

**Pattern Source:** PAT-037 (Leviticus 10:1-3 — Authorized Fire Pattern)
**Build Type:** SOFTWARE — Open-Source Python Library / Developer Tool
**Pivot_Score:** 8.63 (third-highest in BibleWorld history; beats cot-coherence 8.00 by 0.63 points)
**Build Score:** 9.3/10

### Problem Solved
LLM outputs can satisfy Pydantic/JSON Schema structural validation while their semantic meaning drifts dramatically — as models are silently updated, as prompts shift, or as input distributions change. No open-source tool monitors whether LLM outputs remain semantically compliant with a declared behavioral specification over time.

**Three core failure modes this solves:**
1. **Silent model updates:** LLM provider updates model. API schema unchanged. Output distributions shift. Pydantic sees nothing. Users see degraded quality. On-call team is paged weeks later.
2. **Prompt erosion:** Cumulative small prompt changes shift semantic output profiles (shorter reasoning, different classification boundaries). Each change passes regression tests individually. Cumulative drift is invisible.
3. **Input distribution shift:** New user cohort or seasonal shift changes input distribution. Same model, same prompt, same schema — but outputs drift from spec. No existing tool detects this.

### Who It Serves
AI/ML engineers at companies shipping LLM features in production with structured outputs. Specifically:
- Engineers who have been paged for "LLM output quality issues" that weren't caught by existing monitoring
- Platform engineers standardizing LLM quality governance across teams
- ML engineers managing multiple model versions or providers in parallel
- Any team whose LLM output consumers (downstream agents, humans, databases) depend on semantic consistency

### How It Works
Four-component architecture:

1. **Spec Declarator** — Python DSL for declaring semantic specifications on LLM output schemas. Built on Pydantic v2. Adds semantic constraints (value distributions, pattern frequencies, field-level baselines) alongside structural constraints. Declarative, versionable, diffable.

2. **Baseline Calibrator** — Runs over a golden dataset of known-good outputs to establish baseline semantic distributions. Stores baselines in SQLite (local) or PostgreSQL (production). Supports multiple named baselines (production, staging, canary). Baseline versioning with SemVer.

3. **Drift Monitor** — Lightweight wrapper around LLM function calls. Intercepts outputs, runs structural validation (Pydantic), runs semantic compliance checks against declared spec, calculates per-field and per-spec drift scores, logs asynchronously to SQLite/PostgreSQL, fires configurable alerts.

4. **CLI + CI Gate** — `spec-drift check` generates drift report from recent production observations. `spec-drift ci` runs regression checks against a test batch and exits non-zero if semantic drift exceeds threshold. GitHub Action available.

### Key Differentiator
spec-drift is the first open-source tool that distinguishes between structural validation (does the output have the right fields and types?) and semantic specification compliance (do the outputs honor the declared behavioral spec over time?). This gap is the difference between Pydantic and spec-drift: Pydantic catches structural violations; spec-drift catches semantic drift.

### Tech Stack
- Python 3.10+
- Pydantic v2
- SQLite (default), PostgreSQL (production)
- Anthropic API / OpenAI API (LLM judge for semantic checks)
- Rich (terminal output)
- Typer (CLI)
- pytest integration
- PyPI: `pip install spec-drift`
- GitHub Action: `spec-drift/action@v1`

### Acquisition Path
- Datadog (LLM behavioral monitoring suite)
- Anthropic (alignment/safety — semantic specification compliance is an alignment-adjacent problem)
- Pydantic Labs (natural extension of Pydantic ecosystem into production monitoring)
- Confident AI (complement to DeepEval for continuous monitoring vs. batch evaluation)
- Arize (extend Phoenix into semantic spec monitoring)

### Capital Required
ZERO — Python library, PyPI distribution, GitHub Action, SQLite. No infrastructure required.

### Status
PROTOTYPE (full prototype code written this cycle)

### Files
- `.Codex/builds/spec-drift/prototype.py` — Core implementation (200+ lines)
- `.Codex/builds/spec-drift/README.md` — Full README
- Cycle 012 Build Score: 9.3/10

---

## RUNNER-UP DESIGN NOTE: pr-triage-ai (Pivot_Score 8.28)

pr-triage-ai scored 8.28 and is a strong second-place candidate for future cycle development.

**Problem:** OSS maintainers flooded with AI-generated PRs that look correct but miss project conventions.
**Tool:** Automated AI contribution quality scorer. Analyzes PR against project conventions, test coverage patterns, contribution guidelines. Produces quality score (0-10) + AI-generation likelihood + prioritized review checklist. GitHub Action.
**Differentiator:** No open-source tool currently scores AI contribution quality for OSS maintainers.
**Recommended:** Build after spec-drift v0.1 if spec-drift gains traction. Biblical pattern candidate: Matthew 13:24-30 (Parable of the Wheat and Tares — AI wheat vs AI tares in the PR harvest).

---

## PIPELINE STATUS (Post Cycle 012)

| Tool | Pivot_Score | Status |
|---|---|---|
| prompt-lock | 8.70 | IN-DESIGN |
| spec-drift (NEW) | 8.63 | PROTOTYPE |
| drift-guard | 8.60 | PROTOTYPE — READY TO SHIP |
| llm-contract | 8.30 | IN-DESIGN |
| cot-coherence | 8.00 | IN-DESIGN |
