# Canonical Provider Benchmark Packet — benchmark-001 v1.0.0

Schema: provider-benchmark-canonical-packet.v1

## Public specification
{
  "acceptance_criteria": [
    "visible tests pass",
    "evidence preserved",
    "missing metrics are null with reason"
  ],
  "benchmark_id": "benchmark-001",
  "cli_contract": [
    "CLI may run python -m unittest test_dependency_batcher_visible.py in the executor directory.",
    "Executor must produce dependency_batcher.py at the executor directory root.",
    "No network, package installation, or non-standard-library dependency is required."
  ],
  "environment_requirements": [
    "Python 3.11",
    "Windows-first A:\\theestate compatible",
    "Ollama loopback only"
  ],
  "hidden_review_criteria": [
    "clarity",
    "maintainability",
    "security",
    "boundary compliance"
  ],
  "isolation_rules": [
    "executor-specific directories only",
    "no overwrite",
    "path traversal rejected"
  ],
  "permitted_dependencies": [
    "python standard library only"
  ],
  "permitted_languages": [
    "Python 3.11"
  ],
  "provider_model_eligibility": {
    "codex_import_allowed": true,
    "ollama_default_model": "qwen2.5-coder:7b",
    "reference_import_allowed": true
  },
  "purpose": "Compare providers on bounded Python task.",
  "required_files": [
    "dependency_batcher.py"
  ],
  "required_metrics": [
    "wall_clock_seconds",
    "prompt_tokens",
    "output_tokens",
    "total_tokens",
    "total_duration",
    "load_duration",
    "prompt_eval_duration",
    "eval_duration"
  ],
  "schema_version": "provider-benchmark-spec.v1",
  "scoring_weights": {
    "evidence_quality": 10,
    "functional_correctness": 50,
    "maintainability": 10,
    "security": 10,
    "validation": 20
  },
  "source_provenance": [
    "WP-0545_PARALLEL_INDEPENDENT_Engineering_Provider_Benchmark_001.md"
  ],
  "task": {
    "function_signature": "def plan_batches(tasks: list[dict], max_parallel: int) -> list[list[str]]",
    "prompt": "Implement dependency_batcher.py exposing DependencyBatchError and plan_batches with deterministic dependency batching, validation, immutability, and standard library only.",
    "scheduling_rules": [
      "Only schedule a task after all dependencies are completed in previous batches.",
      "At most max_parallel tasks per batch.",
      "Within each batch order eligible tasks by descending priority, ascending duration, then ascending task id.",
      "Do not mutate the input tasks.",
      "Detect cycles and unknown dependencies."
    ],
    "task_schema": {
      "return": "ordered list of batches; each batch is a list of task ids",
      "task": {
        "depends_on": "list of task id strings",
        "duration": "positive int (bool rejected)",
        "id": "non-empty str",
        "priority": "int (bool rejected)"
      }
    },
    "validation_rules": [
      "Raise DependencyBatchError for invalid task collection, task records, duplicate ids, self dependencies, unknown dependencies, cycles, and invalid max_parallel.",
      "Reject bool values where integers are required.",
      "Use deterministic output for equivalent inputs."
    ]
  },
  "time_limit_seconds": 600,
  "title": "Benchmark 001 — Deterministic Dependency Batcher",
  "version": "1.0.0",
  "visible_tests": [
    "success, invalid input, determinism, immutability"
  ]
}

## Exact task schema
{
  "return": "ordered list of batches; each batch is a list of task ids",
  "task": {
    "depends_on": "list of task id strings",
    "duration": "positive int (bool rejected)",
    "id": "non-empty str",
    "priority": "int (bool rejected)"
  }
}

## Function signature
def plan_batches(tasks: list[dict], max_parallel: int) -> list[list[str]]

## Scheduling rules
- Only schedule a task after all dependencies are completed in previous batches.
- At most max_parallel tasks per batch.
- Within each batch order eligible tasks by descending priority, ascending duration, then ascending task id.
- Do not mutate the input tasks.
- Detect cycles and unknown dependencies.

## Validation rules
- Raise DependencyBatchError for invalid task collection, task records, duplicate ids, self dependencies, unknown dependencies, cycles, and invalid max_parallel.
- Reject bool values where integers are required.
- Use deterministic output for equivalent inputs.

## CLI contract
- CLI may run python -m unittest test_dependency_batcher_visible.py in the executor directory.
- Executor must produce dependency_batcher.py at the executor directory root.
- No network, package installation, or non-standard-library dependency is required.

## Dependency constraints
- python standard library only

## Required files
- dependency_batcher.py

## Visible tests
```python
import copy, unittest
from dependency_batcher import plan_batches, DependencyBatchError
class DependencyBatcherTests(unittest.TestCase):
    def test_success_order_and_immutability(self):
        tasks=[{"id":"a","duration":5,"priority":1,"depends_on":[]},{"id":"b","duration":1,"priority":3,"depends_on":["a"]},{"id":"c","duration":1,"priority":3,"depends_on":["a"]},{"id":"d","duration":2,"priority":2,"depends_on":[]}]
        original=copy.deepcopy(tasks); self.assertEqual(plan_batches(tasks,2), [["d","a"],["b","c"]]); self.assertEqual(tasks, original)
    def test_rejects_invalid(self):
        bad=[([{"id":"a","duration":True,"priority":1,"depends_on":[]}],1),([{"id":"a","duration":1,"priority":1,"depends_on":["z"]}],1),([{"id":"a","duration":1,"priority":1,"depends_on":["a"]}],1),([{"id":"a","duration":1,"priority":1,"depends_on":["b"]},{"id":"b","duration":1,"priority":1,"depends_on":["a"]}],1)]
        for tasks, mp in bad:
            with self.assertRaises(DependencyBatchError): plan_batches(tasks,mp)
    def test_deterministic(self):
        tasks=[{"id":x,"duration":1,"priority":1,"depends_on":[]} for x in ["b","a","c"]]; self.assertEqual(plan_batches(tasks,10), [["a","b","c"]])
if __name__ == "__main__": unittest.main()
```

## Isolation rules
- executor-specific directories only
- no overwrite
- path traversal rejected

## Acceptance criteria
- visible tests pass
- evidence preserved
- missing metrics are null with reason

## Hidden-review boundary
Hidden-review tests and criteria beyond the public criteria above are not included in this packet and must not be exposed to executors before finalization.
