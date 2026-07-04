"""Work-package validation execution engine."""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

REPORTS_DIR = Path("operations/validation/reports")
RUNTIME_DIR = Path("runtime/validation/work_packages")
CAPTURE_DIR = RUNTIME_DIR / "captures"


def _root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_wp(work_package_id: str) -> str:
    value = work_package_id.strip().upper()
    if not re.fullmatch(r"WP-\d{4,}", value):
        return re.sub(r"[^A-Za-z0-9_-]", "_", value)[:80] or "UNKNOWN"
    return value


def _git(root: Path, *args: str) -> str | None:
    try:
        return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False).stdout.strip() or None
    except OSError:
        return None


def _cmd(text: str, *, required: bool = True, continue_on_failure: bool | None = None) -> dict[str, Any]:
    classification = "required" if required else "observational"
    return {
        "command": text,
        "classification": classification,
        "required": required,
        "continue_on_failure": (not required) if continue_on_failure is None else continue_on_failure,
    }


VALIDATION_RECIPES: dict[str, dict[str, Any]] = {
    "WP-0056": {
        "recipe_id": "wp-0056-notification-center-workspace",
        "title": "WP-0056 — Notification Center Workspace",
        "description": "Notification Center Workspace validation.",
        "required_checks": ["Steward command center renders", "Notification Center is discoverable"],
        "observational_checks": ["Palette command availability"],
        "expected_artifacts": ["operations/validation/reports/WP-0056_validation.md", "runtime/validation/work_packages/WP-0056_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main steward-command-center --json'),
            _cmd('python -m estate.cli.main global-search "Notification Center" --json'),
            _cmd('python -m estate.cli.main palette-command notification-center --json', required=False),
        ],
    },
    "WP-0057": {
        "recipe_id": "wp-0057-voice-integration-framework",
        "title": "WP-0057 — Voice Integration Framework",
        "description": "Voice Integration Framework validation.",
        "required_checks": ["Steward command center renders", "Assignment queue renders"],
        "observational_checks": ["Voice Integration search result"],
        "expected_artifacts": ["operations/validation/reports/WP-0057_validation.md", "runtime/validation/work_packages/WP-0057_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main steward-command-center --json'),
            _cmd('python -m estate.cli.main assignment-queue --json'),
            _cmd('python -m estate.cli.main global-search "Voice Integration" --json', required=False),
        ],
    },
    "WP-0058": {
        "recipe_id": "wp-0058-steward-recall-operations-view",
        "title": "WP-0058 — Steward Recall Operations View",
        "description": "Steward Recall Operations View validation.",
        "required_checks": ["Steward command center renders", "Steward Recall is discoverable"],
        "observational_checks": ["Palette command availability"],
        "expected_artifacts": ["operations/validation/reports/WP-0058_validation.md", "runtime/validation/work_packages/WP-0058_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main steward-command-center --json'),
            _cmd('python -m estate.cli.main global-search "Steward Recall" --json'),
            _cmd('python -m estate.cli.main palette-command steward-recall --json', required=False),
        ],
    },
    "WP-0059": {
        "recipe_id": "wp-0059-resident-conversations-workspace",
        "title": "WP-0059 — Resident Conversations Workspace",
        "description": "Resident Conversations Workspace validation.",
        "required_checks": ["Steward command center renders", "Resident Conversations is discoverable"],
        "observational_checks": ["Palette command availability"],
        "expected_artifacts": ["operations/validation/reports/WP-0059_validation.md", "runtime/validation/work_packages/WP-0059_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main steward-command-center --json'),
            _cmd('python -m estate.cli.main global-search "Resident Conversations" --json'),
            _cmd('python -m estate.cli.main palette-command resident-conversations --json', required=False),
        ],
    },
    "WP-0060": {
        "recipe_id": "wp-0060-estate-interaction-services-adapter-registry",
        "title": "WP-0060 — Estate Interaction Services and Adapter Registry",
        "description": "Estate Interaction Services and Adapter Registry validation.",
        "required_checks": ["Steward command center renders", "Assignment queue renders", "Interaction Services Adapter Registry is discoverable"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0060_validation.md", "runtime/validation/work_packages/WP-0060_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main steward-command-center --json'),
            _cmd('python -m estate.cli.main assignment-queue --json'),
            _cmd('python -m estate.cli.main global-search "Interaction Services Adapter Registry" --json'),
        ],
    },
    "WP-0074": {
        "recipe_id": "wp-0074-validation-handoff-artifact-workflow",
        "title": "WP-0074 — Validation Handoff Artifact Workflow",
        "description": "Validation handoff artifact workflow validation.",
        "required_checks": ["Handoff workflow renders", "Observations render", "Metrics dashboard renders"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0074_validation.md", "runtime/validation/work_packages/WP-0074_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main validation-handoff-artifact-workflow --json'),
            _cmd('python -m estate.cli.main validation-observations --json'),
            _cmd('python -m estate.cli.main validation-metrics-dashboard --json'),
        ],
    },
    "WP-0079": {
        "recipe_id": "wp-0079-validation-execution-engine-self-check",
        "title": "WP-0079 — Validation Project Continuation self-check",
        "description": "Validation Execution Engine self-check.",
        "required_checks": ["Validation observations render", "Notification Center palette command renders"],
        "observational_checks": ["Steward Recall palette command renders"],
        "expected_artifacts": ["operations/validation/reports/WP-0079_validation.md", "runtime/validation/work_packages/WP-0079_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main validation-observations --json'),
            _cmd('python -m estate.cli.main palette-command notification-center --json'),
            _cmd('python -m estate.cli.main palette-command steward-recall --json', required=False),
        ],
    },
}


def get_validation_recipe(work_package_id: str) -> dict[str, Any] | None:
    return VALIDATION_RECIPES.get(_safe_wp(work_package_id))


def _excerpt(text: str, limit: int = 1200) -> str:
    text = text or ""
    return text if len(text) <= limit else text[:limit] + "\n...[truncated]"


def _write_capture(root: Path, validation_id: str, index: int, stream: str, text: str) -> str | None:
    if not text:
        return None
    path = root / CAPTURE_DIR / validation_id / f"command_{index:02d}_{stream}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", errors="replace")
    return str(path.relative_to(root)).replace("\\", "/")


def _run_command(root: Path, validation_id: str, index: int, spec: dict[str, Any]) -> dict[str, Any]:
    command = str(spec["command"])
    started = datetime.now(timezone.utc)
    env = os.environ.copy()
    src_path = str(root / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else src_path
    try:
        proc = subprocess.run(command, cwd=root, shell=True, text=True, capture_output=True, env=env, check=False)
        exit_code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except OSError as exc:
        exit_code, stdout, stderr = 127, "", str(exc)
    completed = datetime.now(timezone.utc)
    classification = str(spec.get("classification") or ("required" if spec.get("required", True) else "observational"))
    status = "passed" if exit_code == 0 else ("failed" if classification == "required" else "finding")
    stdout_path = _write_capture(root, validation_id, index, "stdout", stdout)
    stderr_path = _write_capture(root, validation_id, index, "stderr", stderr)
    result = {
        "command": command,
        "classification": classification,
        "required": classification == "required",
        "started_at": started.isoformat(timespec="seconds"),
        "completed_at": completed.isoformat(timespec="seconds"),
        "duration_seconds": round((completed - started).total_seconds(), 3),
        "exit_code": exit_code,
        "status": status,
    }
    if stdout_path: result["stdout_path"] = stdout_path
    else: result["stdout_excerpt"] = ""
    if stderr_path: result["stderr_path"] = stderr_path
    else: result["stderr_excerpt"] = ""
    return result


def format_validation_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Work Package Validation Report — {payload['work_package_id']}", "",
        f"- Timestamp: {payload['generated_at']}",
        f"- Work package ID: {payload['work_package_id']}",
        f"- Local branch: {payload.get('git_branch') or 'unknown'}",
        f"- Git commit: {payload.get('git_commit_before') or 'unknown'}",
        f"- Validation status: {payload['validation_status']}",
        f"- Recipe used: {payload.get('recipe_id') or 'none'}",
        f"- Recipe title: {payload.get('recipe_title') or 'none'}", "",
        "## Commands Run",
    ]
    for row in payload.get("command_results", []):
        lines.append(f"- `{row['command']}` — {row['status']} (exit {row['exit_code']}, {row['duration_seconds']}s)")
    lines += ["- None." if not payload.get("command_results") else "", "## Findings"]
    lines += [f"- {f}" for f in payload.get("findings", [])] or ["- None."]
    lines += ["", "## Warnings"] + ([f"- {w}" for w in payload.get("warnings", [])] or ["- None."])
    lines += ["", "## Failures"] + ([f"- {f}" for f in payload.get("failures", [])] or ["- None."])
    lines += ["", "## Generated Artifacts"] + [f"- `{p}`" for p in payload.get("files_written", [])]
    lines += ["", "## Reviewer Recommendation", payload.get("reviewer_recommendation", "Review generated artifacts.")]
    return "\n".join(line for line in lines if line is not None)


def validate_work_package(work_package_id: str, root: str | Path | None = None, write: bool = True) -> dict[str, Any]:
    base = _root(root)
    wp = _safe_wp(work_package_id)
    generated_at = _now()
    validation_id = f"{wp}_{generated_at.replace(':','').replace('+','Z')}"
    recipe = get_validation_recipe(wp)
    warnings: list[str] = []
    failures: list[str] = []
    findings: list[str] = []
    results: list[dict[str, Any]] = []
    if recipe is None:
        warnings.append(f"No validation recipe is registered for {wp}.")
        status = "no_recipe"
        recipe_id = None
    else:
        recipe_id = str(recipe["recipe_id"])
        for idx, spec in enumerate(recipe.get("commands", []), start=1):
            result = _run_command(base, validation_id, idx, spec)
            results.append(result)
            if result["exit_code"] != 0:
                msg = f"Command failed: {result['command']} (exit {result['exit_code']})"
                classification = result.get("classification", "required")
                if classification == "required": failures.append(msg)
                else: findings.append(msg)
                if result.get("classification") == "required" and not spec.get("continue_on_failure", recipe.get("continue_on_failure", False)):
                    break
        status = "failed" if failures else ("passed_with_findings" if findings or warnings else "passed")
    payload: dict[str, Any] = {
        "work_package_id": wp,
        "validation_id": validation_id,
        "generated_at": generated_at,
        "git_branch": _git(base, "branch", "--show-current"),
        "git_commit_before": _git(base, "rev-parse", "HEAD"),
        "git_commit_after": None,
        "validation_status": status,
        "recipe_id": recipe_id,
        "recipe_title": recipe.get("title") if recipe else None,
        "commands_run": [r["command"] for r in results],
        "command_results": results,
        "stdout_summary": f"Captured stdout for {sum(1 for r in results if r.get('stdout_path'))} command(s).",
        "stderr_summary": f"Captured stderr for {sum(1 for r in results if r.get('stderr_path'))} command(s).",
        "files_written": [],
        "warnings": warnings,
        "failures": failures,
        "findings": findings,
        "reviewer_recommendation": "Chief Architect should review failures before approval." if failures else "Ready for Chief Architect validation artifact review.",
    }
    if write:
        md_rel = REPORTS_DIR / f"{wp}_validation.md"
        json_rel = RUNTIME_DIR / f"{wp}_validation.json"
        latest_rel = RUNTIME_DIR / "latest.json"
        payload["files_written"] = [str(md_rel).replace("\\", "/"), str(json_rel).replace("\\", "/"), str(latest_rel).replace("\\", "/")]
        (base / md_rel).parent.mkdir(parents=True, exist_ok=True)
        (base / json_rel).parent.mkdir(parents=True, exist_ok=True)
        (base / md_rel).write_text(format_validation_markdown(payload) + "\n", encoding="utf-8")
        (base / json_rel).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        latest = {"work_package_id": wp, "validation_id": validation_id, "generated_at": generated_at, "json_report": str(json_rel).replace("\\", "/"), "markdown_report": str(md_rel).replace("\\", "/"), "validation_status": status}
        (base / latest_rel).write_text(json.dumps(latest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
