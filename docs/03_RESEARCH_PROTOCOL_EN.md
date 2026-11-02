# Research protocol v0.1

Original protocol: 1 November 2026. English edition: 2 November 2026. Status: draft before data access and the pilot. Complete the decisions below and save an immutable v1.0 before the first final test run. Record subsequent changes in an amendment log and label the affected analyses exploratory.

## 1. Research object and contribution

We study the performance of specific API-model configurations on narrative classification in news paragraphs. For each category, the model also returns a quotation and a short explanation. The practical contribution is a reproducible quality–resource comparison with evaluation on new texts. Developing a new LLM architecture or training a large model is outside the minimum scope.

Proposed scope: English-language climate news. Taxonomy: coarse categories from a verified PolyNarrative release. The release, label dictionary and Other convention are not yet confirmed. `climate_coarse_draft.json` adapts category names from Figure 3 and supplies our own short working definitions. It requires comparison with the official codebook.

We distinguish multilabel classification from source-evidence extraction. We do not describe the task as automatic truth verification, identification of hidden authorial intent or open-world discovery. A quotation makes an answer inspectable but does not explain the model's internal computation.

## 2. Questions and hypotheses

RQ1: What classification differences do we observe between three selected API configurations under identical inputs and taxonomy?

RQ2: How do fixed few-shot examples affect quality, output usability, semantic evidence support and cost relative to zero-shot prompting?

RQ3: Do performance and system rankings transfer to an independently collected sample from the same language and domain?

Working hypotheses: few-shot prompting may improve quality at the expense of additional tokens; higher price does not necessarily produce a better quality–cost trade-off; a new sample may expose additional error types. Do not write expected directions as findings. If the data do not distinguish models convincingly, report uncertainty.

## 3. Decisions to freeze before testing

| Field | Decision |
|---|---|
| Dataset release, source and access terms | Complete after obtaining files |
| Language and domain | Proposed EN / Climate Change |
| Codebook and Other convention | Verify against the release and freeze |
| Category granularity | Coarse for the primary analysis |
| Observation unit | Target paragraph |
| Context | Target paragraph only by default; any other fixed context policy is a separate configuration |
| Train/dev/test | Preserve official article-level boundaries where available |
| Models and providers | Three accessible exact IDs and verification date |
| Zero/few prompts | One versioned codebook and the same output contract |
| Few-shot examples | Fixed training IDs, preferably 4–6 examples covering categories and a negative case |
| Output cap / temperature / reasoning effort | Record supported values or parameter omission |
| Existing test size | After audit: all eligible test records or a predefined article-level subset |
| Primary metric | Macro-F1 over the complete fixed taxonomy |
| Seeds / repetitions | Freeze ordering; evaluate additional repeats separately |
| Human evidence audit | Preselected 50–100 records or the entire small test |
| New sample | Target 150–250 paragraphs from about 30–50 articles, refined after the pilot |
| Budget | Provider monetary cap and a local API-attempt limit |

These are planning sizes, not a statistical power calculation. If data or rare categories are too scarce, narrow the claims and report support for every category.

## 4. Data and leakage prevention

Before conversion, complete `data/templates/provenance.json`: release, URL, retrieval date, use conditions, SHA-256 of original files, exclusions and transformations. Store originals separately and do not modify them.

A normalized record contains id, article_id, text, split, language, dataset_kind and labels. Optional fields include context, source_url and publication_date. Gold `null` means not yet annotated; `[]` means annotated with no applicable categories. These states differ. The API can process unannotated records, but evaluation requires gold.

Paragraphs from one article must not span splits. Otherwise, style, events and related wording can occur in both development/training and test data. The validator detects shared article_id values across splits and exact text matches after case and whitespace normalization. It does not automatically detect semantic duplicates or syndicated copies: inspect those separately and keep an exclusion list. Mirrors of an article should belong to the same group.

Obtain the permitted corpus first. If subsampling is necessary, select articles and then include a consistent set of their paragraphs. CLI `--limit` is intended for technical pilots and randomly selects records; it does not replace a predefined final sample selected by article.

Do not use test or new records to select prompts, thresholds or few-shot examples. Do not change new-set gold labels to favor a model's answer. Retain both initial human annotation sets and a separate adjudication log.

## 5. Systems and controlled conditions

Main matrix: 3 API models × 2 prompt variants = 6 configurations. The CPU TF-IDF centroid system is a separate baseline. It fits vocabulary and centroids only on train and selects its threshold on dev using Macro-F1 over categories with positive gold support. Ties favor the higher threshold. This baseline is not an exact replication of the paper's XLM-R system.

Zero-shot and few-shot variants receive the same category definitions, target and output format. They differ in additional training examples. Do not simultaneously introduce a new instruction and a different output contract, because this would confound the few-shot effect with other changes.

External APIs and a CPU baseline accommodate the absence of a local GPU. This allows service-level efficiency measurement but does not reveal hardware inference costs or energy use. With different providers, describe the comparison as one between model–provider deployments. If one model lacks temperature or JSON mode, disclose that difference.

Select models spanning price levels accessible to the group. Do not compare brands only through general leaderboards: measure quality on this task. Exact IDs and rates remain unassigned because the account and provider are not known.

## 6. Resources and spending limits

Execution is sequential, with concurrency 1. Record order is shuffled reproducibly. Alternate configurations or run them in recorded blocks, since service load can change. The software does not automatically interleave models; the team records the run schedule.

Every HTTP attempt is written to a durable ledger before sending. Responses, including invalid JSON, are retained and accounted for. HTTP 429 and selected 5xx responses receive limited retries. Timeouts are not automatically retried because a request may already have incurred a charge. Invalid model output is also not retried: it is an experimental outcome.

`max_api_calls` limits attempts in one run directory, including retries. It is **not a hard monetary cap**. Set the monetary limit with the provider. Cost is computed using returned usage and configured prices. Missing usage, cached-input rates or uncertain failed-attempt charges produce unknown rather than zero. A known lower bound is only the known portion of spending, not an invoice total.

Ordinary request-cost estimate:

`C = (uncached_input × input_rate + cached_input × cache_rate + output × output_rate) / 1_000_000`.

Output usage may include internal reasoning tokens depending on the provider. Check its billing and usage definitions. Discounts, batch rates, currency conversion and extra fees are not automatically modeled. Attach the pricing URL/date and reconcile with billing where available.

`latency_seconds` measures record processing with retries/backoff but excludes the delay before the next record. CPU-baseline timing measures prediction only, excluding fitting and threshold tuning. CPU and API latency therefore have different scopes. Do not infer absolute architecture speed from them. Report median and p95 for API deployments. p95 is unstable for a few dozen requests, so disclose sample size.

## 7. Classification evaluation

For every category, compute TP, FP, FN, precision, recall and F1. Macro-F1 averages category scores; Micro-F1 first pools TP/FP/FN. The implementation uses zero when the denominator is absent. Primary macro includes all codebook categories, including those absent from gold. Also report macro restricted to categories represented in gold. Always show support: macro scores based on different label subsets are not directly comparable.

Sample-F1 averages across records and assigns zero to empty/empty sets in this implementation. Exact match assigns one to matching empty sets. The metric name records this convention. Do not describe it as the only permissible choice.

Failed or missing responses become empty predictions for F1. This penalizes missed positive categories, but empty output can accidentally match negative gold. Therefore also report end-to-end exact match, which treats every invalid/missing response as a failure, and valid-output coverage. No single measure fully describes the system.

Bootstrap groups records by article_id and resamples entire articles. An exploratory percentile 95% interval is implemented for Macro-F1 over the full taxonomy. Rare categories can be absent from resamples, affecting the interval. This is not proof of significant differences. A rigorous paired comparison requires a paired article-cluster bootstrap of score differences on the same articles; the current version does not implement it. Do not infer significance from overlap or non-overlap of separate intervals alone.

## 8. Evidence and error evaluation

The strict validator checks schema, allowed IDs, duplicate labels, evidence for each predicted category, and exact nonempty quotation membership in the target. Any violation invalidates the entire response. This is a conservative design decision: a quotation error affects end-to-end classification. A separate relaxed classification-only analysis can be implemented, but must not replace the main result after test inspection.

Automatic checking does not assess meaning. For human review, preselect the same record IDs for all models, shuffle responses and hide model/provider/variant. `evidence_review.csv` exports all valid quotations as raw material for that process. Blinding, sampling and aggregation of human support are manual in this version; do not describe them as implemented automatic evaluation.

Support rubric: 1 means the quotation and allowed context support the category; 0 means they do not; unclear means ambiguous. Separately report supported predicted labels, category precision/recall and invalid responses. High support among a few cautious predictions can coexist with low recall.

Error categories: wrong category; confusion between adjacent categories; keyword-driven extra label; missed implicit narrative; error on negative text; quotation/negation/author-stance confusion; target/context confusion; invented quotation; invalid JSON; refusal/truncation; unsupported request; and wording outside the codebook. Analyze cases rather than merely assigning error codes.

## 9. The new sample

Use the same language and domain but articles outside the original corpus. Later publication helps test temporal transfer, but does not prove absence from pretraining without a reliable model cutoff. Newness here means independent collection and no overlap, not guaranteed model unfamiliarity.

Include different sources and genres rather than selecting articles based on a favored model's errors. Predefine the date window and inclusion criteria. Aim for category coverage, but do not call a purposive sample representative of all media. Retain neutral examples and report imbalance.

Use the first 20–30 paragraphs to train annotators and refine the codebook. Exclude them from the final new test. Then freeze the guidelines. Two people independently annotate the final sample. The code computes per-label binary Cohen kappa, set exact agreement and set Jaccard. These are not the same procedure as published Krippendorff alpha. Kappa can be undefined under constant judgments; the software returns null.

After adjudication, run already frozen systems. If you tune a model or prompt on new data, that becomes adaptation and requires another held-out sample.

## 10. Scope, milestones and readiness criteria

Minimum: one language, one domain, coarse taxonomy, 3 models × 2 prompts, CPU baseline, existing test, separate new sample, human evidence audit and resource analysis. Under an API constraint, reduce model count or test size using predefined article-level sampling and disclose the decision. Retain independent new-data evaluation.

Optional extensions after the minimum include fine labels, a second language, retrieval baselines, stability repetitions, a cheap/strong model cascade, or separate corpus-level mining. Graphs and multi-persona extraction add substantial components and are not in the current implementation.

Ready for December: data access and codebook resolved, an executable existing-data benchmark, and real preliminary numbers with provenance. Ready for February: independent new-set annotation and frozen-system evaluation complete. Ready for March: reproducible code, manifests, results, limitations and final report.

## 11. Known implementation limitations

The runner supports non-streaming Chat Completions JSON responses and sequential execution only. Account-specific compatibility requires a smoke test. Official raw PolyNarrative formats are not automatically converted: `import-csv` expects already normalized CSV. Semantic deduplication, automatic article splitting, graph pipelines, LLM judges, paired significance tests and automatic aggregation of human evidence scores are not implemented. Necessary manual steps are described here and in the runbook.

Manifests store data, taxonomy, Python-source and request hashes. API keys are not logged. Complete outputs may contain source text and should be shared only under corpus conditions. If a process crashes after an attempt without a committed prediction, the runner blocks resumption until the ledger and billing are inspected. This prevents silent replay of a potentially charged request.

## Methodological sources

PolyNarrative: https://aclanthology.org/2025.acl-long.1513/.

From Repetition to Recognition: https://arxiv.org/abs/2609.11128.

DiNaM: https://aclanthology.org/2025.emnlp-main.1537/.

NarraBench: https://aclanthology.org/2026.eacl-long.176/.

HELM: https://arxiv.org/abs/2211.09110.

API contract: https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create and https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat. Checked on 1 November 2026. JSON mode constrains format; our implementation validates application-specific semantics and quotation membership.
