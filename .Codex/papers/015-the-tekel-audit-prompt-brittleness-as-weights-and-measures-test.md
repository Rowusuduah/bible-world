# The TEKEL Audit: Prompt Brittleness as a Weights-and-Measures Test
## BibleWorld Research Paper 015

**Author:** Chief Theologian (Senior Agent) + Chief Technologist (Senior Agent)
**Pattern Source:** PAT-048 (Daniel 5:25-28), PAT-049 (Matthew 7:24-27), PAT-050 (Proverbs 17:3)
**Build Application:** prompt-shield (BUILD-014, Pivot_Score 8.75)
**Pattern Scores:** PAT-048 (9.1, Level 3), PAT-049 (9.0, Level 3), PAT-050 (8.4, Level 2)
**Date:** 2026-03-27
**Status:** RESEARCH PAPER — BibleWorld Cycle 015

---

## Abstract

This paper presents three biblical patterns that together define the theoretical foundation for LLM prompt brittleness testing. The first pattern, drawn from Daniel 5:25-28, reveals the "TEKEL structure" — a calibrated weights-and-measures audit that exposes inadequacy in interpretation systems by applying the same content through multiple pathways and measuring whether consistent, correct outputs emerge. The second pattern, from Matthew 7:24-27, provides the stress-test architecture: three independent load vectors (rain/lexical, streams/syntactic, wind/semantic) applied simultaneously to reveal foundation quality that fair-weather inspection cannot detect. The third pattern, from Proverbs 17:3, establishes the certification output: the crucible produces a certificate of quality (the BrittleCertificate), not merely a pass/fail signal. These three patterns converge on a specific technical design: prompt-shield, an open-source Python library that measures prompt output consistency across semantically-equivalent paraphrase variants and produces a brittleness score (0.0–1.0) with a CI gate and deployable certificate. No production open-source library currently provides this capability. The research gap is confirmed by independent web searches finding only academic tools (PromptBench, PromptRobust) with no pip-installable production equivalent.

---

## 1. The Problem: Prompt Brittleness in Production

Large Language Model prompts are brittle. An engineer crafts a prompt, evaluates it on 50–200 representative test cases, observes strong performance, and ships to production. Within days, production failures accumulate from users who phrase their requests in natural language variants that differ from the evaluation inputs. The prompt that scored 95% on the evaluation set scores 60% on real user input variation.

This failure mode is confirmed by multiple independent sources in 2025-2026:
- The METR study (2025) found experienced developers using AI tools took 19% longer than without them — the primary cause cited is debugging failures from AI-generated outputs that are "almost right but not quite"
- The DORA 2025 report found only 24% of developers fully trust AI-generated output
- Multiple peer-reviewed papers (ICLR 2025, EMNLP 2024, TMLR 2025) document "surface-form brittleness" — LLMs performing significantly worse on semantically-equivalent paraphrases of evaluation inputs

The root cause is architectural: **evaluation suites test whether specific inputs produce correct outputs; they do not test whether outputs are consistent across semantically-equivalent variants of those inputs.** This gap between evaluation coverage and production input distribution is where brittleness lives.

Existing tools do not address this:
- DeepEval (50+ metrics): accuracy, relevance, hallucination detection — none measure paraphrase consistency
- Promptfoo: regression testing whether specific inputs still pass — not consistency across variants
- PromptBench/PromptRobust: academic research tools focused on adversarial robustness — not production-integrated CI gates

---

## 2. Pattern 1: The TEKEL Structure (Daniel 5:25-28)

### 2.1 Textual Grounding

Daniel 5 records King Belshazzar's feast and the appearance of mysterious writing on the wall. The text is specific: four words are written — MENE MENE TEKEL PARSIN — in Aramaic. The king's court of interpreters cannot read them. Daniel, called as an independent evaluator, reveals the meaning: each word is a unit from the Babylonian weights-and-measures system, deployed as a four-part audit.

The lexical analysis is significant:
- MENE (מְנֵא, mina) — a unit of weight; "numbered/assessed"
- TEKEL (תְּקֵל, shekel) — a smaller unit of weight; "weighed"
- PERES/PARSIN (פְּרֵס, half-shekel) — the smallest unit; "divided/split"

Daniel's interpretation: "TEKEL — you have been weighed on the scales and found wanting." This is not metaphor — the weighing is the assessment instrument. The scales are the test. "Found wanting" is the output: the measurement revealed that the tested subject does not meet the standard.

Three structural features of the TEKEL audit are technically significant:

**1. The same content through multiple interpreters reveals inconsistency.** The court could not interpret the wall's writing consistently. Different interpretive systems (the king's wisemen) produced no output at all — the failure mode is not wrong output but inability to produce stable, consistent interpretation. The brittleness test reveals whether the interpretation system (the LLM prompt) produces consistent output when the same semantic content is expressed differently.

**2. The evaluator is independent of the system being evaluated.** Daniel explicitly refuses payment before evaluating (Daniel 5:17). The evaluation is not performed by the king's own systems — it is performed by an independent evaluator with different training and different incentives. This maps to the design principle that the brittleness scoring mechanism must not use the LLM being tested as the judge of its own outputs.

**3. The measurement is calibrated, not binary.** The TEKEL score is a measurement on a scale — not merely PASS/FAIL. "Found wanting" indicates a deficit on a continuum. The BrittlenessScore (0.0–1.0) implements this: 0.0 is robust, 1.0 is maximally brittle, with thresholds for ROBUST/CONDITIONAL/BRITTLE verdicts.

### 2.2 Technical Mapping

The TEKEL structure maps to the BrittlenessEngine + BrittlenessScorer pipeline:
1. MENE MENE (numbered/assessed, appearing twice = thorough enumeration) → N variants generated and validated per test input
2. TEKEL (weighed) → BrittlenessScore computed as weighted proportion of deviant outputs
3. PERES (divided/split) → FaultLineAnalyzer identifies which variant types cause fracture along which semantic fault lines
4. Verdict rendered → BrittleCertificate: ROBUST/CONDITIONAL/BRITTLE

The four-word structure is not coincidentally isomorphic — Daniel 5's TEKEL audit is structurally a quality assessment protocol with enumeration, measurement, fracture analysis, and verdict. The BrittlenessEngine implements exactly this structure.

### 2.3 Separation of Technical and Spiritual Content

**This paper applies the TEKEL structure only to its mechanical, structural dimensions.** The spiritual content of Daniel 5 — divine sovereignty over Babylonian empire, God's judgment of pride and desecration, the historical fulfillment of prophetic warning, the holiness of the temple vessels — is not claimed for software systems. LLM prompts do not have moral standing. Brittleness testing is not divine judgment. The TEKEL mapping applies only to the calibrated measurement structure of Daniel 5:25-28, not to its theological content.

---

## 3. Pattern 2: The Two Builders (Matthew 7:24-27)

### 3.1 Textual Grounding

Matthew 7:24-27 concludes the Sermon on the Mount with a structural comparison. Two builders, two houses, one storm. The storm applies three independent force vectors — rain (volume, vertical), streams (lateral pressure, rising), wind (directional, variable) — to both structures simultaneously.

The key structural observations:

**1. The two houses are visually indistinguishable before the storm.** The parable does not say the foolish builder's house looked inferior during construction. Only the storm reveals the foundation difference. This is the critical insight for prompt testing: a brittle prompt and a robust prompt are functionally indistinguishable on standard evaluation inputs (fair weather). The stress test (storm) is the only mechanism that reveals which foundation was built.

**2. The storm consists of three independent stress vectors.** Luke 6:47-49 confirms the depth dimension: the wise builder "dug down deep." The three vectors of the storm test different dimensions of foundation integrity. This maps to the three paraphrase levels:
   - Rain (volume, falling from above — incremental, word-level) → lexical substitution (synonym substitution, vocabulary variation)
   - Streams (lateral pressure, rising around the foundation — structural, horizontal) → syntactic transformation (sentence structure change, clause reordering, active/passive, contraction)
   - Wind (directional, variable, full-force) → semantic rephrasing (full meaning-preserving reformulation)

**3. The collapse is catastrophic and sudden.** "It fell with a great crash." The failure mode of a sand-foundation house under storm conditions is not graceful degradation — it is sudden structural failure. This maps to the production failure mode: brittle prompts do not degrade gradually in production; they produce catastrophic failures on specific user phrasings that expose the sand foundation.

### 3.2 Technical Mapping

The three-level paraphrase stress test IS the storm from Matthew 7. The BrittlenessEngine implements each stress vector as a distinct paraphrase generation strategy:

| Storm Vector | Matthew 7 | BrittlenessEngine Level | Implementation |
|-------------|-----------|------------------------|----------------|
| Rain | Volume, vertical, word-level | `lexical` | WordNet synonym substitution, PPDB lexical paraphrase |
| Streams | Lateral, structural, rising | `syntactic` | Clause reordering, active/passive, contraction expansion |
| Wind | Directional, full-force, semantic | `semantic` | T5-paraphrase model, full meaning-preserving reformulation |

A prompt that survives all three storm vectors — lexical variation, syntactic restructuring, and semantic rephrasing — is built on rock. It relies on genuine semantic understanding, not surface-form pattern matching. A prompt that fails one or more vectors has been built on sand.

The engineer who ran standard eval tests and shipped a brittle prompt is the foolish builder who did not know his foundation was sand until the storm arrived. prompt-shield applies the storm pre-deployment, before users become the storm.

### 3.3 Separation of Technical and Spiritual Content

**The spiritual content of Matthew 7:24-27 — obedience to Christ's teaching as the foundation of a righteous life, the authority of Jesus's words (Matthew 7:28-29), the eschatological judgment of those who do not practice what they hear — is not claimed for software systems.** The parable describes a life-and-death spiritual matter: building one's life on hearing and practicing Christ's words. prompt-shield tests the semantic robustness of LLM prompts. These are categorically different domains. The mapping applies only to the structural/engineering principle that fair-weather testing is insufficient and that stress reveals hidden foundation quality.

---

## 4. Pattern 3: The Refining Crucible (Proverbs 17:3)

### 4.1 Textual Grounding

Proverbs 17:3: "The crucible for silver and the furnace for gold, but the Lord tests the heart." Proverbs 27:21 provides the parallel: "The crucible for silver and the furnace for gold, and people are tested by their praise."

The crucible (כּוּר, kur) is a controlled-heat vessel with a specific purpose: to certify the purity of valuable material by separating impurities through thermal stress. The crucial insight is what the crucible produces: not just tested material, but **certifiable material**. Silver that has passed the crucible can be claimed as pure. This is knowledge that cannot be obtained by visual inspection alone.

The Proverbs 17:3 pattern establishes the **certification output** of the testing process. The testing is not punitive — it is certifying. Material that passes the crucible is now trustworthy in a way that untested material is not.

Supporting texts:
- Zechariah 13:9: "I will refine them like silver and test them like gold" — the testing produces a relationship ("they are my people") based on verified quality
- Malachi 3:3: "He will sit as a refiner and purifier of silver" — the refiner must be present, calibrated, and authoritative
- 1 Peter 1:7: "the proven genuineness of your faith — of greater worth than gold, which perishes even though refined by fire" — the proven genuineness is the output, more valuable than gold

### 4.2 Technical Mapping

The BrittleCertificate is the crucible output. The production pipeline:

| Crucible Stage | Technical Equivalent |
|--------------|---------------------|
| Apply heat | BrittlenessEngine runs N paraphrase variants |
| Dross separates | Deviant outputs identified by BrittlenessScorer |
| Pure material remains | Robust outputs form the stable semantic core |
| Certificate of purity | BrittleCertificate: verdict + score + confidence interval |

The certification function of the crucible is the key insight: the BrittleCertificate is not just a score — it is a **deployable claim**. A team that ships with a BrittleCertificate bearing the ROBUST verdict can assert: "This prompt has been stress-tested across N paraphrase variants at three stress levels and maintained output consistency within the certified tolerance." This is a knowledge claim that standard evaluation cannot support.

### 4.3 Separation of Technical and Spiritual Content

**"The Lord tests the heart" is a claim about divine omniscience and God's knowledge of human character — not a claim about software testing.** LLM prompts do not have hearts. The BrittleCertificate does not certify moral character. The mapping applies only to the structural function of the crucible as a controlled-stress certification mechanism. The theological content (God's knowledge of human hearts, the spiritual significance of testing, the transformative purpose of divine testing in the life of faith) is not claimed for software systems.

---

## 5. Synthesis: The Three-Pattern Architecture

The three biblical patterns together define a complete architecture for prompt brittleness testing:

| Component | Pattern | Biblical Source | Implementation |
|-----------|---------|----------------|----------------|
| Audit structure | TEKEL Audit | Daniel 5:25-28 | BrittlenessEngine — enumeration, measurement, fracture analysis, verdict |
| Stress test design | Two Builders | Matthew 7:24-27 | Three-level paraphrase: lexical, syntactic, semantic |
| Certification output | Refining Crucible | Proverbs 17:3 | BrittleCertificate — deployable proof of robustness |

Each pattern contributes a distinct design principle that cannot be derived from the others:
- Daniel 5 provides the **measurement structure** (four-phase audit, calibrated score, independent evaluator)
- Matthew 7 provides the **stress test architecture** (three independent vectors, simultaneous application, fair-weather inadequacy of standard testing)
- Proverbs 17:3 provides the **certification purpose** (the output is a deployable claim, not just a number)

---

## 6. The Competitive Gap

This paper documents the absence of a production-ready, pip-installable open-source library that implements prompt brittleness scoring with a CI gate and deployable certificate.

**Academic tools (not production-ready):**
- PromptBench (2023, EACL): research benchmark for adversarial robustness — not a pip-installable production library
- PromptSensitivity Index (EMNLP 2024): academic paper, no library
- MOF (Mixture of Formats): GitHub research script, not a production library
- PEARL (ICLR 2025): academic paper on permutation-resilient LLMs, no production library

**Production tools (different problem scope):**
- DeepEval: accuracy/relevance/hallucination on specific inputs — not paraphrase consistency
- Promptfoo: regression testing specific inputs — not variant consistency
- spec-drift (BibleWorld BUILD-011): semantic specification drift in production — not brittleness scoring

**Conclusion:** The brittleness scoring gap is confirmed GREEN. prompt-shield (BUILD-014) is the first production open-source library targeting this specific problem.

---

## 7. Conclusion

Daniel 5's TEKEL audit, Matthew 7's Two Builders stress test, and Proverbs 17:3's Refining Crucible each describe — from different angles, in different genres, across the Old and New Testaments — the same fundamental engineering principle: **quality that is asserted without testing is not knowledge; quality that is demonstrated under stress is certified, deployable, and trustworthy.**

The application to LLM prompt brittleness is not a metaphor — it is a structural mapping. The TEKEL score measures the proportion of interpretation failures under variant stress. The three storm vectors (lexical, syntactic, semantic) test foundation quality simultaneously. The BrittleCertificate is the crucible output.

prompt-shield implements these three patterns as a practical open-source tool. The biblical blueprint is 2,500+ years old. The engineering gap it reveals — the absence of a production CI-integrated prompt brittleness scoring library — exists today, in 2026, and can be closed in four weeks.

---

*This paper is an output of BibleWorld Cycle 015, 2026-03-27.*
*Patterns: PAT-048 (Daniel 5:25-28, Level 3, 9.1), PAT-049 (Matthew 7:24-27, Level 3, 9.0), PAT-050 (Proverbs 17:3, Level 2, 8.4)*
*Build: prompt-shield (BUILD-014, Pivot_Score 8.75)*
