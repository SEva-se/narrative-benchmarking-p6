# Literature review and research position

Version: 2 November 2026. This document provides structured familiarization with the main P6 papers and supplementary sources for the project. The core papers are analyzed by task, method, results and limitations. Large appendices and additional studies are consulted selectively for implementation questions. This is not an exhaustive systematic review of the entire field.

## 1. Map of the field

“Narrative” refers to different objects. In news analysis, it can mean a recurring message or interpretation. In narratology, it can describe a broader structure involving agents, events, the manner of telling and its context. Papers with similar titles therefore do not necessarily solve the same task.

| Study | Object and task | Main evaluation | Role in our project |
|---|---|---|---|
| PolyNarrative | Assign codebook categories to news paragraphs/documents | Multilabel F1 | Main operationalization |
| From Repetition to Recognition | Generate sets of corpus-level labels | Recovery/mining metrics and human discovery validation | Limits of taxonomies and aggregate scores |
| F3 | Human and synthetic true/false news | Detection and transfer | Evaluation on different data |
| NarraBench | Different aspects of narrative understanding | Theoretical taxonomy and benchmark survey | Boundaries of our claims |
| DiNaM | Claims from fact-checking, grouping and narrative labels | Matching expert narratives | Alternative pipeline and stage-level evaluation |
| SemEval Task 10 | Entity roles, narrative labels and explanations | Different protocols for three subtasks | Practical specifications for related tasks |
| Retrieval system | Transfer labels from similar articles | Sample-level F1 | Additional baseline |
| HELM | Multidimensional model evaluation | Quality, efficiency and other properties | Resource-aware protocol |
| EUDisinfoTest | Credible/disinformative narrative statements | Classification with rhetorical variations | Sensitivity to argument form |
| TopicGPT | Generate and assign topics | Topic alignment and interpretability | Categories and evidence as ideas for a different task |

## 2. The four starting papers

### PolyNarrative — Nikolaidis et al., ACL 2025

The authors define a narrative as a recurring explicit or implicit claim promoting an interpretation of a news topic. They develop two-level taxonomies for climate news and Russia's war against Ukraine and annotate paragraphs in four languages. Each item can receive multiple labels.

Fine-tuned XLM-R performs better on detailed categories, while prompted Llama 3.1-70B is more competitive on broad categories. Longer guidelines and hierarchical prompting do not consistently improve performance. Human agreement is limited: α=0.571 for coarse and 0.480 for fine labels.

A crucial qualification is that matching a category does not establish that a text is false. The codebook reflects particular experts' experience and is not intended to be exhaustive.

For our project, we adopt the multilabel paragraph-level task and explicit label definitions. Read sections 3–5, Tables 3–4, Appendix A and Limitations. Recalculate statistics from the actual release: Table 1 and the Conclusion give different overall counts. Source: https://aclanthology.org/2025.acl-long.1513/.

### From Repetition to Recognition — Upravitelev et al., arXiv 2026

The study distinguishes recovery of a corpus's own taxonomy, mining against an independent taxonomy, and discovery of candidates outside existing categories. These are not sequential stages: success in one does not guarantee success in another.

It compares clustering and graph-community pipelines. With default HDBSCAN parameters in one multi-topic corpus, climate labels fall to approximately 2% of generated labels. Lowering the threshold restores coverage while increasing the number of outputs. Graph pipelines retain sparse singleton candidates, some accepted by human annotators.

This motivates category-coverage and parameter diagnostics rather than a universal claim that graphs are superior. Human discovery evaluation is a pilot with two annotators who are co-authors. Agreement about novelty is limited. Absence from a taxonomy does not establish historical novelty.

We adopt multiple diagnostics and separate analysis of rare cases. Read section 3.1, section 4, section 5.2 and Limitations. Version read: arXiv:2609.11128v1, a preprint. Source: https://arxiv.org/abs/2609.11128.

### Fighting Fire with Fire — Lucas et al., EMNLP 2023

F3 investigates disinformation generation and detection. The authors generate news variants, filter examples that fail to match the intended category using PURIFY, and compare zero-shot LLMs with trained detectors.

Results depend on text origin and the extent of alterations; subtle changes are harder to detect. In Table 5, fine-tuned transformers have higher average Macro-F1 than GPT-3.5, although their drop between evaluation settings is larger. Robustness and absolute performance must be discussed separately.

For us, this motivates independent transfer evaluation. The study does not establish current model performance or prices. Synthetic data and automated filtering can introduce artifacts, and a temporal split does not reveal the full pretraining corpus.

Read section 4, section 5.3, section 6 and Table 5. Generating false news is outside our proposed project. Source: https://aclanthology.org/2023.emnlp-main.883/.

### NarraBench — Hamilton et al., EACL 2026

The authors organize narrative understanding around story, narration, discourse and situatedness. Their taxonomy distinguishes 50 tasks and evaluation criteria involving scale, mode and interpretive variance. A survey of 78 benchmarks finds coverage gaps and a predominance of single-answer tasks.

The main point is that identifying names, understanding motivation and interpreting narrative perspective require different evaluations. Their estimate of approximately 27% coverage depends on the proposed taxonomy; it is not a universal percentage of narrative understanding achieved.

For us, the study limits claims: F1 on several news categories does not establish general narrative understanding. The theoretical framework and selection of accessible benchmarks also have limitations, including their narratological tradition and language coverage.

Read section 3, section 4.2, section 5 and Limitations. Reproducing every literary benchmark is unnecessary for our project. Source: https://aclanthology.org/2026.eacl-long.176/.

## 3. A key supplementary paper

### DiNaM — Sosnowski et al., EMNLP 2025

DiNaM converts fact-checking articles into narrative labels: it filters articles, extracts debunked claims, verifies and refines extraction, clusters embeddings and formulates a label for each group. The study uses 10,493 articles and compares its output with an expert narrative set.

Its verification step relies on the fact-checking article. It does not independently determine the truth of arbitrary messages. Retaining debunking context can change the stance represented by an extracted claim.

Separate evaluation of stages is useful for our project. Reported advantages over general methods apply to the selected data and semantic matching. Check the direction of WCD carefully: the paper defines a distance but discusses higher reported scores as better, while the 2026 study explicitly uses WCD↓. Their numbers should not be transferred directly.

Read sections 3–4, section 6 and Appendix B.1. Our minimum project does not reproduce this corpus-level pipeline. Source: https://aclanthology.org/2025.emnlp-main.1537/.

## 4. Sources for development

**SemEval 2025 Task 10.** Section 2 is particularly useful: ST2 assigns categories to documents, while ST3 receives the dominant narrative as input and generates its explanation. Our paragraph-level evidence task is an extension rather than an exact ST3 replication. The study covers five languages, so its release should not be assumed identical to PolyNarrative's four-language setup. https://aclanthology.org/2025.semeval-1.331/.

**Narrative Classification as a Retrieval Task through Story Embeddings.** The authors retrieve similar labeled articles and transfer categories without training a new classifier. This provides an alternative baseline. A limitation is transferring extra labels from partially similar texts. The specific system uses a 7B embedding model and a GPU; a CPU/API project needs a separately accessible implementation rather than a promise to run the same pipeline for free. https://aclanthology.org/2025.semeval-1.228/.

**HELM.** Study its multi-metric approach and section 4.9. We adopt joint reporting of quality and resources. Observed API latency includes service conditions, so it is not equivalent to pure computation time on identical hardware. https://arxiv.org/abs/2211.09110.

**EUDisinfoTest.** Examines credibility judgments under Logos, Ethos and Pathos rhetorical forms. It can support a separate stylistic robustness experiment. Short narrative statements do not replace news articles with paragraph-level labels. https://aclanthology.org/2024.findings-emnlp.862/.

**TopicGPT.** Generates and refines topic categories, then assigns them to documents with supporting quotations. This is useful as an example of interpretable assignment. A topic is not identical to a narrative, so topic-recovery scores do not solve our task. https://aclanthology.org/2024.naacl-long.164/.

## 5. Synthesis and working research gap

Our interpretation of the literature is that a controlled comparison of API deployments on a narrow task, with independent evidence review and transfer evaluation, provides a meaningful scope for a university P6 project. We do not claim that nobody has previously compared LLM costs or narrative extraction. A defensible contribution is a specific, fully disclosed combination of models, data, protocol and new observations.

The methodological decisions are to define the task before choosing a model, allow multiple applicable labels, distinguish narrative presence from truth, report category coverage separately, avoid evaluating novelty only against closed gold sets, acknowledge human ambiguity, and measure resources alongside quality.

## 6. What to add after the pilot

- The exact dataset and codebook versions actually used by the group.
- Sources on the selected API models when their properties affect a hypothesis.
- Studies relevant to error types actually found on development data, without tailoring the review to a desired winner.
- A comparison with published evaluations by annotation unit, label inventory and scoring conventions.
- A clear distinction between replication, adaptation and the new experimental contribution.

A useful personal reading table contains citation, narrative definition, input, output, gold source, metric, main finding, limitation and relevance to our task. Fill it in using your own words and section/page references. This turns a collection of summaries into your own literature review.
