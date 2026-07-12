"""Codex CLI capability discovery and polling policy artifacts.

Discovery is intentionally metadata-only. It may inspect local executable
presence and help/version output, but it never submits prompts, executes work,
or assumes status polling is free.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.provider_catalog import load_provider_catalog

RUNTIME_JSON = Path("runtime/providers/codex_cli_capability_discovery.json")
RUNTIME_MD = Path("runtime/providers/codex_cli_capability_discovery.md")
OFFICE_HANDOFF_MD = Path("operations/engineering_capacity/codex_cli_capability_discovery.md")
CODEX_PROVIDER_ID = "codex.execution.cli"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _run_metadata_command(command: list[str], timeout_seconds: int) -> dict[str, Any]:
    try:
        proc = subprocess.run(command, text=True, capture_output=True, timeout=timeout_seconds, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"command": " ".join(command), "executed": False, "error": str(exc)}
    return {
        "command": " ".join(command),
        "executed": True,
        "returncode": proc.returncode,
        "stdout_preview": proc.stdout[:500],
        "stderr_preview": proc.stderr[:500],
        "stdout_bytes": len(proc.stdout.encode("utf-8")),
        "stderr_bytes": len(proc.stderr.encode("utf-8")),
    }


def discover_codex_cli_capabilities(*, root: str | Path | None = None, probe: bool = True, timeout_seconds: int = 10, write: bool = True) -> dict[str, Any]:
    """Discover local Codex CLI metadata and publish a conservative policy."""
    root_path = _root(root)
    catalog = load_provider_catalog(root_path / "config" / "providers" / "catalog.json")
    provider = catalog.get_provider(CODEX_PROVIDER_ID)
    codex_path = shutil.which("codex")
    observations: list[dict[str, Any]] = []

    if codex_path and probe:
        for command in ([codex_path, "--version"], [codex_path, "--help"], [codex_path, "exec", "--help"]):
            observations.append(_run_metadata_command(command, timeout_seconds))
    elif not codex_path:
        observations.append({"executed": False, "reason": "codex executable not found on PATH"})
    else:
        observations.append({"executed": False, "reason": "probe disabled"})

    metadata_probe_succeeded = any(obs.get("executed") and obs.get("returncode") == 0 for obs in observations)
    installed_state = "metadata_discovered" if metadata_probe_succeeded else "not_discovered"
    polling_policy = {
        "status_polling": "manual_or_disabled_until_billing_delta_verified",
        "automated_interval_seconds": None,
        "allowed_automated_probes": ["--version", "--help", "exec --help"],
        "disallowed_automated_probes": ["prompt submission", "work execution", "frequent /status polling"],
        "rationale": "The Estate has no authoritative local counter proving that Codex CLI status checks do not consume quota, tokens, messages, or other limited capacity.",
    }

    payload = {
        "version": 1,
        "generated_at": utc_now_iso(),
        "provider_id": provider.provider_id,
        "catalog_descriptor": provider.to_dict(office_safe=True),
        "codex_cli_path": codex_path,
        "installed_state": installed_state,
        "capabilities_from_catalog": provider.capabilities,
        "metadata_only": True,
        "does_not_submit_prompts": True,
        "does_not_execute_provider_work": True,
        "observations": observations,
        "polling_policy": polling_policy,
        "provider_registry_policy": "Codex CLI identity and advertised capabilities are owned by config/providers/catalog.json; discovery artifacts may report local metadata but must not mutate catalog status automatically.",
    }

    if write:
        for rel, text in ((RUNTIME_JSON, json.dumps(payload, indent=2, sort_keys=True) + "\n"), (RUNTIME_MD, format_codex_cli_capability_discovery(payload)), (OFFICE_HANDOFF_MD, format_codex_cli_capability_discovery(payload))):
            path = root_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    return payload


def format_codex_cli_capability_discovery(payload: dict[str, Any]) -> str:
    policy = payload.get("polling_policy") or {}
    lines = [
        "# Codex CLI Capability Discovery",
        "",
        f"Generated: {payload.get('generated_at')}",
        f"Provider ID: {payload.get('provider_id')}",
        f"Codex CLI path: {payload.get('codex_cli_path') or 'not found'}",
        f"Installed state: {payload.get('installed_state')}",
        "",
        "## Advertised Capabilities",
    ]
    for capability in payload.get("capabilities_from_catalog") or []:
        lines.append(f"- {capability}")
    lines.extend([
        "",
        "## Polling Policy",
        f"- Status polling: {policy.get('status_polling')}",
        f"- Automated interval seconds: {policy.get('automated_interval_seconds')}",
        f"- Rationale: {policy.get('rationale')}",
        "",
        "## Boundary",
        "- Metadata-only discovery; no prompts are submitted and no provider work is executed.",
        f"- Registry policy: {payload.get('provider_registry_policy')}",
        "",
        "## Observations",
    ])
    for obs in payload.get("observations") or []:
        lines.append(f"- {obs}")
    return "\n".join(lines).rstrip() + "\n"
