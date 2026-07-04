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
