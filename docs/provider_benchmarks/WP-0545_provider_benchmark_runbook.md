# WP-0545 Provider Benchmark Harness Runbook

The harness is an Estate-integrated, operationally isolated subsystem for running or governably importing engineering-provider benchmark results. It stores immutable run evidence under `experiments/provider_benchmarks/<benchmark_id>/<run_id>/` with executor-specific `codex`, `local`, `chief_architect`, and `comparison` directories.

Core commands:

```text
provider-benchmark list
provider-benchmark inspect benchmark-001
provider-benchmark discover-providers
provider-benchmark run-local benchmark-001 --model qwen2.5-coder:7b
provider-benchmark prepare-codex benchmark-001
provider-benchmark import-codex benchmark-001 RESULT_PATH --run-id RUN_ID
provider-benchmark import-reference benchmark-001 RESULT_PATH --run-id RUN_ID
provider-benchmark validate benchmark-001 RUN_ID --executor local
provider-benchmark compare benchmark-001 RUN_ID
provider-benchmark report benchmark-001 RUN_ID
```

Missing provider metrics are recorded as `null` with explanations in `unavailable_metrics`. The Ollama adapter never downloads models and uses only the loopback Ollama API or `ollama list` for discovery. Codex and Chief Architect results are supported through governed import with provenance capture.
