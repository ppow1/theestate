# WP-0545 — Engineering Provider Benchmark 001: Deterministic Dependency Batcher

Status: Pending  
Execution Mode: PARALLEL-INDEPENDENT  
Owner: Office of Chief Architect / Engineering Capacity  
Execution Target: Codex, Local AI Worker, Chief Architect Reference Implementation  
Classification: Estate Internal  
Priority: High

## Objective

Run one controlled medium-complexity software-writing benchmark against three execution paths using the same specification and tests:

1. Codex cloud;
2. one local AI coding worker on the RTX-4090 workstation;
3. Chief Architect reference implementation.

The benchmark measures functional correctness, implementation quality, elapsed time, token usage where available, repair cycles, and operational cost.

## Task

Implement a Python 3.11 standard-library module named `dependency_batcher.py`.

The module must expose:

```python
class DependencyBatchError(ValueError):
    pass


def plan_batches(tasks: list[dict], max_parallel: int) -> list[list[str]]:
    ...
```

Each task object contains:

- `id`: non-empty unique string;
- `duration`: positive integer;
- `priority`: integer, where larger values run first;
- `depends_on`: list of task IDs.

`plan_batches` must return deterministic execution batches. All tasks in one batch are considered to run concurrently and complete before the next batch begins.

## Scheduling Rules

1. A task may enter a batch only when every dependency completed in a prior batch.
2. A batch may contain at most `max_parallel` tasks.
3. Among currently eligible tasks, choose in this order:
   - higher `priority` first;
   - shorter `duration` first;
   - lexicographically smaller `id` first.
4. Return only task IDs in the chosen order.
5. The same input must always produce the same output.
6. Do not mutate caller-provided task objects or lists.

## Validation Rules

Raise `DependencyBatchError` with a useful message when:

- `max_parallel` is not a positive integer;
- the task list is malformed;
- a task ID is missing, empty, non-string, or duplicated;
- duration is not a positive integer;
- priority is not an integer;
- `depends_on` is not a list of strings;
- a dependency refers to an unknown task;
- a task depends on itself;
- the dependency graph contains a cycle.

Boolean values must not be accepted as integers for `duration`, `priority`, or `max_parallel`.

## CLI

Support:

```text
python dependency_batcher.py INPUT.json [--max-parallel N]
```

Input JSON may be either:

```json
{"max_parallel": 2, "tasks": [...]}
```

or a bare task array when `--max-parallel` is supplied.

Successful output must be JSON written to stdout:

```json
{"batches": [["A", "B"], ["C"]]}
```

Validation or input errors must:

- write a concise message to stderr;
- return a non-zero exit code;
- not emit a Python traceback during ordinary invalid-input handling.

## Required Files

Create only within the assigned benchmark result directory:

- `dependency_batcher.py`
- `test_dependency_batcher.py`
- `README.md`
- `run_metadata.json`

`run_metadata.json` must record:

- executor name and model if known;
- start and end timestamps;
- elapsed seconds;
- input tokens, output tokens, and total tokens when available, otherwise `null`;
- number of implementation or repair attempts;
- commands run;
- tests passed and failed;
- notes on unavailable metrics.

## Minimum Tests

Tests must cover:

1. deterministic priority/duration/ID ordering;
2. dependency sequencing;
3. `max_parallel` enforcement;
4. unknown dependencies;
5. duplicate IDs;
6. self-dependency;
7. direct and indirect cycles;
8. malformed fields and Boolean-as-integer rejection;
9. input immutability;
10. CLI success and CLI validation failure.

Use only Python's standard library, including `unittest`.

## Benchmark Isolation

Each executor must write to a separate directory:

- `experiments/provider_benchmark_001/codex/`
- `experiments/provider_benchmark_001/local/`
- `experiments/provider_benchmark_001/chief_architect/`

Executors must not inspect another executor's implementation before their own result is finalized.

## Acceptance Tests

1. `python -m unittest -v test_dependency_batcher.py` passes from the executor result directory.
2. The implementation satisfies all scheduling and validation rules.
3. The CLI produces deterministic JSON and clean error behavior.
4. No third-party dependencies are introduced.
5. Run metadata is complete and distinguishes measured values from unavailable values.
6. No executor output overwrites another executor's files.

## Comparative Evaluation

After all three runs, compare:

- passed/failed tests;
- hidden edge-case review;
- correctness and determinism;
- code clarity and maintainability;
- error quality;
- elapsed time;
- token usage;
- estimated marginal monetary cost;
- repair attempts;
- file and line counts;
- notable design differences.

Do not rank by speed alone. A faster incorrect result is not superior.

## Constraints

- Do not use this benchmark to modify production Estate runtimes.
- Do not permit cross-executor copying.
- Do not infer unavailable token counts.
- Do not claim local execution occurred until the local command has actually completed and produced artifacts.

## Completion Standard

WP-0545 is complete only when all three isolated implementations and their metadata exist, the same tests and independent review have been applied, and a source-lined comparison report states where the local worker matches, exceeds, or falls short of Codex and the Chief Architect reference.