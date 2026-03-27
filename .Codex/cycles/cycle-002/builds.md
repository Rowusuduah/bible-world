# BibleWorld Cycle 002 — Builds
## Buildable Products from Scripture Patterns

**Date:** 2026-03-26
**Cycle Type:** B (BUILD)
**New Builds This Cycle:** 5 (BUILD-003 through BUILD-007)
**Build-Ready (Week 1 MVP):** 4

---

## BUILD-003: DecreeDAO
**Pattern Source:** PAT-013 (Psalm 2:6-7 — The Decree Protocol)
**Build Type:** SOFTWARE — Governance SaaS
**Problem Solved:** African cooperatives and diaspora investment clubs fail because authority is informal, undocumented, and disputed. No one knows who has authority to do what, or how that authority was granted.
**Who It Serves:** Diaspora investment clubs, agricultural cooperatives (shea, cocoa, cassava), NGOs with governance requirements
**How It Works:** Web app where cooperative/club leaders create formal, timestamped, immutable decrees: roles, permissions, spending limits, voting rules. Every decree is logged, versioned, and visible to all members. Constitution builder templates for common organization types.

**Architecture:**
```
Member sign-up → Role assignment → Decree creation (templates + custom)
  → Audit log (immutable) → Member dashboard → Spending approval workflow
```

**Claude API Role:** Claude generates governance templates from org description; drafts decree language; validates consistency of rules across decrees.
**Capital Required:** ZERO
**Build Score:** 7.5
**Status:** IN-DESIGN
**Ship Week 1 MVP?** YES — Next.js + Supabase (auth + database) + Claude API for template generation. Deploy on Vercel.

**Revenue Model:**
- Free tier: 5 members, 3 decrees
- Starter: $19/month (20 members, unlimited decrees)
- Professional: $99/month (100 members, spending workflows, export)
- Enterprise: $499/month (unlimited, API access, white-label for NGO programs)

**Target MRR at 100 orgs:** $5,000-$10,000

---

## BUILD-004: GrantPilot
**Pattern Source:** PAT-014 (Psalm 2:8 — Ask-Receive Distribution)
**Build Type:** SOFTWARE — AI Grant Writing SaaS
**Problem Solved:** African NGOs, cooperatives, and social enterprises leave billions in grant funding on the table because they cannot write proposals that meet funder formatting and quality requirements. The capacity exists; the request mechanism is broken.
**Who It Serves:** Grant consultants (primary — highest willingness to pay), African NGOs and social enterprises, international organizations with Africa programs, accelerators

**How It Works:** User inputs: (1) organization description, (2) program description, (3) funder name or grant call. GrantPilot generates a complete, funder-formatted proposal including: executive summary, problem statement, theory of change, activities, budget framework, M&E plan, sustainability plan, organizational capacity statement.

**Architecture:**
```
Org profile (one-time) → Grant call input → Funder template matching
  → Claude generates full proposal sections → User reviews/edits → Export (Word/PDF)
```

**Claude API Role:** Core product. Claude generates every proposal section. Claude also maintains a knowledge base of funder preferences, common requirements, and template formats.
**Capital Required:** ZERO
**Build Score:** 8.5
**Status:** IN-DESIGN
**Ship Week 1 MVP?** YES — Simple form → Claude API → formatted output in markdown → copy/paste. Full Word/PDF export in week 2.

**Revenue Model:**
- Pay per proposal: $29/proposal
- Monthly: $99/month (10 proposals)
- Professional: $199/month (unlimited + funder template library)
- Enterprise: $499/month (team access + custom templates + CRM integration)

**Target MRR at 100 users:** $15,000-$20,000

**Why This Ships First:** Highest revenue potential, clearest pain point, most straightforward Claude API implementation, international grant consultants are eager-to-pay customers.

---

## BUILD-005: TrustChain
**Pattern Source:** PAT-015 (John 1:35-42 — Referral Chain Trust Propagation)
**Build Type:** SOFTWARE — Deal Flow Platform
**Problem Solved:** Diaspora investors receive cold deal flow from Ghana that they cannot verify. No mechanism exists to see who referred a deal, how trustworthy the referrer is, or how deep the referral chain goes. Result: paralysis or fraud losses.
**Who It Serves:** Diaspora investment clubs, angel investors with Africa focus, fund managers, deal originators who want to build verified reputation

**How It Works:** Every deal submitted to the platform has a visible referral chain. Each referrer has a trust score based on: (1) number of prior successful referrals, (2) outcomes of referred deals, (3) referrer's verified credentials. Investors can filter deals by trust-chain depth and minimum referrer score.

**Architecture:**
```
Deal submission → Referrer identification → Trust chain construction
  → Trust score calculation → Investor dashboard (filter by trust score)
  → Deal tracking → Outcome logging → Trust score update
```

**Claude API Role:** Claude analyzes deal documents for red flags, generates deal summaries, and assists investors in due diligence questions.
**Capital Required:** ZERO
**Build Score:** 8.0
**Status:** IN-DESIGN
**Ship Week 1 MVP?** YES — Web app with deal submission form, referral chain display, simple trust scoring algorithm. No complex infrastructure.

**Revenue Model:**
- Investor club: $49/month per club
- Deal originator: $99/month (build referral reputation, priority listing)
- Fund manager: $299/month (advanced filtering, API access, custom reports)
- Transaction fee: 0.5% on deals closed through platform

**Target MRR at 50 clubs + 20 originators:** $4,430 + transaction fees

---

## BUILD-006: DemoFirst
**Pattern Source:** PAT-016 (John 1:39,46 — "Come and See" Conversion)
**Build Type:** SOFTWARE — Demo Generation Tool
**Problem Solved:** SaaS founders spend weeks building landing pages and demo videos when the most powerful conversion mechanism is direct product experience. But creating interactive demos requires design and engineering time most founders do not have.
**Who It Serves:** SaaS founders, B2B sales teams, product marketers

**How It Works:** Founder describes their product in natural language. DemoFirst generates a clickable, interactive demo (HTML/CSS/JS) that prospects can use immediately. No signup required. The demo is the landing page.

**Architecture:**
```
Product description input → Claude generates interactive demo (HTML/JS)
  → Preview → Customize (colors, data, flow) → Deploy (unique URL)
  → Analytics (who clicked what, how long they stayed)
```

**Claude API Role:** Core — Claude generates the entire interactive demo from a text description. This is a direct application of PAT-001 (God said, it was).
**Capital Required:** ZERO
**Build Score:** 7.6
**Status:** IN-DESIGN
**Ship Week 1 MVP?** PARTIAL — Week 1: Claude generates static HTML demos. Week 2-3: interactive elements, analytics.

**Revenue Model:**
- Free: 1 demo
- Starter: $29/month (5 demos)
- Pro: $99/month (unlimited + analytics + custom domain)
- Enterprise: $299/month (team, API, white-label)

**Target MRR at 100 users:** $5,000-$8,000

---

## BUILD-007: KnowFirst
**Pattern Source:** PAT-017 (John 1:47-49 — Pre-Knowledge Trust Collapse)
**Build Type:** SOFTWARE — AI Pre-Meeting Intelligence
**Problem Solved:** B2B professionals and diaspora founders walk into meetings without sufficient context about the people and organizations they are meeting. Research takes 30-60 minutes per meeting. Most skip it. Result: slower trust-building, missed opportunities, wasted meetings.
**Who It Serves:** B2B sales professionals, diaspora founders meeting Ghana-based partners, consultants, investment professionals

**How It Works:** Input: person name + company name + meeting context. Output: 1-page brief covering person background, company context, likely pain points, recent activity, conversation openers, and red flags. Delivered 30 minutes before meeting.

**Architecture:**
```
Input (name + company + context) → Data aggregation (LinkedIn, web, news)
  → Claude synthesis → 1-page brief → Delivery (email, Slack, web)
  → Meeting outcome logging → Brief quality feedback loop
```

**Claude API Role:** Core — Claude synthesizes aggregated data into a coherent, actionable brief. The AI is the product.
**Capital Required:** ZERO
**Build Score:** 8.3
**Status:** IN-DESIGN
**Ship Week 1 MVP?** YES — Claude API + basic web scraping → synthesized brief. Simple web UI.

**Revenue Model:**
- Individual: $29/month (10 briefs)
- Professional: $49/month (30 briefs)
- Team: $199/month (unlimited + shared briefs)
- API: $0.10/brief for CRM integration

**Target MRR at 100 users:** $4,000-$6,000

---

## BUILD PORTFOLIO SUMMARY

| Build | Pattern | Score | Week 1 MVP? | MRR Target (100 users) | Priority |
|-------|---------|-------|-------------|----------------------|----------|
| BUILD-004 GrantPilot | PAT-014 | 8.5 | YES | $15,000-$20,000 | **#1** |
| BUILD-007 KnowFirst | PAT-017 | 8.3 | YES | $4,000-$6,000 | #2 |
| BUILD-005 TrustChain | PAT-015 | 8.0 | YES | $4,430+ | #3 |
| BUILD-006 DemoFirst | PAT-016 | 7.6 | PARTIAL | $5,000-$8,000 | #4 |
| BUILD-003 DecreeDAO | PAT-013 | 7.5 | YES | $5,000-$10,000 | #5 |

**Total potential MRR at scale:** $33,430-$48,430/month across all 5 products.

**Recommendation:** Ship GrantPilot first. Highest revenue ceiling, clearest pain point, fastest to build.

---
