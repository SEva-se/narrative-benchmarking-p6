# Presentation script

21 slides. All slide text and speaker notes are in English. Research proposal and implementation status, not completed empirical findings.

## 1. Narrative benchmarking

API models, source evidence and resource trade-offs


**Speaker notes:** We propose a P6 project comparing models through APIs. The central task is to recognize narrative categories in news paragraphs and provide inspectable supporting evidence. The implementation and protocol are prepared. Real empirical findings will follow once permitted data and API access are connected. Present this material as a research proposal and demonstration of software readiness.

**Sources:** Course kickoff, slides 7 and 9. Project proposal, 1 November 2026.

## 2. Task boundaries

| Task | Model output |
| --- | --- |
| Classification | Categories from a fixed codebook |
| Evidence extraction | Source quotes supporting a category |
| Narrative discovery | Candidate categories beyond a codebook |

**Speaker notes:** We explicitly separate three tasks. The minimum project covers classification and source-evidence extraction. Discovering new categories requires separate human validation and different metrics. Finding a narrative does not establish that the news is false. A bounded task allows models to be compared on the same inputs.

**Sources:** https://aclanthology.org/2025.acl-long.1513/ ; https://arxiv.org/abs/2609.11128

## 3. An annotation example

- Fictional target: “The column argues that the carbon tax raises bills without reducing emissions.”
- Category: criticism of climate policies
- Evidence: an exact source quotation plus a brief explanation
- A paragraph may express several categories or none

**Speaker notes:** This is a fictional teaching example, not a real article or model result. Explain the distinction between the topic of climate policy and an interpretation portraying that policy as costly and ineffective. Multiple independent interpretations require multiple categories. A topical keyword alone does not automatically justify a label.

**Sources:** Author-created teaching example, data/demo/records.jsonl.

## 4. Literature and project decisions

| Literature | Decision for this project |
| --- | --- |
| PolyNarrative | Paragraph labels and an explicit codebook |
| Repetition to Recognition | Coverage and rare-category diagnostics |
| NarraBench | Narrow claims about measured ability |
| F3 and DiNaM | Transfer checks and stage-level inspection |
| HELM | Quality and resources reported together |

**Speaker notes:** This is a synthesis rather than a claim to replicate all the listed studies. PolyNarrative supplies a useful operationalization. Other sources clarify the boundaries of metrics and transfer. Our study evaluates specific API configurations under declared conditions. Full citations and section-level reading guidance are in the literature review.

**Sources:** https://aclanthology.org/2025.acl-long.1513/ ; https://arxiv.org/abs/2609.11128 ; https://aclanthology.org/2026.eacl-long.176/ ; https://aclanthology.org/2023.emnlp-main.883/ ; https://aclanthology.org/2025.emnlp-main.1537/ ; https://arxiv.org/abs/2211.09110

## 5. A focused research contribution

- A controlled comparison of accessible API deployments
- Classification quality and human-rated evidence support
- Measured token usage, estimated price and observed latency
- Independent validation on newly collected texts

**Speaker notes:** The contribution is a specific reproducible experiment. We do not promise a new architecture or claim that the field is unexplored. Useful findings may include limitations, unstable rankings or insufficient benefit from a more expensive model. Such conclusions must come from actual observations.

**Sources:** Proposed study design. Empirical findings pending.

## 6. Research questions

- RQ1: How do fixed API configurations compare on narrative classification?
- RQ2: What changes when we add fixed training examples?
- RQ3: How well do frozen systems transfer to new texts?

**Speaker notes:** All three questions are measurable. For the second question, change only the inclusion of fixed training examples, keeping the codebook and output contract constant. For the third, do not tune on the new evaluation sample. The direction of the effect is unknown: few-shot examples can help or harm performance.

**Sources:** Project research protocol v0.1.

## 7. Experiment matrix

| System | Zero-shot | Few-shot |
| --- | --- | --- |
| API model A | Fixed codebook | Same codebook + train examples |
| API model B | Same target records | Same example IDs |
| API model C | Same output contract | Same output contract |
| CPU baseline | TF-IDF centroids | Threshold selected on dev |

**Speaker notes:** Three models and two prompting variants produce six API configurations. The baseline is separate: its vocabulary and centroids come from train, and its threshold from dev. Exact models still depend on account access and supported interfaces. This table is an experiment plan rather than a completed comparison.

**Sources:** Proposed experiment matrix. No real API runs have been performed.

## 8. Dataset and split policy

- Initial scope: English climate news and coarse categories
- A verified PolyNarrative release, subject to approved access
- Article-disjoint train, development and test data
- A separate new corpus with independent annotation

**Speaker notes:** The package contains fictional demonstration records and a draft codebook only. Obtain and verify the actual release, including Other handling and split mapping. The validator detects article overlap and exact normalized duplicates, while semantic copies require additional inspection. Humans and models receive the same declared paragraph context.

**Sources:** https://nikon95.github.io/narrative-detection/ ; https://aclanthology.org/2025.acl-long.1513/

## 9. Execution pipeline

| Stage | Stored evidence |
| --- | --- |
| Validate data and codebook | Versions, hashes, split checks |
| Build frozen requests | Prompt version and request hashes |
| Run model or CPU baseline | Raw outputs, attempts and usage |
| Validate and evaluate | Coverage, F1 and errors |
| Review source evidence | Independent human judgments |

**Speaker notes:** Each stage leaves an auditable record. Evaluation gold labels do not enter the target request. Invalid outputs are retained rather than removed. Automatic evidence checking is limited to schema and exact source membership. The final review stage requires people and follows a predefined rubric.

**Sources:** Implementation: narrative_bench/data.py, prompts.py, engine.py, evaluate.py, annotations.py.

## 10. Classification evaluation

- Primary: Macro-F1 over the fixed category inventory
- Also: Micro-F1, per-label support and precision/recall
- Valid-output coverage and end-to-end exact match
- Exploratory uncertainty intervals resample whole articles

**Speaker notes:** Macro-F1 and Micro-F1 describe different aspects of performance. Disclose the treatment of absent categories and empty sets. Invalid and missing outputs remain in the evaluation denominator. They always count as failures for end-to-end exact match. Article-level bootstrap respects paragraph dependence, but separate intervals do not replace a paired significance test.

**Sources:** Implementation: narrative_bench/metrics.py and evaluate.py. Protocol sections 7 and 11.

## 11. Evidence evaluation

| Check | Method |
| --- | --- |
| Output schema and category IDs | Automatic validation |
| Exact quotation in target text | Automatic substring check |
| Quote supports the category | Blinded human review |
| Ambiguous interpretation | Retain unclear and explain disagreements |

**Speaker notes:** A quotation can occur verbatim without supporting the predicted category. For example, the text may reject a position or quote another speaker. In the human audit, hide model and prompt variant, use a shared preselected record set, and retain unclear judgments. Evidence does not establish the model's internal decision mechanism.

**Sources:** Project annotation guide and evidence-review rubric.

## 12. Resource measurements

- Observed input and output usage with a dated pricing snapshot
- Median and p95 record latency, including retry time
- Unknown costs remain unknown
- Latency describes a model–provider deployment

**Speaker notes:** An API does not directly expose hardware utilization or energy consumption. Cost estimates use returned usage and recorded rates rather than prices taken from an old paper. Cached input is handled separately where data are available. A request-count cap is not a monetary ceiling. Set the monetary limit with the provider.

**Sources:** https://arxiv.org/abs/2211.09110 ; project research protocol section 6.

## 13. Independent new-set validation

- Planning target: 150–250 paragraphs from about 30–50 articles
- Two independent annotators before adjudication
- A calibration sample excluded from final evaluation
- Frozen prompts and models evaluated without new-set tuning

**Speaker notes:** The proposed sizes are planning targets to be refined after measuring annotation effort. Do not treat neighboring paragraphs as independent articles. Retain source URLs, dates, inclusion criteria and initial judgments. A new sample does not prove that texts were absent from model training without a verified cutoff.

**Sources:** Proposed new-data protocol. Collection and annotation pending.

## 14. Implemented research software

- Python CLI with no third-party runtime dependencies
- Chat Completions HTTP adapter and a CPU baseline
- Immutable run fingerprints and a durable attempt ledger
- HTML reports, error tables and annotation sheets

**Speaker notes:** Demonstrate validate, run, evaluate and baseline. The HTTP adapter has been tested against a local server, but account-specific compatibility still requires a smoke test. The baseline is TF-IDF nearest centroid. Raw PolyNarrative conversion is not automated: the package defines a normalized CSV/JSONL contract.

**Sources:** Source code in narrative_bench/. Test suite: tests/test_benchmark.py.

## 15. Offline demonstration

- 35 fictional teaching records across train, dev, test and new
- A fixed lexical fixture exercises the request and evaluation path
- Reports include intentional keyword false positives
- Demo scores are software checks only

**Speaker notes:** Open results/demo/test-zero/report.html and errors.csv. The science-museum example illustrates a keyword-matching failure. The demo provider ignores prompts and therefore returns identical zero/few predictions. This is not an LLM comparison. Neither these scores nor the synthetic new split fulfill the course's empirical requirements.

**Sources:** Synthetic data and fixtures authored for this project. No real news corpus or live API result.

## 16. Threats to validity

| Threat | Control and remaining limitation |
| --- | --- |
| Codebook ambiguity | Pilot and independent annotation |
| Leakage and duplicates | Article split checks plus manual review |
| API drift and service load | IDs, timestamps and fixed execution policy |
| Rare categories | Support tables and limited claims |
| Evidence selection bias | Preselected common audit records |

**Speaker notes:** No control eliminates its threat completely. Double annotation does not make a codebook universally true. Exact deduplication misses some syndicated copies. A provider may change a model behind an unchanged alias. Disclose these boundaries instead of treating a checklist as proof that risks are absent.

**Sources:** Project protocol. Dataset limitations: https://aclanthology.org/2025.acl-long.1513/.

## 17. Work plan

| Period | Research milestone |
| --- | --- |
| November 2026 | Literature, access, codebook and pilot |
| December 2026 | Existing-data results and interim presentation |
| January 2027 | Controlled resource-aware comparison |
| February 2027 | New-set validation and final presentation |
| March 2027 | Report and reproducible code submission |

**Speaker notes:** The timeline follows the kickoff. The group assigns internal dates and owners. Divide data/codebook, execution and analysis/report responsibilities, while having at least two people annotate the new sample independently. By December, the objective is real preliminary results rather than only a functioning interface.

**Sources:** Course kickoff slides 7 and 9. Team-level dates remain to be assigned.

## 18. Final deliverables

- A critical literature review and frozen research protocol
- Reproducible code, configurations and run records
- Real quality–resource results and evidence analysis
- A newly annotated validation corpus and final report

**Speaker notes:** The final submission combines software and research reasoning. Document individual contributions. The kickoff weights are literature review 25%, implementation 35%, report 20% and presentations 20%. These describe course grading rather than the completion percentage of the current package.

**Sources:** Course kickoff slide 7. Proposed deliverables in project proposal.

## 19. Current status and next milestone

| Ready | Pending before empirical conclusions |
| --- | --- |
| Implementation and offline reports | Approved dataset and exact codebook |
| Research protocol and annotation rubric | Account-specific API smoke test |
| Literature synthesis and study materials | Frozen model and price selections |
| Presentation and report scaffold | Real runs and independent new-set annotation |

**Speaker notes:** Separate infrastructure readiness from a completed empirical study. The next practical milestone is corpus access and one verified development request for each selected API deployment, followed by a pilot budget. At present, no best model or achieved improvement can be claimed.

**Sources:** Project status on 1 November 2026. Real research results pending.

## 20. Core references

- Nikolaidis et al. 2025. PolyNarrative. ACL
- Upravitelev et al. 2026. From Repetition to Recognition. arXiv preprint
- Lucas et al. 2023. Fighting Fire with Fire. EMNLP
- Hamilton et al. 2026. NarraBench. EACL
- Sosnowski et al. 2025. DiNaM. EMNLP

**Speaker notes:** Full links are provided in these notes and the bibliography. For personal reading, prioritize PolyNarrative and the recovery/mining/discovery framework. Identify each paper's input, output and observation unit before comparing methods.

**Sources:** https://aclanthology.org/2025.acl-long.1513/
https://arxiv.org/abs/2609.11128
https://aclanthology.org/2023.emnlp-main.883/
https://aclanthology.org/2026.eacl-long.176/
https://aclanthology.org/2025.emnlp-main.1537/

## 21. Methods and task references

- Piskorski et al. 2025. SemEval Task 10 overview
- Younus and Qureshi 2025. Narrative Classification as a Retrieval Task
- Liang et al. 2023. Holistic Evaluation of Language Models
- Additional reading: EUDisinfoTest and TopicGPT

**Speaker notes:** These sources help specify the benchmark, but their datasets and scores are not interchangeable. SemEval ST3 receives the dominant narrative as input; our evidence extension is defined separately. HELM explains the limits of efficiency measurements. Retrieval and TopicGPT suggest extensions after the baseline experiment.

**Sources:** https://aclanthology.org/2025.semeval-1.331/
https://aclanthology.org/2025.semeval-1.228/
https://arxiv.org/abs/2211.09110
https://aclanthology.org/2024.findings-emnlp.862/
https://aclanthology.org/2024.naacl-long.164/
