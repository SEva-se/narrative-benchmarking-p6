# Project proposal

**Resource-Aware Benchmarking of API-Based LLMs for Narrative Classification and Evidence Extraction**

Vsevolod Drabych and project group · AI & Society Coding Lab · Project 6

Status: implementation and research proposal prepared on 1 November 2026. Empirical API results are pending.

## Abstract

Online news articles can express recurring interpretations of events through explicit claims or implicit framing. Existing research provides narrative taxonomies and annotated corpora, but model comparisons often leave practical deployment trade-offs and the support for individual predictions insufficiently examined. We propose a controlled benchmark of API-based language models for paragraph-level multilabel narrative classification with source-grounded evidence extraction. We will compare three accessible model configurations and zero-shot versus few-shot prompting against a CPU-based TF-IDF centroid baseline. Evaluation will distinguish classification quality, output validity, quotation fidelity, human-rated evidence support, token usage, estimated cost, and observed request latency. After development-set selection, frozen configurations will be tested on an independently collected and annotated news sample. The intended contribution is a reproducible evaluation pipeline and a transparent account of quality–cost trade-offs and transfer errors. We make no claim of automatic truth verification or general narrative understanding.

## Motivation and relation to prior work

PolyNarrative operationalizes the detection of news narratives as hierarchical multilabel classification and illustrates both difficult fine-grained distinctions and imperfect human agreement [1]. From Repetition to Recognition distinguishes recovery, mining, and discovery, and demonstrates coverage failures that aggregate metrics can miss [2]. DiNaM provides a staged approach to claim extraction and corpus-level narrative induction [3]. NarraBench shows why a narrow benchmark should not be treated as a universal test of narrative understanding [4]. F3 motivates transfer evaluation [5]. HELM provides the methodological basis for reporting efficiency alongside quality [6].

## Research questions

**RQ1.** How do the selected API configurations compare on paragraph-level narrative classification under a fixed codebook and input policy?

**RQ2.** How do zero-shot and fixed few-shot prompting affect classification, output validity, human-rated evidence support, and deployment cost?

**RQ3.** How much of the observed performance transfers to independently collected texts from the same language and domain?

We will treat an advantage of few-shot prompting as a hypothesis, not an expected result. A more expensive model may or may not improve the measures that matter. We will disclose insufficient evidence rather than force a winner.

## Scope

Initial scope: English-language climate news, using a verified coarse narrative codebook aligned to a specific PolyNarrative release, subject to data access. Each record is a target paragraph with a predeclared context policy. The output contains all applicable category IDs and exact source quotations with short explanations.

The primary task uses a predefined taxonomy. Open-world narrative discovery is outside the minimum viable scope. Novel category suggestions may be recorded as qualitative observations but will not be scored as validated discoveries. The evidence task is an extension of classification; it is not an exact reproduction of SemEval Task 10 Subtask 3, which supplies the dominant narrative as input [7].

## Method

We will obtain the permitted dataset release and record its provenance, taxonomy mapping, label conventions and hashes. Official article-level split boundaries will be preserved. Few-shot examples will come only from training data. Baseline threshold selection and all prompt decisions will use development data. The final test set will remain untouched until configurations are frozen.

Three API models will be selected based on actual account access, supported interfaces and a declared price range. We will keep the target text, codebook, output contract, example selection policy, and execution conditions consistent. We will record model IDs, timestamps, request parameters, output-token caps, resolved model names where returned, errors, retries, token usage and pricing snapshots. We will not assume access to hidden model states or GPU telemetry.

A separately collected sample will target 150–250 paragraphs across approximately 30–50 articles, subject to pilot feasibility. Two annotators will label each record independently before adjudication. We will retain initial annotations, disagreement statistics and decisions. Frozen systems will be evaluated without tuning on this new set.

## Evaluation and deliverables

Primary classification metric: Macro-F1 over the fixed label inventory, with label supports and a secondary macro score restricted to labels present in gold. We will also report Micro-F1, precision/recall, coverage and end-to-end exact match. Invalid or missing responses will remain visible. Evidence quotation membership will be checked automatically, while blinded human review will assess semantic support on a preselected sample. Uncertainty estimates will resample articles rather than individual paragraphs.

Resource measures will include observed token usage, list-price cost estimates, median and p95 record latency, and error rates. Missing usage or prices will remain unknown. API latency describes a model–provider deployment and includes network and service effects. We will not infer energy consumption or carbon emissions from token counts.

Deliverables: literature review, versioned benchmark code, data-conversion specification, run manifests and ledgers, evaluation reports, annotation records, newly collected dataset subject to source permissions, and presentations. Existing implementation includes an offline demonstration, baseline, HTTP adapter, strict validation, metrics and reports. The next empirical milestone is a small account-specific API pilot.

## Schedule

November 2026: literature, data access, codebook, pilot and preregistration. December: existing-data benchmark and interim presentation. January 2027: controlled quality–resource experiments and analysis. February: new-set validation and final presentation. March: final report and code submission. These follow the kickoff milestones; exact internal dates remain a team decision.

## References

[1] https://aclanthology.org/2025.acl-long.1513/

[2] https://arxiv.org/abs/2609.11128

[3] https://aclanthology.org/2025.emnlp-main.1537/

[4] https://aclanthology.org/2026.eacl-long.176/

[5] https://aclanthology.org/2023.emnlp-main.883/

[6] https://arxiv.org/abs/2211.09110

[7] https://aclanthology.org/2025.semeval-1.331/
