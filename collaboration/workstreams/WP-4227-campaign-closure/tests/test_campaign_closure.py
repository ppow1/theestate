"""Repository-level invariants for the WP-4220--WP-4226 advisory chain."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[4]
WORKSTREAMS = REPO / "collaboration" / "workstreams"
PACKAGES = (
    WORKSTREAMS / "WP-4218",
    WORKSTREAMS / "WP-4219",
    WORKSTREAMS / "WP-4222",
    WORKSTREAMS / "WP-4223-recommendation-engine",
    WORKSTREAMS / "WP-4224-decision-ledger",
    WORKSTREAMS / "WP-4225-analytics",
    WORKSTREAMS / "WP-4226",
)


def test_schema_identifiers_are_unique_and_versioned() -> None:
    identifiers: dict[str, Path] = {}
    for package in PACKAGES:
        for path in sorted((package / "schemas").glob("*.json")):
            document = json.loads(path.read_text(encoding="utf-8"))
            identifier = document["$id"]
            assert "v1" in identifier and "_v1" in path.name, path
            assert identifier not in identifiers, (path, identifiers.get(identifier))
            identifiers[identifier] = path
    assert len(identifiers) == 22


def test_implementation_has_no_execution_authority_imports() -> None:
    forbidden = {"git", "subprocess", "scheduler", "dispatcher", "assignment_queue"}
    implementation_files = [
        path
        for package in PACKAGES
        for path in package.rglob("*.py")
        if "tests" not in path.parts
    ] + [REPO / "src/estate/core/engineering_campaign_replay.py"]
    for path in implementation_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        assert imported.isdisjoint(forbidden), (path, imported & forbidden)


def test_diagnostic_clis_publish_help() -> None:
    commands = (
        [sys.executable, str(PACKAGES[0] / "reconcile.py"), "--help"],
        [sys.executable, str(PACKAGES[1] / "dashboard_cli.py"), "--help"],
        [sys.executable, str(PACKAGES[2] / "integrate.py"), "--help"],
        [sys.executable, str(PACKAGES[3] / "recommend.py"), "--help"],
        [sys.executable, str(PACKAGES[4] / "ledger_cli.py"), "--help"],
        [sys.executable, str(PACKAGES[5] / "analytics_cli.py"), "--help"],
        [sys.executable, "-m", "estate.cli.engineering_campaign_replay", "--help"],
    )
    for command in commands:
        result = subprocess.run(
            command,
            cwd=REPO,
            env={"PYTHONPATH": str(REPO / "src")},
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, (command, result.stderr)
        assert "usage:" in result.stdout.lower(), command
