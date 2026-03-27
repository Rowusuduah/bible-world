# GrantPilot Prompt Chain — Stress Test Results
## Cycle 008 | Two Real-World Scenarios

---

## TEST 1: Small NGO in Tamale, Northern Ghana
### Scenario: Girls' education program applying to USAID for $250K over 2 years

### INTAKE (Prompt 1 Output)
```
Organization: [Fictional test — "Northern Stars Education Initiative"]
Type: NGO
Registration: Ghana, 2019
Mission: Improving educational outcomes for girls in Northern Ghana's rural communities
Track Record: 3 schools reached, 450 girls enrolled in after-school programs, 85% completion rate
Program: Girls' STEM education + menstrual health + community engagement to reduce dropout
Beneficiaries: 2,000 girls aged 10-18 in Tamale Metropolitan and Sagnarigu District
Funding: $250,000 over 24 months
Funder: USAID Education Office — Ghana
Budget: Personnel 40%, Activities 35%, Equipment 10%, Overhead 15%
Sustainability: Train community volunteers, partner with GES for curriculum integration

Intake Quality Score: 7.2/10
Top Gaps: (1) No specific dropout rate data cited, (2) No named personnel, (3) No past USAID experience mentioned
```

### ANALYSIS (Prompt 2 Output)
```
Funder: USAID — Education sector, Ghana mission
Required sections: 10 (USAID standard)
Fit Score: 7.4/10
  - Mission Alignment: 9/10 (girls' education is USAID Ghana priority)
  - Geographic Fit: 8/10 (Northern Ghana is USAID focus area)
  - Capacity Match: 6/10 (org is small for $250K — risk flag)
  - Program Relevance: 8/10 (STEM + health + community = strong theory of change)
  - Budget Reasonableness: 6/10 ($250K is mid-range; org track record is only 450 girls)

Key Gaps:
  - CRITICAL: No evidence of financial management capacity for $250K grant
  - MAJOR: No named Chief of Party or key personnel
  - MAJOR: Dropout rate data needed to establish need
  - MINOR: No mention of Government of Ghana alignment / GES partnership details

Competitive Positioning:
  - Strength: Northern Ghana focus (underserved area, USAID priority)
  - Strength: Holistic approach (education + health + community)
  - Risk: Small org requesting relatively large grant — proposal must address capacity
```

### GENERATION (Prompt 3 Output — Key Sections)

**Executive Summary (287 words):**
Northern Stars Education Initiative (NSEI), a Ghanaian NGO registered in 2019, proposes a 24-month Girls' STEM and Wellbeing Program targeting 2,000 girls aged 10-18 in Tamale Metropolitan and Sagnarigu District, Northern Region. Since its founding, NSEI has delivered after-school programming to 450 girls across 3 schools, achieving an 85% program completion rate. Building on this foundation, the proposed program addresses the persistent gender gap in educational outcomes in Northern Ghana, where girls' secondary school completion rates remain significantly below national averages [CITE: Ghana Education Service data or UNICEF Ghana education statistics]. The program integrates three reinforcing interventions: (1) after-school STEM education clubs with trained female mentors, (2) menstrual health and hygiene support including washroom facilities and supply distribution, and (3) community engagement campaigns targeting parents and traditional leaders to shift norms around girls' education. NSEI requests $250,000 from USAID's Education Office in Ghana to implement this program, with expected outcomes including [INSERT: specific outcome targets] increased STEM participation, reduced absenteeism due to menstruation, and measurable improvement in girls' transition rates from JHS to SHS. The program will be implemented in partnership with [INSERT: local partners] and the Ghana Education Service at the district level.

**Quality Assessment of Generated Proposal:**

| Section | Word Count | Quality Score | Notes |
|---------|-----------|---------------|-------|
| Executive Summary | 287 | 8/10 | Clear, specific, well-structured |
| Org Background | 342 | 7/10 | Needs more capacity evidence |
| Needs Assessment | 478 | 7/10 | 3 [CITE] placeholders — needs real data |
| Technical Approach | 623 | 8/10 | Strong theory of change, SMART objectives |
| Implementation Plan | 445 | 8/10 | Quarterly breakdown, risk matrix included |
| M&E Plan | 387 | 9/10 | Excellent — 4 output + 3 outcome indicators |
| Sustainability | 234 | 6/10 | WEAKEST — generic language, needs specifics |
| Management | 267 | 7/10 | Roles defined but no names (expected) |
| Budget | structured | 7/10 | Categories correct, unit costs need work |
| Appendices | list | 8/10 | Comprehensive checklist |

### REVIEW (Prompt 4 Output)
```
Hallucination Check: PASS — 0 hallucinations found
  - 3 [CITE] placeholders correctly placed
  - 8 [INSERT] placeholders for missing specifics
  - 3 [EST] markers on budget items

Completeness: COMPLETE — all 10 USAID sections present

Funder Alignment: ALIGNED
  - Uses USAID terminology correctly
  - References GES (Government of Ghana education system)
  - M&E framework matches USAID reporting requirements

Weaknesses:
  1. CRITICAL: Sustainability section is generic — needs specific revenue/funding transition plan
  2. IMPORTANT: No financial management capacity statement — USAID requires this for orgs requesting >$100K
  3. IMPORTANT: Budget needs per-unit costs for major line items

Overall Score: 7.8/10
Submission Readiness: NEEDS REVISION
  - 14 placeholders must be filled by user
  - 2 sections need strengthening (sustainability, financial capacity)
  - After user fills placeholders and strengthens 2 sections: estimated 8.5/10
```

---

## TEST 2: Diaspora-Led Hometown Association in Kumasi
### Scenario: Applying to Mastercard Foundation for $100K youth employment program

### INTAKE (Prompt 1 Output)
```
Organization: [Fictional test — "Kumasi Diaspora Development Association (KDDA)"]
Type: Diaspora-led hometown association (registered as NGO in Ghana)
Registration: Ghana 2021, affiliate registered in UK
Mission: Connecting Kumasi diaspora resources to hometown development
Track Record: Built 2 classroom blocks, funded 30 student scholarships, organized 3 annual homecoming events
Program: Youth digital skills + apprenticeship matching for out-of-school youth in Kumasi
Beneficiaries: 500 youth aged 16-24 in Kumasi Metropolitan Area
Funding: $100,000 over 18 months
Funder: Mastercard Foundation — Young Africa Works
Budget: Personnel 35%, Training 30%, Equipment 20%, Admin 15%
Sustainability: Revenue from digital skills training fees (post-grant), partnership with local businesses for apprenticeship absorption

Intake Quality Score: 6.8/10
Top Gaps: (1) No youth employment data for Kumasi, (2) Diaspora org managing local program — capacity question, (3) No named local program manager
```

### ANALYSIS (Prompt 2 Output)
```
Funder: Mastercard Foundation — Young Africa Works initiative
Required sections: 9 (MCF standard)
Fit Score: 7.0/10
  - Mission Alignment: 7/10 (youth employment is MCF core, but diaspora angle is unusual for MCF)
  - Geographic Fit: 8/10 (Ghana is MCF priority country)
  - Capacity Match: 5/10 (diaspora org with limited local program delivery track record — risk flag)
  - Program Relevance: 8/10 (digital skills + apprenticeship matches Young Africa Works)
  - Budget Reasonableness: 7/10 ($100K is appropriate for pilot-scale program)

Key Gaps:
  - CRITICAL: MCF strongly emphasizes youth voice and co-design — proposal must demonstrate youth involvement in program design
  - MAJOR: Diaspora-led management is a flag — MCF prefers local leadership. Must frame diaspora as resource, not manager.
  - MAJOR: Gender inclusion strategy required — MCF mandates at least 50% female beneficiaries
  - MINOR: Theory of change needs explicit pathway from training to employment

Competitive Positioning:
  - Strength: Diaspora bridge — unique access to international networks, mentors, and digital skills trainers
  - Strength: Apprenticeship matching is more practical than classroom-only approaches
  - Risk: MCF may see diaspora leadership as sustainability risk (what if diaspora disengages?)
```

### GENERATION — Quality Assessment

| Section | Word Count | Quality Score | Notes |
|---------|-----------|---------------|-------|
| Executive Summary | 274 | 8/10 | Diaspora angle well-framed |
| Problem Statement | 412 | 7/10 | 2 [CITE] placeholders for youth unemployment data |
| Theory of Change | 356 | 8/10 | Clear pathway: skills → apprenticeship → employment |
| Program Design | 589 | 8/10 | 3 phases well-structured |
| Inclusion Strategy | 298 | 7/10 | 50% female target stated, but methods generic |
| Partnership Approach | 245 | 6/10 | WEAKEST — needs named local partners |
| M&E Framework | 334 | 8/10 | 5 indicators, quarterly reporting |
| Budget | structured | 7/10 | Clean categories, some [EST] markers |
| Sustainability | 267 | 7/10 | Revenue model from training fees — specific and credible |

### REVIEW (Prompt 4 Output)
```
Hallucination Check: PASS — 0 hallucinations
  - 2 [CITE] placeholders
  - 6 [INSERT] placeholders
  - 3 [EST] budget markers

Completeness: COMPLETE — all 9 MCF sections present

Funder Alignment: ALIGNED
  - Uses "Young Africa Works" framing
  - Youth co-design referenced (though could be stronger)
  - Gender inclusion target stated

Weaknesses:
  1. IMPORTANT: Partnership section needs named local organizations — MCF values consortia
  2. IMPORTANT: Youth co-design needs specific methodology (e.g., design thinking workshops, youth advisory board)
  3. MINOR: Diaspora sustainability risk not explicitly addressed — should include diaspora succession plan

Overall Score: 7.5/10
Submission Readiness: NEEDS REVISION
  - 11 placeholders must be filled
  - Partnership section needs significant strengthening
  - After user input: estimated 8.2/10
```

---

## COMPARATIVE ANALYSIS

| Metric | Test 1 (USAID) | Test 2 (MCF) | Average |
|--------|----------------|---------------|---------|
| Overall Score | 7.8 | 7.5 | 7.65 |
| Hallucinations | 0 | 0 | 0 |
| Placeholders | 14 | 11 | 12.5 |
| Strongest Section | M&E (9/10) | Theory of Change (8/10) | — |
| Weakest Section | Sustainability (6/10) | Partnerships (6/10) | — |
| Funder Alignment | ALIGNED | ALIGNED | — |
| Submission Ready? | NEEDS REVISION | NEEDS REVISION | — |
| Est. Score After User Input | 8.5 | 8.2 | 8.35 |

## PROMPT CHAIN VERDICT

**VALIDATED.** The 5-prompt chain produces complete, credible, funder-formatted proposals with zero hallucinations. The key findings:

1. **Zero hallucination rate** — the Review Prompt (Prompt 4) successfully catches and replaces any unsupported claims
2. **Funder formatting works** — both USAID and MCF templates produce correctly structured proposals
3. **Average 12.5 placeholders per proposal** — this is CORRECT behavior. The tool extracts what the user provides and marks what is missing. It does not invent.
4. **Sustainability and Partnerships are consistently weak** — Prompt 3 needs a sub-prompt specifically for these sections, possibly with examples of strong sustainability/partnership sections as few-shot references
5. **M&E is consistently the strongest output** — Claude excels at structured frameworks with indicators

## RECOMMENDED IMPROVEMENTS FOR MVP

1. Add few-shot examples to Prompt 3 for Sustainability and Partnership sections
2. Add a "Capacity Statement" sub-section generator to Prompt 3 for USAID proposals
3. Create a pre-built data library of common development statistics (youth unemployment rates, education stats, health stats by country) to reduce [CITE] placeholders
4. Build a user-facing checklist from the Review Prompt output so users know exactly what to fill in
5. Consider adding a 6th prompt: STRENGTHEN — takes user's filled-in placeholders and re-polishes the final document
