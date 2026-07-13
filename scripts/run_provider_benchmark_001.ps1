CLS
$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src"
python -m estate.core.provider_benchmark run-local benchmark-001 --model qwen2.5-coder:7b
"Provider Benchmark 001 local run submitted. Review experiments/provider_benchmarks/benchmark-001 for evidence." | Set-Clipboard
