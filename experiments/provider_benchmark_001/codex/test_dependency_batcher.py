import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from dependency_batcher import DependencyBatchError, plan_batches


class DependencyBatcherTests(unittest.TestCase):
    def test_deterministic_priority_duration_id_ordering(self):
        tasks = [
            {"id": "B", "duration": 2, "priority": 10, "depends_on": []},
            {"id": "A", "duration": 2, "priority": 10, "depends_on": []},
            {"id": "C", "duration": 1, "priority": 10, "depends_on": []},
            {"id": "D", "duration": 1, "priority": 5, "depends_on": []},
        ]
        self.assertEqual(plan_batches(tasks, 4), [["C", "A", "B", "D"]])
        self.assertEqual(plan_batches(tasks, 2), [["C", "A"], ["B", "D"]])

    def test_dependency_sequencing(self):
        tasks = [
            {"id": "build", "duration": 3, "priority": 1, "depends_on": ["lint", "test"]},
            {"id": "lint", "duration": 1, "priority": 1, "depends_on": []},
            {"id": "test", "duration": 2, "priority": 1, "depends_on": []},
            {"id": "deploy", "duration": 1, "priority": 99, "depends_on": ["build"]},
        ]
        self.assertEqual(plan_batches(tasks, 3), [["lint", "test"], ["build"], ["deploy"]])

    def test_max_parallel_enforcement(self):
        tasks = [{"id": str(i), "duration": 1, "priority": 1, "depends_on": []} for i in range(5)]
        batches = plan_batches(tasks, 2)
        self.assertEqual(batches, [["0", "1"], ["2", "3"], ["4"]])
        self.assertTrue(all(len(batch) <= 2 for batch in batches))

    def test_unknown_dependency(self):
        with self.assertRaisesRegex(DependencyBatchError, "unknown"):
            plan_batches([{"id": "A", "duration": 1, "priority": 1, "depends_on": ["Z"]}], 1)

    def test_duplicate_ids(self):
        tasks = [
            {"id": "A", "duration": 1, "priority": 1, "depends_on": []},
            {"id": "A", "duration": 2, "priority": 1, "depends_on": []},
        ]
        with self.assertRaisesRegex(DependencyBatchError, "duplicate"):
            plan_batches(tasks, 1)

    def test_self_dependency(self):
        with self.assertRaisesRegex(DependencyBatchError, "itself"):
            plan_batches([{"id": "A", "duration": 1, "priority": 1, "depends_on": ["A"]}], 1)

    def test_direct_and_indirect_cycles(self):
        with self.assertRaisesRegex(DependencyBatchError, "cycle"):
            plan_batches([
                {"id": "A", "duration": 1, "priority": 1, "depends_on": ["B"]},
                {"id": "B", "duration": 1, "priority": 1, "depends_on": ["A"]},
            ], 1)
        with self.assertRaisesRegex(DependencyBatchError, "cycle"):
            plan_batches([
                {"id": "A", "duration": 1, "priority": 1, "depends_on": ["C"]},
                {"id": "B", "duration": 1, "priority": 1, "depends_on": ["A"]},
                {"id": "C", "duration": 1, "priority": 1, "depends_on": ["B"]},
            ], 1)

    def test_malformed_fields_and_boolean_integer_rejection(self):
        bad_cases = [
            ("not-list", 1),
            (["not-dict"], 1),
            ([{"duration": 1, "priority": 1, "depends_on": []}], 1),
            ([{"id": "", "duration": 1, "priority": 1, "depends_on": []}], 1),
            ([{"id": 3, "duration": 1, "priority": 1, "depends_on": []}], 1),
            ([{"id": "A", "duration": 0, "priority": 1, "depends_on": []}], 1),
            ([{"id": "A", "duration": True, "priority": 1, "depends_on": []}], 1),
            ([{"id": "A", "duration": 1, "priority": False, "depends_on": []}], 1),
            ([{"id": "A", "duration": 1, "priority": 1, "depends_on": [1]}], 1),
            ([{"id": "A", "duration": 1, "priority": 1, "depends_on": "B"}], 1),
            ([{"id": "A", "duration": 1, "priority": 1, "depends_on": []}], True),
            ([{"id": "A", "duration": 1, "priority": 1, "depends_on": []}], 0),
        ]
        for tasks, max_parallel in bad_cases:
            with self.subTest(tasks=tasks, max_parallel=max_parallel):
                with self.assertRaises(DependencyBatchError):
                    plan_batches(tasks, max_parallel)

    def test_input_immutability(self):
        tasks = [{"id": "A", "duration": 1, "priority": 1, "depends_on": []}]
        original = copy.deepcopy(tasks)
        plan_batches(tasks, 1)
        self.assertEqual(tasks, original)

    def test_cli_success_and_validation_failure(self):
        script = Path(__file__).with_name("dependency_batcher.py")
        with tempfile.TemporaryDirectory() as tmpdir:
            valid = Path(tmpdir) / "valid.json"
            valid.write_text(json.dumps({"max_parallel": 1, "tasks": [
                {"id": "A", "duration": 1, "priority": 1, "depends_on": []},
                {"id": "B", "duration": 1, "priority": 2, "depends_on": ["A"]},
            ]}), encoding="utf-8")
            result = subprocess.run([sys.executable, str(script), str(valid)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), {"batches": [["A"], ["B"]]})
            self.assertEqual(result.stderr, "")

            invalid = Path(tmpdir) / "invalid.json"
            invalid.write_text(json.dumps([{"id": "A", "duration": 1, "priority": 1, "depends_on": ["Z"]}]), encoding="utf-8")
            bad = subprocess.run([sys.executable, str(script), str(invalid), "--max-parallel", "1"], text=True, capture_output=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("error:", bad.stderr)
            self.assertNotIn("Traceback", bad.stderr)
            self.assertEqual(bad.stdout, "")


if __name__ == "__main__":
    unittest.main()
