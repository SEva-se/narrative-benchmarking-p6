# Running and using the code

Run all commands from the `narrative-benchmark-en` project root. Python 3.10+ is required, with no external runtime dependencies. Start with the demo and tests before making API requests.

## 1. Installation check

```powershell
python --version
python -m narrative_bench --help
python -m unittest discover -s tests -v
```

Installing through pip is optional. If you need the console script, use `python -m pip install -e .`, which may require access to build dependencies. The standard `python -m narrative_bench` commands avoid installation.

## 2. Complete offline demonstration

```powershell
python -m narrative_bench validate --data data/demo/records.jsonl --taxonomy data/demo/taxonomy.json
python -m narrative_bench run --data data/demo/records.jsonl --taxonomy data/demo/taxonomy.json --config configs/demo.json --variant zero --output results/demo/my-zero
python -m narrative_bench run --data data/demo/records.jsonl --taxonomy data/demo/taxonomy.json --config configs/demo.json --variant few --output results/demo/my-few
python -m narrative_bench baseline --data data/demo/records.jsonl --taxonomy data/demo/taxonomy.json --output results/demo/my-baseline
python -m narrative_bench evaluate --data data/demo/records.jsonl --taxonomy data/demo/taxonomy.json --run-dir results/demo/my-zero
python -m narrative_bench evaluate --data data/demo/records.jsonl --taxonomy data/demo/taxonomy.json --run-dir results/demo/my-few
python -m narrative_bench evaluate --data data/demo/records.jsonl --taxonomy data/demo/taxonomy.json --run-dir results/demo/my-baseline
python -m narrative_bench compare --runs results/demo/my-zero results/demo/my-few results/demo/my-baseline --output results/demo/my-comparison.csv
```

Open report.html in each directory. Inspect errors.csv: the science-museum example deliberately tests category transfer based on a keyword. Compare text, gold and predicted. Complete error_type and analyst_note in your own words. Demo results do not measure LLM performance. The teaching keyword provider deliberately ignores few-shot content, so its zero/few predictions match.

## 3. Preparing research data

Create `data/research` and obtain a permitted copy of the selected corpus. Copy and complete the provenance template before conversion. Verify which release files correspond to train/test in the paper: the authors describe a special mapping between shared-task releases and paper splits. Do not infer that mapping from a ZIP filename alone.

`import-csv` accepts **normalized** CSV, not original corpus files. `data/templates/research_records.csv` supplies the header. Example structure:

```csv
id,article_id,text,split,language,dataset_kind,labels_json,context,source_url,publication_date
article12-p3,article12,"Target paragraph text",train,en,research,"[""science""]",,,
article13-p1,article13,"Another target paragraph",test,en,research,[],context if predeclared,,
```

These are structural examples, not real research observations. `labels_json` is a JSON list of IDs present in your codebook. An empty field becomes null, meaning unannotated. Use `[]` for an annotated negative example.

Create `data/research/taxonomy.json` from the actual codebook. The draft template contains coarse climate categories only; verify definitions, mapping and Other handling. The demo taxonomy is unsuitable for comparison with published PolyNarrative results.

```powershell
python -m narrative_bench import-csv --input data/research/normalized.csv --taxonomy data/research/taxonomy.json --output data/research/records.jsonl
python -m narrative_bench validate --data data/research/records.jsonl --taxonomy data/research/taxonomy.json
```

If there is no official split, assign entire articles to train/dev/test using an external reproducible script or table and retain the rule and seed. The package does not implement automatic stratified group splitting. Do not claim support for an uninspected original file format.

## 4. API configuration

Copy `configs/api.example.json` to `configs/model-a.local.json`. Set:

- the exact model ID available to the account;
- the full HTTPS endpoint, including `/chat/completions`;
- the environment-variable name holding the key;
- a supported output-token cap (`max_completion_tokens` or `max_tokens`, only one);
- `response_format` if supported, or omit it otherwise;
- supported temperature/reasoning_effort settings if needed;
- input/output/cached-input prices per million tokens, with source URL and date;
- maximum API attempts and delay between records.

The Chat Completions contract was checked against official OpenAI documentation:
https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create.
JSON mode: https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat.
Another compatible API may support only some fields. This adapter does not implement the native Anthropic Messages API. Verify a new provider with one request first.

Set the key **locally**, outside configuration files and Git. To enter it without displaying it in PowerShell:

```powershell
$secureApiKey = Read-Host 'API key' -AsSecureString
$env:NARRATIVE_API_KEY = [System.Net.NetworkCredential]::new('', $secureApiKey).Password
```

The key resides in the current session's environment and is read only before a live request. Do not send it in chat. Set a provider monetary limit before a large run. `max_api_calls` does not enforce an exact dollar cap.

## 5. Development-set smoke test

```powershell
python -m narrative_bench run --data data/research/records.jsonl --taxonomy data/research/taxonomy.json --config configs/model-a.local.json --split dev --variant zero --limit 1 --output results/research/model-a-smoke --execute-api
python -m narrative_bench evaluate --data data/research/records.jsonl --taxonomy data/research/taxonomy.json --run-dir results/research/model-a-smoke --bootstrap 0
```

Inspect raw_output, validity, response_id, resolved_model, usage and finish_reason. Reconcile with provider billing. One example tests integration, not quality. Before full evaluation, conduct a small pilot on predefined development articles.

For few-shot prompting, populate `example_ids` in the configuration. IDs must refer to train records. Each selected training record must contain evidence with label_id, an exact quote and an explanation. CSV import does not create these annotations automatically: add them to JSONL manually and verify them.

## 6. Full benchmark

After freezing the protocol, use a separate directory for each configuration. Repeat for A/B/C and zero/few:

```powershell
python -m narrative_bench run --data data/research/records.jsonl --taxonomy data/research/taxonomy.json --config configs/model-a.local.json --split test --variant zero --output results/research/model-a-zero-test --execute-api
python -m narrative_bench evaluate --data data/research/records.jsonl --taxonomy data/research/taxonomy.json --run-dir results/research/model-a-zero-test
```

Repeating the identical command with identical data, code and configuration resumes the run, skipping saved predictions. Changing configuration, source code, taxonomy, seed or selected data requires a new directory. The call cap includes previous attempts in that directory. To increase the cap after a pilot, create a new final run rather than calling it a resume.

Invalid outputs remain invalid and are not automatically requested again. If a run stops after a potentially billed request, inspect attempts.jsonl and billing. The runner blocks automatic resumption of such uncommitted attempts. After an informed decision, create a separate recovery run and account explicitly for the previous spending. Automatic recovery merging is not implemented.

## 7. Blinded annotation of the new sample

Prepare a complete JSONL snapshot containing existing train/dev/test and new articles with `split=new`, `labels=null`. Do not add it to an existing run: changing data changes its hash.

```powershell
python -m narrative_bench annotation-export --data data/research/records-with-new.jsonl --taxonomy data/research/taxonomy.json --split new --output data/research/annotator-a.csv
```

Make an independent copy for annotator B before filling A. Enter IDs in `labels_json`, not category names. Use uncertain and note for later discussion. Compute agreement **before** joint editing:

```powershell
python -m narrative_bench agreement --a data/research/annotator-a.csv --b data/research/annotator-b.csv --taxonomy data/research/taxonomy.json --output results/research/agreement.json
python -m narrative_bench annotation-import --data data/research/records-with-new.jsonl --taxonomy data/research/taxonomy.json --split new --sheet data/research/adjudicated.csv --output data/research/final-records.jsonl
```

Use the final snapshot and separate new run directories for directly comparing test and new in the study. Existing demo/report snapshots remain unchanged. Under a whole-dataset hash, adding a split also requires a new manifest; this is an intentional limitation of strict versioning.

## 8. Run-directory contents

| File | Purpose |
|---|---|
| manifest.json | Versions, hashes, key-free configuration and selected IDs |
| attempts.jsonl | Start and outcome of each HTTP attempt, with usage |
| predictions.jsonl | Raw output, validated prediction, errors and latency |
| metrics.json | Machine-readable metrics |
| report.html | Browser-readable report |
| errors.csv | Manual error-analysis material |
| evidence_review.csv | Material for blinded semantic-support review |

Evaluation regenerates review/error CSVs. Save completed human reviews under different filenames to avoid overwriting them. Outputs containing raw source text may be subject to corpus access terms.

## 9. Troubleshooting

**Unknown label.** Check IDs and mapping; do not expand the taxonomy solely because a model invented a category.

**Cross-split leakage.** Return all paragraphs from an article to one split and inspect duplicates and syndicated copies.

**HTTP 400.** Check supported parameters and the exact model ID. HTTP error-body text is deliberately not logged to avoid exposing sensitive information; consult provider documentation or its dashboard.

**HTTP 401/403.** Verify the environment variable and key permissions. The runner does not print the key.

**HTTP 429.** Reduce the request rate and inspect quota. Limited retries are recorded in the ledger.

**Unknown cost.** Prices, usage or cache rates are missing, or an attempt's cost is uncertain. Reconcile billing instead of replacing unknown with zero.

**Invalid quote / JSON.** This is a model outcome. Inspect raw_output and errors. Improve prompts on dev under a new configuration version.

**run.lock.** Confirm that the process has stopped. Removing a stale lock does not resolve uncommitted ledger entries; inspect those separately.
