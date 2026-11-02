# Final report scaffold

**This is a writing scaffold, not a completed empirical report.** Replace pending fields only with evidence from real runs. Synthetic demonstration scores must not appear in research result tables.

## Title and authors

Resource-Aware Benchmarking of API-Based LLMs for Narrative Classification and Evidence Extraction

Vsevolod Drabych and confirmed project group members. State individual contributions at the end.

## Abstract

Write after the experiments. State the task, corpus release, number of articles and paragraphs, model configurations, evaluation design, central observed result, and principal limitation. Distinguish classification from evidence support and from truth verification. Do not state an improvement before computing it.

## 1. Introduction

Explain the practical need to identify recurring interpretations in news. Define the exact task. Explain why quality alone is insufficient for deployment and why new-data evaluation is needed. End with RQ1–RQ3 and the actual contributions delivered.

## 2. Related work

Organize by tasks rather than article chronology: taxonomy-based classification; corpus-level induction and discovery; general narrative understanding; model evaluation and resource measurements. Use the literature matrix in the literature review. Explicitly identify where your method adapts a previous task rather than reproducing it.

## 3. Task and data

Give the input and output contract, target unit, context policy, category inventory, Other convention and negative-instance definition. Describe release provenance and conversion. Report source selection, exclusions and split boundaries.

| Dataset/split | Articles | Paragraphs | Positive records | Label inventory | Source/version |
|---|---:|---:|---:|---|---|
| Existing train | Pending | Pending | Pending | Pending | Pending |
| Existing dev | Pending | Pending | Pending | Same fixed codebook | Pending |
| Existing test | Pending | Pending | Pending | Same fixed codebook | Pending |
| Independent new test | Pending | Pending | Pending | Same fixed codebook | Pending |

Show per-label supports. State how duplicates and article overlap were checked. Describe the calibration sample separately from final annotation.

## 4. Systems and protocol

Describe the TF-IDF centroid baseline, training-only vocabulary, positive class centroids and dev threshold selection. Describe each API model–provider pair and exact ID. State prompt variants and fixed training examples. Provide prompt/config versions or hashes and output caps. Explain refusal/invalid output treatment, retries and missing records.

| Run ID | Provider | Requested/resolved model | Prompt version | Output cap | Run dates | Pricing snapshot |
|---|---|---|---|---:|---|---|
| Pending real run | Pending | Pending | Pending | Pending | Pending | Pending |

Discuss equal conditions and unavoidable interface differences. Mention if model aliases may have changed during collection. Describe any protocol amendment after preregistration.

## 5. Evaluation

Define primary and secondary F1 measures, absent-label handling, sample-F1 conventions, coverage and end-to-end exact match. Explain article-cluster bootstrap and its exploratory nature. State what human evidence review assesses and how annotators were blinded. Define cost estimates, unknown usage, latency scope and provider-side confounds.

## 6. Results

Only populate these tables from real outputs. Report precision appropriate to sample size, uncertainty, support and failure counts.

| Configuration | Macro-F1 all labels | Micro-F1 | Valid coverage | End-to-end exact match | Articles / records |
|---|---:|---:|---:|---:|---|
| CPU baseline | Pending | Pending | Pending | Pending | Pending |
| Model A zero | Pending | Pending | Pending | Pending | Pending |
| Model A few | Pending | Pending | Pending | Pending | Pending |
| Model B zero/few | Pending | Pending | Pending | Pending | Pending |
| Model C zero/few | Pending | Pending | Pending | Pending | Pending |

| Configuration | Input/output tokens | Known cost lower bound | Complete estimate? | Median / p95 seconds | HTTP attempts |
|---|---|---:|---|---|---:|
| Pending | Pending | Pending | Pending | Pending | Pending |

Show a quality–cost scatter plot only when data are real and comparable. Label configurations and identify nondominated points without converting all trade-offs into a subjective single score. If cost is unknown, mark it explicitly and exclude it from cost-based ranking.

## 7. Independent new-set validation

Report collection criteria, annotation agreement before adjudication, support and version. Compare frozen systems with existing test results. Discuss changed distributions rather than attributing every change to model generalization. New publication dates do not prove absence from training without a verified model cutoff.

| Configuration | Existing score | New-set score | Difference | Coverage change | Interpretation |
|---|---:|---:|---:|---|---|
| Pending | Pending | Pending | Pending | Pending | Pending |

## 8. Evidence and error analysis

Report human support as 1/0/unclear with the predeclared denominator. Explain sampling and blinding. Discuss exact quotation separately from semantic support. Present several short source-permitted examples covering different error types. Include false positives on neutral text and false negatives on implicit categories. Avoid cherry-picking one model's successes against another's worst cases.

## 9. Discussion

Answer each RQ with its practical limits. Discuss the cost of any quality improvement, whether few-shot helps consistently, and how stable conclusions are across samples. If evidence is insufficient, state that directly. Relate observations to the literature without claiming to validate all of a paper's conclusions.

## 10. Limitations and responsible use

Address codebook perspective, human disagreement, label imbalance, sample size, source selection, pretraining contamination uncertainty, API model drift, inference-parameter differences, retry and cache costs, latency confounds, and the limited scope of evidence explanations. Describe corpus access conditions and whether raw data can be redistributed. Follow the course policy for disclosure of AI-assisted code and writing.

## 11. Conclusion

State what was actually learned and under which conditions. Explain the usable artifact delivered. Suggest one next study that resolves a real limitation rather than listing every possible expansion.

## Reproducibility and contributions

Provide software version/source hash, dataset and taxonomy hashes, environment, seeds, commands, run manifests, prompt/config files, annotation records, and exclusions. Keep API secrets out of the submission. Document each team member's reading, coding, annotation and analysis contribution.

## Appendices

A: verified codebook and mappings. B: complete prompts and few-shot IDs. C: detailed label supports and metrics. D: annotation guidelines, independent agreement and adjudication log. E: resource accounting, pricing snapshots and failures. F: protocol amendments and additional exploratory analyses.
