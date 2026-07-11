"""Codex CLI status cost characterization.

This module records evidence about whether status polling is safe. It never
invokes model prompts, dispatches work, or assumes status checks are free.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

RUNTIME_JSON = Path("runtime/engineering_capacity/codex_status_cost_characterization.json")
RUNTIME_MD = Path("runtime/engineering_capacity/codex_status_cost_characterization.md")
OFFICE_HANDOFF_MD = Path("operations/engineering_capacity/codex_status_cost_characterization.md")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def characterize_codex_status_cost(*, root: str | Path | None = None, probe: bool = True, timeout_seconds: int = 10, write: bool = True) -> dict[str, Any]:
    root_path = _root(root)
    codex_path = shutil.which("codex")
    observations: list[dict[str, Any]] = []
    if codex_path and probe:
        # Prefer help/version style metadata probes only. Do not run prompts or live work.
        for command in ([codex_path, "--version"], [codex_path, "status", "--help"]):
            try:
                proc = subprocess.run(command, text=True, capture_output=True, timeout=timeout_seconds, check=False)
                observations.append({
                    "command": " ".join(command[1:]),
                    "returncode": proc.returncode,
                    "stdout_bytes": len(proc.stdout.encode("utf-8")),
                    "stderr_bytes": len(proc.stderr.encode("utf-8")),
                    "executed": True,
                })
            except (OSError, subprocess.TimeoutExpired) as exc:
                observations.append({"command": " ".join(command[1:]), "executed": False, "error": str(exc)})
    elif not codex_path:
        observations.append({"executed": False, "reason": "codex executable not found on PATH"})
    else:
        observations.append({"executed": False, "reason": "probe disabled"})

    measured_billing_delta = None
    safe_polling_policy = "disabled_until_verified"
    recommendation = "Do not schedule frequent Codex CLI status polling until quota/token/message deltas can be measured before and after status queries."
    if codex_path and any(o.get("executed") for o in observations):
        recommendation = "Only metadata/help probes were executed; no billed quota delta source was available. Keep automated status polling disabled or manual/on-demand."

    payload = {
        "version": 1,
        "generated_at": utc_now_iso(),
        "constraints": {
            "advisory_only": True,
            "does_not_run_prompts": True,
            "does_not_dispatch_work": True,
            "assumes_status_is_not_free": True,
        },
        "codex_cli_path": codex_path,
        "observations": observations,
        "measured_billing_delta": measured_billing_delta,
        "safe_polling_policy": safe_polling_policy,
        "recommended_minimum_interval_seconds": None,
        "recommendation": recommendation,
        "evidence_gap": "No authoritative local counter for Codex quota, token, message, or billing deltas was available during characterization.",
    }
    if write:
        _write_json(root_path / RUNTIME_JSON, payload)
        text = format_codex_status_cost_characterization(payload)
        for rel in (RUNTIME_MD, OFFICE_HANDOFF_MD):
            path = root_path / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    return payload


def format_codex_status_cost_characterization(payload: dict[str, Any]) -> str:
    lines = [
        "# Codex CLI Status Cost Characterization",
        "",
        f"Generated: {payload.get('generated_at')}",
        "",
        "Advisory only: this characterization does not run prompts, dispatch work, or assume status polling is free.",
        "",
        f"- Codex CLI path: {payload.get('codex_cli_path') or 'not found'}",
        f"- Safe polling policy: {payload.get('safe_polling_policy')}",
        f"- Measured billing delta: {payload.get('measured_billing_delta')}",
        f"- Recommendation: {payload.get('recommendation')}",
        f"- Evidence gap: {payload.get('evidence_gap')}",
        "",
        "## Observations",
    ]
    for obs in payload.get("observations") or []:
        lines.append(f"- {obs}")
    return "\n".join(lines).rstrip() + "\n"
