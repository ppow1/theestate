from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from estate.core.codex_cli_capability_discovery import discover_codex_cli_capabilities


def test_codex_cli_capability_discovery_no_probe_writes_artifacts(tmp_path):
    root = Path.cwd()
    payload = discover_codex_cli_capabilities(root=root, probe=False)

    assert payload["provider_id"] == "codex.execution.cli"
    assert payload["metadata_only"] is True
    assert payload["does_not_submit_prompts"] is True
    assert "repository_implementation" in payload["capabilities_from_catalog"]
    assert payload["polling_policy"]["status_polling"] == "manual_or_disabled_until_billing_delta_verified"
    assert (root / "runtime/providers/codex_cli_capability_discovery.json").exists()
    assert (root / "operations/engineering_capacity/codex_cli_capability_discovery.md").exists()


def test_codex_cli_capability_discovery_cli_json_no_probe():
    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "codex-cli-capability-discovery", "--no-probe", "--json"],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        env={"PYTHONPATH": str(Path.cwd() / "src")},
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout)
    assert payload["provider_id"] == "codex.execution.cli"
    assert payload["provider_registry_policy"].startswith("Codex CLI identity")
