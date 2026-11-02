# Annotation guidelines v0.1

This is a working research draft for the group. Before reproducing PolyNarrative, reconcile it with the official annotation guidelines for the actual release. Do not claim that this package's brief definitions are equivalent to the authors' complete codebook.

## Annotation unit

The target is one paragraph. If the protocol permits context, humans and models receive the same context. Annotate what the target expresses. A category that occurs only in a neighboring paragraph is not automatically transferred.

Select every applicable category from the fixed inventory, rather than exactly one. If none applies, enter `[]`. Leave labels_json empty if the record has not been reviewed. Missing annotation is different from a negative judgment.

## Procedure

1. Read the entire target and available context.
2. Formulate its main interpretation of events in your own words in a private draft.
3. Match that interpretation to category definitions and inclusion/exclusion examples.
4. Select all supported categories, avoiding keyword-only decisions.
5. If uncertain, flag uncertain and explain the issue in note while retaining your best judgment.
6. Do not inspect model outputs or another annotator's labels before completing independent annotation.

A narrative can be implicit, but an inference must be grounded in the text. General topic, negative tone and your assessment of factual accuracy do not substitute for category membership.

## Teaching examples

All sentences below are fictional and intended only for annotation training.

| Text | Interpretation |
|---|---|
| The column argues that the carbon tax increases household costs without reducing emissions. | Working category: criticism of climate policies. The text evaluates the effect of a climate measure. |
| The notice lists the opening hours of a science museum. | No climate narrative. The word science alone does not justify a category. |
| The editorial criticizes climate taxes and calls wind turbines unreliable. | Two categories: criticism of policies and controversy about green technologies. |
| The article names the committee that published the climate report. | Mentioning an institution alone is insufficient for criticism of institutions. |

## Quotation, negation and authorial stance

Resolve this issue before freezing the codebook. A text can quote, reject or promote a narrative. These cases should not automatically receive identical treatment. Verify the chosen corpus's official rule: does presence count regardless of stance, or must the text present/promote the interpretation?

Example: “Some claim the policy is a conspiracy, but the report rejects that claim.” The word conspiracy occurs, but the authorial position differs from the quoted position. Do not leave the decision to each annotator's intuition. Record a convention during the pilot and apply it consistently. An extension may add a separate stance column, but should not thereby change official gold when reproducing a benchmark.

## Other and no narrative

An official Other category may mean that a narrative is present but not covered by detailed categories, or another specific case. In our base schema, `[]` means no applicable categories in the current taxonomy. It does not assert the absence of every possible narrative.

If using Other, add an explicit ID and definition and decide whether it participates in F1. Do not silently convert all official Other labels to negative examples. Retain the mapping table and exclusions.

## Independence and adjudication

Both annotators first work independently. Compute agreement on their original versions. Then discuss disagreements and create a third final table. For difficult cases, retain record ID, annotator A labels, annotator B labels, final decision and rationale.

The software computes binary Cohen kappa per category, exact agreement between label sets and mean Jaccard. These measure agreement rather than objective truth. Kappa may be null for constant judgments. Report positive counts and typical disputes.

Calibrate on 20–30 paragraphs before final annotation and exclude them from the final new test. Changes to guidelines after seeing final model answers must be disclosed and usually require another held-out sample.

## Reviewing model evidence

There are two levels of review. The code checks whether an exact quotation occurs in the target. Humans assess whether it supports the predicted category. A quotation may describe another speaker's position or negate it; matching characters does not resolve that distinction.

For blinded review, preselect a shared set of record IDs, collect outputs from all configurations, hide model/run/variant and shuffle order. Work on copies of `evidence_review.csv`. Do not select only successful answers or only errors.

| Rating | Criterion |
|---|---|
| 1 | The quotation and permitted context sufficiently support the specific category. |
| 0 | The quotation is on-topic but does not support the category, or contradicts it. |
| unclear | The decision cannot be made confidently without a rule change or additional context. |

Retain reviewer and comment. Do not remove unclear judgments; report their share. Support can be aggregated as a strict score, where only 1 is positive, and as a separate 1/0/unclear distribution. Predeclare the rule. The software exports human-review material but does not automatically perform this aggregation.

The baseline returns the full target as its quotation. This is technically a source match but may be broad or fail to support the category. Do not automatically compare its length with concise LLM quotations as a quality measure without a predefined rubric.

## Decision-log template

| Record ID | A | B | Decision | Rationale | Rule version |
|---|---|---|---|---|---|
| Complete with a real example | | | | | |

Retain original spreadsheets/CSVs separately. Evaluation commands regenerate review CSVs, so keep completed human reviews under different filenames.
