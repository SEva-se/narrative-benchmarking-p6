# Reproduction protocol and differences

## Research question

Can an independent implementation of PolyNarrative's labels-only zero-shot method assign fine-grained URW labels to English news paragraphs, and how does their union perform against approved document-level gold?

This is a predefined scope for the proposed first experiment; it remains a team proposal, not instructor-approved scope or a claim of novel research.

| Component | Paper or official source | This implementation | Status |
|---|---|---|---|
| Main source | PolyNarrative, ACL 2025, section 5 / Appendix C.1 | Same methodological source | Verified |
| Model | Llama 3.1-70B | User-specified exact provider deployment | Pending; different model is an extension |
| Languages / domains | BG, EN, PT, RU; CC and URW with uneven coverage | EN / URW | Deliberately narrowed |
| Data | Paper TEST corresponds to SemEval development | Authorized dev articles and ST2 document gold | Not obtained |
| Label inventory | Two-level URW taxonomy | Public taxonomy, 11 parents / 38 named children + Other options | Release agreement pending |
| Prompt | Appendix C.1, taxonomy only | Transcribed template; ASCII apostrophe; real codebook list substituted | Source-derived, not authors' code |
| Message roles | Exact API role placement not recovered | Instructions as system, tagged article as user | Declared assumption |
| Paragraphs | Original paragraph units | Importer splits on blank lines, retaining title | Unverified boundary adaptation |
| Output | Paragraph tags and semicolon-separated label names | Same format, no JSON/no evidence requirement | Method aligned |
| Document evaluation | Separate paragraph/document experiments | Union of predicted paragraph labels against document gold | Explicit adaptation |
| Postprocessing | Filter hallucinated labels; normalize case/punctuation | Deterministic character normalization, separate strict/filtered views | Authors' exact code unavailable |
| Decoding | Full settings not recovered | Temperature 0, explicit output cap | Declared assumptions |
| Quality | Macro-F1 and sample-F1 | Both; two Macro-F1 label-universe conventions, Micro-F1, exact match | No scorer parity yet |
| Resources | Not a verified energy reproduction | API observed latency/usage/optional prices | Extension, not hardware energy |

## Execution sequence

1. Confirm data access, permitted use, split, gold availability and English URW membership. Preserve source archive hashes externally if possible; importer records gold/IDs/article hashes. Clarify the duplicate ZIP naming on the author's page.
2. Inspect actual release category strings. Resolve schema/version mismatch before execution. Never create a codebook solely from test gold or infer missing paragraph labels from document gold.
3. Run offline tests and inspect a five-article request preview. Preview excludes evaluation gold; it includes the whole taxonomy and selected source text.
4. Record provider, exact model ID, revision/quantization if exposed, date, endpoint, decoding and prices. If the original deployment is unavailable, label the run a method reimplementation with a model substitution.
5. Run a diagnostic pilot. Resolve purely technical defects on separate development material, then freeze the protocol for the reported evaluation. If TEST labels informed prompt tuning, disclose it and do not describe that evaluation as untouched.
6. Run the whole prespecified selection. Publish aggregated metrics and method differences, respecting dataset terms. Do not upload private prompts/responses/article-level annotations.
7. Only after the base run: add other models under identical selection and prompt. Further prompting conditions, XLM-R fine-tuning, paragraph-gold evaluation and a new independently annotated corpus are subsequent work.

## Interpretation boundaries

- Reproducing one method on a subset is not reproducing the full paper or its multilingual averages.
- High synthetic-fixture scores have no scientific meaning. Offline tests validate mechanics, not model performance.
- Narrative presence does not establish falsehood or endorsement; follow the approved annotation convention.
- No claim of emissions, energy efficiency, statistical significance or original narrative discovery is supported by this initial API pathway.
- Original scorer, original paragraph labels/segmentation, exact model deployment and unavailable settings are substantive reproducibility gaps, not details to conceal.

## Sources checked

- https://aclanthology.org/2025.acl-long.1513/ (paper PDF, sections 5 and C)
- https://nikon95.github.io/narrative-detection/ (access and split correspondence)
- https://propaganda.math.unipd.it/semeval2025task10/ (format, scoring, access, use conditions)
- https://propaganda.math.unipd.it/semeval2025task10/NARRATIVE-TAXONOMIES.pdf (URW figure; SHA-256 in taxonomy JSON)

Checked 8 November 2026. Targeted repository searches and the linked pages did not identify an official baseline source repository. Authors may provide it through the approved task page or upon request. No contact was sent on the user's behalf.
