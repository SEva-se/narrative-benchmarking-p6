# Reproduce PolyNarrative Experiment

An independent, **partial reimplementation** of the zero-shot labels-only Llama experiment in Nikolaidis et al., ACL 2025. This is the group's proposed first practical experiment. It is not the authors' repository and has not produced real model results yet.

## What this experiment does

Scope: **English, Ukraine-Russia War (URW), labels-only zero-shot prompting**. A whole article is sent in one request with `[paragraph_N:]` tags. The response assigns fine-grained labels to each paragraph. We union those predictions into document labels, derive coarse labels through the hierarchy, and compare them with document-level gold. No supporting quotations or JSON response schema are requested. No model training or local GPU is required for this API pathway.

This provides an implementable first slice, not a recreation of all domains/languages/models/prompting conditions in Table 4. In particular, paragraph-to-document aggregation is an explicit adaptation: it must not be presented as a verified recreation of the paper's separate document-level configuration.

## What was verified on 8 November 2026

- The [paper](https://aclanthology.org/2025.acl-long.1513/) describes XLM-R fine-tuning and four Llama 3.1-70B prompting variants. Section 5 and Appendix C are the implementation sources.
- The [author's data page](https://nikon95.github.io/narrative-detection/) directs researchers to registration and vetting for [SemEval Task 10](https://propaganda.math.unipd.it/semeval2025task10/). Data and official scoring scripts are available through the team page after access approval.
- Paper **TRAIN** = shared-task training batches 1-3 plus additional Russian training data. Paper **TEST** = shared-task **development** release, not the later competition test release.
- The author's page repeats the same ZIP filename for TRAIN and TEST; filenames alone are therefore insufficient to verify the split. Inspect archive contents, release description and approved IDs. Seek organizer clarification if ambiguous.
- The article-level ST2 gold format is publicly documented as `article_id<TAB>coarse_labels<TAB>fine_labels`, with semicolon-separated labels. This importer implements that format only. It does not pretend to understand unavailable original paragraph annotations.
- The public [taxonomy PDF](https://propaganda.math.unipd.it/semeval2025task10/NARRATIVE-TAXONOMIES.pdf) contains 11 URW parent categories and 38 named subcategories. `taxonomy_urw.json` adds the documented parent-specific `: Other` options and global `Other` (50 fine options total). Verify against the actual approved release before using it.
- No official baseline source repository was located via the paper landing page, author data page, task page or targeted repository search. This is a search finding, not proof that no code exists. No third-party participant system has been substituted for the authors' code.

## What you still need

1. Obtain approved access to the dataset and its permitted research use. Download the **development articles and gold corresponding to the paper TEST set**. The public page says development gold was released; confirm it is available in your approved account.
2. Obtain the corresponding original paragraph annotations/segmentation and official scorer if you want paragraph metrics and exact scorer parity. This first slice uses document gold instead.
3. Prepare an explicit list of English URW article filenames. Establish domain from authorized metadata or manual source review, including all-Other articles. Never select examples based on model success.
4. Use a provider/model deployment you can access. Llama 3.1-70B is the paper's family/size. The paper does not resolve every deployment detail, including exact revision/chat template and decoding settings. Verify whether your endpoint is Instruct/base, quantized, or otherwise different. A different model is an extension, not same-model replication.
5. Ensure the dataset's use conditions permit your chosen hosted inference route. Keep source articles, gold, prompts and provider responses out of GitHub. The shared-task page prohibits redistribution of the dataset.

**Adding an API key alone is not enough: approved data and gold are also required.** There is no hidden download or login bypass in this project. No real dataset, passcode or API credential is bundled.

## Run locally (Python 3.10+, standard library only)

Run the following commands from this folder. Offline tests need no credentials:

```powershell
python -m unittest discover -s . -p 'test_*.py' -v
```

Put approved files under `data/private/`. Unzip locally; this tool never automatically extracts an archive. Example layout:

```text
data/private/articles/EN_10001.txt
data/private/gold.tsv
data/private/english_urw_ids.txt
```

The IDs file has one exact filename per line, without a header. `gold.tsv` has exactly three tab-separated fields and no header, as above. Example filenames are illustrative, not shipped data. If the approved release has different schemas or label names, stop and adapt the importer explicitly; do not silently translate labels or invent paragraph gold.

Import after checking the release mapping:

```powershell
python reproduce.py prepare --articles data/private/articles --gold data/private/gold.tsv --ids data/private/english_urw_ids.txt --release 'APPROVED_RELEASE_NAME' --note 'Describe verified source, split and domain selection' --confirm-paper-test --output data/private/paper_test_en_urw.json
python reproduce.py validate --data data/private/paper_test_en_urw.json
Copy-Item api.example.json api.local.json
```

Edit `api.local.json`: set the full endpoint URL and exact model ID; check token/context limits and optional prices. The example endpoint/model are placeholders, not verified service offerings. `temperature=0`, a 4096-token output cap and system/user message placement are declared implementation choices, not recovered author settings. Never paste a key into this JSON file.

Read the key without displaying it in PowerShell:

```powershell
$secureKey = Read-Host 'API key' -AsSecureString
$env:POLYNARRATIVE_API_KEY = [System.Net.NetworkCredential]::new('', $secureKey).Password
```

Preview the exact requests **offline**, then run at most five articles initially:

```powershell
python reproduce.py preview --data data/private/paper_test_en_urw.json --config api.local.json --limit 5 --output results/private/preview.json
python reproduce.py run --data data/private/paper_test_en_urw.json --config api.local.json --limit 5 --output results/live/pilot --execute-api
python reproduce.py evaluate --data data/private/paper_test_en_urw.json --run-dir results/live/pilot --output results/private/pilot_report.json
Remove-Item Env:POLYNARRATIVE_API_KEY
```

On Linux/macOS, use `cp api.example.json api.local.json`, `read -rs POLYNARRATIVE_API_KEY; export POLYNARRATIVE_API_KEY`, and the same Python commands; clear it afterwards with `unset POLYNARRATIVE_API_KEY`.

Requests are ordered by article ID; `--limit` selects the first N, a diagnostic pilot rather than a representative estimate. Remove `--limit` for the complete prespecified English URW selection. Increase `max_api_calls` **before** starting that run, choose a fresh output directory, and use the same selection for all models. Changing a configuration or selection during an existing run is refused. Re-running an unchanged run skips completed attempts, including failed/invalid ones. It never automatically retries paid calls. A crash with an unresolved started attempt blocks automatic replay; inspect provider billing and the ledger before creating a separate recovery run. A stale `.run.lock` must be inspected before manual removal.

The character cap prevents silent truncation but is not tokenization. Check the exact provider's context window. If an article exceeds it, record the exclusion or design a separately named chunking experiment; do not silently change this protocol.

## Outputs and interpretation

- `manifest.json`: frozen config, selected IDs, dataset/code/prompt/taxonomy/request hashes and completion status.
- `attempts.jsonl`: durable pre-request/finished ledger.
- `responses/`: complete raw provider JSON, including usage. These contain restricted source-derived material; keep private.
- `predictions.jsonl`: raw text, normalized predictions, paragraph parsing issues, model response identifier, observed latency and cost estimate when known.
- `pilot_report.json`: document-level fine/coarse sample-F1, two explicit Macro-F1 conventions, Micro-F1, exact match, per-label support, missing/invalid counts, and resource summary.

Primary **strict-format** scores treat a missing, truncated, or malformed document response as an empty predicted set (not as `Other`). Secondary **filtered diagnostic** scores retain recognized labels even from malformed outputs. All selected articles remain in both denominators. Keep both views visible: filtering away invalid responses can otherwise inflate quality.

Label normalization changes case, Unicode form, punctuation and spacing; it never uses semantic/fuzzy matching. Unrecognized strings are preserved in diagnostics. `Other` is removed from a union containing specific labels; parent-specific `: Other` is preserved. These are our explicit conventions pending official-code/scorer comparison. Coarse predictions are derived from fine predictions; gold hierarchy inconsistency raises an error.

Macro-F1 is reported over both the fixed inventory and observed gold/prediction union because absent categories can alter the result, especially in one-language subsets. Sample-F1 averages per-document set F1. Empty/empty would score zero, but valid gold requires explicit `Other`, so silent empty gold cannot inflate a result. No official-scorer parity, confidence interval, significance claim or energy measurement is claimed.

Cost stays `null` when usage, pricing, or a required cache price is unavailable. Known recorded cost is a lower bound; provider charges for failed requests may be unknown. API latency measures the particular deployment/service, not pure GPU computation. The call cap plus output cap bounds request count/output size, not a guaranteed dollar budget. Prices must be recorded from your actual provider when available.

## How to compare with the paper

Table 4 URW Llama labels-only document values are Macro-F1 coarse **0.475**, sample-F1 coarse **0.425**, Macro-F1 fine **0.210**, sample-F1 fine **0.245**. They are **averaged across languages**, not an English-only target. This program does not output a misleading reproduction gap against those numbers. They are contextual references only; paragraph-union predictions also need to be distinguished from the paper's separate document configuration.

For a stronger reproduction: obtain authors' code/settings and original paragraph segmentation/gold; verify the exact model revision and codebook; match postprocessing, label universe and scorer; run all intended languages using the same evaluation procedure. Add language/domain support explicitly rather than translating text or relabeling the English subset as multilingual.

See [REPRODUCTION_PROTOCOL.md](REPRODUCTION_PROTOCOL.md) for the decision log and [STATUS.md](STATUS.md) for actual completion status. The old project's evidence/JSON pipeline, synthetic metrics and TF-IDF baseline are not used as PolyNarrative replication results.
