# BibleWorld Build Registry
## Living Record of All Software, Apps, Models, and Business Designs

**Last Updated:** Cycle 012
**Total Builds:** 11
**Builds in Design:** 8 (BUILD-001 EvalGate, BUILD-002 LogosSchema, BUILD-003 DecreeDAO, BUILD-005 TrustChain, BUILD-006 DemoFirst, BUILD-007 KnowFirst, BUILD-008 prompt-lock, BUILD-009 llm-contract)
**Builds at TESTABLE:** 1 (BUILD-004 GrantPilot — prompt chain designed, tested, validated)
**Builds at PROTOTYPE:** 2 (BUILD-010 drift-guard — full implementation ready to ship; BUILD-011 spec-drift — prototype written cycle 012)
**Builds Deployed:** 0

---

## HOW TO READ THIS REGISTRY

Each build entry contains:
- **Build ID** — sequential (BLD-001, BLD-002...)
- **Build Name** — short name
- **Pattern Source** — which PAT-NNN inspired this build
- **Build Type** — SOFTWARE / APP / BUSINESS_MODEL / RESEARCH / PROTOTYPE / FRAMEWORK
- **Problem Solved** — specific, real problem this addresses
- **Who It Serves** — specific user type
- **How It Works** — technical description
- **Claude API Role** — how Claude specifically powers the core
- **Capital Required** — ZERO / LOW / MEDIUM / HIGH
- **Build Score** — 0-10
- **Status** — CONCEPT / IN-DESIGN / PROTOTYPE / TESTABLE / DEPLOYED
- **Agent Responsible** — which agent is building it
- **Cycle Started** — which cycle

---

## BUILDS IN DESIGN

### BUILD-001: EvalGate
**Pattern Source:** PAT-009 (Genesis 1 Evaluation Loop)
**Build Type:** SOFTWARE — AI Infrastructure Middleware
**Problem Solved:** AI agent pipelines propagate hallucinations through steps unchecked; each step compounds errors from prior steps
**Who It Serves:** AI application developers, enterprise LLM deployment teams
**How It Works:** Middleware layer inserted between agent steps; calculates confidence score on each output; blocks progression if score below threshold; retries or escalates to human review
**Claude API Role:** Claude as the evaluator — each checkpoint calls Claude to assess whether the prior step's output is coherent, grounded, and safe to use as input
**Capital Required:** ZERO (build with laptop + Claude API)
**Build Score:** 7.8
**Status:** IN-DESIGN
**Agent Responsible:** Chief Builder
**Cycle Started:** 001

---

### BUILD-002: LogosSchema
**Pattern Source:** PAT-012 (Logos as Generative Schema)
**Build Type:** SOFTWARE — Business Design Tool
**Problem Solved:** African startups build before designing; no explicit business schema = institutional fragility at scale
**Who It Serves:** African tech founders, accelerators, incubators
**How It Works:** Guided web UI walks founders through entity definition, relationship mapping, rule specification, payment flow design; outputs machine-readable business schema; generates database schema, API skeleton, and data dictionary
**Claude API Role:** Claude guides schema definition dialogue, validates consistency of rules, generates code artifacts from schema
**Capital Required:** ZERO (build with laptop + Claude API)
**Build Score:** 7.6
**Status:** IN-DESIGN
**Agent Responsible:** Chief Builder + Chief Innovator
**Cycle Started:** 001

---

### BUILD-003: DecreeDAO
**Pattern Source:** PAT-013 (Psalm 2:6-7 — Decree Protocol)
**Build Type:** SOFTWARE — Governance SaaS
**Problem Solved:** African cooperatives and diaspora investment clubs fail because authority is informal, undocumented, and disputed
**Who It Serves:** Diaspora investment clubs, agricultural cooperatives, NGOs
**How It Works:** Web app for formal, timestamped, immutable decrees: roles, permissions, spending limits, voting rules. Constitution builder templates.
**Claude API Role:** Generates governance templates, drafts decree language, validates rule consistency
**Capital Required:** ZERO
**Build Score:** 7.5
**Status:** IN-DESIGN
**Agent Responsible:** Chief Builder + Chief Innovator
**Cycle Started:** 002

---

### BUILD-004: GrantPilot
**Pattern Source:** PAT-014 (Ask-Receive) + PAT-019 (Water-to-Wine) + PAT-028 (Bethesda Bottleneck) + PAT-029 (Pattern Replication) + PAT-030 (Patience Pricing) + PAT-031 (Psalm 51 Chain) + PAT-032 (Loaves Efficiency) + PAT-033 (Shelter Positioning)
**Build Type:** SOFTWARE — AI Grant Writing SaaS
**Problem Solved:** African organizations leave billions in grant funding untapped because they cannot write proposals meeting funder requirements
**Who It Serves:** Grant consultants (primary), African NGOs, international organizations, accelerators
**How It Works:** 5-prompt chain: INTAKE (12 structured questions) → ANALYSIS (funder matching + gap identification) → GENERATION (all 10 proposal sections) → REVIEW (hallucination check + quality audit) → FORMAT (funder-specific output). Full prompt chain documented in cycle-007/grantpilot-prompt-chain.md
**Claude API Role:** Core — Claude powers all 5 prompts. ~19,500 tokens per proposal. ~$0.15-0.30 API cost per proposal.
**Capital Required:** ZERO
**Build Score:** 9.0 (stress-tested cycle 005, prompt chain validated cycle 008)
**Status:** TESTABLE — prompt chain designed, tested on 2 scenarios, 0 hallucinations, avg 7.65/10 quality
**Agent Responsible:** Chief Builder
**Cycle Started:** 002
**Prompt Chain Completed:** Cycle 007
**Stress Test Passed:** Cycle 008 (2 scenarios: USAID $250K + MCF $100K)
**Priority:** #1 — SHIP NOW
**Pricing:** $29/proposal, $99/mo (10), $199/mo unlimited, $499/mo enterprise
**Funder Templates:** USAID, IFC, Mastercard Foundation, AfDB (4 active; 8 more planned)
**Test Results:** USAID scenario 7.8/10, MCF scenario 7.5/10, zero hallucinations both tests
**Known Weaknesses:** Sustainability section (generic), Partnership section (needs named partners), budget unit costs
**Improvements Needed:** Few-shot examples for weak sections, development data library, 6th STRENGTHEN prompt

---

### BUILD-005: TrustChain
**Pattern Source:** PAT-015 (John 1:35-42 — Referral Chain Trust)
**Build Type:** SOFTWARE — Deal Flow Platform
**Problem Solved:** Diaspora investors receive unverifiable cold deal flow from Ghana. No mechanism to see who referred a deal or how trustworthy the referrer is.
**Who It Serves:** Diaspora investment clubs, angel investors, fund managers, deal originators
**How It Works:** Every deal has a visible referral chain with scored referrers. Investors filter by trust-chain depth and referrer score.
**Claude API Role:** Analyzes deal documents for red flags, generates deal summaries, assists due diligence
**Capital Required:** ZERO
**Build Score:** 8.0
**Status:** IN-DESIGN
**Agent Responsible:** Chief Builder + Chief Innovator
**Cycle Started:** 002

---

### BUILD-006: DemoFirst
**Pattern Source:** PAT-016 (John 1:39,46 — "Come and See")
**Build Type:** SOFTWARE — Demo Generation Tool
**Problem Solved:** SaaS founders spend weeks on landing pages when direct product experience is the best converter
**Who It Serves:** SaaS founders, B2B sales teams, product marketers
**How It Works:** Founder describes product in natural language. DemoFirst generates clickable interactive demo (HTML/JS) that prospects use immediately.
**Claude API Role:** Core — generates entire interactive demo from text description
**Capital Required:** ZERO
**Build Score:** 7.6
**Status:** IN-DESIGN
**Agent Responsible:** Chief Builder
**Cycle Started:** 002

---

### BUILD-007: KnowFirst
**Pattern Source:** PAT-017 (John 1:47-49 — Pre-Knowledge Trust Collapse)
**Build Type:** SOFTWARE — AI Pre-Meeting Intelligence
**Problem Solved:** Professionals walk into meetings without context. Research takes 30-60 min per meeting. Most skip it.
**Who It Serves:** B2B sales professionals, diaspora founders, consultants, investors
**How It Works:** Input: name + company + context. Output: 1-page brief with background, pain points, conversation openers, red flags.
**Claude API Role:** Core — synthesizes aggregated data into actionable brief
**Capital Required:** ZERO
**Build Score:** 8.3
**Status:** IN-DESIGN
**Agent Responsible:** Chief Builder + Chief Technologist
**Cycle Started:** 002
**Priority:** #2

---

### BUILD-008: prompt-lock
**Pattern Source:** PAT-034 (Nehemiah Wall Guards) + PAT-009 (EvalGate) + PAT-012 (Logos Schema)
**Build Type:** SOFTWARE — Open-Source Python Library / Developer Tool
**Problem Solved:** LLM engineers ship prompt changes without quality regression checks. No framework-agnostic, git-native tool provides prompt change detection + judge calibration + trace-linked eval scoring in a single CI/CD integration.
**Who It Serves:** AI/ML engineers at any company shipping LLM features in production. Primary persona: engineers who modify prompts frequently and cannot tell which change caused quality to drop.
**How It Works:** git diff detects changed prompt files → calibration check validates LLM judge trustworthiness (>80% agreement with human labels) → eval suite runs for changed prompts only → scores compared against configurable thresholds/baseline → CI gate passes or fails → trace logged to SQLite with commit SHA + prompt hash + scores.
**Claude API Role:** Claude powers the LLM-as-judge scorer AND is the recommended default model for judge calibration (claude-3-5-haiku for eval, claude-3-5-sonnet for high-stakes gates).
**Capital Required:** ZERO (Python library, PyPI, GitHub Actions — no infrastructure)
**Pivot_Score:** 8.70 (highest in BibleWorld pivot history; beats cot-coherence 8.00 by 0.70 points)
**Build Score:** 9.5
**Status:** IN-DESIGN (full design complete, v0.1 sprint plan written)
**Agent Responsible:** Chief Builder + Chief Technologist
**Cycle Started:** 009
**Key Differentiator:** Judge calibration module — the only tool that validates whether your LLM judge agrees with humans on your specific task before trusting it as a CI gate.
**Acquisition Path:** OpenAI (security eval = Promptfoo, quality regression eval = prompt-lock), Anthropic (trust evaluation mission), Microsoft (Copilot quality gap)

---

---

### BUILD-009: llm-contract
**Pattern Source:** PAT-035 (Acts 2:1-13 — The Pentecost Contract)
**Build Type:** SOFTWARE — Open-Source Python Library / Developer Tool
**Problem Solved:** LLM function calls lack behavioral contract enforcement. Pydantic validates structure; nothing validates whether output *behaves* as specified — especially across provider switches and silent model updates.
**Who It Serves:** AI/ML engineers maintaining LLM function calls in production; platform engineers standardizing LLM usage organization-wide; teams that get paged when model updates break behavioral expectations
**How It Works:** `@contract` decorator applies to any LLM function. Layer 1: Pydantic structural validation. Layer 2: LLM-as-judge semantic rule evaluation. Contract versioning (SemVer for behavior). CI gate via CLI + GitHub Action. SQLite drift logging with rolling violation rate monitoring and alerts.
**Claude API Role:** Claude powers the LLM judge for semantic rule evaluation (claude-3-5-haiku-20241022 default); Claude Sonnet for high-stakes gates
**Capital Required:** ZERO (Python library, PyPI distribution, GitHub Actions)
**Pivot_Score:** 8.30 (second-highest in BibleWorld history; beats cot-coherence 8.00 by 0.30 points)
**Build Score:** 9.6
**Status:** IN-DESIGN (full spec written cycle 010)
**Agent Responsible:** Chief Builder + Senior Agent (Chief Technologist)
**Cycle Started:** 010
**Key Differentiator:** The only open-source library that defines, versions, and enforces *behavioral* (not just structural) contracts on LLM function calls — provider-agnostic, CI-integrated, drift-detecting
**Acquisition Path:** Anthropic (alignment/trust mission), OpenAI (complement Promptfoo), Datadog (LLM behavioral monitoring), Pydantic Labs (natural extension)
**Design Location:** `.Codex/builds/llm-contract/README.md`
**v0.1 Plan:** Pure Python; decorator pattern; Pydantic + Claude API; pip install llm-contract; 2-3 week sprint

---

---

### BUILD-010: drift-guard
**Pattern Source:** PAT-036 (Romans 7:7 — The Law Makes Violations Visible)
**Build Type:** SOFTWARE — Open-Source Python Library / Developer Tool
**Problem Solved:** AI-assisted PRs create 1.7x more production issues than human PRs due to intent drift: PR descriptions say one thing, AI code does another. No open-source tool verifies whether code changes actually fulfill stated PR intent.
**Who It Serves:** AI/ML engineers and senior developers at companies using AI-assisted coding (Copilot, Cursor, Claude, Gemini Code). Also: platform engineers, engineering managers, OSS maintainers reviewing AI contributions.
**How It Works:** Three layers: (1) Intent Parser — extracts structured clauses (adds X, removes Y, ensures Z, does not W) from PR description. (2) Diff Parser — fetches and parses git diff into DiffHunk objects. (3) LLM Verifier — Claude checks each clause against the diff, returns PASS/FAIL/WARN/SKIP with evidence quotes and drift score 0.0–1.0. SQLite trace log persists all verifications. CI gate fails if drift_score exceeds threshold (default 0.30).
**Claude API Role:** Core — Claude claude-3-5-haiku-20241022 powers the semantic clause verifier. Receives intent clauses + diff text; returns structured JSON verdict with per-clause status and overall drift score.
**Capital Required:** ZERO (Python library, PyPI, git — no infrastructure)
**Pivot_Score:** 8.60 (second-highest in BibleWorld history; beats llm-contract 8.30 by 0.30, beats cot-coherence 8.00 by 0.60)
**Build Score:** 9.3
**Status:** PROTOTYPE (full implementation written, test suite written, pyproject.toml complete — ready for PyPI)
**Agent Responsible:** Chief Builder + Senior Agent (Chief Technologist)
**Cycle Started:** 011
**Key Differentiator:** The only open-source tool that verifies whether PR code changes fulfill the stated PR intent — pre-merge, with a configurable CI gate, for any git repo.
**Acquisition Path:** GitHub (native code review integration), Salesforce (complement to internal intent reconstruction system), Microsoft (Copilot quality signal), Linear/Jira (ticket-to-PR intent verification)
**Design Location:** `.Codex/builds/drift-guard/`
**Files Written:** drift_guard.py (450+ lines), README.md (300+ lines), tests/test_drift_guard.py (200+ lines), pyproject.toml

---

---

### BUILD-011: spec-drift
**Pattern Source:** PAT-037 (Leviticus 10:1-3 — The Authorized Fire Pattern)
**Build Type:** SOFTWARE — Open-Source Python Library / Developer Tool
**Problem Solved:** LLM outputs pass structural validation (Pydantic/JSON Schema) while their semantic meaning drifts silently — due to model updates, prompt erosion, or input distribution shift. No open-source tool monitors continuous semantic compliance with a declared behavioral specification.
**Who It Serves:** AI/ML engineers at companies shipping LLM features in production with structured outputs. Teams who get paged for "quality issues" not caught by existing monitoring.
**How It Works:** `@spec` decorator attaches semantic constraints to Pydantic models. `DriftMonitor` wraps LLM functions, intercepts outputs, runs structural + semantic checks, logs observations to SQLite, fires alerts when rolling violation rate exceeds thresholds. CLI provides `check` (drift reports), `ci` (CI gate), and `compare` (model version diffing) commands.
**Claude API Role:** Claude powers the LLM judge for complex semantic constraint evaluation (prose-level checks) — planned for v0.3. Core semantic checks (authorized values, length bounds, distributions, patterns) run deterministically.
**Capital Required:** ZERO (Python library, PyPI, SQLite, GitHub Action — no infrastructure)
**Pivot_Score:** 8.63 (third-highest in BibleWorld history; beats cot-coherence 8.00 by 0.63 points)
**Build Score:** 9.3/10
**Status:** PROTOTYPE (prototype.py written cycle 012, README complete)
**Agent Responsible:** Chief Builder (Senior Agent) + Chief Technologist (Senior Agent)
**Cycle Started:** 012
**Key Differentiator:** The first open-source tool that distinguishes structural validation (Pydantic) from semantic specification compliance (spec-drift) and monitors the latter continuously in production.
**Acquisition Path:** Datadog (LLM behavioral monitoring), Anthropic (alignment/safety), Pydantic Labs (natural extension), Confident AI (complement to DeepEval)
**Design Location:** `.Codex/builds/spec-drift/`
**Files Written:** prototype.py (240+ lines), README.md (300+ lines)

---

## COMPLETED BUILDS

*Populated as builds reach TESTABLE or DEPLOYED status*

---
