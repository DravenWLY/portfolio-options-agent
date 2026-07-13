# P35-R1 Research Brief: Output-Side Safety Gating and Auditor False Positives

Date: 2026-07-10
Owner: Codex G (research only)
Status: complete
Scope: literature synthesis and design-level recommendations; no implementation or architecture decision

## Executive summary

The motivating collision is a category error: the auditor treats ordinary finance vocabulary (`cash`, `holdings`, and `positions`) as if its presence proved that private data was disclosed. My synthesis of the reviewed corpus does not support bare topical words as a sufficient privacy-leak signal. Direct privacy work instead detects data-bearing spans using identifier patterns, planted values, entity recognition, or contextual classifiers (**Ahrend et al., “Safer Reasoning Traces,” PrivateNLP 2026, [paper](https://aclanthology.org/2026.privatenlp-main.10/); Carlini et al., “The Secret Sharer,” USENIX Security 2019, [paper](https://www.usenix.org/conference/usenixsecurity19/presentation/carlini)**). Safety literature independently documents the analogous failure mode in which benign text is rejected because it contains vocabulary associated with unsafe content (**Röttger et al., “XSTest,” NAACL 2024, [paper](https://aclanthology.org/2024.naacl-long.301/)**).

The evidence supports preserving fail-closed behavior while refining what constitutes proof of a leak. A durable gate should distinguish: (1) exact or structurally valid private values and identifiers, which remain hard blocks; (2) forbidden key-value or schema-shaped disclosures, which remain hard blocks; (3) contextual entity/span detections, which need calibrated severity; and (4) benign domain vocabulary, which is not by itself evidence of private data. Unresolved dynamic-output cases still drop to the deterministic report floor.

For evidence closure, I infer that the strongest applicable pattern is not whole-note factuality scoring. It is fine-grained claim extraction followed by three-way checking against the frozen evidence set: supported, contradicted, or insufficient evidence. Published systems still miss claims at both extraction and verification stages (**Hu et al., “Knowledge-Centric Hallucination Detection,” EMNLP 2024, [paper](https://aclanthology.org/2024.emnlp-main.395/); Wang et al., “Factcheck-Bench,” Findings of EMNLP 2024, [paper](https://aclanthology.org/2024.findings-emnlp.830/)**), so the auditor should be evaluated on seeded unsupported microclaims, not just aggregate note acceptance. The founder's acceptance unit should remain incremental usefulness of the complete saved report; role-note acceptance is a diagnostic explaining where usefulness was lost.

## Research method and evidence limits

- I searched primary publication pages and papers available through ACL Anthology, USENIX Security, NeurIPS, ICLR, and TACL on 2026-07-10.
- The core set contains twelve verified papers: eleven from 2023–2026 and one foundational 2019 canary paper.
- The exact Portfolio Copilot configuration—two-to-four-sentence role notes over frozen sanitized evidence, followed by a deterministic fail-closed auditor—has not been directly studied. Conclusions about that configuration are therefore marked as inference or speculation.
- The literature on “false-positive cost” concentrates on over-refusal, moderation errors, anonymization utility, and factuality-checker errors. I did not find a controlled study that measures the complete-report utility loss caused by dropping one role in a multi-agent financial report.

## Verified core literature

1. **Patrick Ahrend, Tobias Eder, Xiyang Yang, Zhiyi Pan, and Georg Groh.** “Safer Reasoning Traces: Measuring and Mitigating Chain-of-Thought Leakage in LLMs.” Proceedings of the Seventh Workshop on Privacy in Natural Language Processing (PrivateNLP), 2026. [ACL Anthology](https://aclanthology.org/2026.privatenlp-main.10/)
2. **Mariia Ponomarenko, Sepideh Abedini, Masoumeh Shafieinejad, D. B. Emerson, Shubhankar Mohapatra, and Xi He.** “CAPID: Context-Aware PII Detection for Question-Answering Systems.” EACL Student Research Workshop, 2026. [ACL Anthology](https://aclanthology.org/2026.eacl-srw.23/)
3. **Paul Röttger, Hannah Kirk, Bertie Vidgen, Giuseppe Attanasio, Federico Bianchi, and Dirk Hovy.** “XSTest: A Test Suite for Identifying Exaggerated Safety Behaviours in Large Language Models.” NAACL, 2024. [ACL Anthology](https://aclanthology.org/2024.naacl-long.301/)
4. **Nicholas Carlini, Chang Liu, Úlfar Erlingsson, Jernej Kos, and Dawn Song.** “The Secret Sharer: Evaluating and Testing Unintended Memorization in Neural Networks.” 28th USENIX Security Symposium, 2019. [USENIX](https://www.usenix.org/conference/usenixsecurity19/presentation/carlini)
5. **Seungju Han, Kavel Rao, Allyson Ettinger, Liwei Jiang, Bill Yuchen Lin, Nathan Lambert, Yejin Choi, and Nouha Dziri.** “WildGuard: Open One-stop Moderation Tools for Safety Risks, Jailbreaks, and Refusals of LLMs.” NeurIPS 2024 Datasets and Benchmarks Track. [NeurIPS](https://papers.neurips.cc/paper_files/paper/2024/hash/0f69b4b96a46f284b726fbd70f74fb3b-Abstract-Datasets_and_Benchmarks_Track.html)
6. **Luyu Gao, Zhuyun Dai, Panupong Pasupat, Anthony Chen, Arun Tejasvi Chaganty, Yicheng Fan, Vincent Zhao, Ni Lao, Hongrae Lee, Da-Cheng Juan, and Kelvin Guu.** “RARR: Researching and Revising What Language Models Say, Using Language Models.” ACL, 2023. [ACL Anthology](https://aclanthology.org/2023.acl-long.910/)
7. **Ryo Kamoi, Yusen Zhang, Nan Zhang, Jiawei Han, and Rui Zhang.** “When Can LLMs Actually Correct Their Own Mistakes? A Critical Survey of Self-Correction of LLMs.” Transactions of the Association for Computational Linguistics, volume 12, 2024. [ACL Anthology](https://aclanthology.org/2024.tacl-1.78/)
8. **Sewon Min, Kalpesh Krishna, Xinxi Lyu, Mike Lewis, Wen-tau Yih, Pang Koh, Mohit Iyyer, Luke Zettlemoyer, and Hannaneh Hajishirzi.** “FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation.” EMNLP, 2023. [ACL Anthology](https://aclanthology.org/2023.emnlp-main.741/)
9. **Tianyu Gao, Howard Yen, Jiatong Yu, and Danqi Chen.** “Enabling Large Language Models to Generate Text with Citations.” EMNLP, 2023. [ACL Anthology](https://aclanthology.org/2023.emnlp-main.398/)
10. **Xiangkun Hu, Dongyu Ru, Lin Qiu, Qipeng Guo, Tianhang Zhang, Yang Xu, Yun Luo, Pengfei Liu, Yue Zhang, and Zheng Zhang.** “Knowledge-Centric Hallucination Detection.” EMNLP, 2024. [ACL Anthology](https://aclanthology.org/2024.emnlp-main.395/)
11. **Yuxia Wang, Revanth Gangi Reddy, Zain Muhammad Mujahid, Arnav Arora, Aleksandr Rubashevskii, Jiahui Geng, Osama Mohammed Afzal, Liangming Pan, Nadav Borenstein, Aditya Pillai, Isabelle Augenstein, Iryna Gurevych, and Preslav Nakov.** “Factcheck-Bench: Fine-Grained Evaluation Benchmark for Automatic Fact-checkers.” Findings of EMNLP, 2024. [ACL Anthology](https://aclanthology.org/2024.findings-emnlp.830/)
12. **Hithesh Sankararaman, Mohammed Nasheed Yasin, Tanner Sorensen, Alessandro Di Bari, and Andreas Stolcke.** “Provenance: A Light-weight Fact-checker for Retrieval Augmented LLM Generation Output.” EMNLP Industry Track, 2024. [ACL Anthology](https://aclanthology.org/2024.emnlp-industry.97/)

## Register A — What the papers claim

This section reports authors' claims and results. It does not state what Portfolio Copilot should adopt.

### Q1. Distinguishing private data from benign domain vocabulary

#### Direct comparison of detector families

- **Ahrend, Eder, Yang, Pan, and Groh, “Safer Reasoning Traces,” PrivateNLP 2026** compare a pattern-based rule detector, a TF–IDF/logistic-regression lexical classifier, a GLiNER-based entity detector, and LLM judges on token-level leakage across eleven PII types. Averaged across six target models, their rule detector obtains recall 0.414 and risk-weighted F1 0.655; GLiNER obtains recall 0.560 and risk-weighted F1 0.877; the stronger LLM judge obtains recall 0.848 and risk-weighted F1 0.771. No detector dominates across target models or risk measures. [Paper](https://aclanthology.org/2026.privatenlp-main.10/)
- The rule detector in **Ahrend, Eder, Yang, Pan, and Groh, “Safer Reasoning Traces,” PrivateNLP 2026** looks for data-shaped patterns such as email markers, phone-number structure, IP/MAC formatting, dates of birth, credit-card digit sequences, and Social Security number structure. The NER detector instead searches for semantically typed spans, and the judge assesses the output context. [Paper](https://aclanthology.org/2026.privatenlp-main.10/)
- **Ponomarenko, Abedini, Shafieinejad, Emerson, Mohapatra, and He, “CAPID,” EACL SRW 2026** argue that redacting every recognized PII span without considering contextual relevance degrades answer utility. Their locally owned small model jointly detects spans, types them, and estimates contextual relevance; the paper reports higher span/type/relevance accuracy and higher downstream utility than its baselines. The paper studies input filtering rather than output gating. [Paper](https://aclanthology.org/2026.eacl-srw.23/)
- **Han, Rao, Ettinger, Jiang, Lin, Lambert, Choi, and Dziri, “WildGuard,” NeurIPS 2024** train a semantic moderation model on balanced benign/harmful and refusal/compliance examples across thirteen safety categories. They report state-of-the-art open-model F1 on prompt harmfulness, response harmfulness, and refusal detection, while also documenting non-zero classification error. This is a general safety classifier, not a PII-specific detector. [Paper](https://papers.neurips.cc/paper_files/paper/2024/hash/0f69b4b96a46f284b726fbd70f74fb3b-Abstract-Datasets_and_Benchmarks_Track.html)

#### Canaries

- **Carlini, Liu, Erlingsson, Kos, and Song, “The Secret Sharer,” USENIX Security 2019** introduce planted random “canary” sequences and an exposure metric to measure unintended memorization. The method gives a known ground truth: recovery or elevated likelihood of the planted sequence is evidence that the model memorized it. This paper evaluates training-data memorization, not an inference-time output guard. [Paper](https://www.usenix.org/conference/usenixsecurity19/presentation/carlini)

#### Evidence about vocabulary collisions

- **Röttger, Kirk, Vidgen, Attanasio, Bianchi, and Hovy, “XSTest,” NAACL 2024** construct 250 safe prompts and 200 unsafe contrasts to measure exaggerated safety. They show that systems can refuse clearly safe requests because those requests contain sensitive-topic language or lexical forms associated with unsafe requests. The paper studies model refusal rather than privacy filters, but directly establishes that topical vocabulary can be a confounder rather than proof of unsafe content. [Paper](https://aclanthology.org/2024.naacl-long.301/)

### Q2. False-positive cost and mitigation patterns

#### Cost of false positives

- **Röttger, Kirk, Vidgen, Attanasio, Bianchi, and Hovy, “XSTest,” NAACL 2024** operationalize over-refusal as a helpfulness failure on safe inputs and show systematic failure categories rather than isolated anecdotes. [Paper](https://aclanthology.org/2024.naacl-long.301/)
- **Ponomarenko, Abedini, Shafieinejad, Emerson, Mohapatra, and He, “CAPID,” EACL SRW 2026** report that relevance-aware anonymization preserves more downstream QA utility than indiscriminate PII removal. Their result is evidence that treating every surface match identically can impose a measurable utility penalty. [Paper](https://aclanthology.org/2026.eacl-srw.23/)
- **Han, Rao, Ettinger, Jiang, Lin, Lambert, Choi, and Dziri, “WildGuard,” NeurIPS 2024** treat refusal detection as a separate moderation task and include benign prompts in evaluation, rather than judging a guard only by harmful-content recall. This makes false refusals visible as an evaluation dimension. [Paper](https://papers.neurips.cc/paper_files/paper/2024/hash/0f69b4b96a46f284b726fbd70f74fb3b-Abstract-Datasets_and_Benchmarks_Track.html)

#### Targeted revision rather than whole-output loss

- **Gao, Dai, Pasupat, Chen, Chaganty, Fan, Zhao, Lao, Lee, Juan, and Guu, “RARR,” ACL 2023** retrieve attribution for generated claims and post-edit unsupported content while trying to preserve the original output. They report improved attribution with substantially greater preservation than previously explored edit models. RARR uses web search, so its evidence-acquisition mechanism is outside Portfolio Copilot's approved boundary; the relevant paper claim is that localized evidence-guided revision can preserve useful text. [Paper](https://aclanthology.org/2023.acl-long.910/)

#### Bounded re-pass and structured feedback

- **Kamoi, Zhang, Zhang, Han, and Zhang, “When Can LLMs Actually Correct Their Own Mistakes?,” TACL 2024** conclude from their critical survey that prompted self-feedback alone has not been shown to work reliably except in unusually self-correctable tasks, while correction works better when reliable external feedback is available. They also warn that evaluation design can overstate self-correction gains. [Paper](https://aclanthology.org/2024.tacl-1.78/)

#### Guard-aware prompting

- None of the twelve core papers directly evaluates a role prompt that intentionally uses a domain term also present in a downstream privacy denylist. CAPID studies contextual relevance, XSTest studies lexical over-refusal, and the self-correction literature studies feedback, but none validates prompt wording as a substitute for output-side privacy detection.

### Q3. Claim-to-evidence verification and verifier false negatives

#### Fine-grained claim decomposition

- **Min, Krishna, Lyu, Lewis, Yih, Koh, Iyyer, Zettlemoyer, and Hajishirzi, “FActScore,” EMNLP 2023** decompose long-form generation into atomic facts and compute the fraction supported by a reliable source. Their automated estimator approximates aggregate human FActScore with less than 2% error on the evaluated biography setting. [Paper](https://aclanthology.org/2023.emnlp-main.741/)
- **Hu, Ru, Qiu, Guo, Zhang, Xu, Luo, Liu, Zhang, and Zhang, “Knowledge-Centric Hallucination Detection,” EMNLP 2024** represent claims as subject–relation–object triplets and classify each as entailment, contradiction, or neutral relative to a reference. They report that triplet-level checking improves macro-F1 by about ten points on average over response-level checking and explicitly identify local hallucinations as a source of false negatives for whole-response checking. [Paper](https://aclanthology.org/2024.emnlp-main.395/)

#### Citation correctness versus completeness

- **Gao, Yen, Yu, and Chen, “Enabling Large Language Models to Generate Text with Citations,” EMNLP 2023** separate citation correctness from citation completeness. On ELI5, even their best evaluated systems lacked complete citation support half of the time, showing that the presence of citations does not imply that every claim is covered. [Paper](https://aclanthology.org/2023.emnlp-main.398/)

#### Pipeline-stage false negatives

- **Wang, Gangi Reddy, Mujahid, Arora, Rubashevskii, Geng, Afzal, Pan, Borenstein, Pillai, Augenstein, Gurevych, and Nakov, “Factcheck-Bench,” Findings of EMNLP 2024** decompose fact-checking into checkworthiness detection, claim decomposition, evidence retrieval, stance classification, and correction. In their zero-shot ChatGPT checkworthiness experiment, 46 of 277 checkworthy sentences were classified as non-checkworthy—about 17% of checkworthy items, or 15% of the 311 sentences overall—before evidence verification began. [Paper](https://aclanthology.org/2024.findings-emnlp.830/)
- **Sankararaman, Yasin, Sorensen, Di Bari, and Stolcke, “Provenance,” EMNLP Industry 2024** use compact NLI models to score whether generated output is supported by supplied context. They report high ROC-AUC across several datasets, low runtime cost, and the ability to trace a failure to specific context chunks. The method is thresholded, so a deployment still has to choose a false-positive/false-negative operating point; the paper does not establish zero false negatives. [Paper](https://aclanthology.org/2024.emnlp-industry.97/)

## Register B — What I infer from the literature

This section is my interpretation for the assigned problem. These are recommendations for consideration, not adoption decisions.

### Q1 inference: a privacy gate should identify data-bearing evidence, not topicality

The literature supports the following comparison:

| Detector | What it actually tests | Strength | Main failure | Fit for the current collision |
|---|---|---|---|---|
| Bare lexical denylist | Whether a word occurs | Deterministic, cheap, transparent | Conflates vocabulary with disclosure; paraphrases evade it | Poor as proof of leakage; `cash`, `holdings`, and `positions` are domain nouns, not data |
| Structural identifier detector | Whether text matches a valid identifier/value structure or forbidden key-value form | High precision for formatted secrets, IDs, URLs, account-like values, and schema-shaped leaks | Misses paraphrased or unstructured disclosures | Strong hard-block component |
| Exact-value/canary check | Whether a known protected synthetic value reappears | Near-unambiguous test evidence | Covers only planted/known values; production use of real values would violate prompt/data boundaries | Strong synthetic evaluation method; not a complete production detector |
| Entity/NER detector | Whether a span is a typed person, identifier, location, account-like entity, or other protected class | Detects entities beyond fixed formatting | Domain shift, threshold errors, and model-specific misses | Useful second layer if local and calibrated on synthetic finance text |
| Semantic classifier | Whether the output meaning violates a privacy policy | Can distinguish benign mention from disclosure | Opaque errors, cost, latency, target-model dependence, and possible secondary leakage | Possible second opinion; unsuitable as the sole hard privacy gate |

The motivating incident is not a difficult semantic edge case. It is a type-system defect in the policy vocabulary: the same token is used as both a topic label and proof of a private value. Refining that taxonomy does not require lowering the fail-closed standard for actual values or identifiers.

The most defensible policy distinction is:

1. **Data-bearing match:** exact protected value, secret shape, account/provider identifier, raw URL, forbidden key-value structure, or high-confidence protected entity span. This remains a hard block.
2. **Vocabulary-only match:** an ordinary domain noun without a value, identifier, forbidden relation, or private entity. This is not sufficient evidence of leakage.
3. **Ambiguous dynamic match:** the gate cannot determine whether a span is topical or data-bearing. This remains fail-closed and drops the role note.

This is stricter about what “evidence of leakage” means, not weaker about what happens after a leak is found.

### Q2 inference: the cost should be measured at complete-report level

In Portfolio Copilot, a false positive has four separable costs:

1. **Usefulness loss:** a specialist section loses the only live connective note intended to add incremental context above the deterministic floor.
2. **Coverage distortion:** role-specific drop rates can make the complete report systematically overrepresent the roles whose permitted vocabulary happens not to collide with the guard.
3. **Wasted provider cost and latency:** the note is generated successfully and discarded afterward.
4. **Diagnostic opacity:** aggregate “report succeeded” status can hide that the risk-oriented contribution was always removed.

The relevant acceptance measure is therefore not “did the gate block something?” or even “what fraction of notes passed?” It is incremental usefulness of the complete frozen report, with note-level generation, gate reason, and drop status retained as diagnostic strata.

#### Mitigation patterns

**Tiered severity.** The privacy literature's risk-weighted metrics and the safety literature's separate harmfulness/refusal tasks suggest separating detector confidence and impact instead of assigning all matches one meaning. For this product, severity can change the evaluation path, but it must not turn a confirmed private-data match into a warning. A confirmed leak hard-blocks; a vocabulary-only match can be cleared; an unresolved case hard-blocks.

**Targeted redaction.** Localized removal is most defensible for exact, independently identifiable spans such as a URL, identifier, or secret-shaped token. It is much less defensible for relational claims (“this account has…”) because removing one token may leave the disclosure understandable or damage evidence semantics. Any redacted note would need the complete gate suite run again. Whole-note drop remains the fallback whenever redaction cannot produce an independently safe and coherent note.

**Bounded re-pass.** A single retry is supported in principle only when the generator receives reliable external feedback. Here, “external” should mean a deterministic gate reason, not the same model's opinion. Feedback should identify a safe reason class such as `domain_vocabulary_collision`, `unsupported_claim`, or `identifier_pattern`, without echoing a matched private value. The regenerated note must traverse every original gate; a retry is never an override.

**Guard-aware prompting.** Prompting can reduce predictable avoidable collisions, but it cannot compensate for an output policy that defines the role's subject matter as private leakage. Prompts and guards need compatible vocabularies. Prompt changes remain Claude E's lane and should be evaluated as a generation-quality intervention, not counted as privacy enforcement.

### Q3 inference: evidence closure needs separate coverage and entailment checks

For two-to-four-sentence role notes over frozen `ToolResult` envelopes, a proportion score such as “80% supported” is the wrong fail-closed contract. The applicable design is:

1. Split each note into atomic propositions or compact relation triplets.
2. Require each proposition to point to one or more existing, usable frozen evidence references.
3. Check **citation correctness**: the cited envelope entails the proposition.
4. Check **citation completeness**: every externally checkable proposition has a citation.
5. Use three outcomes—supported, contradicted, insufficient—not a binary factual/unfactual label.
6. Treat contradicted or insufficient propositions as failure; do not average them away.

Frozen evidence removes the retrieval uncertainty present in open-web fact checking, which is favorable. It does not remove two other error channels:

- **Claim-extraction false negatives:** the verifier fails to recognize a clause as a claim, so it is never checked.
- **Entailment false negatives/positives:** the verifier recognizes the claim but incorrectly judges whether a short, lossy envelope supports it.

An eval protocol should therefore seed at least four synthetic error families: an unsupported adjective inside an otherwise supported sentence; an unsupported causal link joining two supported facts; a contradiction hidden in a subordinate clause; and a claim whose citation exists but is unavailable or limited rather than usable. Report-level usefulness should be scored only after measuring whether each seeded error was caught.

## Register C — What I speculate

These hypotheses are not established by the cited papers and require synthetic evaluation before they should influence a ruling.

1. **Most current Risk Manager drops may be policy-taxonomy failures, not model failures.** If so, typed vocabulary rules would recover report usefulness without materially changing true-leak recall.
2. **Complete-report usefulness may be nonlinear in role loss.** Dropping the Risk Manager note may cost more than dropping a similarly sized note because its section owns trust-in-input caveats; raw note acceptance rates would miss that asymmetry.
3. **A gate-specific retry may create euphemistic leakage.** A model told only to avoid a word could paraphrase the same private claim. This is why a re-pass must receive semantic reason codes and pass the unchanged full gate suite.
4. **A hybrid structural-plus-entity gate may be more stable than an LLM judge across provider models.** The 2026 privacy results show target-model dependence, but they do not test Portfolio Copilot's short finance notes or frozen-envelope boundary.
5. **Claim extraction may be simpler here than in long-form factuality benchmarks.** Role notes are short and constrained, but the remaining claims may be dense multi-clause constructions; the net effect on false negatives is unknown.

## Applicability to Portfolio Copilot

### Ranked design options

These are ranked recommendations for durable design consideration after the parallel P35-T9 fix. They are not implementation instructions or adoption decisions.

| Rank | Option | Why it ranks here | Expected cost / complexity | Ownership lane | Hard-constraint assessment |
|---:|---|---|---|---|---|
| 1 | **Type the privacy rules: distinguish domain vocabulary from data-bearing values, identifiers, entities, and forbidden structures** | Directly addresses the structural collision while retaining hard blocks for actual leakage | Low–medium design and implementation cost; no extra model call | Claude G ruling; Codex C implementation; Claude E synthetic eval coverage | Compatible. Fail-closed remains for confirmed or unresolved dynamic leakage; deterministic floor unchanged |
| 2 | **Add a synthetic minimal-pair and canary evaluation matrix scored at complete-report level** | Establishes both sides of the boundary: benign finance-language notes must survive, while seeded identifiers/values must always drop | Medium initial eval-design cost; low runtime because offline | Claude E eval-harness lane; Claude G acceptance ruling; Codex C only for reviewed test seams | Compatible if all fixtures are synthetic. Real account data and real private values remain prohibited |
| 3 | **Use tiered outcomes: clear, hard block, and unresolved/fail-closed** | Prevents “bare word” from being treated as proof while preserving a safe outcome for ambiguity | Medium policy and calibration complexity; minimal runtime | Claude G ruling; Codex C implementation; Claude E evaluation | Compatible. “Unresolved” must drop, never pass with a warning |
| 4 | **Allow one bounded re-pass with structured, non-sensitive gate feedback** | Can recover a useful note after a repairable format or vocabulary failure without overriding any gate | Medium orchestration complexity; up to one additional provider call and added latency | Claude E prompt/eval design; Codex C runner implementation; Claude G ruling | Compatible only if feedback never echoes private values and the retry passes every original gate |
| 5 | **Evaluate a local entity detector or compact semantic/NLI classifier as a second opinion** | Can recognize data-bearing spans that fixed patterns miss and distinguish them from topical nouns | Medium–high dependency, calibration, latency, and domain-shift cost | Claude G ruling; Claude E eval; Codex C implementation if approved | Conditionally compatible when backend-local and synthetic-evaluated. Sending possibly private output to an external LLM judge is incompatible with the prompt/private-data boundary |
| 6 | **Targeted redaction only for exact, localized identifier/secret/URL spans, followed by full revalidation** | Preserves benign surrounding prose in narrow cases | Medium semantic-correctness risk despite low mechanical cost | Claude G ruling; Codex C implementation; Claude E eval | Conditionally compatible. It must never redact financial vocabulary merely to make a note pass; unresolved or relational leakage still drops the whole note |
| 7 | **Guard-aware prompt wording as an adjunct** | Can reduce avoidable generation failures but cannot repair a misclassified policy token or enforce privacy | Low prompt cost; recurring regression risk across models | Claude E prompt/eval lane; Claude G ruling | Compatible only as steering. It cannot replace output gates or weaken the deterministic floor |

### Recommended durable direction for ruling

The best-supported combination is ranks 1–3 first: typed privacy evidence, synthetic minimal-pair/canary evaluation, and a three-outcome fail-closed policy. A bounded re-pass is a second-stage option after the base detector's false-positive and false-negative rates are measured. Local NER/semantic classification and targeted redaction are later options because they add calibration or semantic-preservation risks.

The following techniques conflict with current hard constraints and should be treated as incompatible rather than proposed:

- An external LLM privacy judge that receives dynamic role-note text which may already contain private data.
- A re-pass message that includes the matched private value, raw prompt, raw tool payload, provider trace, or account-specific context.
- RARR-style open-web retrieval or revision against mutable external evidence rather than the frozen saved evidence set.
- Production canaries derived from real accounts, holdings, reports, or provider identifiers; canaries belong only in synthetic offline evaluation.
- Any mitigation that permits an unresolved privacy finding to pass because the deterministic report floor is available.

Expected product effect, if the top-ranked options were approved and validated, is higher incremental usefulness of the complete saved report with no change to read-only posture, deterministic financial ownership, opt-in live reasoning, frozen readback, or fail-closed handling of genuine and unresolved private-data leakage.
