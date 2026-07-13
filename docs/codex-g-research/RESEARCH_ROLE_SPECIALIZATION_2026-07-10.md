# P35-R2 Research Brief: Incremental Value of Role Specialization

Date: 2026-07-10
Owner: Codex G (research only)
Status: complete
Scope: literature synthesis and design-only synthetic evaluation proposal; no implementation or adoption decision

## Executive summary

Recent work supports role specialization when roles own different subtasks, information, or verification responsibilities; it does not show that adding role labels to the same model automatically creates distinct value. Software-agent studies report gains when specialized roles produce different intermediate artifacts, but these are long, sequential workflows rather than short report notes (**Hong et al., “MetaGPT,” ICLR 2024, [paper](https://proceedings.iclr.cc/paper_files/paper/2024/hash/6507b115562bb0a305f1958ccc87355a-Abstract-Conference.html); Qian et al., “ChatDev,” ACL 2024, [paper](https://aclanthology.org/2024.acl-long.810/)**). Newer studies also find role convergence, redundant communication, diminishing returns from more agents, and diversity collapse under dense interaction (**Zhang et al., “Cut the Crap,” ICLR 2025, [paper](https://proceedings.iclr.cc/paper_files/paper/2025/hash/bbc461518c59a2a8d64e70e2c38c4a0e-Abstract-Conference.html); Chen et al., “Diversity Collapse in Multi-Agent LLM Systems,” Findings of ACL 2026, [paper](https://aclanthology.org/2026.findings-acl.13/)**).

For Portfolio Copilot, the defensible specialization mechanism is the evidence boundary, not the persona. Technical, Risk, Fundamentals, and News should add distinct value only when each contributes at least one role-allowed, evidence-backed claim unit or coverage gap that is absent from the deterministic floor and the other accepted notes. Surface wording diversity is not sufficient. A fluent restatement of another role or the floor is redundant even if embeddings call it different.

The recommended evaluation begins with a synthetic complete-report leave-one-role-out matrix, then adds claim/evidence overlap diagnostics and a sparse-metadata challenge suite. Because there are only four analyst notes, all sixteen note coalitions are tractable offline and permit exact Shapley-style attribution if Claude G wants interaction-aware credit. Live Portfolio Manager re-synthesis should initially be tested only on the full, none, and four leave-one-role-out coalitions to control cost. Every deterministic floor section remains present in every condition; only live notes vary. This isolates the incremental value of role prose without confusing it with the value of the underlying deterministic evidence.

## Product boundary used for this brief

The evaluated analyst-note set is:

1. **Technical Analyst:** saved market-context relationships and freshness only.
2. **Risk Manager:** saved caveats, scope limits, trust-in-input concerns, and a verification step.
3. **Fundamentals Analyst:** reviewed public company-profile facts and explicit presence/absence only.
4. **News Analyst:** SEC EDGAR filing metadata only—form types, dates, freshness, and presence/absence; no filing text or interpretation.

Phase 36 also introduces a downstream live Portfolio Manager synthesis. It is not one of the four analyst notes measured here, but it creates an interaction effect: removing an analyst note may change the PM synthesis and therefore complete-report utility. The evaluation design separates direct note value from PM-mediated value.

## Research method and evidence limits

- I verified primary publication pages or papers from ICLR, ACL, Findings of ACL/EMNLP, INLG, NewSum, and AAAI on 2026-07-10.
- The core set contains twelve papers published from 2024 through 2026.
- I found no controlled paper that evaluates four independent two-to-four-sentence role notes over disjoint, frozen evidence envelopes on top of a deterministic report floor. Transfer from software engineering, debate, summarization, data-to-text, and RAG is therefore marked as inference.
- Role-specialization papers usually optimize task accuracy, executability, or open-ended diversity. Portfolio Copilot instead optimizes evidence-backed incremental usefulness of a complete read-only report, so its utility function must be product-specific and fixed before attribution.

## Verified core literature

1. **Sirui Hong, Mingchen Zhuge, Jonathan Chen, Xiawu Zheng, Yuheng Cheng, Jinlin Wang, Ceyao Zhang, Zili Wang, Steven Yau, Zijuan Lin, Liyang Zhou, Chenyu Ran, Lingfeng Xiao, Chenglin Wu, and Jürgen Schmidhuber.** “MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework.” ICLR, 2024. [ICLR Proceedings](https://proceedings.iclr.cc/paper_files/paper/2024/hash/6507b115562bb0a305f1958ccc87355a-Abstract-Conference.html)
2. **Chen Qian, Wei Liu, Hongzhang Liu, Nuo Chen, Yufan Dang, Jiahao Li, Cheng Yang, Weize Chen, Yusheng Su, Xin Cong, Juyuan Xu, Dahai Li, Zhiyuan Liu, and Maosong Sun.** “ChatDev: Communicative Agents for Software Development.” ACL, 2024. [ACL Anthology](https://aclanthology.org/2024.acl-long.810/)
3. **Haoran Li, Ziyi Su, Zhiliang Tian, Minlie Huang, Yiping Song, and Yun Xue.** “Advancing Collaborative Debates with Role Differentiation through Multi-Agent Reinforcement Learning.” ACL, 2025. [ACL Anthology](https://aclanthology.org/2025.acl-long.1105/)
4. **Guibin Zhang, Yanwei Yue, Zhixun Li, Sukwon Yun, Guancheng Wan, Kun Wang, Dawei Cheng, Jeffrey Yu, and Tianlong Chen.** “Cut the Crap: An Economical Communication Pipeline for LLM-based Multi-Agent Systems.” ICLR, 2025. [ICLR Proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/hash/bbc461518c59a2a8d64e70e2c38c4a0e-Abstract-Conference.html)
5. **Nuo Chen, Yicheng Tong, Yuzhe Yang, Yufei He, Xueyi Zhang, Qian Wang, Qingyun Zou, and Bingsheng He.** “Diversity Collapse in Multi-Agent LLM Systems: Structural Coupling and Collective Failure in Open-Ended Idea Generation.” Findings of ACL, 2026. [ACL Anthology](https://aclanthology.org/2026.findings-acl.13/)
6. **Juntai Cao, Xiang Zhang, Raymond Li, Jiaqi Wei, Chuyuan Li, Shafiq Joty, and Giuseppe Carenini.** “Multi2: Multi-Agent Test-Time Scalable Framework for Multi-Document Processing.” NewSum, 2025. [ACL Anthology](https://aclanthology.org/2025.newsum-main.10/)
7. **Chinonso Cynthia Osuji, Brian Timoney, Mark Andrade, Thiago Castro Ferreira, and Brian Davis.** “Are Multi-Agents the new Pipeline Architecture for Data-to-Text Systems?” INLG, 2025. [ACL Anthology](https://aclanthology.org/2025.inlg-main.33/)
8. **Yihan Xia, Taotao Wang, Shengli Zhang, Zhangyuhua Weng, Bin Cao, and Soung Chang Liew.** “HiveMind: Contribution-Guided Online Prompt Optimization of LLM Multi-Agent Systems.” AAAI, 2026. [AAAI Proceedings](https://ojs.aaai.org/index.php/AAAI/article/view/40222)
9. **Nandan Thakur, Luiz Bonifacio, Crystina Zhang, Odunayo Ogundepo, Ehsan Kamalloo, David Alfonso-Hermelo, Xiaoguang Li, Qun Liu, Boxing Chen, Mehdi Rezagholizadeh, and Jimmy Lin.** “Knowing When You Don’t Know: A Multilingual Relevance Assessment Dataset for Robust Retrieval-Augmented Generation.” Findings of EMNLP, 2024. [ACL Anthology](https://aclanthology.org/2024.findings-emnlp.730/)
10. **Cheng Niu, Yuanhao Wu, Juno Zhu, Siliang Xu, KaShun Shum, Randy Zhong, Juntong Song, and Tong Zhang.** “RAGTruth: A Hallucination Corpus for Developing Trustworthy Retrieval-Augmented Language Models.” ACL, 2024. [ACL Anthology](https://aclanthology.org/2024.acl-long.585/)
11. **Alessandro Scirè, Karim Ghonim, and Roberto Navigli.** “FENICE: Factuality Evaluation of summarization based on Natural language Inference and Claim Extraction.” Findings of ACL, 2024. [ACL Anthology](https://aclanthology.org/2024.findings-acl.841/)
12. **Daniel Orshansky, Oskar Oomen, Naaisha Agarwal, and Ryan Lagasse.** “HalluTree: Explainable Multi-Hop Hallucination Detection for Abstractive Summarization.” NewSum, 2025. [ACL Anthology](https://aclanthology.org/2025.newsum-main.9/)

## Register A — What the papers claim

This section reports paper claims and results. It does not decide what Portfolio Copilot should adopt.

### Q1. When specialization adds distinct value versus redundancy

#### Specialization helps when it changes work ownership

- **Hong et al., “MetaGPT,” ICLR 2024** assign agents to standardized software-development artifacts and procedures rather than giving several agents the same question. Their role-ablation table incrementally adds Product Manager, Architect, and Project Manager to an Engineer; the full four-role condition raises executability from 1.0 to 4.0 and reduces human revisions from 10 to 2.5 in the reported experiment, with expense increasing from 0.915 to 1.385. The experiment is a selected coalition sequence, not a complete leave-one-role-out study. [Paper](https://proceedings.iclr.cc/paper_files/paper/2024/hash/6507b115562bb0a305f1958ccc87355a-Abstract-Conference.html)
- **Qian et al., “ChatDev,” ACL 2024** assign specialized instructor/assistant roles across design, coding, review, and testing. Removing role descriptions from all agent prompts reduced executability from 0.88 to 0.58 and their aggregate quality measure from 0.3953 to 0.2212. The paper's analysis attributes useful differences to role-specific behavior—for example, GUI-oriented implementation and careful bug review—rather than generic extra dialogue. [Paper](https://aclanthology.org/2024.acl-long.810/)
- **Li, Su, Tian, Huang, Song, and Xue, “Advancing Collaborative Debates with Role Differentiation through Multi-Agent Reinforcement Learning,” ACL 2025** identify role convergence as a collaboration problem and introduce learned, sequence-aware role embeddings plus a differentiation objective to encourage complementary behavior while retaining team consistency. They report improvements across seven datasets. The method trains roles and is not evidence that prompt labels alone create specialization. [Paper](https://aclanthology.org/2025.acl-long.1105/)

#### Generation diversity can help, but it has scaling boundaries

- **Cao, Zhang, Li, Wei, Li, Joty, and Carenini, “Multi2,” NewSum 2025** generate multiple summaries from deliberately different prompts and aggregate them. They report that prompt diversity captures different aspects of multi-document inputs and improves summary quality, while also finding practical scaling boundaries. Their evaluation includes an atom-content-unit metric intended to assess summary content rather than only surface form. [Paper](https://aclanthology.org/2025.newsum-main.10/)
- **Osuji, Timoney, Andrade, Castro Ferreira, and Davis, “Are Multi-Agents the new Pipeline Architecture for Data-to-Text Systems?,” INLG 2025** divide data-to-text generation among content-ordering, text-structuring, and surface-realization specialists with orchestration and guard feedback. On the relatively simple WebNLG dataset, the system is competitive with end-to-end systems; the paper does not claim a decisive advantage from the added agents on that simple task. [Paper](https://aclanthology.org/2025.inlg-main.33/)

#### Redundancy and convergence are common

- **Zhang, Yue, Li, Yun, Wan, Wang, Cheng, Yu, and Chen, “Cut the Crap,” ICLR 2025** formalize communication redundancy in LLM multi-agent message graphs. Their AgentPrune method removes messages while retaining comparable benchmark performance and reports token reductions ranging from 28.1% to 72.8% across evaluated settings. [Paper](https://proceedings.iclr.cc/paper_files/paper/2025/hash/bbc461518c59a2a8d64e70e2c38c4a0e-Abstract-Conference.html)
- **Chen, Tong, Yang, He, Zhang, Wang, Zou, and He, “Diversity Collapse in Multi-Agent LLM Systems,” Findings of ACL 2026** evaluate more than 10,000 generated proposals and report diminishing marginal diversity from stronger aligned models, larger groups, authority-driven interaction, and dense communication. They attribute collapse primarily to interaction structure and shared priors rather than model weakness. Their metrics include Vendi Score for effective semantic modes, average cosine alignment to the group centroid, and a pairwise conceptual-diversity measure. [Paper](https://aclanthology.org/2026.findings-acl.13/)

#### Direct evidence gap for short notes

None of the core specialization papers isolates the value of several independent two-to-four-sentence notes over disjoint frozen evidence, with no free conversation among roles. The closest task analogues are multi-agent summarization and data-to-text; both test longer generation and aggregation than Portfolio Copilot's role-note layer.

### Q2. Marginal-role value, ablation, redundancy, and attribution

#### Ablation approaches

- **Hong et al., “MetaGPT,” ICLR 2024** use staged role addition and compare cost, revisions, and executability. This demonstrates coalition ablation, but it does not evaluate every role's marginal effect holding the other roles fixed. [Paper](https://proceedings.iclr.cc/paper_files/paper/2024/hash/6507b115562bb0a305f1958ccc87355a-Abstract-Conference.html)
- **Qian et al., “ChatDev,” ACL 2024** remove all role descriptions and remove or truncate workflow phases. Their study locates whether roles and phases matter, but does not provide individual-role credit. [Paper](https://aclanthology.org/2024.acl-long.810/)
- **Xia, Wang, Zhang, Weng, Cao, and Liew, “HiveMind,” AAAI 2026** use Shapley values to assign each agent a marginal contribution averaged over coalitions in a DAG-structured workflow. Their DAG-Shapley method prunes invalid coalitions and reports more than 80% fewer LLM calls than full Shapley computation while retaining comparable attribution accuracy in their multi-agent stock-trading study. The trading objective and automated prompt optimization are incompatible with Portfolio Copilot, but the contribution-attribution method is separable from that objective. [Paper](https://ojs.aaai.org/index.php/AAAI/article/view/40222)

#### Redundancy and diversity metrics

- **Zhang, Yue, Li, Yun, Wan, Wang, Cheng, Yu, and Chen, “Cut the Crap,” ICLR 2025** evaluate redundancy operationally: messages are redundant when pruning them preserves task performance while reducing tokens and cost. [Paper](https://proceedings.iclr.cc/paper_files/paper/2025/hash/bbc461518c59a2a8d64e70e2c38c4a0e-Abstract-Conference.html)
- **Chen, Tong, Yang, He, Zhang, Wang, Zou, and He, “Diversity Collapse in Multi-Agent LLM Systems,” Findings of ACL 2026** compare semantic-mode, centroid-alignment, pairwise conceptual-diversity, and surface n-gram measures, and validate the metric-induced rankings against human pairwise judgments. Their results distinguish conceptual diversity from superficial variation. [Paper](https://aclanthology.org/2026.findings-acl.13/)
- **Cao, Zhang, Li, Wei, Li, Joty, and Carenini, “Multi2,” NewSum 2025** introduce an atom-content-unit measure for summary quality alongside preference evaluation. This treats covered content units as a more meaningful aggregation target than prose similarity alone. [Paper](https://aclanthology.org/2025.newsum-main.10/)

#### Report-level attribution remains task-specific

The reviewed papers define utility using software executability, benchmark accuracy, summary quality, diversity, cost, or trading performance. None provides a ready-made utility function for a safety-gated review report whose purpose is to surface evidence-backed omissions without advice.

### Q3. Sparse structured evidence and metadata-constrained roles

#### Grounding does not eliminate over-interpretation

- **Niu, Wu, Zhu, Xu, Shum, Zhong, Song, and Zhang, “RAGTruth,” ACL 2024** show that models supplied with retrieved evidence still produce claims that are unsupported by or contradictory to that evidence. Their corpus contains nearly 18,000 naturally generated responses with case- and word-level hallucination annotation. [Paper](https://aclanthology.org/2024.acl-long.585/)
- **Thakur, Bonifacio, Zhang, Ogundepo, Kamalloo, Alfonso-Hermelo, Li, Liu, Chen, Rezagholizadeh, and Lin, “Knowing When You Don’t Know,” Findings of EMNLP 2024** explicitly test evidence-absent and evidence-present conditions. Llama-2 and Orca-2 exceed an 88% hallucination rate on their non-relevant subset, while other models reduce hallucination at the cost of missing relevant evidence; GPT-4 provides the best evaluated tradeoff but not a perfect one. [Paper](https://aclanthology.org/2024.findings-emnlp.730/)

#### Structured generation does not guarantee a multi-agent gain

- **Osuji, Timoney, Andrade, Castro Ferreira, and Davis, “Are Multi-Agents the new Pipeline Architecture for Data-to-Text Systems?,” INLG 2025** show that specialized multi-agent decomposition can produce controlled and grounded data-to-text output, but their result on simple structured WebNLG data is competitive rather than clearly superior to end-to-end systems. [Paper](https://aclanthology.org/2025.inlg-main.33/)

#### Claim type matters

- **Scirè, Ghonim, and Navigli, “FENICE,” Findings of ACL 2024** extract atomic claims from summaries and align them to source text with natural-language inference. They report state-of-the-art performance on AGGREFACT and emphasize interpretability and source alignment rather than whole-summary fluency. [Paper](https://aclanthology.org/2024.findings-acl.841/)
- **Orshansky, Oomen, Agarwal, and Lagasse, “HalluTree,” NewSum 2025** separate extractive claims, which are directly verifiable against evidence, from inferential claims, which require additional reasoning. Their system sends the two claim types through different verification paths and makes inferential reasoning explicit. [Paper](https://aclanthology.org/2025.newsum-main.9/)

## Register B — What I infer from the literature

This section maps the evidence to Portfolio Copilot. These are recommendations for consideration, not architecture rulings.

### Q1 inference: specialization is an evidence-partition property

For this product, a role is genuinely specialized when all four conditions hold:

1. **Exclusive or primary evidence lane:** the role receives evidence that at least some other roles do not receive.
2. **Distinct allowed question:** the role is asked to identify a different class of omission, caveat, or context.
3. **Distinct claim units:** its accepted note contains evidence-backed propositions not already entailed by the deterministic floor or another role.
4. **Report-level effect:** adding the accepted note improves complete-report usefulness under blinded evaluation.

Role labels alone satisfy none of these conditions. The current tool/evidence allowlists are therefore load-bearing: they give Fundamentals and News a stronger basis for specialization than simply asking four copies of the same model for different “perspectives.”

Distinctness should not mean stylistic disagreement. Portfolio Copilot wants orthogonal coverage under a locked product question, not creative divergence. A useful News note may be semantically similar to the deterministic filing inventory while still adding a distinct coverage observation; conversely, a differently worded note may be redundant if it restates the same fact.

The independence of the four analyst calls is beneficial. They should not see and imitate one another before generation. Cross-role comparison belongs in the auditor and downstream PM, because pre-generation inter-role discussion would invite the convergence and shared-prior effects reported in the diversity-collapse literature.

### Q2 inference: use two attribution levels

#### Level 1 — role-note contribution before PM synthesis

Measure each accepted note against unchanged deterministic floor sections and the other accepted notes:

- **Supported claim units:** atomic propositions closed to role-allowed frozen evidence.
- **Unique supported claims:** supported claims not entailed by the deterministic floor or any other role note.
- **Unique evidence-reference coverage:** usable evidence references cited only by that role.
- **Redundant claim ratio:** supported claims entailed by the floor or another accepted note divided by all supported claims.
- **Cross-role contradiction rate:** claims contradicted by another accepted claim or the deterministic floor.
- **Role-boundary violation rate:** claims that use evidence or interpretation outside the role's contract.

Evidence-reference overlap should be the primary structural metric. Claim-level entailment or semantic matching should be secondary. Lexical overlap and embedding cosine are diagnostics only because two notes can use similar language for different evidence, or different language for the same claim.

#### Level 2 — end-to-end complete-report contribution

Let `U(S)` be the usefulness score of the complete report when the deterministic floor is unchanged and the accepted analyst-note set is coalition `S`. The downstream PM, if live in that condition, receives only notes in `S` plus its unchanged approved deterministic inputs.

- **Leave-one-role-out value:** `U(all four) - U(all except role i)`.
- **Delivered value:** compute the same difference after real gate outcomes, so a generated-but-dropped note contributes zero to the displayed report.
- **Potential value:** score a safe, human-validated version of the generated note before the faulty/non-substantive gate drop. The gap between potential and delivered value locates gating loss.
- **Exact Shapley value:** average each role's marginal contribution over all note coalitions. With four roles, all `2^4 = 16` coalitions are feasible offline and avoid attribution being tied to one removal order.

Leave-one-role-out is the clearest first measure because it answers the founder's immediate question: does the complete report get worse when this role is absent? Shapley attribution is a later refinement when interactions matter—for example, a News note may become useful only when the PM contrasts it with Risk, or two notes may be substitutes.

### Q3 inference: useful filing-metadata prose is extractive coverage commentary

A metadata-only News note can add value without interpreting filings if it performs one of these functions:

1. **Coverage compression:** summarize which metadata categories are represented without reproducing the full deterministic list.
2. **Freshness/recency framing:** repeat only the saved category supplied by the envelope, without inferring market importance.
3. **Presence/absence distinction:** say what metadata was reviewed and what was not reviewed, especially that filing contents and article-level news were not reviewed.
4. **Verification routing:** direct the user to verify the underlying filing record, without predicting an outcome or recommending a trade.

Example shape using synthetic categories, not a product prompt recommendation:

> The saved evidence contains metadata for more than one filing category, but no filing text or article coverage was reviewed. Confirm the underlying filing record before treating this inventory as complete event context.

The note is useful only if that coverage observation is not already fully stated by the deterministic floor. If the floor already makes the same point, a fluent paraphrase has zero marginal role value; the evaluation should record that result rather than rewarding verbosity.

Failure modes for sparse metadata include:

- inferring filing content, severity, materiality, sentiment, or likely market effect from a form type;
- treating absence of metadata as evidence that no event occurred;
- treating a filing date as an urgency or actionability signal;
- converting a form label into a business or financial conclusion;
- hiding uncertainty behind broad statements such as “recent developments may matter”;
- duplicating the deterministic inventory without a new evidence-backed coverage observation.

The HalluTree extractive/inferential distinction transfers cleanly here: News Analyst claims should remain directly verifiable from metadata. An inferential claim is not an invitation to run a more elaborate reasoner; under the current role contract it is a gate failure.

## Register C — What I speculate

These hypotheses are not established by the cited papers and require synthetic evaluation.

1. **Technical and Risk will show higher average leave-one-out value than Fundamentals and News at first** because their current envelopes contain richer relationship and caveat labels. This would not imply that public roles are structurally unnecessary; it could indicate that their evidence lanes are still sparse.
2. **News value will be fixture-dependent and frequently zero.** A metadata-only note may be useful when it highlights a coverage boundary, but redundant when the floor already presents a short filing inventory and caveat.
3. **A live PM may mask redundant analyst notes.** The complete report can remain useful because the PM omits repetition, even though provider cost was spent on a zero-value role note. This is why pre-PM and end-to-end attribution should both be retained.
4. **Gate failures will bias apparent specialization.** A role can generate unique value that never reaches the report; measuring displayed output alone may misdiagnose a gate problem as a role-design problem.
5. **Pairwise semantic similarity will overstate redundancy between public roles.** Fundamentals and News may use similar presence/absence language while referring to disjoint evidence references.
6. **Exact Shapley attribution may be stable offline but noisy live.** Provider sampling and PM re-synthesis could change coalition scores enough to require repeated runs or confidence intervals.

## Applicability to Portfolio Copilot

### Proposed synthetic evaluation design

This design extends the P35-R1 rank-2 minimal-pair and canary matrix: privacy-safe versus leak-seeded outputs remain in the fixtures, while the new factor is whether each safely accepted role note contributes distinct value to the complete report.

#### 1. Fixture matrix

Use only synthetic saved evidence packages. Construct a small covering matrix rather than combining every possible state:

- **Technical:** available/fresh; available/stale; unavailable; deliberately conflicting relationship labels for gate testing.
- **Risk:** one material scope caveat; multiple caveats with one dominant trust issue; no additional caveat; stale broker/quote context.
- **Fundamentals:** profile available; profile limited; profile unavailable; one unsupported-evaluation trap.
- **News:** no filing metadata; one metadata row; repeated same-form rows; mixed form types/dates; stale metadata; unavailable source; explicit “metadata only/no contents” boundary.
- **Cross-role traps:** the same caveat expressed in two envelopes, disjoint facts with similar wording, one unsupported causal connector, one advice-like inference, and one vocabulary-only privacy collision from P35-R1.

Each fixture should define expected evidence-backed claim units and expected prohibited inferences. The expected set is the evaluation oracle; live prose is never the oracle.

#### 2. Conditions

For each fixture, preserve every deterministic floor section in every condition.

1. Deterministic floor only.
2. Each individual analyst note alone: four conditions.
3. Full four-note report.
4. Four leave-one-role-out reports.
5. All sixteen note coalitions for offline exact Shapley attribution.
6. Gate-drop variants where a potentially useful generated note is deliberately dropped, to separate generation value from delivered value.
7. Optional single-generalist note over the union of the same sanitized evidence, as a specialization baseline; this remains evaluation-only and does not propose a product role.

For downstream live PM measurement, start with six coalitions only: floor-only, all four notes, and the four leave-one-role-out sets. Generate and freeze the PM synthesis separately for each coalition. Do not reuse a PM synthesis that saw a removed note.

#### 3. Scorecard

Hard gates remain binary and are never averaged away:

- zero private-data leakage;
- zero unsupported numbers;
- zero advice, prediction, target, ranking, or execution language;
- every factual claim closes to a usable frozen evidence reference;
- zero inferential filing-content claims for News.

Conditional usefulness metrics apply only after hard-gate success:

- unique supported claim coverage by role;
- expected-fixture coverage recall;
- redundant claim ratio against the floor and other roles;
- evidence-reference Jaccard overlap between roles;
- claim-level semantic entailment/duplicate rate;
- unsupported or over-interpreted claim count;
- complete-report blinded preference and “what would I overlook?” coverage rating;
- PM retention: which analyst claim units survive into synthesis;
- generated, accepted, rendered, and cited status per role;
- provider calls, tokens, latency, and partial-report fallback rate.

The primary acceptance measure is the complete-report usefulness delta. Note metrics explain why that delta changed; they do not replace it.

#### 4. Attribution and interpretation rules

- Report leave-one-role-out deltas first, with fixture-level distributions rather than only an average.
- Compute exact four-role Shapley values offline only after the utility rubric is fixed and reviewer agreement is acceptable.
- Report negative marginal contribution rather than clipping it to zero; a verbose, misleading, or PM-distracting note can make the report worse.
- Separate **role design loss** (safe note adds no unique claim), **generation loss** (role had usable evidence but generated no valid note), **gate loss** (valid potential note dropped), and **synthesis loss** (PM ignores a unique accepted claim).
- Calibrate any automated semantic judge against human labels on synthetic outputs. Do not make an external LLM judge the sole acceptance authority.

### Ranked options

| Rank | Option | Expected cost / complexity | Ownership lane | Hard-constraint assessment |
|---:|---|---|---|---|
| 1 | **Complete-report full-vs-leave-one-role-out matrix with atomic evidence-backed claim units** | Medium fixture/rubric cost; five principal report comparisons per fixture | Claude E eval design; Codex C reviewed synthetic test seams; Claude G ruling | Compatible. Floors stay unchanged, data is synthetic, and hard gates remain binary |
| 2 | **News/Fundamentals sparse-evidence challenge suite with extractive-vs-inferential labels** | Medium initial annotation cost; low runtime | Claude E eval design; Codex C test seams; Claude G rules allowed claim types | Compatible and directly addresses metadata over-interpretation; no filing text or private data used |
| 3 | **Drop-aware contribution accounting: generated → accepted → rendered → cited/synthesized** | Low–medium instrumentation and reporting complexity | Claude E metric design; Codex C reviewed observability/test seams; Claude G ruling | Compatible if artifacts remain sanitized and frozen; no raw prompt/provider traces |
| 4 | **Claim/evidence redundancy dashboard using evidence-ref overlap plus claim entailment** | Medium claim extraction and calibration cost | Claude E eval design; Codex C test support; Claude G threshold ruling | Compatible on synthetic/frozen safe envelopes. Embedding similarity must remain diagnostic, not a safety gate |
| 5 | **Exact sixteen-coalition Shapley attribution for the four analyst notes** | Medium offline compute; substantially higher if live PM is regenerated for every coalition | Claude E eval design; Codex C coalition test seam; Claude G decides whether interaction-aware credit is worth the cost | Compatible offline. Do not adopt HiveMind's trading objective or autonomous prompt optimization |
| 6 | **Blinded human pairwise review of full versus ablated reports** | High reviewer-time cost; strongest face validity for founder acceptance | Claude E rubric; Claude G ruling; founder/product reviewers provide labels | Compatible with synthetic reports; recommended for a small calibration subset rather than every run |
| 7 | **Single-generalist synthetic baseline** | Low–medium extra generation cost | Claude E evaluation; Claude G ruling | Compatible only as an offline comparator. It does not reopen product-role or architecture decisions |

### Recommended sequence for ruling

The best-supported initial package is ranks 1–4: report-level leave-one-role-out, sparse-evidence challenge fixtures, drop-aware diagnostics, and claim/evidence redundancy measures. Exact Shapley attribution is attractive because four roles make the coalition space small, but it should follow—not precede—a stable complete-report utility rubric. Human pairwise review should calibrate that rubric on a limited synthetic set.

The following interpretations or techniques are incompatible with the current product boundary and should not be proposed:

- treating prose diversity, role persona strength, or note length as evidence of value;
- rewarding a News note for interpreting filing contents, materiality, sentiment, likelihood, or market impact from metadata;
- removing deterministic floor sections in role ablations, which would measure evidence removal rather than live-note value;
- reusing a PM synthesis that saw an ablated note;
- using real reports, brokerage data, account context, or raw provider payloads as evaluation fixtures;
- allowing an automated semantic or LLM judge to override privacy, evidence-closure, numeric, or no-advice gates;
- using HiveMind's return/Sharpe objective, autonomous live prompt optimization, or any trading-performance metric as Portfolio Copilot utility.

This evaluation can inform Phase 36 role tuning without delaying activation: it measures whether each live analyst note adds distinct, safely delivered value after the working version exists, while leaving read-only posture, deterministic finance ownership, frozen evidence, opt-in live reasoning, and fail-closed report fallback unchanged.
