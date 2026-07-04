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

    "WP-0112": {
        "recipe_id": "wp-0112-parallel-workstream-standard",
        "title": "WP-0112 — Parallel Workstream Isolation and Install Handoff Standard",
        "description": "Validates the durable parallel workstream standard, transition boundary, install manifest example, and local-first number allocation ledger.",
        "required_checks": ["Parallel standard document exists", "Transition boundary is explicit", "Install manifest example is parseable", "Number allocation ledger is parseable", "Completion receipt exists"],
        "observational_checks": ["Production readiness command remains locally executable"],
        "expected_artifacts": ["docs/operations/Parallel_Workstream_Isolation_and_Install_Handoff_Standard_v1.md", "collaboration/work_packages/work_package_range_ledger.json", "collaboration/workstreams/WP-0112/install_manifest.example.json", "operations/validation/reports/WP-0112_validation.md", "runtime/validation/work_packages/WP-0112_validation.json", "collaboration/work_packages/completions/WP-0112_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from pathlib import Path; p=Path('docs/operations/Parallel_Workstream_Isolation_and_Install_Handoff_Standard_v1.md'); t=p.read_text(); required=['SERIES','PARALLEL-STAGED','PARALLEL-INDEPENDENT','INSTALL-HANDOFF','WP-0097 through WP-0111','GitHub search','collaboration/workstreams/WP-XXXX/install_manifest.json']; missing=[x for x in required if x not in t]; missing += ['staged work is not installed work'] if 'staged work is not installed work' not in t.lower() else []; assert p.is_file() and not missing, missing\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('collaboration/work_packages/work_package_range_ledger.json').read_text()); assert data['ranges'] and 'GitHub search' in data['source_of_truth']; assert any(r['start']=='WP-6000' for r in data['ranges'])\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('collaboration/workstreams/WP-0112/install_manifest.example.json').read_text()); assert data['workstream_mode']=='PARALLEL-STAGED'; assert data['staged_work_is_installed'] is False; assert data['validation_commands']\""),
            _cmd("python -c \"from pathlib import Path; t=Path('docs/operations/Codex_Task_Template_Standard_v1.md').read_text(); required=['Parallel Workstream Compatibility Addendum','Workstream Mode','Conflict Surface','Install Manifest','Required Install Handoff']; missing=[x for x in required if x not in t]; assert not missing, missing\""),
            _cmd('python -m estate.cli.main workstream validate --id WP-0112 --json'),
            _cmd('python -m estate.cli.main work-package-ranges --json'),
            _cmd('python -m estate.cli.main validation-production-readiness --json', required=False),
        ],
    },

    "WP-0015": {
        "recipe_id": "wp-0015-message-acknowledgement-reply-flow",
        "title": "WP-0015 — Message Acknowledgement + Reply Flow",
        "description": "Validates local collaboration acknowledgement and reply flow CLI surfaces.",
        "required_checks": ["Message acknowledgement command is available", "Message reply command is available"],
        "observational_checks": ["Message acknowledgement and reply flow is discoverable"],
        "expected_artifacts": ["operations/validation/reports/WP-0015_validation.md", "runtime/validation/work_packages/WP-0015_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main message-ack --help'),
            _cmd('python -m estate.cli.main message-reply --help'),
            _cmd('python -m estate.cli.main global-search "Message Acknowledgement" --json', required=False),
        ],
    },
    "WP-0019": {
        "recipe_id": "wp-0019-alfred-operational-activation",
        "title": "WP-0019 — Alfred Operational Activation",
        "description": "Validates read-only Alfred operational activation surfaces.",
        "required_checks": ["Alfred status renders", "Alfred operational briefing renders"],
        "observational_checks": ["Alfred artifacts listing renders"],
        "expected_artifacts": ["operations/validation/reports/WP-0019_validation.md", "runtime/validation/work_packages/WP-0019_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main alfred-status --json'),
            _cmd('python -m estate.cli.main alfred-operational-briefing --json'),
            _cmd('python -m estate.cli.main alfred-artifacts --json', required=False),
        ],
    },

    "WP-0020": {
        "recipe_id": "wp-0020-helen-hr-operational-onboarding",
        "title": "WP-0020 — Helen HR Operational Onboarding",
        "description": "Validates Helen's initial HR onboarding source artifacts and registry/mailbox resolution without granting additional authority.",
        "required_checks": ["Helen onboarding artifacts exist", "Helen personnel identity resolves", "Onboarding manifests remain valid"],
        "observational_checks": ["Helen HR onboarding is discoverable"],
        "expected_artifacts": ["operations/validation/reports/WP-0020_validation.md", "runtime/validation/work_packages/WP-0020_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from pathlib import Path; paths=['docs/onboarding/Helen_HR_Operational_Onboarding.md','docs/operations/helen/operating_brief.md','residents/helen.md','data/registry/personnel.json','data/registry/mailboxes.json']; missing=[p for p in paths if not Path(p).is_file()]; assert not missing, missing\""),
            _cmd("python -c \"from estate.core.personnel_identity import resolve_personnel_identity; r=resolve_personnel_identity('Helen'); assert r.get('resolved') and r.get('employee_id') == 6 and r.get('mailbox_id') == 6 and r.get('resident_id') == 'RES-000003', r\""),
            _cmd('python -m estate.cli.main onboarding-manifest-check --json'),
            _cmd('python -m estate.cli.main estate-search "Helen HR" --json', required=False),
        ],
    },
    "WP-0021": {
        "recipe_id": "wp-0021-personnel-identity-mailbox-resolver",
        "title": "WP-0021 — Personnel Identity + Mailbox Resolver",
        "description": "Validates personnel and mailbox resolver read-only surfaces.",
        "required_checks": ["Personnel resolver command is available", "Mailbox index renders"],
        "observational_checks": ["Worker inboxes render"],
        "expected_artifacts": ["operations/validation/reports/WP-0021_validation.md", "runtime/validation/work_packages/WP-0021_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main personnel-resolve --help'),
            _cmd('python -m estate.cli.main mailbox-index --json'),
            _cmd('python -m estate.cli.main worker-inboxes --json', required=False),
        ],
    },
    "WP-0027": {
        "recipe_id": "wp-0027-institutional-search-v1",
        "title": "WP-0027 — Institutional Search v1",
        "description": "Validates local institutional and global search surfaces.",
        "required_checks": ["Estate search returns JSON", "Global search returns JSON"],
        "observational_checks": ["Document registry renders"],
        "expected_artifacts": ["operations/validation/reports/WP-0027_validation.md", "runtime/validation/work_packages/WP-0027_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main estate-search "Institutional Search" --json'),
            _cmd('python -m estate.cli.main global-search "Institutional Search" --json'),
            _cmd('python -m estate.cli.main document-registry --json', required=False),
        ],
    },
    "WP-0029": {
        "recipe_id": "wp-0029-artifact-provenance-model",
        "title": "WP-0029 — Artifact Provenance Model",
        "description": "Validates local discoverability of artifact provenance documentation and registry surfaces.",
        "required_checks": ["Artifact provenance is discoverable", "Document registry renders"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0029_validation.md", "runtime/validation/work_packages/WP-0029_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main global-search "Artifact Provenance" --json'),
            _cmd('python -m estate.cli.main document-registry --json'),
        ],
    },
    "WP-0036": {
        "recipe_id": "wp-0036-gotify-adapter-v1",
        "title": "WP-0036 — Gotify Adapter v1",
        "description": "Validates non-sending notification router and Gotify command availability surfaces.",
        "required_checks": ["Notification router renders", "Gotify send-test command is available without sending"],
        "observational_checks": ["Gotify adapter is discoverable"],
        "expected_artifacts": ["operations/validation/reports/WP-0036_validation.md", "runtime/validation/work_packages/WP-0036_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main notification-router --json'),
            _cmd('python -m estate.cli.main gotify-send-test --help'),
            _cmd('python -m estate.cli.main global-search "Gotify" --json', required=False),
        ],
    },
    "WP-0037": {
        "recipe_id": "wp-0037-recall-audit-log-v1",
        "title": "WP-0037 — Recall Audit Log v1",
        "description": "Validates read-only audit surfaces for recall audit evidence.",
        "required_checks": ["Audit summary renders", "Audit command is available"],
        "observational_checks": ["Recall audit is discoverable"],
        "expected_artifacts": ["operations/validation/reports/WP-0037_validation.md", "runtime/validation/work_packages/WP-0037_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main audit-summary --json'),
            _cmd('python -m estate.cli.main audit --help'),
            _cmd('python -m estate.cli.main global-search "Recall Audit" --json', required=False),
        ],
    },
    "WP-0038": {
        "recipe_id": "wp-0038-morning-briefing-v1",
        "title": "WP-0038 — Morning Briefing v1",
        "description": "Validates morning briefing local report surfaces.",
        "required_checks": ["Morning briefing renders", "Alfred briefing renders"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0038_validation.md", "runtime/validation/work_packages/WP-0038_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main morning-briefing --json'),
            _cmd('python -m estate.cli.main alfred-briefing --json'),
        ],
    },

    "WP-0052": {
        "recipe_id": "wp-0052-daily-board-parking-lot-workspace",
        "title": "WP-0052 — Daily Board + Parking Lot Workspace",
        "description": "Validates Daily Board and operations board workspace surfaces.",
        "required_checks": ["Daily board renders", "Operations board renders"],
        "observational_checks": ["Daily Board is discoverable"],
        "expected_artifacts": ["operations/validation/reports/WP-0052_validation.md", "runtime/validation/work_packages/WP-0052_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [_cmd('python -m estate.cli.main daily-board --json'), _cmd('python -m estate.cli.main operations-board --json'), _cmd('python -m estate.cli.main global-search "Daily Board" --json', required=False)],
    },
    "WP-0053": {
        "recipe_id": "wp-0053-expansion-roadmap-workspace",
        "title": "WP-0053 — Expansion Roadmap Workspace",
        "description": "Validates local discoverability of Expansion Roadmap workspace artifacts.",
        "required_checks": ["Expansion Roadmap is discoverable", "Steward command center renders"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0053_validation.md", "runtime/validation/work_packages/WP-0053_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [_cmd('python -m estate.cli.main global-search "Expansion Roadmap" --json'), _cmd('python -m estate.cli.main steward-command-center --json')],
    },
    "WP-0065": {
        "recipe_id": "wp-0065-steward-presence-recall-state-machine",
        "title": "WP-0065 — Steward Presence + Recall State Machine",
        "description": "Validates Steward presence and recall state reporting surfaces.",
        "required_checks": ["Steward presence renders", "Steward recall palette command renders"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0065_validation.md", "runtime/validation/work_packages/WP-0065_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [_cmd('python -m estate.cli.main steward-presence --json'), _cmd('python -m estate.cli.main global-search "Steward Recall" --json')],
    },
    "WP-0066": {
        "recipe_id": "wp-0066-overnight-operations-morning-briefing-coordinator",
        "title": "WP-0066 — Overnight Operations + Morning Briefing Coordinator",
        "description": "Validates overnight operations and morning briefing read-only surfaces.",
        "required_checks": ["Morning briefing renders", "Alfred operational briefing renders"],
        "observational_checks": ["Autonomous operations audit renders"],
        "expected_artifacts": ["operations/validation/reports/WP-0066_validation.md", "runtime/validation/work_packages/WP-0066_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [_cmd('python -m estate.cli.main morning-briefing --json'), _cmd('python -m estate.cli.main alfred-operational-briefing --json'), _cmd('python -m estate.cli.main autonomous-operations-audit --json', required=False)],
    },
    "WP-0067": {
        "recipe_id": "wp-0067-autonomous-operations-control-loop",
        "title": "WP-0067 — Autonomous Operations Control Loop",
        "description": "Validates read-only autonomous operations control-loop surfaces.",
        "required_checks": ["Autonomous scheduler renders", "Worker runtime summary renders"],
        "observational_checks": ["Alfred status renders"],
        "expected_artifacts": ["operations/validation/reports/WP-0067_validation.md", "runtime/validation/work_packages/WP-0067_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [_cmd('python -m estate.cli.main autonomous-work-queue-scheduler --json'), _cmd('python -m estate.cli.main worker-runtime-summary --json'), _cmd('python -m estate.cli.main alfred-status --json', required=False)],
    },
    "WP-0068": {
        "recipe_id": "wp-0068-autonomous-operations-audit-trail",
        "title": "WP-0068 — Autonomous Operations Audit Trail",
        "description": "Validates autonomous operations audit trail reporting surfaces.",
        "required_checks": ["Autonomous operations audit renders", "Audit summary renders"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0068_validation.md", "runtime/validation/work_packages/WP-0068_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [_cmd('python -m estate.cli.main autonomous-operations-audit --json'), _cmd('python -m estate.cli.main audit-summary --json')],
    },
    "WP-0070": {
        "recipe_id": "wp-0070-validation-observation-log",
        "title": "WP-0070 — Validation Observation Log",
        "description": "Validates validation observation log reporting surfaces.",
        "required_checks": ["Validation observations render"],
        "observational_checks": ["Validation metrics dashboard renders"],
        "expected_artifacts": ["operations/validation/reports/WP-0070_validation.md", "runtime/validation/work_packages/WP-0070_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [_cmd('python -m estate.cli.main validation-observations --json'), _cmd('python -m estate.cli.main validation-metrics-dashboard --json', required=False)],
    },
    "WP-0080": {
        "recipe_id": "wp-0080-helen-employee-onboarding-orchestrator",
        "title": "WP-0080 — Helen Employee Onboarding Orchestrator",
        "description": "Validates safe Helen onboarding manifest and command availability surfaces without onboarding a real person.",
        "required_checks": ["Onboarding manifest check renders", "Helen onboarding command is available"],
        "observational_checks": ["Helen onboarding is discoverable"],
        "expected_artifacts": ["operations/validation/reports/WP-0080_validation.md", "runtime/validation/work_packages/WP-0080_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [_cmd('python -m estate.cli.main onboarding-manifest-check --json'), _cmd('python -m estate.cli.main helen-onboard --help'), _cmd('python -m estate.cli.main global-search "Helen" --json', required=False)],
    },
    "WP-0081": {
        "recipe_id": "wp-0081-estate-service-catalog",
        "title": "WP-0081 — Estate Service Catalog",
        "description": "Validates Estate service catalog and adjacent service registry surfaces.",
        "required_checks": ["Estate service catalog renders", "Services list renders"],
        "observational_checks": ["Service readiness renders"],
        "expected_artifacts": ["operations/validation/reports/WP-0081_validation.md", "runtime/validation/work_packages/WP-0081_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [_cmd('python -m estate.cli.main estate-service-catalog --json'), _cmd('python -m estate.cli.main services --json'), _cmd('python -m estate.cli.main service-readiness --json', required=False)],
    },
    "WP-0085": {
        "recipe_id": "wp-0085-operator-activity-stream",
        "title": "WP-0085 — Operator Activity Stream",
        "description": "Validates Operator Activity Stream and adjacent Operations Center activity surfaces.",
        "required_checks": ["Operator activity stream renders", "Service status board renders"],
        "observational_checks": ["Operations board renders"],
        "expected_artifacts": ["operations/validation/reports/WP-0085_validation.md", "runtime/validation/work_packages/WP-0085_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [_cmd('python -m estate.cli.main operator-activity-stream --json'), _cmd('python -m estate.cli.main service-status-board --json'), _cmd('python -m estate.cli.main operations-board --json', required=False)],
    },
    "WP-0088": {
        "recipe_id": "wp-0088-operations-center-layout-framework",
        "title": "WP-0088 — Operations Center Layout Framework",
        "description": "Validates the modular Operations Center layout framework, browser-local preference persistence, dockable activity console, status bar, command console, and tab management surfaces.",
        "required_checks": ["Steward command center renders", "Layout framework regression tests pass", "Layout framework is discoverable in rendered HTML"],
        "observational_checks": ["Production readiness report generates"],
        "expected_artifacts": ["operations/validation/reports/WP-0088_validation.md", "runtime/validation/work_packages/WP-0088_validation.json", "collaboration/work_packages/completions/WP-0088_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "Recipe returns no_recipe"],
        "success_criteria": ["Required commands exit zero and recipe does not return no_recipe"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main steward-command-center --json'),
            _cmd('pytest -q tests/test_steward_command_center.py'),
            _cmd('python -m estate.cli.main steward-command-center --json'),
            _cmd('test -f runtime/steward/command_center.html && rg -q "restoreLayoutPreferences" runtime/steward/command_center.html && rg -q "activity-console" runtime/steward/command_center.html && rg -q "status-bar" runtime/steward/command_center.html'),
            _cmd('python -m estate.cli.main validation-production-readiness --json', required=False),
        ],
    },
    "WP-0089": {
        "recipe_id": "wp-0089-operations-center-workspace-profiles",
        "title": "WP-0089 — Operations Center Workspace Profiles",
        "description": "Validates persisted Operations Center workspace profiles, rapid profile resolution, layout compatibility metadata, operator profile integration, and unavailable-panel handling.",
        "required_checks": ["Workspace profile resolves", "Workspace profile saves", "Workspace profile tests pass", "Steward command center embeds profile metadata"],
        "observational_checks": ["Production readiness report generates"],
        "expected_artifacts": ["operations/validation/reports/WP-0089_validation.md", "runtime/validation/work_packages/WP-0089_validation.json", "collaboration/work_packages/completions/WP-0089_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "Recipe returns no_recipe"],
        "success_criteria": ["Required commands exit zero and recipe does not return no_recipe"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main operations-center-profile --json --profile validation'),
            _cmd('python -m estate.cli.main operations-center-profile --json --profile active-projects --save-profile active-review --active-tab work-packages'),
            _cmd('pytest -q tests/test_operations_center_workspace_profiles.py'),
            _cmd('python -m estate.cli.main steward-command-center --json'),
            _cmd('python -m estate.cli.main validation-production-readiness --json', required=False),
        ],
    },

    "WP-0097": {
        "recipe_id": "wp-0097-operations-center-local-server-bootstrap",
        "title": "WP-0097 — Operations Center Local Server Bootstrap",
        "description": "Validates local-first Operations Center server bootstrap, status inspection, settings loading, service health preflight, and safe shutdown behavior.",
        "required_checks": ["Operations Center status command renders", "Bootstrap regression tests pass", "Start/status/stop command surfaces are registered", "Static entry point renders"],
        "observational_checks": ["Production readiness report generates"],
        "expected_artifacts": ["operations/validation/reports/WP-0097_validation.md", "runtime/validation/work_packages/WP-0097_validation.json", "collaboration/work_packages/completions/WP-0097_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "Recipe returns no_recipe", "Bootstrap bypasses Steward authorization or executes work packages"],
        "success_criteria": ["Required commands exit zero and recipe does not return no_recipe"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main operations-center status --json'),
            _cmd('pytest -q tests/test_operations_center_bootstrap.py'),
            _cmd('python -m estate.cli.main operations-center start --port 8877 --json && python -m estate.cli.main operations-center status --json && python -m estate.cli.main operations-center stop --json'),
            _cmd('python -m estate.cli.main steward-command-center --json'),
            _cmd('test -f runtime/steward/command_center.html && rg -q "Office of the Steward" runtime/steward/command_center.html'),
            _cmd('python -m estate.cli.main validation-production-readiness --json', required=False),
        ],
    },

    "WP-0098": {
        "recipe_id": "wp-0098-operations-center-launch-script",
        "title": "WP-0098 — Operations Center Launch Script",
        "description": "Validates the Steward-facing local PowerShell launcher, Estate root/dependency checks, settings loading, existing bootstrap usage, URL reporting, degraded optional component reporting, and safe shutdown guidance.",
        "required_checks": ["Launch script exists", "Launch script uses existing Operations Center bootstrap", "Launch script regression tests pass", "Status/settings command surfaces render"],
        "observational_checks": ["Production readiness report generates"],
        "expected_artifacts": ["launch_operations_center.ps1", "operations/validation/reports/WP-0098_validation.md", "runtime/validation/work_packages/WP-0098_validation.json", "collaboration/work_packages/completions/WP-0098_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "Recipe returns no_recipe", "Launcher bypasses local server bootstrap or changes command authority"],
        "success_criteria": ["Required commands exit zero and recipe does not return no_recipe"],
        "continue_on_failure": True,
        "commands": [
            _cmd('test -f launch_operations_center.ps1 && rg -q "operations-center.*start" launch_operations_center.ps1 && rg -q "Safe shutdown" launch_operations_center.ps1'),
            _cmd('pytest -q tests/test_operations_center_launch_script.py'),
            _cmd('python -m estate.cli.main operations-center-settings --json'),
            _cmd('python -m estate.cli.main operations-center status --json'),
            _cmd('python -m estate.cli.main operations-center start --port 8878 --json && python -m estate.cli.main operations-center stop --json'),
            _cmd('python -m estate.cli.main validation-production-readiness --json', required=False),
        ],
    },



    "WP-0099": {
        "recipe_id": "wp-0099-operations-center-pre-handoff-readiness-check",
        "title": "WP-0099 — Operations Center Pre-Handoff Readiness Check",
        "description": "Validates the Operations Center pre-handoff readiness checkpoint document, local command surface evidence, completion receipt, and production-readiness compatibility without expanding UI scope or governance authority.",
        "required_checks": ["Readiness checkpoint exists", "Readiness checkpoint references implemented and degraded capabilities", "Local Operations Center command surfaces render", "Completion receipt exists"],
        "observational_checks": ["Production readiness report generates"],
        "expected_artifacts": ["operations/readiness/operations_center_pre_handoff_readiness_check.md", "operations/validation/reports/WP-0099_validation.md", "runtime/validation/work_packages/WP-0099_validation.json", "collaboration/work_packages/completions/WP-0099_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "Recipe returns no_recipe", "Readiness checkpoint claims unsupported Operationally Validated status"],
        "success_criteria": ["Required commands exit zero and recipe does not return no_recipe"],
        "continue_on_failure": True,
        "commands": [
            _cmd('test -f operations/readiness/operations_center_pre_handoff_readiness_check.md && rg -q "Capability Checklist" operations/readiness/operations_center_pre_handoff_readiness_check.md && rg -q "Known Gaps" operations/readiness/operations_center_pre_handoff_readiness_check.md && rg -q "Handoff Notes for Chief Architect #5" operations/readiness/operations_center_pre_handoff_readiness_check.md'),
            _cmd('rg -q "server was observed stopped|server not running" operations/readiness/operations_center_pre_handoff_readiness_check.md && rg -q "does not assert Operationally Validated" operations/readiness/operations_center_pre_handoff_readiness_check.md'),
            _cmd('python -m estate.cli.main steward-command-center --json'),
            _cmd('python -m estate.cli.main operations-center-settings --json'),
            _cmd('python -m estate.cli.main operations-center status --json'),
            _cmd('test -f collaboration/work_packages/completions/WP-0099_codex_done.json'),
            _cmd('python -m estate.cli.main validation-production-readiness --json', required=False),
        ],
    },

    "WP-0096": {
        "recipe_id": "wp-0096-operations-center-notification-center",
        "title": "WP-0096 — Operations Center Notification Center",
        "description": "Validates read-only aggregation from existing operational notification-like artifacts, missing-source handling, severity filtering, local-only acknowledgement behavior, Operations Center Status Bar embedding, Operator Activity Stream compatibility, and source-link integrity.",
        "required_checks": ["Notification Center CLI renders", "Notification Center regression tests pass", "Steward command center embeds notification panel", "Rendered artifacts exist"],
        "observational_checks": ["Production readiness report generates"],
        "expected_artifacts": ["operations/validation/reports/WP-0096_validation.md", "runtime/validation/work_packages/WP-0096_validation.json", "collaboration/work_packages/completions/WP-0096_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "Recipe returns no_recipe", "Notification Center mutates authoritative source events"],
        "success_criteria": ["Required commands exit zero and recipe does not return no_recipe"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main operations-notification-center --json'),
            _cmd('pytest -q tests/test_operations_notification_center.py'),
            _cmd('python -m estate.cli.main steward-command-center --json'),
            _cmd('test -f runtime/notifications/operations_notification_center.json && test -f operations/notifications/operations_notification_center.md && rg -q "Operations Center Notification Center" runtime/steward/command_center.html'),
            _cmd('python -m estate.cli.main validation-production-readiness --json', required=False),
        ],
    },
    "WP-0093": {
        "recipe_id": "wp-0093-operations-center-settings-manager",
        "title": "WP-0093 — Operations Center Settings Manager",
        "description": "Validates local-first, version-aware Operations Center settings defaults, persistence, invalid setting handling, UI/About integration, and command surface.",
        "required_checks": ["Settings CLI renders", "Settings regression tests pass", "Steward command center embeds settings metadata"],
        "observational_checks": ["Production readiness report generates"],
        "expected_artifacts": ["operations/validation/reports/WP-0093_validation.md", "runtime/validation/work_packages/WP-0093_validation.json", "collaboration/work_packages/completions/WP-0093_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "Recipe returns no_recipe"],
        "success_criteria": ["Required commands exit zero and recipe does not return no_recipe"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main operations-center-settings --json'),
            _cmd('pytest -q tests/test_operations_center_settings.py tests/test_steward_command_center.py tests/test_operations_center_workspace_profiles.py'),
            _cmd('python -m estate.cli.main steward-command-center --json'),
            _cmd('test -f runtime/steward/command_center.html && rg -q "Settings version:" runtime/steward/command_center.html && rg -q "operations-center-settings-v1" runtime/steward/command_center.html'),
            _cmd('python -m estate.cli.main validation-production-readiness --json', required=False),
        ],
    },
    "WP-0092": {
        "recipe_id": "wp-0092-operations-center-help-and-about",
        "title": "WP-0092 — Operations Center Help and About",
        "description": "Validates Operations Center Help and About informational surfaces, command help, workspace/panel listings, source links, unavailable-feature handling, and production-readiness compatibility.",
        "required_checks": ["Steward command center renders", "Help/About regression tests pass", "Help surface is discoverable in rendered HTML"],
        "observational_checks": ["Production readiness report generates"],
        "expected_artifacts": ["operations/validation/reports/WP-0092_validation.md", "runtime/validation/work_packages/WP-0092_validation.json", "collaboration/work_packages/completions/WP-0092_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "Recipe returns no_recipe"],
        "success_criteria": ["Required commands exit zero and recipe does not return no_recipe"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main steward-command-center --json'),
            _cmd('pytest -q tests/test_steward_command_center.py'),
            _cmd('test -f runtime/steward/command_center.html && rg -q "Operations Center Help" runtime/steward/command_center.html && rg -q "Command Console Help" runtime/steward/command_center.html && rg -q "Component / Version Inventory" runtime/steward/command_center.html'),
            _cmd('python -m estate.cli.main validation-production-readiness --json', required=False),
        ],
    },
    "WP-0087": {
        "recipe_id": "wp-0087-operator-verbosity-filter-profiles",
        "title": "WP-0087 — Operator Verbosity and Filter Profiles",
        "description": "Validates Operator Activity Stream profile persistence, per-source verbosity, severity filtering, and production-readiness compatibility.",
        "required_checks": ["Operator activity stream profile saves", "Saved profile reloads", "Operator stream tests pass"],
        "observational_checks": ["Production readiness report generates"],
        "expected_artifacts": ["operations/validation/reports/WP-0087_validation.md", "runtime/validation/work_packages/WP-0087_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero and recipe does not return no_recipe"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main operator-activity-stream --json --source workers --severity warning --source-verbosity workers=detailed --save-profile worker-watch --ui-theme dark'),
            _cmd('python -m estate.cli.main operator-activity-stream --json --profile worker-watch'),
            _cmd('pytest -q tests/test_operator_activity_stream.py'),
            _cmd('python -m estate.cli.main validation-production-readiness --json', required=False),
        ],
    },
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
    "WP-0075": {
        "recipe_id": "wp-0075-operational-readiness-dashboard",
        "title": "WP-0075 — Operational Readiness Dashboard",
        "description": "Operational Readiness Dashboard validation. Uses operational-readiness-dashboard as the implemented dashboard CLI surface.",
        "required_checks": ["Operational readiness dashboard renders"],
        "observational_checks": ["Operational validation report renders", "Estate health renders", "Service readiness renders", "Validation metrics dashboard renders"],
        "expected_artifacts": ["operations/validation/reports/WP-0075_validation.md", "runtime/validation/work_packages/WP-0075_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main operational-readiness-dashboard --json'),
            _cmd('python -m estate.cli.main operational-validation --json', required=False),
            _cmd('python -m estate.cli.main estate-health --json', required=False),
            _cmd('python -m estate.cli.main service-readiness --json', required=False),
            _cmd('python -m estate.cli.main validation-metrics-dashboard --json', required=False),
        ],
    },
    "WP-0076": {
        "recipe_id": "wp-0076-estate-capability-registry",
        "title": "WP-0076 — Estate Capability Registry",
        "description": "Estate Capability Registry validation. Uses estate-capability-registry as the direct authoritative registry CLI surface.",
        "required_checks": ["Estate capability registry renders"],
        "observational_checks": ["Capabilities list renders", "Services list renders", "Capability lifecycle renders", "Capability help renders"],
        "expected_artifacts": ["operations/validation/reports/WP-0076_validation.md", "runtime/validation/work_packages/WP-0076_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main estate-capability-registry --json'),
            _cmd('python -m estate.cli.main capabilities --json', required=False),
            _cmd('python -m estate.cli.main services --json', required=False),
            _cmd('python -m estate.cli.main capability-lifecycle --json', required=False),
            _cmd('python -m estate.cli.main capability-help --json', required=False),
        ],
    },

    "WP-0077": {
        "recipe_id": "wp-0077-capability-dependency-visualization",
        "title": "WP-0077 — Capability Dependency Visualization and Mission Control integration",
        "description": "Validates the capability dependency visualization CLI and adjacent Mission Control / Steward Command Center integration surfaces.",
        "required_checks": ["Capability dependency visualization renders", "Estate capability registry renders"],
        "observational_checks": ["Steward Command Center renders", "Capability Dependency is discoverable in Estate search", "Capability Dependency is discoverable in global search"],
        "expected_artifacts": ["operations/validation/reports/WP-0077_validation.md", "runtime/validation/work_packages/WP-0077_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main capability-dependency-visualization --json'),
            _cmd('python -m estate.cli.main estate-capability-registry --json'),
            _cmd('python -m estate.cli.main steward-command-center --json', required=False),
            _cmd('python -m estate.cli.main estate-search "Capability Dependency" --json', required=False),
            _cmd('python -m estate.cli.main global-search "Capability Dependency" --json', required=False),
        ],
    },
    "WP-0078": {
        "recipe_id": "wp-0078-capability-gap-report-planned-evidence",
        "title": "WP-0078 — Capability Gap Report and planned-evidence handling refinement",
        "description": "Validates Capability Gap Report generation and adjacent registry, dependency, Mission Control, and search evidence surfaces.",
        "required_checks": ["Capability Gap Report renders", "Estate capability registry renders"],
        "observational_checks": ["Capability dependency visualization renders", "Steward Command Center renders", "Capability Gap is discoverable in global search"],
        "expected_artifacts": ["operations/validation/reports/WP-0078_validation.md", "runtime/validation/work_packages/WP-0078_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main capability-gap-report --json'),
            _cmd('python -m estate.cli.main estate-capability-registry --json'),
            _cmd('python -m estate.cli.main capability-dependency-visualization --json', required=False),
            _cmd('python -m estate.cli.main steward-command-center --json', required=False),
            _cmd('python -m estate.cli.main global-search "Capability Gap" --json', required=False),
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
    "WP-0086": {
        "recipe_id": "wp-0086-validation-recipe-expansion-self-check",
        "title": "WP-0086 — Validation Continuation #3: Recipe Expansion self-check",
        "description": "Confirms WP-0075 and WP-0076 validation recipes are visible through the validation runner and executable.",
        "required_checks": ["WP-0075 validation runner execution", "WP-0076 validation runner execution"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0086_validation.md", "runtime/validation/work_packages/WP-0086_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main validate-work-package --id WP-0075 --json'),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0076 --json'),
        ],
    },

    "WP-0095": {
        "recipe_id": "wp-0095-production-readiness-validation-finalization",
        "title": "WP-0095 — Validation Finalization: Production Readiness",
        "description": "Confirms production-readiness validation loop and existing WP-0077/WP-0078 validation still execute.",
        "required_checks": ["Production readiness report generation", "WP-0077 validation runner execution", "WP-0078 validation runner execution"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0095_validation.md", "runtime/validation/work_packages/WP-0095_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main validation-production-readiness --json'),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0077 --json'),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0078 --json'),
        ],
    },

    "WP-0091": {
        "recipe_id": "wp-0091-validation-recipe-expansion-0077-0078-self-check",
        "title": "WP-0091 — Validation Continuation #4: Add validation recipes for WP-0077 and WP-0078",
        "description": "Confirms WP-0077 and WP-0078 validation recipes are visible through the validation runner and executable.",
        "required_checks": ["WP-0077 validation runner execution", "WP-0078 validation runner execution"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0091_validation.md", "runtime/validation/work_packages/WP-0091_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main validate-work-package --id WP-0077 --json'),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0078 --json'),
        ],
    },

    "WP-0101": {
        "recipe_id": "wp-0101-codex-task-template-standard",
        "title": "WP-0101 — Codex Task Template Standard",
        "description": "Confirms the Codex task template standard exists, is registered, and is discoverable through local Estate search.",
        "required_checks": ["Document registry includes the Codex task template standard", "Estate search discovers the Codex task template standard"],
        "observational_checks": ["Production readiness report generation"],
        "expected_artifacts": ["operations/validation/reports/WP-0101_validation.md", "runtime/validation/work_packages/WP-0101_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main document-registry --json'),
            _cmd('python -m estate.cli.main estate-search "Codex Task Template" --json'),
            _cmd('python -m estate.cli.main validation-production-readiness --json', required=False),
        ],
    },

    "WP-0102": {
        "recipe_id": "wp-0102-backlog-codex-template-retrofit-closure",
        "title": "WP-0102 — Backlog Codex Template Retrofit Validation",
        "description": "Confirms WP-0102 mechanically retrofitted pending backlog task files without implementing their missions.",
        "required_checks": ["Codex task template standard exists", "WP-0102 retrofit notices are present", "WP-0102 completion receipt is complete", "No WP-0102-created implementation completions for pending backlog targets"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0102_validation.md", "runtime/validation/work_packages/WP-0102_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from pathlib import Path; template=Path('docs/operations/Codex_Task_Template_Standard_v1.md'); source=Path('collaboration/work_packages/pending/WP-0101_SERIES_codex_task_template_standard.md'); assert template.is_file(), template; assert source.is_file(), source\""),
            _cmd("python -c \"from pathlib import Path; pending=Path('collaboration/work_packages/pending'); ids=['0086','0087','0088','0089','0091','0092','0093','0094','0095','0096','0097','0098','0099','0100']; missing=[]; [missing.append(f'WP-{wp}') for wp in ids for files in [list(pending.glob(f'WP-{wp}_*.md'))] if not files or not any('WP-0102 Template Retrofit Notice' in path.read_text(encoding='utf-8') for path in files)]; assert not missing, missing\""),
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt(\'WP-0102\'); assert r[\'receipt_status\']==\'complete\', r\""),
            _cmd("python -c \"import json; from pathlib import Path; d=Path('collaboration/work_packages/completions'); targets=[f'WP-{i:04d}' for i in range(86,101)]; suspicious=[]; [suspicious.append(p.name) for wp in targets if (p:=d / f'{wp}_codex_done.json').exists() for data in [json.loads(p.read_text(encoding='utf-8'))] for scoped in [{k:v for k,v in data.items() if k not in {'production_readiness_command_status', 'validation_recipe_status'}}] for text in [json.dumps(scoped).lower()] if 'wp-0102' in text and ('retrofit' in text or 'template' in text)]; assert not suspicious, suspicious\"")
        ],
    },
    "WP-0103": {
        "recipe_id": "wp-0103-historical-validation-recipe-coverage",
        "title": "WP-0103 — Historical Validation Recipe Coverage Through WP-0085",
        "description": "Confirms production-readiness generation and WP-0103 validation recipe coverage without returning no_recipe.",
        "required_checks": ["Production readiness report generation", "WP-0015 validation runner execution", "WP-0027 validation runner execution"],
        "observational_checks": ["WP-0085 validation runner execution"],
        "expected_artifacts": ["operations/validation/reports/WP-0103_validation.md", "runtime/validation/work_packages/WP-0103_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main validation-production-readiness --json'),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0015 --json'),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0027 --json'),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0085 --json', required=False),
        ],
    },
    "WP-0106": {
        "recipe_id": "wp-0106-resident-runtime-presence-model",
        "title": "WP-0106 — Resident Runtime Presence Model",
        "description": "Validates local resident presence inspection, resident-card integration, stale/missing behavior tests, completion receipt, and production-readiness compatibility without granting resident authority or autonomous execution.",
        "required_checks": ["Resident presence JSON renders", "Alfred presence JSON renders", "Resident presence tests pass", "Completion receipt exists"],
        "observational_checks": ["Office command center JSON renders", "Production readiness report generation"],
        "expected_artifacts": ["src/estate/core/resident_presence.py", "runtime/residents/presence.json", "collaboration/work_packages/completions/WP-0106_codex_done.json", "runtime/validation/work_packages/WP-0106_validation.json"],
        "failure_criteria": ["Any required command exits non-zero", "Validation returns no_recipe", "Presence implies autonomous execution authority"],
        "success_criteria": ["Required commands exit zero", "Presence payload marks autonomous_execution false"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main resident-presence --json'),
            _cmd('python -m estate.cli.main resident-presence --resident Alfred --json'),
            _cmd('python -m pytest tests/test_resident_presence.py tests/test_resident_cards.py tests/test_steward_command_center.py'),
            _cmd("python -c \"from pathlib import Path; assert Path('collaboration/work_packages/completions/WP-0106_codex_done.json').is_file()\""),
            _cmd('python -m estate.cli.main steward-command-center --json', required=False),
            _cmd('python -m estate.cli.main validation-production-readiness --json', required=False),
        ],
    },


    "WP-0107": {
        "recipe_id": "wp-0107-alfred-online-duty-runner",
        "title": "WP-0107 — Alfred Online Duty Runner",
        "description": "Validates Alfred's local bounded duty runner, visible resident presence integration, source artifact references, graceful degradation, command surfaces, completion receipt, and production-readiness compatibility without changing governance, validation, merge, or Steward authority.",
        "required_checks": ["Alfred duty JSON renders", "Resident duty alias renders", "Alfred presence JSON renders", "Alfred duty tests pass", "Completion receipt exists"],
        "observational_checks": ["Office command center JSON renders", "Production readiness report generation"],
        "expected_artifacts": ["src/estate/core/alfred_duty.py", "runtime/alfred/duty_state.json", "runtime/residents/presence.json", "collaboration/work_packages/completions/WP-0107_codex_done.json", "runtime/validation/work_packages/WP-0107_validation.json"],
        "failure_criteria": ["Any required command exits non-zero", "Validation returns no_recipe", "Duty payload implies approval, validation, merge, notification, or work-package execution authority"],
        "success_criteria": ["Required commands exit zero", "Duty payload records source artifacts and authority limitations", "Resident presence marks autonomous_execution false"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main alfred-duty --json'),
            _cmd('python -m estate.cli.main resident-duty --resident Alfred --json'),
            _cmd('python -m estate.cli.main resident-presence --resident Alfred --json'),
            _cmd('python -m pytest tests/test_alfred_duty.py tests/test_resident_presence.py tests/test_resident_cards.py'),
            _cmd("python -c \"from pathlib import Path; assert Path('collaboration/work_packages/completions/WP-0107_codex_done.json').is_file()\""),
            _cmd('python -m estate.cli.main steward-command-center --json', required=False),
            _cmd('python -m estate.cli.main validation-production-readiness --json', required=False),
        ],
    },

    "WP-0108": {
        "recipe_id": "wp-0108-helen-online-duty-runner",
        "title": "WP-0108 — Helen Online Duty Runner",
        "description": "Validates Helen's local bounded HR/onboarding duty runner, visible resident presence integration, source artifact references, graceful degradation, command surfaces, completion receipt, and production-readiness compatibility without changing personnel, HR governance, validation, merge, or Steward authority.",
        "required_checks": ["Helen duty JSON renders", "Resident duty alias renders", "Helen presence JSON renders", "Helen duty tests pass", "Completion receipt exists"],
        "observational_checks": ["Office command center JSON renders", "Production readiness report generation"],
        "expected_artifacts": ["src/estate/core/helen_duty.py", "runtime/helen/duty_state.json", "runtime/residents/presence.json", "collaboration/work_packages/completions/WP-0108_codex_done.json", "runtime/validation/work_packages/WP-0108_validation.json"],
        "failure_criteria": ["Any required command exits non-zero", "Validation returns no_recipe", "Duty payload implies personnel authorization, HR governance, validation, merge, notification, or work-package execution authority"],
        "success_criteria": ["Required commands exit zero", "Duty payload records source artifacts and authority limitations", "Resident presence marks autonomous_execution false"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main helen-duty --json'),
            _cmd('python -m estate.cli.main resident-duty --resident Helen --json'),
            _cmd('python -m estate.cli.main resident-presence --resident Helen --json'),
            _cmd('python -m pytest tests/test_helen_duty.py tests/test_resident_presence.py tests/test_resident_cards.py'),
            _cmd("python -c \"from pathlib import Path; assert Path('collaboration/work_packages/completions/WP-0108_codex_done.json').is_file()\""),
            _cmd('python -m estate.cli.main steward-command-center --json', required=False),
            _cmd('python -m estate.cli.main validation-production-readiness --json', required=False),
        ],
    },

    "WP-0109": {
        "recipe_id": "wp-0109-resident-conversation-session-audit-trail",
        "title": "WP-0109 — Resident Conversation Session and Audit Trail",
        "description": "Validates local file-backed resident conversation sessions, CLI JSON surfaces, workspace summaries, source artifact references, and explicit non-authoritative authority labels.",
        "required_checks": ["Resident conversation help renders", "Resident conversation tests pass", "Workspace renders", "Completion receipt exists"],
        "observational_checks": ["Production readiness report generation"],
        "expected_artifacts": ["src/estate/core/resident_conversation_sessions.py", "src/estate/core/resident_conversations.py", "runtime/resident_conversations/sessions", "collaboration/work_packages/completions/WP-0109_codex_done.json", "runtime/validation/work_packages/WP-0109_validation.json"],
        "failure_criteria": ["Any required command exits non-zero", "Validation returns no_recipe", "Conversation session implies governance, validation, merge, Steward, HR, or work-package execution authority"],
        "success_criteria": ["Required commands exit zero", "Session summaries expose non-authoritative labels", "Workspace consumes session summaries when available"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main resident-conversation --help'),
            _cmd('python -m pytest tests/test_resident_conversation_sessions.py tests/test_resident_conversations.py'),
            _cmd('python -m estate.cli.main steward-command-center --json'),
            _cmd("python -c \"from pathlib import Path; assert Path('collaboration/work_packages/completions/WP-0109_codex_done.json').is_file()\""),
            _cmd('python -m estate.cli.main validation-production-readiness --json', required=False),
        ],
    },


    "WP-0110": {
        "recipe_id": "wp-0110-resident-action-authority-boundary",
        "title": "WP-0110 — Resident Action Authority Boundary",
        "description": "Validates local resident authority checks, safe default denial, Alfred/Helen explicit boundaries, duty/conversation integration, audit storage, CLI JSON, and completion receipt without changing governance, validation, merge, personnel, or Steward authority.",
        "required_checks": ["Authority CLI allows Alfred summarize", "Authority CLI denies Alfred execution", "Authority CLI allows Helen summarize", "Authority CLI denies Helen personnel modification", "Unknown action denied", "Resident authority tests pass", "Completion receipt exists"],
        "observational_checks": ["Resident duty runners render", "Resident conversation help renders", "Operations Center command center renders", "Production readiness report generation"],
        "expected_artifacts": ["src/estate/core/resident_authority.py", "tests/test_resident_authority.py", "runtime/residents/authority_decisions.jsonl", "collaboration/work_packages/completions/WP-0110_codex_done.json", "runtime/validation/work_packages/WP-0110_validation.json"],
        "failure_criteria": ["Any required command exits non-zero", "Validation returns no_recipe", "Unknown actions are allowed silently", "Resident payload implies governance, validation, merge, personnel, Steward, or work-package execution authority"],
        "success_criteria": ["Required commands exit zero", "Boundary decisions include reasons and source references", "Duty runners and conversations expose authority decisions", "Audit path is local"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main resident-authority check --resident Alfred --action summarize --json'),
            _cmd('python -m estate.cli.main resident-authority check --resident Alfred --action execute-work-package --json'),
            _cmd('python -m estate.cli.main resident-authority check --resident Helen --action summarize --json'),
            _cmd('python -m estate.cli.main resident-authority check --resident Helen --action modify-personnel --json'),
            _cmd('python -m estate.cli.main resident-authority check --resident Alfred --action unknown-action --json'),
            _cmd('python -m estate.cli.main resident-authority list --resident Alfred --json'),
            _cmd('python -m pytest tests/test_resident_authority.py tests/test_alfred_duty.py tests/test_helen_duty.py tests/test_resident_conversation_sessions.py tests/test_resident_cards.py'),
            _cmd("python -c \"from pathlib import Path; assert Path('collaboration/work_packages/completions/WP-0110_codex_done.json').is_file()\""),
            _cmd('python -m estate.cli.main resident-duty --resident Alfred --json', required=False),
            _cmd('python -m estate.cli.main resident-duty --resident Helen --json', required=False),
            _cmd('python -m estate.cli.main resident-conversation --help', required=False),
            _cmd('python -m estate.cli.main steward-command-center --json', required=False),
            _cmd('python -m estate.cli.main validation-production-readiness --json', required=False),
        ],
    },

    "WP-0111": {
        "recipe_id": "wp-0111-first-batch-burn-down-self-validation",
        "title": "WP-0111 — First Production-Readiness Backlog Burn-Down Batch",
        "description": "Validates WP-0111's first-batch burn-down artifacts, confirms WP-0020 was selected and validated, and confirms WP-0106 through WP-0110 remain implementation backlog rather than validation-only repairs.",
        "required_checks": ["First-batch markdown report exists", "First-batch JSON report parses", "WP-0020 selected as first batch", "WP-0106 through WP-0110 remain pending implementation", "WP-0020 validates", "WP-0111 completion receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/backlog_burn_down/WP-0111_first_batch_report.md", "runtime/validation/backlog_burn_down/WP-0111_first_batch_report.json", "collaboration/work_packages/completions/WP-0111_codex_done.json", "operations/validation/reports/WP-0111_validation.md", "runtime/validation/work_packages/WP-0111_validation.json"],
        "failure_criteria": ["Any required command exits non-zero", "WP-0106 through WP-0110 are marked complete by the WP-0111 report"],
        "success_criteria": ["Required commands exit zero", "WP-0111 remains limited to validating WP-0020 and recommending pending Helen implementation work"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from pathlib import Path; paths=['operations/validation/backlog_burn_down/WP-0111_first_batch_report.md','runtime/validation/backlog_burn_down/WP-0111_first_batch_report.json']; missing=[p for p in paths if not Path(p).is_file()]; assert not missing, missing\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/backlog_burn_down/WP-0111_first_batch_report.json').read_text(encoding='utf-8')); assert data.get('selected_batch_package_ids') == ['WP-0020'], data.get('selected_batch_package_ids')\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/backlog_burn_down/WP-0111_first_batch_report.json').read_text(encoding='utf-8')); pending={item.get('work_package_id'): str(item.get('reason','')).lower() for item in data.get('packages_discovered_as_genuinely_pending_unimplemented', [])}; required={f'WP-{i:04d}' for i in range(106,111)}; missing=sorted(required-set(pending)); not_pending=[wp for wp, reason in pending.items() if wp in required and 'implementation backlog' not in reason]; assert not missing and not not_pending, {'missing': missing, 'not_pending': not_pending}\""),
            _cmd("python -c \"from pathlib import Path; text=Path('operations/validation/backlog_burn_down/WP-0111_first_batch_report.md').read_text(encoding='utf-8').lower(); required=['wp-0106','wp-0107','wp-0108','wp-0109','wp-0110','pending','unimplemented']; missing=[term for term in required if term not in text]; assert not missing, missing\""),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0020 --json'),
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0111'); assert r['receipt_status']=='complete', r\""),
        ],
    },

    "WP-0105": {
        "recipe_id": "wp-0105-validation-closure-repair-0102-0103",
        "title": "WP-0105 — Validation Closure Repair for WP-0102 and WP-0103",
        "description": "Confirms WP-0102 and WP-0103 validation closure repair while preserving representative historical recipe coverage.",
        "required_checks": ["WP-0101 validates", "WP-0102 validates", "WP-0103 validates", "Representative historical packages validate", "Production readiness report generates"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0105_validation.md", "runtime/validation/work_packages/WP-0105_validation.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -m estate.cli.main validate-work-package --id WP-0101 --json'),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0102 --json'),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0103 --json'),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0080 --json'),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0081 --json'),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0085 --json'),
            _cmd('python -m estate.cli.main validation-production-readiness --json'),
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
    pr = payload.get("production_readiness") or {}
    receipt = payload.get("receipt_validation") or {}
    lines += ["", "## Receipt Validation", f"- Receipt status: {receipt.get('receipt_status', 'unknown')}", f"- Completion artifact: {receipt.get('completion_artifact_path') or 'missing'}", "- Receipt gaps: " + (", ".join(payload.get("receipt_gaps", [])) or "None")]
    lines += ["", "## Production Readiness", f"- Production ready: {pr.get('production_ready', False)}", f"- Execution status: {pr.get('execution_status', payload.get('validation_status'))}", f"- Receipt status: {pr.get('receipt_status', 'unknown')}", "- Blocking reasons: " + ("; ".join(pr.get("blocking_reasons", [])) or "None"), "- Non-blocking findings: " + ("; ".join(pr.get("non_blocking_findings", [])) or "None")]
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
    from estate.core.production_readiness_validation import validate_receipt, calculate_production_readiness
    receipt = validate_receipt(wp, base)
    payload["receipt_validation"] = receipt
    payload["completion_artifact_path"] = receipt.get("completion_artifact_path")
    payload["receipt_gaps"] = receipt.get("receipt_gaps", [])
    payload["production_readiness"] = calculate_production_readiness(status, receipt, "covered" if recipe else "no_recipe", findings)
    if write:
        md_rel = REPORTS_DIR / f"{wp}_validation.md"
        json_rel = RUNTIME_DIR / f"{wp}_validation.json"
        latest_rel = RUNTIME_DIR / "latest.json"
        payload["files_written"] = [str(md_rel).replace("\\", "/"), str(json_rel).replace("\\", "/"), str(latest_rel).replace("\\", "/")]
        (base / md_rel).parent.mkdir(parents=True, exist_ok=True)
        (base / json_rel).parent.mkdir(parents=True, exist_ok=True)
        (base / md_rel).write_text(format_validation_markdown(payload) + "\n", encoding="utf-8")
        (base / json_rel).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        latest = {
            "work_package_id": wp,
            "validation_id": validation_id,
            "generated_at": generated_at,
            "latest_validation_report_path": str(md_rel).replace("\\", "/"),
            "markdown_report": str(md_rel).replace("\\", "/"),
            "json_report": str(json_rel).replace("\\", "/"),
            "validation_status": status,
        }
        (base / latest_rel).write_text(json.dumps(latest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
