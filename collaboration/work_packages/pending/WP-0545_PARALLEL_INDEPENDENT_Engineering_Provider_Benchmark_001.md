# WP-0545 — Engineering Provider Benchmark Harness

Status: Pending  
Execution Mode: SERIES  
Owner: Office of Chief Architect / Engineering Capacity  
Execution Target: Codex  
Classification: Estate Internal  
Priority: High

## Objective

Implement a production-grade Engineering Provider Benchmark Harness that can run the same bounded software-engineering assignment through multiple execution providers, collect measured evidence, validate each result independently, and produce a normalized comparison report.

This is not a one-off benchmark script and not an MVP. It is a reusable Estate engineering asset for evaluating cloud and local execution providers over time.

The first commissioned benchmark must compare:

1. Codex cloud;
2. one local Ollama coding model running on the RTX-4090 workstation;
3. a Chief Architect reference implementation supplied separately after the other executors finalize.

## Existing Evidence and Constraints

Verified current facts:

- The Estate repository is available locally at `A:\theestate`.
- Ollama is installed and currently exposes at least:
  - `qwen2.5-coder:7b`;
  - `qwen3:8b`;
  - `llama3.1:8b`;
  - `llama3:8b`;
  - `llama3.2:3b`.
- The first local benchmark model is `qwen2.5-coder:7b` unless the Steward explicitly selects another installed model.
- Codex capacity is metered per business seat.
- Three Codex business seats are actively monitored for the current workflow.
- Refreshed Codex Analytics currently exposes weekly usage and does not display the previously visible five-hour card.

The harness must not assume that browser-profile count equals active seat count.

## Required Architecture

Implement the benchmark harness as an Estate-integrated but operationally isolated subsystem.

Required components:

1. Benchmark specification schema.
2. Executor adapter contract.
3. Codex executor adapter.
4. Ollama executor adapter.
5. Manual/reference-result import adapter.
6. Isolated workspace manager.
7. Execution recorder.
8. Test and validation runner.
9. Metric normalization runtime.
10. Comparative scoring and report generator.
11. CLI surface.
12. Documentation, fixtures, migrations, tests, and completion receipt.

Reuse existing Estate provider, capacity, health, routing, execution-session, workspace, validation, evidence, and audit infrastructure through adapters wherever those systems are available.

Do not create a second provider registry, scheduler, dispatch authority, execution-session authority, validation authority, or credential store.

## Canonical Benchmark Specification

Define a versioned benchmark specification containing at least:

- benchmark ID and version;
- title and purpose;
- task specification;
- permitted languages and dependencies;
- required files;
- visible tests;
- hidden-review criteria;
- time limit;
- provider/model eligibility;
- isolation rules;
- environment requirements;
- required metrics;
- acceptance criteria;
- scoring weights;
- source and provenance references.

The benchmark specification must be immutable after a run begins. Revisions create a new version.

## Executor Adapter Contract

Every executor adapter must expose a common contract for:

- availability discovery;
- provider and model identity;
- execution preparation;
- prompt or assignment submission;
- streaming or final response capture;
- start and end timestamps;
- wall-clock timing;
- token metrics when exposed;
- provider-native duration metrics when exposed;
- output collection;
- cancellation;
- timeout handling;
- failure classification;
- cleanup;
- raw evidence preservation.

Unavailable metrics must be recorded as `null` with an explanation. They must never be invented or estimated as measured facts.

## Ollama Adapter Requirements

The Ollama adapter must:

- discover installed models using the local Ollama API or `ollama list`;
- select `qwen2.5-coder:7b` by default when installed;
- allow an explicit installed-model override;
- never download a model without explicit Steward authorization;
- call the local Ollama service directly;
- capture `prompt_eval_count`, `eval_count`, `total_duration`, `load_duration`, `prompt_eval_duration`, and `eval_duration` when returned;
- preserve the raw request and response;
- support deterministic settings, including temperature zero where supported;
- fail clearly when Ollama is unavailable or the requested model is missing;
- run fully locally without external API calls.

## Codex Adapter Requirements

The Codex adapter must:

- consume a governed work package or benchmark specification;
- operate in a dedicated branch and isolated result directory;
- record Codex seat identity as an Estate seat reference without storing credentials;
- preserve branch, commit, pull-request, command, timing, test, and result evidence;
- ingest provider-reported token or usage metrics when available;
- record unavailable metrics honestly;
- support import of a completed Codex result when direct launch is not available to the harness;
- prevent access to other executors' result directories until the run is finalized.

The initial implementation may use a governed import workflow for Codex results if direct Codex execution cannot be safely automated with current repository infrastructure. The import must still validate provenance, branch, commit, and result integrity.

## Workspace and Isolation Requirements

Each benchmark run must create immutable executor-specific result locations under:

```text
experiments/provider_benchmarks/<benchmark_id>/<run_id>/
  codex/
  local/
  chief_architect/
  comparison/
```

Requirements:

- deterministic run IDs or collision-safe generated IDs;
- no executor may inspect another executor's implementation before finalization;
- existing output must never be silently overwritten;
- partial and failed runs must be preserved;
- source task, prompts, raw responses, generated files, commands, logs, and metadata must be retained;
- path traversal and writes outside the assigned result directory must be rejected;
- reruns create new run records rather than mutating completed evidence.

## Execution Metadata

Every executor result must produce versioned machine-readable metadata containing at least:

- benchmark ID and version;
- run ID;
- executor type;
- provider;
- model;
- Estate seat reference when applicable;
- environment and relevant software versions;
- start and end timestamps;
- wall-clock seconds;
- provider-native timing values;
- prompt, output, and total tokens when available;
- number of generation attempts;
- number of repair attempts;
- commands run;
- files produced;
- file and line counts;
- tests passed and failed;
- validation status;
- exit codes;
- failure classification;
- unavailable metrics and reasons;
- provenance and evidence references.

## Validation Runtime

The harness must run the same visible tests against each executor result from its isolated directory.

It must also support independent hidden-review tests or static review criteria that are not disclosed to executors before completion.

Validation must include:

- required-file checks;
- syntax or compile checks;
- unit tests;
- CLI or integration tests when specified;
- dependency-policy checks;
- determinism checks;
- input-mutation checks where relevant;
- security and path-safety checks;
- output-schema validation;
- raw-evidence completeness.

A result that fails validation remains preserved and comparable. The harness must not erase or silently repair it.

## Comparison and Scoring

Produce both JSON and Markdown comparison reports.

Compare at least:

- functional correctness;
- visible tests passed and failed;
- hidden-review findings;
- determinism;
- code clarity;
- maintainability;
- error quality;
- security and boundary compliance;
- elapsed time;
- prompt, output, and total tokens;
- estimated marginal monetary cost, clearly labeled as estimate;
- repair attempts;
- files and lines produced;
- notable implementation differences;
- provider and model limitations;
- confidence and missing evidence.

Do not rank by speed or token count alone. A faster incorrect result is not superior.

Scoring weights must be specified in the benchmark definition and included in the final report. Raw measurements must remain visible beside any aggregate score.

## CLI Requirements

Provide an Estate CLI surface with commands equivalent to:

```text
provider-benchmark list
provider-benchmark inspect BENCHMARK_ID
provider-benchmark discover-providers
provider-benchmark run-local BENCHMARK_ID --model MODEL
provider-benchmark prepare-codex BENCHMARK_ID
provider-benchmark import-codex BENCHMARK_ID RESULT_PATH
provider-benchmark import-reference BENCHMARK_ID RESULT_PATH
provider-benchmark validate BENCHMARK_ID RUN_ID
provider-benchmark compare BENCHMARK_ID RUN_ID
provider-benchmark report BENCHMARK_ID RUN_ID
```

PowerShell intended for the Steward must begin with `CLS` and, where practical, copy a concise result summary to the clipboard.

## First Commissioned Benchmark

Ship Benchmark 001 as a fixture and commissioning test.

### Benchmark 001 — Deterministic Dependency Batcher

Implement a Python 3.11 standard-library module named `dependency_batcher.py` exposing:

```python
class DependencyBatchError(ValueError):
    pass


def plan_batches(tasks: list[dict], max_parallel: int) -> list[list[str]]:
    ...
```

Each task contains:

- `id`: non-empty unique string;
- `duration`: positive integer;
- `priority`: integer, higher values first;
- `depends_on`: list of task IDs.

Scheduling rules:

1. A task enters a batch only when every dependency completed in a prior batch.
2. A batch contains at most `max_parallel` tasks.
3. Eligible tasks sort by:
   - higher priority;
   - shorter duration;
   - lexicographically smaller ID.
4. Return task IDs only.
5. Input must not be mutated.
6. Output must be deterministic.

Validation must reject malformed input, Boolean-as-integer values, duplicate IDs, unknown dependencies, self-dependencies, and direct or indirect cycles.

The fixture must include a CLI and tests for successful and invalid input behavior using Python's standard library only.

## Production Requirements

- Python 3.11 compatibility.
- Windows-first operation under `A:\theestate`.
- No required third-party Python package for the core harness unless an existing Estate dependency already provides the capability and its use is justified.
- Versioned schemas and forward-compatible migrations.
- Atomic metadata writes.
- Crash-safe preservation of partial runs.
- Concurrent-run isolation.
- Structured errors.
- Complete audit trail.
- No credential storage.
- No automatic model downloads.
- No silent fallback to cloud execution.
- No fabricated timing, token, cost, or success metrics.

## Required Tests

Implement unit, integration, recovery, concurrency, security, and Windows end-to-end tests covering at least:

1. benchmark schema validation and versioning;
2. installed Ollama model discovery;
3. explicit model selection and missing-model failure;
4. raw Ollama metric capture;
5. executor isolation and path traversal rejection;
6. timeout, cancellation, malformed response, and unavailable-provider behavior;
7. preservation of failed and partial runs;
8. metadata validation and atomic writes;
9. Codex governed import and provenance validation;
10. reference-result import;
11. identical visible-test execution across providers;
12. hidden-review execution after finalization;
13. comparison with missing metrics;
14. deterministic report generation;
15. repeat runs without overwriting prior evidence;
16. Benchmark 001 end-to-end local execution using an installed model or a deterministic mocked Ollama response in CI.

## Deliverables

- benchmark and run schemas;
- executor adapter contract;
- Ollama adapter;
- Codex governed-import adapter and direct adapter only if current infrastructure safely supports it;
- reference-result import adapter;
- workspace and isolation runtime;
- execution and metric recorder;
- validation runtime;
- comparison and reporting runtime;
- Estate CLI integration;
- Benchmark 001 fixture;
- Steward-facing PowerShell launcher beginning with `CLS`;
- unit, integration, recovery, concurrency, security, and Windows end-to-end tests;
- documentation and operator runbook;
- migration/backfill support;
- validation recipe;
- completion receipt.

## Constraints

- Do not modify production provider-routing decisions as part of this package.
- Do not create a new scheduler, dispatch system, provider registry, execution authority, validation authority, or credential store.
- Do not expose one executor's result to another before finalization.
- Do not make network calls for local execution beyond the loopback Ollama service.
- Do not download models automatically.
- Do not claim benchmark completion until real or explicitly mocked commissioning evidence is recorded.
- Do not delete failed benchmark evidence.

## Completion Standard

WP-0545 is complete only when the Estate can define a versioned benchmark once, execute or governably import multiple provider results into isolated workspaces, capture truthful timing and token evidence, run identical validation, preserve failures, and generate reproducible JSON and Markdown comparisons.

Completion additionally requires Benchmark 001 to be commissioned through the harness with:

- a verified Codex result or governed Codex-result import;
- a local `qwen2.5-coder:7b` result on the RTX-4090 workstation, unless the Steward explicitly selects another installed model;
- a separately imported Chief Architect reference result;
- a final comparison report that states where the local worker matches, exceeds, or falls short of Codex and the reference implementation.