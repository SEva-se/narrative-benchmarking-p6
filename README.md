# Narrative Benchmarking P6

**A working software and research preparation package for university Project 6.**

Author: Vsevolod Drabych and project group. Package version: 0.1.0. Original package prepared on 1 November 2026; English edition prepared on 2 November 2026.

**Proposed first practical experiment (8 November 2026): [Reproduce PolyNarrative Experiment](experiments/reproduce-polynarrative/README.md).** This separate package implements a narrowed, labels-only English URW experiment derived from the paper. It includes an importer, original-format prompting, API runner, scoring and 23 offline tests. User-supplied development data/gold have now been prepared privately; an actual model run is still pending. Read its reproduction protocol for differences from the paper. The original materials below remain an earlier project proposal and synthetic demonstration, not a completed replication or a finalized team decision.

The project compares API-based models on paragraph-level narrative classification and extraction of supporting source evidence. Evaluation covers quality, output usability, cost and latency. Frozen configurations are subsequently tested on a separately collected and independently annotated sample.

**Status:** the implementation works on teaching data, including an HTTP adapter tested against a local server. Real API experiments and PolyNarrative validation have not yet been performed. Data access, exact models, prices and budget still need to be confirmed. The presentation describes the proposed study and implemented method, rather than completed empirical findings.

## What to open first

1. [Getting started and materials map](docs/00_START_HERE_EN.md).
2. [Literature review](docs/01_LITERATURE_REVIEW_EN.md).
3. [Project proposal](docs/02_PROJECT_PROPOSAL_EN.md).
4. [Detailed research protocol](docs/03_RESEARCH_PROTOCOL_EN.md).
5. [Execution runbook](docs/04_RUNBOOK_EN.md).
6. [Annotation and evidence-review guidelines](docs/05_ANNOTATION_GUIDE_EN.md).
7. [Course and defense preparation](docs/06_STUDY_AND_DEFENSE_EN.md).
8. [Final report scaffold](docs/07_REPORT_TEMPLATE_EN.md).
9. [References](docs/08_REFERENCES.md).
10. [Editable presentation](presentation/narrative_benchmark_project_en.pptx) and [slide text with speaker notes](presentation/SLIDES_AND_NOTES.md).

## Five-minute start

Python 3.10 or later is required. No third-party runtime packages are needed. Open a terminal **in this directory**, containing README.md and narrative_bench.

```powershell
python --version
python -m narrative_bench validate --data data/demo/records.jsonl --taxonomy data/demo/taxonomy.json
python -m narrative_bench run --data data/demo/records.jsonl --taxonomy data/demo/taxonomy.json --config configs/demo.json --output results/demo/zero
python -m narrative_bench evaluate --data data/demo/records.jsonl --taxonomy data/demo/taxonomy.json --run-dir results/demo/zero
```

Open `results/demo/zero/report.html` in a browser. It is a local report and needs no server. On Linux/macOS, replace `python` with `python3` if necessary. Alternatively, run `powershell -File scripts/demo.ps1` or `sh scripts/demo.sh`.

**All 35 records in data/demo are fictional.** The demonstration provider uses fixed keywords, is not an LLM and makes no API requests. Identical zero-shot and few-shot results are expected: this fixture does not interpret the prompt. These scores must not be used as scientific findings.

Prepared report examples are available in `results/demo/test-zero`, `test-few`, `test-baseline` and the corresponding `new-*` directories. The demo `new` split is also synthetic and does not satisfy the course requirement for a new real dataset.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Tests cover metrics on examples that can be checked by hand, split leakage, exclusion of evaluation gold labels from requests, strict quote validation, run resumption, costs of invalid outputs, incomplete runs, and HTTP transport through a local test server. No real API tokens are required. If an environment blocks localhost, run the HTTP test in an ordinary local terminal.

## Moving to a real experiment

See the runbook for details. Obtain a permitted dataset copy, convert it to normalized JSONL, replace the teaching taxonomy with a verified codebook, and create a local configuration. The API key is read only from an environment variable. Real requests require the explicit `--execute-api` flag.

`configs/api.example.json` contains an example endpoint and an unfilled model ID. It deliberately cannot run without editing. Parameter compatibility depends on the selected model and provider. The adapter implements Chat Completions rather than native Responses or Anthropic Messages APIs.

Neither raw PolyNarrative data nor original scientific paper PDFs are included in the archive. The original English study brief is included. Sources and access procedures are listed in the documentation. Do not add API keys, billing records or real research data to a public Git repository.

## Architecture

| Module | Responsibility |
|---|---|
| data.py | JSON/JSONL contracts, hashes and split-overlap checks |
| prompts.py | Versioned prompt and training-only few-shot examples |
| engine.py | HTTP adapter, request cap, attempt ledger and resumption |
| baseline.py | CPU-only TF-IDF nearest-centroid baseline |
| metrics.py | Multilabel metrics, article-cluster bootstrap and annotator agreement |
| evaluate.py | Accounting for all selected records, HTML reports, error and evidence CSVs |
| annotations.py | Blinded annotation sheets, imports and agreement |
| cli.py | Commands for execution, evaluation and comparison |

Implementation limitations and fair-comparison rules are documented in the protocol. In particular, automatic quotation checking establishes source membership; humans assess whether the quotation actually supports the category.


## English study brief and complete download

- [Four-paper study brief, English PDF, 14 pages](docs/literature/four_papers_study_brief_en.pdf): the four kickoff papers, methods, results, limitations, metrics and discussion preparation.
- [Complete English project ZIP](downloads/narrative_benchmark_complete_en.zip): code, documentation, editable presentation, demonstration reports and the English study brief.

The PDF is an original study summary, not a redistribution of the four source papers. Real API findings and independent real-data annotation remain pending, as documented throughout the project.
