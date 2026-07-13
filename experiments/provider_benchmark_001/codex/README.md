# Codex Provider Benchmark 001

This directory contains the Codex implementation for WP-0545, the deterministic dependency batcher benchmark.

## Files

- `dependency_batcher.py` — Python 3.11 standard-library implementation and CLI.
- `test_dependency_batcher.py` — `unittest` coverage for scheduling, validation, immutability, and CLI behavior.
- `run_metadata.json` — measured run metadata for this Codex execution.

## Usage

```bash
python dependency_batcher.py INPUT.json [--max-parallel N]
```

Input may be an object containing `max_parallel` and `tasks`, or a bare task array when `--max-parallel` is supplied.

Successful output is compact JSON, for example:

```json
{"batches":[["A","B"],["C"]]}
```

Invalid input writes a concise error to stderr and exits non-zero without an ordinary validation traceback.

## Test

From this directory run:

```bash
python -m unittest -v test_dependency_batcher.py
```
