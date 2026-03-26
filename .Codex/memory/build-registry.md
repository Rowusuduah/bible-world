# BibleWorld Build Registry
## Living Record of All Software, Apps, Models, and Business Designs

**Last Updated:** Cycle 001
**Total Builds:** 2
**Builds in Design:** 4 (PAT-001 Voice Builder, PAT-006 Babel Reversal, BUILD-001 EvalGate, BUILD-002 LogosSchema)
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

## COMPLETED BUILDS

*Populated as builds reach TESTABLE or DEPLOYED status*

---
