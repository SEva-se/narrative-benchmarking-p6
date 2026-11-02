$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    python -m narrative_bench validate --data data/demo/records.jsonl --taxonomy data/demo/taxonomy.json
    if ($LASTEXITCODE -ne 0) { throw 'Validation failed' }
    python -m narrative_bench run --data data/demo/records.jsonl --taxonomy data/demo/taxonomy.json --config configs/demo.json --output results/demo/zero
    if ($LASTEXITCODE -ne 0) { throw 'Demo run failed' }
    python -m narrative_bench evaluate --data data/demo/records.jsonl --taxonomy data/demo/taxonomy.json --run-dir results/demo/zero
    if ($LASTEXITCODE -ne 0) { throw 'Demo evaluation failed' }
    Write-Output 'Open results/demo/zero/report.html. All data and scores are synthetic teaching fixtures.'
} finally { Pop-Location }
