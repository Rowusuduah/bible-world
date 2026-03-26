# BibleWorld Cycle 001 — Builds

**Cycle:** 001 | **Date:** 2026-03-26
**Builds This Cycle:** 2 (specced, not yet coded)

---

## BUILD-001: EvalGate — AI Agent Evaluation Architecture
**Source Pattern:** PAT-009 (Genesis 1 Evaluation Loop)
**Build Type:** Software — AI Infrastructure
**Status:** SPECCED

### What It Is
EvalGate is a middleware layer for multi-step AI agent pipelines that enforces mandatory evaluation checkpoints between generation steps. The agent cannot proceed to the next tool call or generation step without clearing a confidence threshold at the current step. Built for LangChain, CrewAI, and raw API chains.

### The Problem It Solves
Current AI agent pipelines generate hallucinations that propagate through subsequent steps unchecked. Step 1 produces an error. Step 2 takes the error as input and compounds it. Step 3 takes the compound error and compounds further. By the time the human sees output, the error is deeply embedded and hard to trace. EvalGate stops propagation at the source.

### Architecture
```
Step N Output
     ↓
EvalGate Checkpoint
  ├── Confidence score calculation (embedding similarity to ground truth, or LLM self-evaluation)
  ├── If score >= threshold: proceed to Step N+1
  └── If score < threshold: retry Step N (max 3 retries) or halt + flag for human review
     ↓
Step N+1 Input (verified)
```

### Revenue Model
- Open source core (MIT license) — drives adoption
- EvalGate Cloud: hosted evaluation service with pre-built evaluators, audit logs, and dashboards
- Pricing: $0.001 per evaluation checkpoint call
- Enterprise: $500/month flat rate, unlimited calls, SLA, custom evaluators
- Target: AI application developers, enterprise LLM deployments

### What Kills It
- OpenAI/Anthropic builds native evaluation into their APIs (likely within 18 months)
- Evaluation overhead adds latency — users opt out for speed
- Confidence scoring itself is unreliable (evaluating the evaluator problem)

### Moat
First-mover in checkpoint-native pipeline design. Network effects from evaluation benchmark dataset built from all EvalGate Cloud users. Enterprise audit log compliance differentiation.

### Can You Start With Laptop + Claude?
Yes. Week 1: build Python library with LangChain integration. Week 2: publish to PyPI. Week 3: gather early users from AI Discord communities. Week 4: instrument telemetry, begin building cloud service.

### Ghana/Africa Version
Same product. Target African AI development teams (Accra, Lagos, Nairobi tech scenes). Price in GHS/NGN/KES. Partner with Pan-African AI accelerators (e.g., Google for Startups Africa, Zindi) for distribution.

---

## BUILD-002: LogosSchema — Schema-First Business Design Tool
**Source Pattern:** PAT-012 (Logos as Generative Schema)
**Build Type:** Software — Business Infrastructure
**Status:** SPECCED

### What It Is
LogosSchema is a web tool that forces founders to define their business constitution before writing any code. The tool guides founders through defining: entity types (customers, suppliers, products, transactions), relationships between entities, rules governing each relationship, payment flows, and dispute resolution processes. The output is a machine-readable business schema (JSON-LD or similar) from which API structures, database schemas, and basic CRUD scaffolding are auto-generated.

### The Problem It Solves
Most African tech startups fail not because of bad code but because the business schema was never explicitly defined. The database ends up shaped by whatever the first developer felt like building. Relationships are implicit. Rules are tribal knowledge held by the founder. When the founder leaves or the team scales, the system collapses because there is no schema — only accumulated decisions.

### Architecture
```
Guided Schema Builder (web UI)
     ↓
Business Constitution (structured JSON)
     ↓
┌───────────────────────────────┐
│  Code Generator               │
│  ├── Database schema (SQL)    │
│  ├── API skeleton (FastAPI)   │
│  ├── Admin panel scaffolding  │
│  └── Data dictionary (docs)   │
└───────────────────────────────┘
```

### Revenue Model
- Free tier: up to 3 entity types, basic code generation
- Pro: $49/month, unlimited entities, full code generation, team collaboration
- Enterprise: $299/month, custom rules engine, audit trail, API access
- Africa Startup Pack: $15/month (PPP-adjusted pricing for West/East Africa)

### What Kills It
- Low-code tools (Bubble, Retool) already do parts of this
- Founders resist constraint — they want to code immediately, not design first
- The code generation quality is often lower than a decent developer writing from scratch

### Moat
Unique framing (business constitution = competitive advantage): the tool teaches a discipline, not just a feature. The schema becomes the company's most valuable internal document. Network effects if schemas can be shared as templates within industry verticals.

### Can You Start With Laptop + Claude?
Yes. Week 1: build the guided schema builder in React, output JSON. Week 2: build the database schema generator (SQLAlchemy models from JSON schema). Week 3: beta with 3 African startup founders. Week 4: add API skeleton generator.

### Ghana/Africa Version
Price at GHS 75/month (Pro tier). Partner with MEST Africa, iBEC, mHub Malawi, iHub Nairobi for distribution. Offer a free Cohort License for accelerator batches.

---

## BUILD REGISTRY UPDATE
- BUILD-001 (EvalGate) added to build registry
- BUILD-002 (LogosSchema) added to build registry
- Total active builds: 2
