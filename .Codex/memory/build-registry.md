# BibleWorld Build Registry
## Living Record of All Software, Apps, Models, and Business Designs

**Last Updated:** Cycle 025 (completed 2026-04-08)
**Total Builds:** 25
**Builds in Design:** 18 (BUILD-001 EvalGate, BUILD-002 LogosSchema, BUILD-003 DecreeDAO, BUILD-005 TrustChain, BUILD-006 DemoFirst, BUILD-007 KnowFirst, BUILD-008 prompt-lock, BUILD-009 llm-contract, BUILD-012 model-parity, BUILD-014 prompt-shield, BUILD-017 cot-fidelity, BUILD-018 semantic-pass-k, BUILD-020 invariant-probe, BUILD-021 session-lens, BUILD-022 livelock-probe, BUILD-023 pressure-gauge, BUILD-024 covenant-keeper, BUILD-025 observer-probe)
**Builds at TESTABLE:** 1 (BUILD-004 GrantPilot — prompt chain designed, tested, validated)
**Builds at PROTOTYPE:** 4 (BUILD-010 drift-guard; BUILD-011 spec-drift; BUILD-015 context-lens; BUILD-016 chain-probe — full spec written cycle 017)
**Builds Deployed:** 0

---

### BUILD-025: observer-probe [PIVOT-PHASE CYCLE 025]
**Pattern Source:** PAT-086 (Psalm 10:6,11 — The Hidden Actor Pattern)
**Build Type:** SOFTWARE — Developer Testing Library (Python, pip-installable)
**Problem Solved:** AI agents are evaluated in test environments with explicit eval-mode system prompts, then deployed under production-mode context. If an agent's output distribution SHIFTS based on whether system context signals "evaluation mode" vs. "production mode" — even with identical tasks — teams have no way to know. Evaluation gaming is a documented concern in RLHF-trained systems (Anthropic alignment team). No pip library measures ObservabilityBias.
**Who It Serves:** ML engineers deploying agents with system prompts; alignment researchers studying evaluation gaming; AI safety teams; QA engineers; teams who have observed different agent behavior in eval vs. production.
**How It Works:** ObserverProbe runs the agent on identical task prompts under two system context conditions — eval-evident and production-evident — embeds outputs, computes pairwise cosine similarity, reports ObservabilityBias = 1 - mean(similarity). Verdict: CONSISTENT, DRIFTS_IN_PROD, or DRIFTS_IN_EVAL. CI-gateable via pytest plugin and CLI gate command.
**Key Technical Innovation:** First pip-installable tool to isolate context-mode signal sensitivity as an independent variable. New named metric: ObservabilityBias. Orthogonal to invariant-probe (general perturbation), pressure-gauge (fill-level drift), covenant-keeper (adversarial commitment testing).
**Capital Required:** ZERO (sentence-transformers + anthropic/openai SDK + click + rich + numpy + matplotlib + pyyaml)
**Pivot_Score:** 8.675/10 — THIRD HIGHEST in BibleWorld history
**Sprint Estimate:** 6 weeks to pip-publishable v0.1
**Competitive Status:** GREEN — 12 tools/papers audited, NONE implement ObservabilityBias. Window: 4-6 months.
**Acquisition Target:** Anthropic (core alignment mission — evaluation gaming), Google, Microsoft. NOT OpenAI (owns Promptfoo).
**Open Questions:** KU-072 through KU-075
**Status:** IN-DESIGN
**Cycle:** 025

---

### BUILD-024: covenant-keeper [PIVOT-PHASE CYCLE 024]
**Pattern Source:** PAT-082 (Daniel 6:4-10 — The Lion's Den Invariance Pattern)
**Build Type:** SOFTWARE — Developer Testing Library (Python, pip-installable)
**Problem Solved:** AI agents are tested for breakage (offense-focused: can adversarial inputs make the model do something harmful?) but NOT for commitment fidelity (defense-focused: does the agent maintain its declared behavioral commitments when the environment becomes adversarial?). Every deployed agent has a system prompt with behavioral commitments. No pip library tests whether those specific commitments survive tailored adversarial pressure.
**Who It Serves:** ML engineers deploying agents with system prompts; security teams verifying AI agent behavioral guarantees; QA engineers building adversarial test suites; compliance teams verifying constraint stability; platform teams running CI/CD.
**How It Works:** CovenantSuite takes a list of behavioral commitments (from system prompt or manual list), generates adversarial scenarios TAILORED to each commitment (using an LLM), runs the agent under each scenario, embeds outputs, compares to baseline committed behavior, and reports CovenantFidelity = fraction of commitments maintained under adversarial pressure. CLI: `ckeeper test/show/gate/generate/quick`. pytest plugin.
**Key Technical Innovation:** First pip-installable tool to produce CovenantFidelity — behavioral commitment invariance under tailored adversarial conditions. Distinct from: Promptfoo (offense-focused red-teaming), Augustus (generic adversarial scanning), invariant-probe (environmental perturbation), ToolGuard (tool call testing), Guardrails AI (format validation).
**Capital Required:** ZERO (sentence-transformers + anthropic/openai SDK + click + rich + numpy + pyyaml)
**Build Score:** 9.0/10
**Pivot_Score:** 8.30
**Status:** DESIGN
**Agent Responsible:** Chief Builder (Senior Agent)
**Cycle Started:** 024
**Implementation:** Full API spec (CovenantSuite, CovenantConfig, CovenantReport, @covenant_test decorator, CLI ckeeper test/show/gate/generate/quick, pytest plugin), sprint plan (6 weeks), known unknowns (KU-068 through KU-071), competitive differentiation matrix (10 tools differentiated)
**Competitive Moat:** GREEN [WEB-FRESH 2026-04-01] — 10 tools audited — NONE implement CovenantFidelity. Window: 4-6 months.

---

### BUILD-023: pressure-gauge [PIVOT-PHASE CYCLE 023]
**Pattern Source:** PAT-078 (Daniel 5:5-6, 27 — The TEKEL Pressure Drift Pattern)
**Build Type:** SOFTWARE — Developer Testing Library (Python, pip-installable)
**Problem Solved:** Long-running LLM agents change behavior as their context window fills — a phenomenon named "context anxiety" in 2026 developer literature. Agents wrap up prematurely, rush steps, and falsely declare tasks complete when the context window is near capacity. No pip library measures this behavioral drift as a function of context fill level. pressure-gauge runs a controlled fill-level sweep: executes the same agent task at 10%, 30%, 50%, 70%, 90% fill, embeds all outputs, computes ContextPressureScore = mean cosine similarity to baseline (10% fill), reports pressure_onset_token, plots ContextDriftCurve, provides CI gate.
**Who It Serves:** ML engineers deploying long-running agents; platform teams managing context window costs; QA engineers building reliability suites; DevOps teams adding agent behavioral stability checks to CI/CD pipelines; any developer using Claude Code or similar long-session agents.
**How It Works:** PressureGauge.sweep() runs agent_fn at each fill level by padding context with inject_history / repeat_text / lorem_ipsum strategy. Embeds outputs with sentence-transformers. Computes cosine similarity of each fill-level output vector vs. baseline vector. ContextPressureScore = 1 - mean_drift. pressure_onset_token = first token count where similarity < stability_threshold. ContextDriftCurve shows drift shape across fill levels.
**Key Technical Innovation:** First pip-installable tool to produce ContextPressureScore and ContextDriftCurve measuring LLM behavioral drift as a function of context fill level. Distinct from: invariant-probe (external environmental perturbations), livelock-probe (zero-progress detection), session-lens (session memory fidelity), Langfuse (execution tracing), Arize Phoenix (output quality scoring).
**Capital Required:** ZERO (sentence-transformers + anthropic/openai SDK + click + rich + numpy + matplotlib + pyyaml)
**Build Score:** 9.1/10
**Pivot_Score:** 8.65
**Status:** DESIGN
**Agent Responsible:** Chief Builder (Senior Agent)
**Cycle Started:** 023
**Implementation:** Full API spec (PressureGauge, PressureConfig, PressureReport, DriftPoint, @pressure_probe, CLI pgauge run/show/gate/plot/quick/onset/estimate, pytest plugin), sprint plan (6 weeks), known unknowns (KU-064 through KU-067), competitive differentiation matrix (7 tools differentiated)
**Competitive Moat:** GREEN [WEB-FRESH 2026-04-01] — 9 tools audited (Langfuse, Arize Phoenix, invariant-probe, session-lens, livelock-probe, DeepEval, Braintrust, W&B Weave, AgentOps) — NONE produce ContextPressureScore. Window: 4-6 months.

---

### BUILD-022: livelock-probe [PIVOT-PHASE CYCLE 022]
**Pattern Source:** PAT-075 (John 5:5-9 — The 38-Year Stuck State Pattern)
**Build Type:** SOFTWARE — Developer Testing Library (Python, pip-installable)
**Problem Solved:** AI agents in production enter STRUCTURALLY STUCK states — active, not erroring, consuming tokens — but making zero net progress toward their goal. This is livelock: a race-condition or resource-competition mechanism the agent cannot win. No current pip library detects this state or produces LivelockScore. Claude Code quota exhaustion (The Register, March 2026) is a documented real-world instance.
**Who It Serves:** ML engineers deploying agents to production; platform teams managing agent token budgets; QA engineers building reliability suites; enterprise teams with CI/CD pipelines for agent workflows; DevOps teams debugging why agents consume quota without completing tasks.
**How It Works:** Instruments agent step outputs. Embeds each step output with sentence-transformers. Computes Progress Vector: cosine similarity of step output to goal embedding per step. Detects LivelockPattern: k consecutive steps where progress delta < ε (near-zero net progress despite activity). Reports LivelockScore = fraction of steps with near-zero progress. CI gate: `lprobe gate --max-livelock-score 0.15`. Distinct from AgentRx (first-unrecoverable-step) — livelock steps are recoverable-looking.
**Key Technical Innovation:** First pip-installable tool to produce LivelockScore (structural stuck-state detection) for AI agent workflows. Distinguishes livelock from slowness, deadlock, and explicit errors. CI-gateable. LLM-agnostic. Framework-agnostic.
**Capital Required:** ZERO (sentence-transformers + anthropic/openai SDK + click + rich + numpy + pyyaml)
**Build Score:** 9.0/10
**Pivot_Score:** 8.175
**Status:** DESIGN
**Agent Responsible:** Chief Builder (Senior Agent)
**Cycle Started:** 022
**Implementation:** Full API spec (LivelockSuite, ProgressConfig, LivelockReport, @livelock_probe), CLI (lprobe run/show/gate/report/estimate/replay), pytest plugin, LivelockScore algorithm (progress vector computation), sprint plan (8 weeks), known unknowns (KU-060 through KU-063)
**Competitive Moat:** GREEN [WEB-FRESH 2026-04-01] — Langfuse (tracing, not progress detection), Arize Phoenix (observability, not livelock), AgentRx (first-unrecoverable-step — confirmed different problem), LangSmith (tracing, not stuck-state), Braintrust (evaluation, not progress vector), Maxim AI (no LivelockScore). Window: 4-6 months.

---

### BUILD-021: session-lens [PIVOT-PHASE CYCLE 021]
**Pattern Source:** PAT-071 (John 4:16-18 — The Hidden History Verification Pattern)
**Build Type:** SOFTWARE — Developer Testing Library (Python, pip-installable)
**Problem Solved:** Long-session AI agents accumulate history in context windows / memory stores. No tool verifies that the agent's recalled history matches ground truth at the event level. Anthropic's cache bug (March 2026) produced 10-20x cost inflation because session memory integrity failed — agents behaved as if prior context was missing. Cache miss events, vector store ordering errors, context truncation, and hallucinated recall all go undetected.
**Who It Serves:** ML engineers using long-session agents, RAG teams with multi-turn workflows, platform engineers managing session caching infrastructure.
**How It Works:** Takes a ground truth session transcript (JSON). Auto-generates probe questions across 4 types (recall, ordering, attribution, negation). Runs agent against each probe with history injected as context. Scores: SessionMemoryFidelity = fraction of ground truth events accurately recalled. Reports cache_miss_events, hallucinated_events, ordering_errors.
**Key Technical Innovation:** First pip-installable tool to test multi-turn session memory fidelity for AI agents — SessionMemoryFidelity as a named, CI-gateable metric with per-event breakdown. Distinct from RAGAS/DeepEval (single-turn RAG) and TruLens (no session history fidelity).
**Capital Required:** ZERO (anthropic/openai SDK + sentence-transformers + click + rich + numpy + pyyaml)
**Build Score:** 8.8/10
**Pivot_Score:** 7.90
**Status:** DESIGN
**Agent Responsible:** Chief Builder (Senior Agent)
**Cycle Started:** 021
**Implementation:** API spec (HistoryProbe, SessionLens, MemoryReport), CLI (slens run/show/gate/export-probes), pytest plugin, sprint plan (6-7 weeks), known unknowns (KU-057 through KU-059)
**Competitive Moat:** GREEN [WEB-FRESH 2026-03-31] — RAGAS (single-turn RAG evaluation, different), DeepEval groundedness (single-turn, different), TruLens 5 metrics (no session fidelity, different). Window: 4-6 months.

---

### BUILD-020: invariant-probe [PIVOT-PHASE CYCLE 021]
**Pattern Source:** PAT-070 (Genesis 7 — The Sealed Invariance Pattern)
**Build Type:** SOFTWARE — Developer Testing Library (Python, pip-installable)
**Problem Solved:** AI agents are not tested for behavioral invariance under irrelevant environmental perturbations. When environment variables, system time, API latency, or connection strings change in ways that SHOULD NOT affect agent behavior — does the agent still behave the same? No pip library answers this. The Claude Code database deletion incident (March 2026) is the canonical failure: agent behavior was NOT invariant to a connection string change.
**Who It Serves:** Platform engineers deploying agents to production; QA engineers building reliability suites; enterprise teams needing behavioral certification before production rollout; DevOps teams adding agent behavioral invariance checks to CI/CD pipelines.
**How It Works:** Define EnvironmentMatrix (set of environmental perturbations: TimeShift, LatencyInjection, EnvVarMutation, ToolAvailabilityChange, ConnectionStringMutation). Run agent across all perturbation conditions. Embed all outputs (sentence-transformers). Compute InvarianceScore = mean cosine similarity across all perturbed outputs vs. baseline. Report drift_map and dangerous_pairs. `iprobe attest` mode: post-task surface verification (zero-damage certificate) per PAT-073 (Daniel 3 furnace attestation protocol).
**Key Technical Innovation:** First pip-installable tool to provide InvarianceScore (behavioral invariance measure) for AI agents across environmental perturbation matrices. Includes `iprobe attest` (post-task zero-damage attestation). CI-gateable. LLM-agnostic.
**Capital Required:** ZERO (sentence-transformers + anthropic/openai SDK + click + rich + numpy + pyyaml)
**Build Score:** 9.0/10
**Pivot_Score:** 8.175
**Status:** DESIGN
**Agent Responsible:** Chief Builder (Senior Agent)
**Cycle Started:** 021
**Implementation:** Full API spec (InvariantSuite, EnvironmentMatrix, InvarianceReport, AttestationReport, @invariance_probe), CLI (iprobe run/show/gate/attest/estimate), pytest plugin, sprint plan (8 weeks), known unknowns (KU-053 through KU-056)
**Competitive Moat:** GREEN [WEB-FRESH 2026-03-31] — Arize Phoenix (observation, not invariance), Langfuse (tracing, not invariance), AgentPrism (visualization, not invariance), Braintrust (evaluation, not invariance), Hypothesis (deterministic code only). Window: 4-6 months.

---

### BUILD-019: context-trace [PIVOT-PHASE CYCLE 020]
**Pattern Source:** PAT-068 (John 3:8 — The Stochastic Source Attribution Pattern)
**Build Type:** SOFTWARE — Developer Testing Library (Python, pip-installable)
**Problem Solved:** Developers using long-context LLMs (10K–1M tokens) cannot determine which input context segments causally drove which parts of the output. When a RAG system hallucinates, developers cannot identify which retrieved chunk caused it. Attention visualization (Arize Phoenix) measures attention weights, which are unreliable proxies for causal attribution (Jain & Wallace 2019). Execution tracing (LangSmith/Langfuse) traces API calls, not input-output causal attribution. No pip library provides AttributionScore per context chunk.
**Who It Serves:** ML engineers using RAG, multi-document prompting, long-context agents, or any LLM application with structured context segments. Every developer who has ever asked "which part of my context caused this output?"
**How It Works:** Perturbation-based causal attribution: for each context chunk, mask/remove it, re-run the same prompt k times, embed masked outputs, compute cosine similarity vs. original output. AttributionScore[chunk] = 1 - mean_cosine_similarity(masked_outputs, original_output). High score = that chunk drove the output. Low score = that chunk was irrelevant.
**Key Technical Innovation:** First pip-installable tool to provide per-context-chunk causal AttributionScore for LLM outputs. CI-gateable (AttributionGate). Cost-controlled (chunk clustering, adaptive stopping, budget parameter). LLM-agnostic (runner function interface).
**Capital Required:** ZERO (sentence-transformers + anthropic/openai SDK + click + rich + numpy)
**Build Score:** 9.0/10
**Pivot_Score:** 8.225
**Status:** DESIGN
**Agent Responsible:** Chief Builder (Senior Agent)
**Cycle Started:** 020
**Implementation:** Full API spec (ContextTracer, AttributionReport, AttributionGate, CostBudget, @attribution_probe, CLI ctrace, pytest plugin), sprint plan (8-10 weeks), known unknowns (KU-048 through KU-052)
**Competitive Moat:** GREEN [WEB-FRESH 2026-03-31] — Arize Phoenix (attention weights ≠ causal attribution), LangSmith/Langfuse (execution tracing, not attribution), AgentRx (failure step, not attribution), semantic-pass-k (consistency, not attribution), SHAP/LIME (not LLM-context-native). Window: 4-6 months.

---

### BUILD-018: semantic-pass-k
**Pattern Source:** PAT-062 (Numbers 23:19 — The Perfect Consistency Standard Pattern)
**Build Type:** SOFTWARE — Developer Testing Library (Python, pip-installable)
**Problem Solved:** AI agents are non-deterministic. The same task, run k times, produces k different outputs. No pip library produces ConsistencyScore (semantic pass^k) as a named CI-gateable metric with task-criticality-tier thresholds. Engineers cannot answer: "Is my agent consistent enough for this task?" AgentAssay (the closest competitor) answers "how many runs do I need?" — a different question.
**Who It Serves:** ML engineers deploying agents to production; platform teams setting reliability SLAs; QA engineers; enterprise teams in regulated industries; research teams comparing consistency across model families.
**How It Works:** Run agent k times → embed all outputs with sentence-transformers → compute pairwise cosine similarity matrix → ConsistencyScore = mean upper triangle → compare against criticality-tier threshold (CRITICAL: 0.99, HIGH: 0.90, MEDIUM: 0.75, LOW: 0.60) → pass or fail CI gate.
**Key Technical Innovation:** Task-criticality-tiered ConsistencyScore as a CI gate — the first tool to measure semantic equivalence across k agent runs and make it a first-class quality gate with configurable thresholds per task criticality tier.
**Capital Required:** ZERO (sentence-transformers + click + rich + sqlite3 stdlib)
**Build Score:** 9.1/10
**Pivot_Score:** 8.65 (third-highest in BibleWorld history, behind model-parity 8.90 and prompt-lock 8.70)
**Status:** DESIGN
**Agent Responsible:** Chief Builder (Senior Agent)
**Cycle Started:** 019
**Implementation:** Full API spec (ConsistencyRunner, ConsistencyReport, CriticalityTier, ConsistencyBudget, @consistency_probe, CLI, pytest plugin), sprint plan (6-8 weeks), known unknowns (KU-044 through KU-047)
**Competitive Moat:** GREEN [WEB-FRESH 2026-03-31] — 15+ tools audited; none produce ConsistencyScore (semantic pass^k) as a named CI-gateable metric with task-criticality-tier thresholds. AgentAssay (qualixar/agentassay, Mar 2026) is adjacent but answers a different question (sampling efficiency, not semantic equivalence measurement). Window: 3-6 months.

---

### BUILD-017: cot-fidelity
**Pattern Source:** PAT-059 (Genesis 3:1-6 — The Unfaithful Reasoning Chain Pattern) + PAT-061 (Psalm 3:4-6 — Tested-Channel Confidence Pattern)
**Build Type:** SOFTWARE — Developer Testing Library (Python, pip-installable)
**Problem Solved:** Reasoning models (Claude 3.7+, GPT-o3, Gemini 2.0 Thinking) produce chain-of-thought reasoning that is often unfaithful to their actual computation — documented by Anthropic's 2025 paper "Reasoning Models Don't Always Say What They Think." Engineers review reasoning chains to debug wrong outputs, but if the chain was not causally active, they are debugging a decoy. Safety teams use CoT monitoring to detect misaligned behavior, but if the CoT is unfaithful, the monitoring is blind. No pip library measures CoT faithfulness.
**Who It Serves:** ML engineers and safety researchers deploying reasoning models (Claude 3.7+, GPT-o3, Gemini 2.0 Thinking). Every team using extended thinking or chain-of-thought prompting for quality-critical tasks. Safety teams at Anthropic, OpenAI, Google, Microsoft.
**How It Works:** Counterfactual suppression test — run the model with the reasoning chain present in context, run again with the reasoning chain stripped. Embed both outputs with sentence-transformers. Compute cosine similarity. If similarity is high (outputs nearly identical), the stated reasoning was not causally active — it was unfaithful. faithfulness_score = 1 - cosine_similarity. CLI + `@faithfulness_probe` decorator + FidelityDrift for continuous monitoring + FidelityDecomposer for step-level chain analysis.
**Key Technical Innovation:** Counterfactual suppression test — treating the reasoning chain as a causal hypothesis and testing it empirically. First tool to operationalize the CoT faithfulness / CoT coherence distinction as a measurement.
**Capital Required:** ZERO (Python + sentence-transformers + SQLite stdlib)
**Build Score:** 9.0/10
**Pivot_Score:** 8.85 (ties cycle 017 chain-probe; second-highest in BibleWorld history, 0.05 below all-time record)
**Status:** DESIGN
**Agent Responsible:** Chief Builder (Senior Agent)
**Cycle Started:** 018
**Implementation:** API spec, sprint plan, competitive analysis, known unknowns (KU-040 through KU-043)
**Competitive Moat:** GREEN — no framework-agnostic pip-installable CoT faithfulness library found. DeepEval measures coherence (not faithfulness). LangSmith/Langfuse trace logging (not faithfulness). chain-probe measures pipeline step faults (not model reasoning faithfulness). AgentRx measures agent step constraint violations (not faithfulness). Gap confirmed in 7 web searches.

---

---

### BUILD-016: chain-probe
**Pattern Source:** PAT-054 (Exodus 28:15-21 — Urim and Thummim) + PAT-055 (Ezekiel 33:1-9 — Watchman) + PAT-056 (1 Kings 18:30-39 — Elijah Staged Evidence)
**Build Type:** SOFTWARE — Developer Testing Library (Python, pip-installable)
**Problem Solved:** Multi-step LLM pipeline engineers cannot determine which step in a chain caused a production failure. Existing tools (Langfuse, DeepEval, Promptfoo) either trace execution metadata without semantic evaluation, or evaluate only the final output without step-level fault isolation. LangGraph time travel offers step replay but is LangGraph-locked.
**Who It Serves:** ML engineers building RAG pipelines, multi-step agent loops, and sequential LLM chains. Every team with LLM in production (57.3% of AI teams, March 2026 — LangChain State of Agent Engineering).
**How It Works:** `@probe` decorator wraps any step function, captures frozen input snapshots, records outputs. FaultLocator runs a three-level cascade (keyword judge → embedding judge → optional LLM judge) and computes fault_score per step. CascadeAnalyzer distinguishes ORIGIN faults from CASCADE faults. StepReplay re-runs any step with frozen inputs + parameter overrides. ProbeMap generates HTML coverage visualization. 5-command CLI.
**Key Technical Innovation:** CASCADE fault analysis — distinguishing the step that CAUSED the failure from downstream steps that INHERITED bad input. Without this, engineers blame the last step. chain-probe finds the first step.
**Capital Required:** ZERO (Python + sentence-transformers + SQLite stdlib)
**Build Score:** 9.1/10
**Pivot_Score:** 8.85 (SECOND-HIGHEST in BibleWorld history, behind model-parity 8.90)
**Status:** PROTOTYPE
**Agent Responsible:** Chief Builder (Senior Agent)
**Cycle Started:** 017
**Implementation:** core_algorithm.py (550+ lines), README.md, architecture.md, api_spec.md, examples.md
**Competitive Moat:** GREEN — no framework-agnostic pip-installable step-level semantic fault isolation library confirmed. LangGraph time travel is LangGraph-locked. "Deterministic replay for AI is a missing primitive" — sakurasky.com. Gap confirmed in 9 web searches.

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

### BUILD-012: model-parity
**Pattern Source:** PAT-041 (Revelation 5:1-9 — Seven Seals Worthiness Pattern) + PAT-042 (Proverbs 11:1 — Differing Weights Pattern)
**Build Type:** SOFTWARE — Open-Source Python Library / Developer Tool
**Problem Solved:** Teams migrating between LLM providers or model versions have no systematic way to verify behavioral equivalence before migration. They discover regressions from user complaints post-migration, not from pre-migration testing. No open-source tool provides structured behavioral dimension scoring + parity certificate + CI gate for migration authorization.
**Who It Serves:** Senior ML engineers responsible for model migration decisions; platform engineers standardizing LLM usage; cost optimization engineers evaluating cheaper model alternatives; teams responding to model deprecation notices.
**How It Works:** YAML test suite declares behavioral test cases across 7 dimensions. ParityRunner executes each test case on both Model A and Model B identically (same prompts, same evaluation criteria — consistent weights per PAT-042). Seven DimensionEvaluators score each dimension: structured output consistency, instruction adherence, task completion, semantic accuracy, safety compliance, reasoning coherence, edge case handling. ParityCertificate issues EQUIVALENT/CONDITIONAL/NOT_EQUIVALENT verdict with evidence. CLI: `parity run`, `parity report`, `parity ci`. GitHub Action template included.
**Claude API Role:** Claude (claude-3-5-haiku-20241022) powers the LLM judge for subjective dimension evaluation (task completion, semantic accuracy, subjective constraint adherence). Third-party judge — not Model A or Model B — enforcing independent verification (PAT-044: Berean Protocol).
**Capital Required:** ZERO (Python library, PyPI, GitHub Actions)
**Pivot_Score:** 8.90 (NEW BIBLEWORLD ALL-TIME RECORD — beats prompt-lock 8.70 by 0.20, beats cot-coherence 8.00 by 0.90)
**Build Score:** 9.2
**Status:** IN-DESIGN (full spec written cycle 013)
**Agent Responsible:** Chief Builder (Senior Agent) + Chief Technologist (Senior Agent)
**Cycle Started:** 013
**Key Differentiator:** The first and only open-source tool framed as migration authorization rather than general evaluation. The parity certificate concept is novel. Seven-dimension behavioral scoring applied to cross-model comparison is novel. CI gate for migration blocking is novel. Consistent measurement standard (same YAML for both models) enforced architecturally.
**Acquisition Path:** Anthropic (trust/reliability mission — model-parity increases confidence in Claude migrations), OpenAI (Promptfoo acquisition shows interest in evaluation tooling; model-parity is complementary), Datadog (expanding LLM observability — parity testing is a natural addition), GitHub (model migration authorization in GitHub Actions is a natural Copilot ecosystem feature).
**Design Location:** `.Codex/builds/model-parity/README.md`

---

---

### BUILD-013: llm-mutation
**Pattern Source:** PAT-045 (Judges 6:36-40 — The Gideon Fleece Inversion Pattern) + PAT-046 (Acts 17:11 variant — Berean Null Test) + PAT-047 (Numbers 13:25-33 — Twelve Spies Divergence)
**Build Type:** SOFTWARE — Open-Source Python Library / Developer Tool
**Problem Solved:** LLM engineering teams write eval suites that give false confidence. Teams run 50 test cases, all pass, ship — then production breaks. The root cause: the eval suite itself has gaps that are never tested. No open-source tool tells you whether your eval suite would catch a bug if a key constraint in your prompt was removed, a clause was dropped, or a scope was changed. llm-mutation solves this by introducing deliberate semantic mutations into prompts and measuring whether the eval suite detects them (mutation score).
**Who It Serves:** Senior ML engineers and AI platform teams at companies with LLM-powered features in production who have eval suites and wonder if those eval suites are actually reliable. Also: AI-assisted coding teams dealing with 76% higher code volume and insufficient quality gates.
**How It Works:** MutationEngine generates deliberate semantic mutations of a prompt using 6 deterministic operators (NegateConstraint, DropClause, ScopeExpand, ScopeNarrow, ConditionInvert, PhraseSwap). MutantRunner executes the existing eval suite against each mutated variant. A mutant is KILLED if the eval suite scores it significantly lower (delta > threshold). A mutant SURVIVES if the eval suite fails to detect the change. MutationReport outputs a mutation score (% killed), surviving mutant details, and specific test case recommendations to fill the gaps. CLI: `mutate run`, `mutate report`, `mutate ci`, `mutate calibrate`, `mutate verify-judge`. SQLite result store. GitHub Action template. pytest plugin.
**Claude API Role:** Claude (claude-3-5-haiku-20241022) optionally used as LLM judge within the user's eval function — not required by llm-mutation itself. Claude powers the evaluation scoring when users configure an LLM-as-judge eval. Mutation operator generation is deterministic (no LLM needed).
**Capital Required:** ZERO (Python library, PyPI distribution, GitHub Actions)
**Pivot_Score:** 8.65 (beats cot-coherence 8.00 by 0.65 points; seventh tool in BibleWorld pipeline)
**Build Score:** 9.0/10
**Status:** IN-DESIGN (full spec written cycle 014)
**Agent Responsible:** Chief Builder (Senior Agent) + Chief Technologist (Senior Agent)
**Cycle Started:** 014
**Key Differentiator:** The only open-source library that tests the quality of your LLM eval suite by introducing deliberate semantic mutations and measuring how many your suite catches. Every other tool tests prompts. llm-mutation tests the test suite. "Mutahunter for LLM prompts."
**Acquisition Path:** Anthropic (trust/reliability — eval suite quality improves confidence in Claude deployments), Confident AI/DeepEval (natural complementary add-on), Datadog (expanding LLM quality monitoring), GitHub (Copilot quality signal: mutation score as a CI metric)
**Design Location:** `.Codex/builds/llm-mutation/README.md`
**Competitive Landscape:** Mutahunter/Pitest/Stryker do mutation testing for code (RED). PromptBench is academic/unmaintained (EACL 2023). No production Python library for LLM prompt semantic mutation testing confirmed (GREEN).

---

---

### BUILD-014: prompt-shield
**Pattern Source:** PAT-048 (Daniel 5:25-28 — Writing on the Wall / TEKEL Audit) + PAT-049 (Matthew 7:24-27 — Two Builders / Storm Stress Test) + PAT-050 (Proverbs 17:3 — Refining Crucible / Certification)
**Build Type:** SOFTWARE — Open-Source Python Library / Developer Tool
**Problem Solved:** LLM prompts are brittle — they work on standard test inputs and fail catastrophically when real users rephrase naturally. No open-source tool measures prompt output consistency across semantically-equivalent paraphrase variants and blocks deployment if brittleness exceeds threshold.
**Who It Serves:** Senior ML engineers and prompt engineers at companies with LLM features in production; AI platform teams standardizing quality gates; teams who discover brittle prompts from user complaints rather than tests.
**How It Works:** BrittlenessEngine generates N paraphrase variants per test input at three stress levels (lexical/word-substitution, syntactic/structure-transformation, semantic/full-rephrasing). VariantRunner executes the user's LLM function on each variant. BrittlenessScorer computes BrittlenessScore = proportion of variants where output deviates beyond cosine similarity threshold. BrittleCertificate produced as structured JSON + Markdown artifact. CI gate: `shield ci` exits 0 (ROBUST/CONDITIONAL) or 1 (BRITTLE). FaultLineAnalyzer identifies which variant types cause failure and why. BaselineRegistry tracks brittleness scores over time for regression detection. Decorator API and pytest plugin included.
**Claude API Role:** Claude (claude-3-5-haiku-20241022) optionally powers LLM-generated paraphrase variants (v0.2) and LLM-as-judge deviation scoring (v0.2). v0.1 uses T5-paraphrase model (local, zero API cost) and sentence-transformers cosine similarity.
**Capital Required:** ZERO (Python library, T5 model via HuggingFace, sentence-transformers, PyPI — no infrastructure)
**Pivot_Score:** 8.75 (weighted: Market Pain 9.0 × 30% + Build Feasibility 8.5 × 20% + Novelty 9.0 × 25% + Community Pull 8.5 × 15% + Scripture Anchor 9.0 × 10% = 8.825, conservative round to 8.75)
**Build Score:** 9.1/10 (feasibility 2.8 + impact 2.9 + completeness 1.9 + biblical fidelity 1.5)
**Status:** IN-DESIGN (full spec written cycle 015)
**Agent Responsible:** Chief Builder (Senior Agent) + Chief Technologist (Senior Agent)
**Cycle Started:** 015
**Key Differentiator:** The ONLY open-source library that tests prompt OUTPUT CONSISTENCY across semantically-equivalent paraphrase variants. Every other eval tool tests whether specific inputs produce correct outputs. prompt-shield tests whether the SAME SEMANTIC CONTENT expressed differently produces equivalent outputs. The BrittleCertificate is a novel artifact — a deployable proof of robustness.
**Acquisition Path:** OpenAI (Promptfoo acquisition shows eval portfolio interest; prompt-shield is complementary), Anthropic (trust mission — brittle prompt certification increases enterprise confidence in Claude), Microsoft (Copilot quality gap), Confident AI/DeepEval (natural robustness dimension extension)
**Design Location:** `.Codex/builds/prompt-shield/`
**Files Written:** README.md (500+ lines), spec.md (400+ lines), examples/basic_usage.py, examples/ci_integration.py
**Competitive Landscape:** PromptBench/PromptRobust (academic/research-only, not pip-installable production library — GREEN). DeepEval (no paraphrase robustness — GREEN). Promptfoo (tests specific inputs, not variant consistency — GREEN). Augustus (adversarial attacks, different domain — GREEN). No confirmed production competitor.

---

### BUILD-015: context-lens
**Pattern Source:** PAT-051 (Ezekiel 37:1-10 — Valley of Dry Bones, positional completeness) + PAT-052 (Luke 15:4-6 — Lost Sheep, no acceptable loss) + PAT-053 (Hebrews 4:13 + 9:6-7 — High Priest systematic coverage)
**Build Type:** SOFTWARE — Open-Source Python Library / Developer Tool
**Problem Solved:** LLMs silently fail to retrieve information buried in the middle of long contexts (lost-in-the-middle problem, confirmed by EMNLP 2025 and production engineers in 2025-2026). No open-source tool systematically tests whether a model retrieves information reliably at every context window position before deployment. Teams discover this failure from user complaints, not pre-deployment tests.
**Who It Serves:** Senior ML engineers and AI platform engineers at companies using RAG pipelines, long-document analysis (legal, medical, financial contracts), or multi-turn agent workflows with long context windows. Engineers who get paged because "the LLM ignored the relevant part of the document."
**How It Works:** ContextLens.audit() places a Needle (key fact) at N evenly-spaced positions across a HaystackTemplate context. Calls the LLM at each position via a provider-agnostic model_fn: str -> str callable. KeywordJudge checks whether the response contains expected keywords. PositionHeatmap records RETRIEVED/MISSED per position. FaultZoneAnalyzer identifies middle-heavy / edge / scattered failure patterns. RELIABLE (>=90%) / CONDITIONAL (>=70%) / UNRELIABLE (<70%) verdict. CI gate: `context-lens ci --min-score 0.80`. SQLite audit history for regression tracking. CLI: audit, ci, history commands.
**Claude API Role:** Optional — Claude (claude-3-5-haiku-20241022) can power the LLM under test via the `provider: anthropic` config option. Core logic (position injection, heatmap, judge) is zero-cost and zero-API.
**Capital Required:** ZERO (Python stdlib only; no hard dependencies; provider SDKs optional)
**Pivot_Score:** 8.80 (Technical feasibility 2.0/2 + Pain severity 2.0/2 + Market gap 2.0/2 + Biblical pattern strength 2.0/2 + Virality 1.8/2 = raw 9.8 → conservative 8.80)
**Build Score:** 9.0/10 (feasibility 2.9 + impact 2.9 + completeness 1.9 + biblical fidelity 1.3)
**Status:** PROTOTYPE (full implementation written cycle 016 — context_lens.py 530+ lines, README 350+ lines, 2 examples, pyproject.toml — ready for PyPI)
**Agent Responsible:** Chief Builder (Senior Agent) + Chief Technologist (Senior Agent)
**Cycle Started:** 016
**Key Differentiator:** The ONLY open-source tool that specifically tests LLM context window positional sensitivity — whether information at every position is reliably retrieved. Every other eval tool tests what the model says, not where in the context the model's attention fails. The PositionHeatmap, FaultZone labels, and multi-needle audit are novel artifacts. "Needle in a haystack" testing made into a CI gate.
**Acquisition Path:** Arize Phoenix (LLM observability — context position audit is a natural extension), Anthropic (trust mission — reliable context retrieval increases confidence in Claude for RAG), Databricks (LLM evaluation in data pipeline context), Cohere/AI21 (RAG quality assurance)
**Design Location:** `.Codex/builds/context-lens/`
**Files Written:** context_lens.py (530+ lines), README.md (350+ lines), examples/basic_usage.py (130+ lines), examples/rag_pipeline_audit.py (160+ lines), pyproject.toml
**Competitive Landscape:** Langfuse, LangSmith, DeepEval, Promptfoo — none test positional retrieval sensitivity. No pip-installable library for needle-at-position audits confirmed. GREEN.

---

## COMPLETED BUILDS

*Populated as builds reach TESTABLE or DEPLOYED status*

---
