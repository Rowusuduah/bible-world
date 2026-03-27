# BibleWorld Known Unknowns Register
## Open Questions the World Is Actively Working On

**Last Updated:** Cycle 014
**Active Unknowns:** 20
**Resolved Unknowns:** 0

---

### KU-001
**Question:** Which books of the Bible contain the highest density of technology-applicable patterns?
**Why It Matters:** Resource allocation — knowing where to mine first maximises early output
**Assigned To:** Chief Theologian
**Status:** OPEN
**Cycle Added:** 000

---

### KU-002
**Question:** Are there Biblical patterns for which the infrastructure does not yet exist but is within 5 years?
**Why It Matters:** Early identification of emerging infrastructure gaps = first-mover advantage
**Assigned To:** Chief Futurist
**Status:** OPEN
**Cycle Added:** 000

---

### KU-003
**Question:** Which PAT-001 voice-to-software applications are genuinely buildable TODAY with only Claude API?
**Why It Matters:** Determines the Tier 0 build priority for the founder
**Assigned To:** Chief Builder
**Status:** OPEN
**Cycle Added:** 000

---

### KU-004
**Question:** Is there a Biblical pattern for artificial intelligence itself — not just its applications?
**Why It Matters:** If Scripture anticipated intelligence beyond human biology, what does it say about alignment, purpose, and limits?
**Assigned To:** Chief Theologian + Chief Technologist
**Status:** OPEN
**Cycle Added:** 000

---

### KU-005
**Question:** What did the original Hebrew/Greek of Genesis 1:1-3 convey about the mechanism of creation that modern translations may underrepresent?
**Why It Matters:** Deeper textual grounding of PAT-001 (God spoke → creation) strengthens the LLM mapping
**Assigned To:** Chief Theologian
**Status:** OPEN
**Cycle Added:** 000

---

### KU-006
**Question:** Are there historical examples of societies that applied Biblical governance patterns (Jubilee, Sabbath economics, gleaning laws) to their economic systems? What were the outcomes?
**Why It Matters:** Historical validation strengthens pattern scores and makes business model applications more credible
**Assigned To:** Chief Historian
**Status:** OPEN
**Cycle Added:** 000

---

### KU-007
**Question:** How does modern neuroscience's understanding of how the brain processes language compare to the Biblical model of the spoken word having creative power?
**Why It Matters:** Science correlation cycle — if neuroscience validates that language literally shapes neural reality, PAT-001 gets a science anchor
**Assigned To:** Chief Scientist
**Status:** OPEN
**Cycle Added:** 000

---

### KU-008
**Question:** Which of the 8 seed patterns (PAT-001 through PAT-008) has the highest immediate commercial potential for a solo founder with a laptop and Claude?
**Why It Matters:** Determines first build priority in the Innovation Lab
**Assigned To:** Chief Builder + Chief Innovator
**Status:** OPEN
**Cycle Added:** 000

---

### KU-009
**Question:** What is the optimal algorithm for semantic contract validation in llm-contract? Embedding distance? LLM-as-judge (Claude)? Rule-based NLP? Hybrid?
**Why It Matters:** The choice of semantic validation algorithm determines llm-contract's accuracy, latency, and cost profile. Wrong choice = high false positive rate = engineers distrust the tool.
**Assigned To:** Senior Agent (Chief Technologist) + Chief Scientist
**Status:** OPEN
**Cycle Added:** 010

---

### KU-010
**Question:** How should "breaking" vs. "non-breaking" behavioral contract changes be formally defined for LLM function calls?
**Why It Matters:** The SemVer for behavior concept in llm-contract requires a formal specification of what constitutes a breaking change (major version bump) vs. additive change (minor) vs. clarification (patch). Without clear rules, versioning is subjective and the system loses trust.
**Assigned To:** Chief Engineer + Chief Technologist (Senior)
**Status:** OPEN
**Cycle Added:** 010

---

### KU-011
**Question:** Does Acts 2:14-36 (Peter's structured three-part argument) warrant its own pattern — PAT-036: Citation-Anchored Reasoning — for formal output verification?
**Why It Matters:** Peter's speech demonstrates: context declaration → evidence with citations → conclusion with required action. This maps to structured LLM outputs that must cite their reasoning. A dedicated pattern could anchor a build around citation verification / grounded generation.
**Assigned To:** Chief Theologian
**Status:** OPEN
**Cycle Added:** 010

---

### KU-012
**Question:** Are there Romans 1-8 patterns specifically applicable to formal verification of AI systems (the concept of "law" vs. "grace" in software reliability)?
**Why It Matters:** Romans is on the reading list for cycle 010+. The tension between law (formal specification) and grace (graceful degradation) in Romans maps intriguingly to the debate between hard contract enforcement vs. soft contract warnings in AI systems. Needs exploration.
**Assigned To:** Chief Theologian + Chief Scientist
**Status:** OPEN
**Cycle Added:** 010

---

### KU-013
**Question:** What is the optimal handling for large diffs (> 8000 chars) in drift-guard? Should the tool: (a) truncate and warn, (b) chunk and aggregate, (c) summarize at function level?
**Why It Matters:** drift-guard v0.2 must handle large AI-generated PRs gracefully. Current prototype truncates — this may miss violations in truncated sections.
**Assigned To:** Chief Engineer + Chief Builder (Senior)
**Status:** OPEN
**Cycle Added:** 011

---

### KU-014
**Question:** How should 'does-not' clauses be weighted differently from 'does' clauses in drift-guard verifier?
**Why It Matters:** 'does not include X' violations are often more severe than 'includes Y' violations. Asymmetric weighting would improve drift score accuracy.
**Assigned To:** Chief Technologist (Senior)
**Status:** OPEN
**Cycle Added:** 011

---

### KU-015
**Question:** What is the optimal system prompt for drift-guard's LLM judge? Need 50+ labeled PR/diff pairs.
**Why It Matters:** The judge prompt directly affects false positive/negative rate. Without labeled data, calibration is guesswork.
**Assigned To:** Chief Builder (Senior) + Pattern Discovery Director
**Status:** OPEN
**Cycle Added:** 011

---

### KU-016
**Question:** How should Jira/Linear ticket intent integrate with drift-guard v0.2?
**Why It Matters:** PR descriptions often reference ticket IDs. Enriching drift-guard with ticket context would improve intent extraction quality.
**Assigned To:** Chief Engineer
**Status:** OPEN
**Cycle Added:** 011

---

### KU-017
**Question:** What is the optimal LLM judge prompt for spec-drift semantic constraint evaluation?
**Why It Matters:** spec-drift's semantic constraint evaluation quality depends on the judge prompt. Complex constraints ("the response should be empathetic") require careful prompting.
**Assigned To:** Chief Builder (Senior) + Chief Technologist (Senior)
**Status:** OPEN
**Cycle Added:** 012

---

### KU-018
**Question:** What is the zero-shot baseline calibration strategy for spec-drift when no golden dataset exists?
**Why It Matters:** Most teams adopting spec-drift will not have labeled examples. The tool must work well out-of-the-box without calibration data.
**Assigned To:** Chief Scientist + Chief Technologist (Senior)
**Status:** OPEN
**Cycle Added:** 012

---

### KU-019
**Question:** What is the minimum viable YAML test suite for model-parity to be useful? How many test cases per dimension?
**Why It Matters:** The enrollment problem: teams need to write test cases before model-parity helps them. If the minimum useful suite requires 50 test cases, adoption will be slow. If 5 test cases per dimension (35 total) is sufficient for reliable parity scoring, adoption is much easier.
**Assigned To:** Chief Builder (Senior) + Chief Scientist
**Status:** OPEN
**Cycle Added:** 013

---

### KU-020
**Question:** How should model-parity handle non-determinism in LLM outputs? Running each test case once may produce unreliable parity scores if the model has high temperature variance.
**Why It Matters:** A model that sometimes follows instructions and sometimes doesn't will score differently on repeated runs. Should model-parity run each test case N times and average? What is the optimal N vs. cost tradeoff?
**Assigned To:** Chief Scientist + Chief Technologist (Senior)
**Status:** OPEN
**Cycle Added:** 013

---

### KU-021
**Question:** Should model-parity support partial/incremental parity certificates? (e.g., certify only structured_output and instruction_adherence dimensions for a targeted migration decision)
**Why It Matters:** Teams may not need all 7 dimensions for every migration. A partial certificate for only the relevant dimensions would reduce cost and time. But partial certificates create a risk of incomplete authorization.
**Assigned To:** Chief Engineer + Chief Builder (Senior)
**Status:** OPEN
**Cycle Added:** 013

---

### KU-022
**Question:** What is the correct scoring formula when Model B performs BETTER than Model A on some dimensions? Is higher parity score always better, or should model-parity flag improvements as well as regressions?
**Why It Matters:** If Model B has better safety compliance than Model A, that is not a parity failure — it is an improvement. But the current parity formula (1 - abs(score_a - score_b)) scores this as low parity. Need a directed parity formula that distinguishes improvement from regression.
**Assigned To:** Chief Scientist + Chief Engineer
**Status:** OPEN
**Cycle Added:** 013

---

### KU-023
**Question:** What is the minimum effective operator set for llm-mutation v0.1? All 6 operators are specified but shipping all 6 may add complexity. Is a 3-operator MVP (NegateConstraint, DropClause, ScopeExpand) sufficient for useful mutation score?
**Why It Matters:** Scope determines v0.1 build timeline. A 3-operator MVP ships faster and establishes the pattern; 3 more operators can ship in v0.2. But if the 3 core operators don't cover enough mutation space, the mutation score will be artificially high.
**Assigned To:** Chief Builder (Senior) + Chief Engineer
**Status:** OPEN
**Cycle Added:** 014

---

### KU-024
**Question:** How do you determine whether a mutant is truly KILLED when the eval function is non-deterministic? If the same prompt scores 0.87 on one run and 0.91 on another, a mutant scoring 0.85 might be "killed" on one run and "survived" on another.
**Proposed solution (cycle 014):** Run each test case 3 times, use median. Configure delta_threshold at 0.15. Does median-of-3 provide sufficient stability, or is median-of-5 needed for high-variance eval functions? Cost and latency implications?
**Why It Matters:** False kill rate (eval suite incorrectly credited with catching a mutation) damages mutation score reliability — the core value proposition of the tool.
**Assigned To:** Chief Scientist + Chief Builder (Senior)
**Status:** OPEN — proposed solution needs validation
**Cycle Added:** 014

---

### KU-025
**Question:** What is the correct mutation score threshold for a "good enough" eval suite? The cycle 014 spec proposes 80% as the default recommendation. Is 80% too high for early-stage eval suites? Too low for production-critical prompts?
**Why It Matters:** The CI gate `mutate ci --min-score 0.80` must be set to a threshold that is useful without being so aggressive it blocks all CI pipelines or so lenient it provides false confidence. The right threshold may vary by domain (medical AI vs. content moderation vs. code review bot).
**Assigned To:** Chief Innovator + Chief Engineer
**Status:** OPEN
**Cycle Added:** 014

---

### KU-026
**Question:** For llm-mutation v0.2, should mutation operators be LLM-generated (auto-generate mutations by asking an LLM to introduce subtle bugs into a prompt) vs. deterministic (rule-based, as in v0.1)? What are the tradeoffs?
**LLM-generated pros:** Can produce more natural-sounding mutations, can discover mutation types that rule-based operators miss, scales to arbitrary prompt structures.
**LLM-generated cons:** Non-deterministic (two runs of the same prompt produce different mutations), harder to reproduce in CI, LLM may generate "equivalent mutations" that the eval suite correctly ignores. Deterministic operators are reproducible and auditable.
**Why It Matters:** Determines the v0.2 architecture direction. Hybrid approach (deterministic operators for v0.1, optional LLM-generated operators for v0.2) may be the right answer.
**Assigned To:** Chief Technologist (Senior) + Chief Builder (Senior)
**Status:** OPEN
**Cycle Added:** 014

---
