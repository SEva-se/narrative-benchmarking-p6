#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python3 -m narrative_bench validate --data data/demo/records.jsonl --taxonomy data/demo/taxonomy.json
python3 -m narrative_bench run --data data/demo/records.jsonl --taxonomy data/demo/taxonomy.json --config configs/demo.json --output results/demo/zero
python3 -m narrative_bench evaluate --data data/demo/records.jsonl --taxonomy data/demo/taxonomy.json --run-dir results/demo/zero
printf '%s\n' 'Open results/demo/zero/report.html. All data and scores are synthetic teaching fixtures.'
