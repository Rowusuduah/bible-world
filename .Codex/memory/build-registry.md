# BibleWorld Build Registry
## Living Record of All Software, Apps, Models, and Business Designs

**Last Updated:** Cycle 002
**Total Builds:** 7
**Builds in Design:** 7 (BUILD-001 EvalGate, BUILD-002 LogosSchema, BUILD-003 DecreeDAO, BUILD-004 GrantPilot, BUILD-005 TrustChain, BUILD-006 DemoFirst, BUILD-007 KnowFirst)
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
**Pattern Source:** PAT-014 (Psalm 2:8 — Ask-Receive Distribution)
**Build Type:** SOFTWARE — AI Grant Writing SaaS
**Problem Solved:** African organizations leave billions in grant funding untapped because they cannot write proposals meeting funder requirements
**Who It Serves:** Grant consultants (primary), African NGOs, international organizations, accelerators
**How It Works:** User inputs org description + program + funder. GrantPilot generates complete funder-formatted proposal with all standard sections.
**Claude API Role:** Core — Claude generates every proposal section and maintains funder preference knowledge
**Capital Required:** ZERO
**Build Score:** 8.5
**Status:** IN-DESIGN
**Agent Responsible:** Chief Builder
**Cycle Started:** 002
**Priority:** #1 — Highest revenue ceiling, clearest pain, fastest to build

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

## COMPLETED BUILDS

*Populated as builds reach TESTABLE or DEPLOYED status*

---
