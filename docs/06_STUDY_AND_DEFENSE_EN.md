# Course and project-defense preparation

## 1. Explain the project in 30 seconds

“We compare API models on recognizing recurring interpretations of events in news. A model must select narrative categories and show supporting text passages. We measure quality, output usability, cost and latency, then test frozen configurations on a newly collected and independently annotated sample. The study does not require training a large model on our own GPU.”

Before real experiments are complete, add: “The pipeline and protocol are prepared, and the software demonstration is verified on synthetic data. Findings about actual models remain to be established.”

## 2. Terms you should explain confidently

| Term | Plain-language explanation |
|---|---|
| Claim | A specific assertion whose truth can be discussed. |
| Topic | The subject area, such as climate policy. |
| Narrative | A recurring interpretation expressed through different texts. |
| Taxonomy / codebook | Category inventory, definitions and application rules. |
| Multilabel | A text may receive several categories. |
| Coarse / fine | Broad categories and more specific subcategories. |
| Zero-shot | The prompt contains no labeled examples of the task. |
| Few-shot | The prompt includes a few labeled training examples. |
| Embedding | A numerical text representation used for comparison or retrieval. |
| TF-IDF | A word receives more weight when characteristic of a text and less common across the corpus. |
| Baseline | A simple system used to assess the benefit of a more complex one. |
| Gold | Reference annotation, which can itself be ambiguous. |
| Leakage | Information from evaluation influences system selection or training. |
| Transfer | A frozen system's performance on a different sample. |
| Evidence | A source passage intended to support a specific category. |
| Validity | Compliance with the response format and application contract. |
| Calibration | Whether stated confidence matches actual correctness; our minimum study does not measure it. |
| Pareto frontier | Configurations that no available alternative improves simultaneously in quality and cost. |
| Recovery / mining / discovery | Recovering the corpus taxonomy, matching an independent taxonomy, and finding candidates beyond existing inventories. |

Do not begin every explanation with mathematics. Give an example first, followed by the precise boundary.

## 3. Metrics through a concrete example

For one paragraph, gold = {A, B} and prediction = {A, C}. Correct category A gives TP=1. Extra category C gives FP=1. Missed category B gives FN=1. Precision = 1/(1+1) = 0.5, recall = 1/(1+1) = 0.5, and F1 = 0.5. Exact match is zero because the sets differ.

Macro-F1 computes each category's F1 and averages with equal weight. It highlights rare categories but becomes sensitive to limited support. Micro-F1 pools TP/FP/FN and reflects frequent categories more strongly. Report both with support.

For gold=[] and prediction=[], exact match is one. Sample-F1 is zero under this implementation's explicit convention. End-to-end exact match is always zero for an invalid answer. Know these conventions to interpret your own report correctly.

## 4. How the implementation works

First, data.py reads JSONL and the codebook, checks IDs and allowed labels, and detects shared articles or exact normalized texts across splits. prompts.py then builds the request from category definitions and the target, adding training-only examples. Evaluation gold is excluded from the request.

engine.py sends HTTP requests or invokes the teaching fixture. It writes the attempt ledger before execution and retains usage and raw outputs afterward. The validator checks IDs and exact quotation membership. evaluate.py matches predictions to every selected ID, including missing responses, computes metrics and creates HTML/CSV outputs.

baseline.py fits TF-IDF on train, averages positive vectors for each category and selects a threshold on dev. It is nearest-centroid classification, not logistic regression or a fine-tuned transformer. Explain the algorithm actually implemented.

## 5. Likely instructor questions and strong answers

**Why is this research rather than a few API calls?** It has a controlled task, fixed data, comparable configurations, independent evaluation, resource measurement and transfer testing. An API call alone is not a scientific contribution.

**What is your contribution?** A reproducible protocol and comparison implementation, empirical quality–cost trade-offs, evidence analysis and a new manually annotated evaluation sample. We do not claim a new architecture. The empirical contribution will emerge after the experiments.

**Why include a baseline?** It establishes whether a complex paid system adds value over a simple method. A baseline win is a substantive result to check and explain.

**Why not train your own LLM?** P6 concerns external model evaluation. APIs permit comparison without a local GPU. Avoiding training does not remove the need for rigorous evaluation.

**Why one language and domain?** It controls workload and permits careful codebook study, error analysis and human annotation. A second language or domain requires additional data and validation.

**How were models selected?** By actual account availability, interface support and a declared price range, with exact IDs recorded. General leaderboards do not substitute for our experiment.

**Can gold labels be trusted?** We use them as a working reference while disclosing ambiguity and agreement. New-set initial labels are retained before adjudication. Agreement does not establish objective truth.

**Why not randomly split paragraphs?** Paragraphs in one article are related and can expose familiar events and wording in test. Splitting and resampling should operate at article level.

**Why does narrative presence not imply fake news?** A narrative describes an interpretation. Factual accuracy and authorial intent are separate questions not established by category assignment.

**Can evidence explain the model?** It provides a basis that can be checked against the source. It does not prove that the passage causally determined the model's internal decision.

**Why use people when LLM judges exist?** A judge can err and share another model's preferences. Our minimum study uses human review as an independent assessment of support rather than having an LLM grade itself.

**Why do Macro-F1 and Micro-F1 disagree?** They weight categories differently. Frequent labels can hide poor performance on rare ones. Inspect support and per-label results.

**What does high demo F1 mean?** It describes a fixture's behavior on fictional teaching sentences. It is neither an LLM result nor evidence of real-news performance.

**Why does few-shot prompting change nothing in the demo?** The demo provider is a lexical fixture that ignores prompts. The two modes check pipeline plumbing; real differences require real models.

**How was cost calculated?** From observed usage and recorded prices, including cache rates where known. Unknown remains unknown. Provider invoices can differ from list-price estimates.

**Can you compare energy efficiency?** No. APIs do not expose sufficient hardware telemetry. We compare price and observed latency of particular deployments.

**What makes the dataset new?** It is separately collected and independently annotated, without overlap with the original corpus. This does not guarantee that the provider never trained on its texts.

**How will you establish significance?** The current implementation provides exploratory article-cluster intervals but no paired significance test. We avoid strong significance claims without an appropriate additional procedure.

**What if there are too few examples?** We show support and uncertainty and narrow our conclusions. More API models do not make a small dataset statistically larger.

**How does the project differ from DiNaM?** DiNaM induces corpus-level labels through claim extraction and clustering. Our minimum evaluates fixed-category assignment to target paragraphs and supporting evidence. Their metrics are not interchangeable.

**What is the main validity threat?** Initially, mismatch between the operational definition and codebook; subsequently leakage, selective human review and deployment effects on latency. The protocol predeclares these decisions.

## 6. What to read yourself

PolyNarrative: sections 3–5, Tables 3–4, Limitations and selected definitions in Appendix A. From Repetition to Recognition: section 3.1, section 4, section 5.2 and Limitations. DiNaM: sections 3–4, section 6 and Appendix B.1. NarraBench: section 3, section 4.2 and section 5. F3: section 4, section 5.3, section 6 and Table 5. HELM: section 4.9. SemEval overview: section 2 and evaluation. Source pages are in the bibliography.

For each study, write three statements: what it measures, how it measures it, and why its conclusion is limited. If you can do this without copying the abstract, you understand the literature sufficiently to discuss it.

## 7. Rehearsal and self-check

For an eight-minute presentation, use slides 1–4, 6, 8–11, 14, 17 and 19, keeping the others for discussion. For 15–20 minutes, present the main deck more fully. Timing depends on delivery, so rehearse.

Before the defense, independently:

- explain one multilabel example and one negative example;
- calculate F1 by hand;
- show where the request contains taxonomy and excludes test gold;
- locate the hash and model configuration in a manifest;
- show an invalid output and explain its effect on metrics;
- identify two limitations of the new sample;
- distinguish a paper's finding from your design decision;
- state which experiments were actually conducted and which remain planned.

If you do not know an answer, say “that was not measured under the current protocol” and explain how it could be measured rather than inventing a finding.
