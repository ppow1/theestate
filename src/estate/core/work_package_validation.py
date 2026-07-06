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

    "WP-0016": {
        "recipe_id": "wp-0016-work-package-registry-architecture-artifact-presence",
        "title": "WP-0016 — Work Package Registry Architecture",
        "description": "Conservatively validates the architecture-only registry proposal artifact, normalized receipt, and implementation-not-authorized boundary.",
        "required_checks": ["ADR-0002 exists", "Receipt is complete", "Implementation remains unauthorized"],
        "observational_checks": [],
        "expected_artifacts": ["Architecture/ADR/ADR-0002-Work-Package-Registry-Proposal.md", "collaboration/work_packages/completions/WP-0016_architecture_done.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from pathlib import Path; p=Path('Architecture/ADR/ADR-0002-Work-Package-Registry-Proposal.md'); t=p.read_text(encoding='utf-8'); required=['Work Package Registry','status','mode','owner','dependencies','validation','completion','CA review']; missing=[x for x in required if x.lower() not in t.lower()]; assert p.is_file() and not missing, missing\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('collaboration/work_packages/completions/WP-0016_architecture_done.json').read_text(encoding='utf-8')); assert data.get('implementation_authorized') is False; assert data.get('architecture_artifact')=='Architecture/ADR/ADR-0002-Work-Package-Registry-Proposal.md'; assert data.get('ready_for_ca_review') is True\""),
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0016'); assert r['receipt_status']=='complete', r\""),
        ],
    },
    "WP-0017": {
        "recipe_id": "wp-0017-work-package-state-machine-architecture-artifact-presence",
        "title": "WP-0017 — Work Package State Machine Architecture",
        "description": "Conservatively validates the architecture-only state-machine proposal artifact, normalized receipt, and implementation-not-authorized boundary.",
        "required_checks": ["ADR-0003 exists", "Receipt is complete", "Implementation remains unauthorized"],
        "observational_checks": [],
        "expected_artifacts": ["Architecture/ADR/ADR-0003-Work-Package-State-Machine-Proposal.md", "collaboration/work_packages/completions/WP-0017_architecture_done.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from pathlib import Path; p=Path('Architecture/ADR/ADR-0003-Work-Package-State-Machine-Proposal.md'); t=p.read_text(encoding='utf-8'); required=['state machine','proposed','approved','in_progress','ca_review_pending','merge_authorized','closed']; missing=[x for x in required if x.lower() not in t.lower()]; assert p.is_file() and not missing, missing\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('collaboration/work_packages/completions/WP-0017_architecture_done.json').read_text(encoding='utf-8')); assert data.get('implementation_authorized') is False; assert data.get('architecture_artifact')=='Architecture/ADR/ADR-0003-Work-Package-State-Machine-Proposal.md'; assert data.get('ready_for_ca_review') is True\""),
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0017'); assert r['receipt_status']=='complete', r\""),
        ],
    },
    "WP-0073": {
        "recipe_id": "wp-0073-validation-to-mission-control-integration",
        "title": "WP-0073 — Validation to Mission Control Integration",
        "description": "Validates that Mission Control exposes validation health without becoming the source of truth.",
        "required_checks": ["Mission Control validation health fields exist", "Receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["src/estate/core/mission_control_workspace.py", "collaboration/work_packages/completions/WP-0073_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.mission_control_workspace import build_mission_control_workspace; p=build_mission_control_workspace(write=False); v=p['data']['validation_health']; required=['overall_validation_status','open_observations_count','confirmed_defects_count','conditional_pass_count','most_recent_validation_activity','artifact_links','recommended_next_validation_action']; missing=[k for k in required if k not in v]; assert not missing, missing; assert 'source' in v.get('source_of_truth_boundary','').lower()\""),
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0073'); assert r['receipt_status']=='complete', r\""),
        ],
    },
    "WP-0094": {
        "recipe_id": "wp-0094-operations-center-status-bar",
        "title": "WP-0094 — Operations Center Status Bar",
        "description": "Validates the persistent Operations Center status bar fields, quiet refresh region, activity console, and receipt.",
        "required_checks": ["Status bar exposes operational fields", "Receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["src/estate/core/steward_command_center.py", "collaboration/work_packages/completions/WP-0094_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.steward_command_center import generate_command_center; p=generate_command_center(write=False); s=p['status_bar']; required={'estate_status','validation_state','active_workers','active_recall_count','pending_decisions','health_state','recommended_next_action'}; assert required <= set(s), s; assert 'status_bar' in p['layout_framework']['data']['quiet_refresh_regions']; assert p['activity_console']['collapsed_by_default'] is True\""),
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0094'); assert r['receipt_status']=='complete', r\""),
        ],
    },
    "WP-0121": {
        "recipe_id": "wp-0121-final-four-closure-self-validation",
        "title": "WP-0121 — Final Four Production-Readiness Closure",
        "description": "Self-validates final-four reports, classifications, receipts, dependent validations, production-readiness regeneration, and preserved quarantine/runtime statuses.",
        "required_checks": ["Reports exist and parse", "All four blockers classified", "Readiness command executes", "Prior packages pass", "Receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/backlog_burn_down/WP-0121_final_four_closure_report.md", "runtime/validation/backlog_burn_down/WP-0121_final_four_closure_report.json", "collaboration/work_packages/completions/WP-0121_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"import json; from pathlib import Path; md=Path('operations/validation/backlog_burn_down/WP-0121_final_four_closure_report.md'); js=Path('runtime/validation/backlog_burn_down/WP-0121_final_four_closure_report.json'); assert md.is_file(); data=json.loads(js.read_text(encoding='utf-8')); ids={'WP-0016','WP-0017','WP-0073','WP-0094'}; assert ids <= set(data.get('initial_blockers', [])); assert data.get('before_totals') and data.get('after_totals'); assert ids <= set(data.get('classifications', {})); assert all(v.get('validation_result') for v in data.get('packages_repaired', {}).values()); assert all(v.get('next_action') for v in data.get('packages_left_blocked', {}).values()); assert data.get('alfred_helen_runtime_path_status',{}).get('ready') is True; assert data.get('vo_0001',{}).get('status') in {'closed','preserved','open'}; assert data.get('wp_9999_quarantine_status',{}).get('promoted') is False\""),
            _cmd("python -m estate.cli.main validation-production-readiness --json"),
            _cmd("python -c \"import json; from pathlib import Path; ids=['WP-0116','WP-0117','WP-0118','WP-0119','WP-0120']; bad=[]; [bad.append(wp) for wp in ids if json.loads(Path(f'runtime/validation/work_packages/{wp}_validation.json').read_text(encoding='utf-8')).get('validation_status') not in {'passed','passed_with_findings'}]; assert not bad, bad\""),
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0121'); assert r['receipt_status']=='complete', r\""),
        ],
    },

    "WP-0122": {
        "recipe_id": "wp-0122-alfred-operational-resident-runtime-standup",
        "title": "WP-0122 — Alfred Operational Resident Runtime Stand-Up",
        "description": "Self-validates Alfred operational stand-up reports, runtime presence/duty/authority commands, Operations Center visibility, dependent package validation, production-readiness execution, and receipt completeness.",
        "required_checks": ["Alfred operational reports exist and parse", "Identity and mailbox mapping are reported", "Presence and duty commands succeed", "Authority decisions are reported", "Operations Center visibility is available", "Production readiness executes", "Dependent packages pass", "Receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["operations/residents/alfred/WP-0122_alfred_operational_standup_report.md", "runtime/residents/alfred/WP-0122_alfred_operational_standup_report.json", "collaboration/work_packages/completions/WP-0122_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "Alfred identity/mailbox mapping is absent", "WP-9999 is falsely promoted"],
        "success_criteria": ["Required commands exit zero", "Alfred is visible through existing resident/runtime surfaces", "Dependent package validations pass"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -c "import json; from pathlib import Path; md=Path(\'operations/residents/alfred/WP-0122_alfred_operational_standup_report.md\'); js=Path(\'runtime/residents/alfred/WP-0122_alfred_operational_standup_report.json\'); assert md.is_file(); data=json.loads(js.read_text(encoding=\'utf-8\')); identity=data.get(\'alfred_identity_mapping\',{}); mailbox=data.get(\'mailbox_mapping\',{}); assert identity.get(\'employee_id\') == 7 and identity.get(\'resident_id\') == \'RES-000001\'; assert mailbox.get(\'personnel_mailbox_id\') == 7 and mailbox.get(\'legacy_intake_mailbox_reference\',{}).get(\'mailbox_id\') == 10100; assert data.get(\'authority_check_results\',{}).get(\'summarize\',{}).get(\'allowed\') is True; assert data.get(\'authority_check_results\',{}).get(\'execute_work_package\',{}).get(\'allowed\') is False; assert data.get(\'operations_center_visibility\',{}).get(\'steward_command_center_generated\') is True"'),
            _cmd("python -m estate.cli.main resident-presence --resident Alfred --json"),
            _cmd("python -m estate.cli.main alfred-duty --json"),
            _cmd("python -m estate.cli.main resident-duty --resident Alfred --json"),
            _cmd("python -m estate.cli.main resident-authority check --resident Alfred --action summarize --json"),
            _cmd("python -m estate.cli.main resident-authority check --resident Alfred --action execute-work-package --json"),
            _cmd("python -m estate.cli.main steward-command-center --json"),
            _cmd("python -m estate.cli.main validation-production-readiness --json"),
            _cmd("python -m estate.cli.main validate-work-package --id WP-0106 --json"),
            _cmd("python -m estate.cli.main validate-work-package --id WP-0107 --json"),
            _cmd("python -m estate.cli.main validate-work-package --id WP-0109 --json"),
            _cmd("python -m estate.cli.main validate-work-package --id WP-0110 --json"),
            _cmd("python -m estate.cli.main validate-work-package --id WP-0119 --json"),
            _cmd("python -m estate.cli.main validate-work-package --id WP-0121 --json"),
            _cmd('python -c "from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt(\'WP-0122\'); assert r[\'receipt_status\']==\'complete\', r"'),
        ],
    },

    "WP-0123": {
        "recipe_id": "wp-0123-helen-online-onboarding",
        "title": "WP-0123 — Bring Helen Online Through Alfred or Manual HR Onboarding",
        "description": "Self-validates Helen online onboarding reports, runtime presence/duty/authority commands, Operations Center visibility, dependent work-package validations, production-readiness execution, and completion receipt.",
        "required_checks": ["Helen online reports exist and parse", "Onboarding path is reported", "Identity and mailbox mapping are present", "Presence and duty commands succeed", "Authority checks are reported", "CA5 onboarding readiness is stated", "Production readiness executes", "Dependent packages pass", "Receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["operations/residents/helen/WP-0123_helen_online_onboarding_report.md", "runtime/residents/helen/WP-0123_helen_online_onboarding_report.json", "collaboration/work_packages/completions/WP-0123_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "Helen identity/mailbox mapping is absent", "Onboarding path is absent", "WP-9999 is falsely promoted"],
        "success_criteria": ["Required commands exit zero", "Helen is visible through existing resident/runtime surfaces", "Dependent package validations pass"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -c "import json; from pathlib import Path; md=Path(\'operations/residents/helen/WP-0123_helen_online_onboarding_report.md\'); js=Path(\'runtime/residents/helen/WP-0123_helen_online_onboarding_report.json\'); assert md.is_file(); data=json.loads(js.read_text(encoding=\'utf-8\')); identity=data.get(\'helen_identity_mapping\',{}); mailbox=data.get(\'mailbox_mapping\',{}); path=data.get(\'onboarding_path\',{}); assert path.get(\'path\') in {\'alfred_assisted\', \'manual_onboarding_with_alfred_readiness_inspection\', \'manual_onboarding\'}; assert \'alfred_performed_or_assisted\' in path; assert identity.get(\'resident_id\') == \'RES-000003\' and identity.get(\'mailbox_id\') == 6; assert mailbox.get(\'mailbox_id\') == 6 and mailbox.get(\'resident_id\') == \'RES-000003\'; assert data.get(\'authority_results\',{}).get(\'summarize\',{}).get(\'allowed\') is True; assert data.get(\'authority_results\',{}).get(\'modify_personnel\',{}).get(\'allowed\') is False; assert isinstance(data.get(\'ready_to_hire_onboard_chief_architect_5\'), bool)"'),
            _cmd("python -m estate.cli.main resident-presence --resident Helen --json"),
            _cmd("python -m estate.cli.main helen-duty --json"),
            _cmd("python -m estate.cli.main resident-duty --resident Helen --json"),
            _cmd("python -m estate.cli.main resident-authority list --resident Helen --json"),
            _cmd("python -m estate.cli.main resident-authority check --resident Helen --action summarize --json"),
            _cmd("python -m estate.cli.main resident-authority check --resident Helen --action modify-personnel --json"),
            _cmd("python -m estate.cli.main steward-command-center --json"),
            _cmd("python -m estate.cli.main validation-production-readiness --json"),
            _cmd("python -m estate.cli.main validate-work-package --id WP-0020 --json"),
            _cmd("python -m estate.cli.main validate-work-package --id WP-0080 --json"),
            _cmd("python -m estate.cli.main validate-work-package --id WP-0108 --json"),
            _cmd("python -m estate.cli.main validate-work-package --id WP-0110 --json"),
            _cmd("python -m estate.cli.main validate-work-package --id WP-0119 --json"),
            _cmd("python -c \"import json; from pathlib import Path; p=Path('runtime/validation/work_packages/WP-0122_validation.json'); assert p.is_file(); assert json.loads(p.read_text(encoding='utf-8')).get('validation_status') in {'passed','passed_with_findings'}\""),
            _cmd('python -c "from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt(\'WP-0123\'); assert r[\'receipt_status\']==\'complete\', r"'),
        ],
    },

    "WP-0124": {
        "recipe_id": "wp-0124-helen-led-chief-architect-5-hiring-onboarding",
        "title": "WP-0124 — Helen-Led Chief Architect #5 Hiring and Onboarding",
        "description": "Self-validates Chief Architect #5 personnel identity, mailbox assignment, onboarding packet, Helen involvement, communication/audit trail, dependent validations, production-readiness execution, and receipt completeness.",
        "required_checks": ["WP-0124 report exists", "JSON companion parses", "Chief Architect #5 onboarding packet exists", "Identity assignment is present", "Mailbox assignment is present", "Helen involvement is explicitly reported", "Communication/audit record is present", "Production readiness executes", "WP-0122 and WP-0123 remain passing", "Receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["operations/onboarding/WP-0124_chief_architect_5_hiring_onboarding_report.md", "runtime/onboarding/WP-0124_chief_architect_5_hiring_onboarding_report.json", "docs/onboarding/chief_architects/chief_architect_5_onboarding_packet.md", "collaboration/messages/msg_helen_20260705_0001_ca5_hiring_onboarding_notice.json", "runtime/onboarding/WP-0124_helen_hr_onboarding_action.json", "collaboration/work_packages/completions/WP-0124_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "Chief Architect #5 identity or mailbox assignment is absent", "Helen involvement is not reported", "Communication/audit evidence is absent", "WP-9999 is falsely promoted"],
        "success_criteria": ["Required commands exit zero", "Chief Architect #5 has durable personnel/mailbox/onboarding evidence", "Dependent package validations pass"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -c "import json; from pathlib import Path; md=Path(\'operations/onboarding/WP-0124_chief_architect_5_hiring_onboarding_report.md\'); js=Path(\'runtime/onboarding/WP-0124_chief_architect_5_hiring_onboarding_report.json\'); packet=Path(\'docs/onboarding/chief_architects/chief_architect_5_onboarding_packet.md\'); assert md.is_file(); data=json.loads(js.read_text(encoding=\'utf-8\')); assert packet.is_file(); identity=data.get(\'chief_architect_5_identity_assignment\',{}); mailbox=data.get(\'mailbox_assignment\',{}); assert identity.get(\'employee_id\') == 8 and identity.get(\'role_title\') == \'Chief Architect #5\'; assert mailbox.get(\'mailbox_id\') == 8 and mailbox.get(\'mailbox_path\') == \'collaboration/mailboxes/0008\'; assert data.get(\'helen_performed_or_orchestrated_hire\') is True; assert Path(data.get(\'communication_notice_path\', \'\')).is_file(); assert Path(data.get(\'audit_runtime_record_path\', \'\')).is_file()"'),
            _cmd('python -c "import json; from pathlib import Path; personnel=json.loads(Path(\'data/registry/personnel.json\').read_text(encoding=\'utf-8\')); ca5=[p for p in personnel if p.get(\'employee_id\')==8 and p.get(\'display_name\')==\'Chief Architect #5\' and p.get(\'mailbox_id\')==8]; assert ca5; assert Path(\'collaboration/mailboxes/0008/inbox\').is_dir(); assert Path(\'collaboration/mailboxes/0008/sent\').is_dir(); assert Path(\'collaboration/mailboxes/0008/archive\').is_dir()"'),
            _cmd("python -c \"import json; from pathlib import Path; p=Path('runtime/validation/work_packages/WP-0122_validation.json'); assert p.is_file(); assert json.loads(p.read_text(encoding='utf-8')).get('validation_status') in {'passed','passed_with_findings'}\""),
            _cmd("python -c \"import json; from pathlib import Path; p=Path('runtime/validation/work_packages/WP-0123_validation.json'); assert p.is_file(); assert json.loads(p.read_text(encoding='utf-8')).get('validation_status') in {'passed','passed_with_findings'}\""),
            _cmd("python -m estate.cli.main validation-production-readiness --json"),
            _cmd('python -c "from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt(\'WP-0124\'); assert r[\'receipt_status\']==\'complete\', r"'),
        ],
    },


    "WP-0125": {
        "recipe_id": "wp-0125-engineering-department-establishment",
        "title": "WP-0125 — Estate Engineering Department for CueMastery Execution",
        "description": "Self-validates Engineering Department charter, operating guide, CueMastery handoff, establishment reports, prerequisite status reporting, production-readiness execution, and receipt completeness.",
        "required_checks": ["Engineering charter exists", "Operating guide exists", "CueMastery handoff exists", "Reports exist and parse", "CueMastery is primary objective", "Work-package and validation discipline are stated", "Immediate CueMastery next steps are present", "Production readiness executes", "Alfred/Helen and prerequisite statuses are reported", "Receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["operations/departments/engineering/engineering_department_charter.md", "operations/departments/engineering/engineering_department_operating_guide.md", "operations/departments/engineering/cuemastery_execution_handoff.md", "operations/departments/engineering/WP-0125_engineering_department_establishment_report.md", "runtime/departments/engineering/WP-0125_engineering_department_establishment_report.json", "runtime/departments/engineering/WP-0125_engineering_department_status.json", "collaboration/work_packages/completions/WP-0125_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "Authority or resident status reporting is absent", "WP-9999 is falsely promoted"],
        "success_criteria": ["Required commands exit zero", "Engineering Department is represented by durable artifacts", "Dependent package statuses are reported", "Receipt is complete"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -c "import json; from pathlib import Path; charter=Path(\'operations/departments/engineering/engineering_department_charter.md\'); guide=Path(\'operations/departments/engineering/engineering_department_operating_guide.md\'); handoff=Path(\'operations/departments/engineering/cuemastery_execution_handoff.md\'); report=Path(\'operations/departments/engineering/WP-0125_engineering_department_establishment_report.md\'); status=Path(\'runtime/departments/engineering/WP-0125_engineering_department_status.json\'); data=json.loads(Path(\'runtime/departments/engineering/WP-0125_engineering_department_establishment_report.json\').read_text(encoding=\'utf-8\')); assert charter.is_file() and guide.is_file() and handoff.is_file() and report.is_file() and status.is_file(); ct=charter.read_text(encoding=\'utf-8\').lower(); gt=guide.read_text(encoding=\'utf-8\').lower(); ht=handoff.read_text(encoding=\'utf-8\').lower(); assert \'cuemastery\' in ct and \'initial primary objective\' in ct; assert \'work package\' in gt and \'validation\' in gt; assert \'immediate engineering discovery steps\' in ht and \'cuemastery\' in ht; assert data.get(\'alfred_helen_status\') and data.get(\'precondition_status\'); assert all(k in data.get(\'precondition_status\', {}) for k in [\'WP-0121\',\'WP-0122\',\'WP-0123\',\'WP-0124\']); assert data.get(\'wp_9999_status\',{}).get(\'promoted\') is False"'),
            _cmd("python -m estate.cli.main validation-production-readiness --json"),
            _cmd("python -m estate.cli.main validate-work-package --id WP-0121 --json"),
            _cmd("python -c \"import json; from pathlib import Path; p=Path('runtime/validation/work_packages/WP-0122_validation.json'); assert p.is_file(); assert json.loads(p.read_text(encoding='utf-8')).get('validation_status') in {'passed','passed_with_findings'}\""),
            _cmd("python -c \"import json; from pathlib import Path; p=Path('runtime/validation/work_packages/WP-0123_validation.json'); assert p.is_file(); assert json.loads(p.read_text(encoding='utf-8')).get('validation_status') in {'passed','passed_with_findings'}\""),
            _cmd("python -c \"import json; from pathlib import Path; p=Path('runtime/validation/work_packages/WP-0124_validation.json'); assert p.is_file(); assert json.loads(p.read_text(encoding='utf-8')).get('validation_status') in {'passed','passed_with_findings'}\""),
            _cmd('python -c "from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt(\'WP-0125\'); assert r[\'receipt_status\']==\'complete\', r"'),
        ],
    },

    "WP-0126": {
        "recipe_id": "wp-0126-resident-interaction-framework",
        "title": "WP-0126 — Resident Interaction Framework and Local LLM Governance",
        "description": "Validates resident interaction framework reports, templates, chat persistence, redaction, surface inspection, dependent packages, production readiness, and receipt.",
        "required_checks": ["Reports exist", "Templates exist", "Chat persists", "Redaction suppresses normal history", "Surface inspection reports versions", "Extension mechanism documents CDE mood arc", "Prerequisites pass", "Receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["operations/residents/WP-0126_resident_interaction_framework_report.md", "runtime/residents/WP-0126_resident_interaction_framework_report.json", "docs/operations/residents/resident_interaction_template.md", "docs/operations/residents/resident_api_surface_standard.md", "docs/operations/residents/resident_implementation_profile_template.md", "docs/operations/residents/resident_api_extension_proposal_template.md", "collaboration/work_packages/completions/WP-0126_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Resident chat, memory redaction, surface inspection, versioning, and extension artifacts validate"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -c "import json; from pathlib import Path; md=Path(\'operations/residents/WP-0126_resident_interaction_framework_report.md\'); js=Path(\'runtime/residents/WP-0126_resident_interaction_framework_report.json\'); assert md.is_file(); data=json.loads(js.read_text(encoding=\'utf-8\')); required=[\'local_llm_adapter_discovery_status\',\'deterministic_fallback_status\',\'conversation_persistence_path\',\'forget_redaction_mechanism\',\'authority_handling\',\'resident_api_surface_inspection_path\',\'resident_api_standard_versioning_mechanism\',\'resident_implementation_versioning_mechanism\',\'resident_api_surface_extension_mechanism\',\'character_development_engineer_extensibility_example\']; missing=[k for k in required if not data.get(k)]; assert not missing, missing"'),
            _cmd('python -c "from pathlib import Path; paths=[\'docs/operations/residents/resident_interaction_template.md\',\'docs/operations/residents/resident_api_surface_standard.md\',\'docs/operations/residents/resident_implementation_profile_template.md\',\'docs/operations/residents/resident_api_extension_proposal_template.md\']; assert all(Path(p).is_file() for p in paths); text=Path(paths[-1]).read_text(encoding=\'utf-8\'); assert \'character.mood_arc.evaluate\' in text"'),
            _cmd('python -c "from estate.core.resident_interaction import process_chat, load_history, forget_conversation, resident_surface; import tempfile; root=tempfile.mkdtemp(); p=process_chat(\'alfred\', \'WP-0126 validation prompt\', root=root); assert p[\'turn\'][\'resident_surface\'][\'resident_api_standard_version\']==\'resident-api-standard-v1\'; assert p[\'turn\'][\'authority\'][\'action_executed\'] is False; h=load_history(\'alfred\', session_id=p[\'session_id\'], root=root); assert h[\'sessions\'][0][\'turns\']; f=forget_conversation(p[\'session_id\'], root=root); assert f[\'ok\']; h2=load_history(\'alfred\', session_id=p[\'session_id\'], root=root); assert h2[\'sessions\'][0][\'turns\']==[]; s=resident_surface(\'alfred\'); assert s[\'resident_implementation_version\']; assert any(c[\'id\']==\'character.mood_arc.evaluate\' for c in s[\'capabilities\'])"'),
            _cmd('python -m estate.cli.main resident-interaction-surface --resident alfred --json'),
            _cmd("python -c \"import json; from pathlib import Path; p=Path('runtime/validation/work_packages/WP-0122_validation.json'); assert p.is_file(); assert json.loads(p.read_text(encoding='utf-8')).get('validation_status') in {'passed','passed_with_findings'}\""),
            _cmd("python -c \"import json; from pathlib import Path; p=Path('runtime/validation/work_packages/WP-0123_validation.json'); assert p.is_file(); assert json.loads(p.read_text(encoding='utf-8')).get('validation_status') in {'passed','passed_with_findings'}\""),
            _cmd("python -c \"import json; from pathlib import Path; p=Path('runtime/validation/work_packages/WP-0124_validation.json'); assert p.is_file(); assert json.loads(p.read_text(encoding='utf-8')).get('validation_status') in {'passed','passed_with_findings'}\""),
            _cmd("python -c \"import json; from pathlib import Path; p=Path('runtime/validation/work_packages/WP-0125_validation.json'); assert p.is_file(); assert json.loads(p.read_text(encoding='utf-8')).get('validation_status') in {'passed','passed_with_findings'}\""),
            _cmd('python -m estate.cli.main validation-production-readiness --json'),
            _cmd('python -c "from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt(\'WP-0126\'); assert r[\'receipt_status\']==\'complete\', r"'),
        ],
    },


    "WP-0127": {
        "recipe_id": "wp-0127-alfred-operations-center-chat",
        "title": "WP-0127 — Alfred Operations Center Chat Implementation",
        "description": "Validates Alfred's Operations Center front-door chat UI, local resident interaction endpoint wiring, conversation persistence, version reporting, authority/memory messaging, prerequisite framework status, and completion receipt.",
        "required_checks": ["Reports exist", "JSON companion parses", "Operations Center HTML contains Alfred chat input", "Operations Center HTML contains Alfred send control", "Alfred chat endpoint accepts prompt", "Conversation persists", "Surface versions reported", "Authority and memory behavior reported", "WP-0126 remains passing", "Production readiness executes", "Receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["operations/residents/alfred/WP-0127_alfred_operations_center_chat_report.md", "runtime/residents/alfred/WP-0127_alfred_operations_center_chat_report.json", "collaboration/work_packages/completions/WP-0127_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "Alfred chat claims privileged execution authority"],
        "success_criteria": ["Alfred Operations Center chat validates through the WP-0126 resident interaction framework"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -c "import json; from pathlib import Path; md=Path(\'operations/residents/alfred/WP-0127_alfred_operations_center_chat_report.md\'); js=Path(\'runtime/residents/alfred/WP-0127_alfred_operations_center_chat_report.json\'); assert md.is_file(); data=json.loads(js.read_text(encoding=\'utf-8\')); required=[\'wp_0126_framework_status\',\'alfred_ui_surfaces_changed\',\'endpoint_paths_used\',\'alfred_resident_api_standard_version\',\'alfred_resident_implementation_version\',\'conversation_persistence_path\',\'example_prompt_and_response\',\'authority_and_memory_behavior_shown_to_steward\',\'server_startup_status\']; missing=[k for k in required if not data.get(k)]; assert not missing, missing"'),
            _cmd('python -c "from estate.core.steward_command_center import generate_command_center, render_command_center_html; html=render_command_center_html(generate_command_center(write=False)); assert \'id=\\\"alfred-chat-input\\\"\' in html; assert \'id=\\\"alfred-chat-send\\\"\' in html; assert \'/api/residents/alfred/surface\' in html"'),
            _cmd('python -c "from estate.core.resident_interaction import process_chat, load_history, resident_surface; import tempfile; root=tempfile.mkdtemp(); p=process_chat(\'alfred\', \'Alfred, what should I look at first?\', root=root); assert p[\'ok\']; assert p[\'turn\'][\'authority\'][\'action_executed\'] is False; h=load_history(\'alfred\', session_id=p[\'session_id\'], root=root); assert h[\'sessions\'][0][\'turns\']; s=resident_surface(\'alfred\', root=root); assert s[\'resident_api_standard_version\']==\'resident-api-standard-v1\'; assert s[\'resident_implementation_version\']==\'alfred-operations-implementation-v1\'"'),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0126 --json'),
            _cmd('python -m estate.cli.main validation-production-readiness --json'),
            _cmd('python -c "from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt(\'WP-0127\'); assert r[\'receipt_status\']==\'complete\', r"'),
        ],
    },


    "WP-0128": {
        "recipe_id": "wp-0128-alfred-local-llm-response-path",
        "title": "WP-0128 — Alfred Local LLM Response Path Repair",
        "description": "Validates Alfred's local Ollama adapter path, prompt/context construction, fallback metadata, UI mode transparency, distinct mocked local LLM answers, reports, dependent validations, and receipt.",
        "required_checks": ["WP-0128 report exists", "JSON companion parses", "Local Ollama adapter exists", "Alfred qwen3 selection policy exists", "process_chat local LLM path exists", "Fallback remains available", "Role and mode tests exist", "Persisted LLM metadata exists", "UI/API mode transparency exists", "Production readiness executes", "Receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["operations/residents/alfred/WP-0128_alfred_local_llm_response_path_report.md", "runtime/residents/alfred/WP-0128_alfred_local_llm_response_path_report.json", "collaboration/work_packages/completions/WP-0128_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "Role and mode prompts return identical mocked local LLM responses"],
        "success_criteria": ["Alfred uses local_llm when available and exposes mode/model metadata while preserving deterministic fallback"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -c "import json; from pathlib import Path; md=Path(\'operations/residents/alfred/WP-0128_alfred_local_llm_response_path_report.md\'); js=Path(\'runtime/residents/alfred/WP-0128_alfred_local_llm_response_path_report.json\'); assert md.is_file(); data=json.loads(js.read_text(encoding=\'utf-8\')); required=[\'local_model_discovery_mechanism\',\'selected_alfred_model_policy\',\'provider_endpoint\',\'prompt_construction_summary\',\'context_packet_summary\',\'fallback_behavior\',\'ui_mode_transparency_changes\',\'example_role_prompt_and_response\',\'example_mode_prompt_and_response\',\'tests_run\',\'validation_commands_run\']; missing=[k for k in required if not data.get(k)]; assert not missing, missing"'),
            _cmd('python -c "from pathlib import Path; t=Path(\'src/estate/core/resident_interaction.py\').read_text(encoding=\'utf-8\'); required=[\'class LocalOllamaAdapter\',\'api/tags\',\'qwen3:8b\',\'_alfred_prompt\',\'_context_packet\',\'adapter.generate\',\'_fallback_response\',\'fallback_reason\']; missing=[x for x in required if x not in t]; assert not missing, missing"'),
            _cmd('python -c "from pathlib import Path; t=Path(\'tests/test_resident_interaction.py\').read_text(encoding=\'utf-8\'); required=[\'Good afternoon Alfred, define your role for me.\',\'Alfred, are you running from JSON files or an LLM right now?\',\'MockOllamaAdapter\',\'fallback_used\']; missing=[x for x in required if x not in t]; assert not missing, missing"'),
            _cmd("python -c \"from pathlib import Path; t=Path(\'src/estate/core/steward_command_center.py\').read_text(encoding=\'utf-8\'); assert \'Mode:\' in t and \'llmSourceLine\' in t and \'provider\' in t and \'model\' in t\""),
            _cmd('python -m pytest tests/test_resident_interaction.py tests/test_steward_command_center.py -q'),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0126 --json'),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0127 --json'),
            _cmd('python -m estate.cli.main validation-production-readiness --json'),
            _cmd('python -c "from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt(\'WP-0128\'); assert r[\'receipt_status\']==\'complete\', r"'),
        ],
    },


    "WP-0129": {
        "recipe_id": "wp-0129-resident-multimodal-paste",
        "title": "WP-0129 — Resident Multimodal Paste and Image Discussion",
        "description": "Validates local-first resident attachments, Alfred paste UI, bounded attachment storage, local vision fallback/summary behavior, redaction, reports, and receipt.",
        "required_checks": ["Reports exist", "JSON companion parses", "Attachment model exists", "Local vision adapter exists", "Paste UI exists", "Endpoint accepts attachments", "Attachment tests pass", "Receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["operations/residents/alfred/WP-0129_resident_multimodal_paste_report.md", "runtime/residents/alfred/WP-0129_resident_multimodal_paste_report.json", "collaboration/work_packages/completions/WP-0129_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "Attachments escape bounded runtime storage", "Alfred fakes visual inspection when no local vision model is available"],
        "success_criteria": ["Pasted image/text attachments persist locally and are linked to resident turns with truthful local vision status"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -c "import json; from pathlib import Path; md=Path(\'operations/residents/alfred/WP-0129_resident_multimodal_paste_report.md\'); js=Path(\'runtime/residents/alfred/WP-0129_resident_multimodal_paste_report.json\'); assert md.is_file(); data=json.loads(js.read_text(encoding=\'utf-8\')); required=[\'attachment_storage_path\',\'schema_summary\',\'api_design\',\'ui_paste_behavior\',\'local_vision_adapter_status\',\'detected_vision_capable_models\',\'fallback_behavior\',\'example_pasted_image_turn_metadata\',\'forget_redaction_behavior\',\'tests_run\',\'validation_commands_run\',\'known_limitations\',\'recommended_next_action\']; missing=[k for k in required if k not in data]; assert not missing, missing"'),
            _cmd('python -c "from pathlib import Path; t=Path(\'src/estate/core/resident_interaction.py\').read_text(encoding=\'utf-8\'); required=[\'ATTACHMENT_STORE\',\'class LocalVisionAdapter\',\'create_attachment\',\'data_base64\',\'vision_status\',\'attachments\']; missing=[x for x in required if x not in t]; assert not missing, missing"'),
            _cmd('python -c "from pathlib import Path; t=Path(\'src/estate/core/steward_command_center.py\').read_text(encoding=\'utf-8\'); required=[\'alfred-pending-attachments\',\'clipboard_paste\',\'paste\',\'attachmentHtml\',\'data-remove-attachment\']; missing=[x for x in required if x not in t]; assert not missing, missing"'),
            _cmd('python -m pytest tests/test_resident_interaction.py tests/test_steward_command_center.py -q'),
            _cmd('python -c "from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt(\'WP-0129\'); assert r[\'receipt_status\']==\'complete\', r"'),
        ],
    },

    "WP-0130": {
        "recipe_id": "wp-0130-local-vision-model-enablement",
        "title": "WP-0130 — Local Vision Model Enablement for Resident Images",
        "description": "Validates local-only Ollama vision model configuration, detection, Alfred image summary integration, truthful fallback, reports, and completion receipt.",
        "required_checks": ["Vision config exists", "Reports exist", "JSON companion parses", "Vision detection helpers exist", "No cloud guarantee exists", "Attachment vision metadata exists", "Alfred summary tests exist", "Receipt is complete"],
        "observational_checks": ["Steward local smoke test documented"],
        "expected_artifacts": ["runtime/residents/alfred/vision_model_config.json", "operations/residents/alfred/WP-0130_local_vision_model_enablement_report.md", "runtime/residents/alfred/WP-0130_local_vision_model_enablement_report.json", "collaboration/work_packages/completions/WP-0130_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "Cloud vision is enabled", "Alfred fakes visual inspection when no local vision model is available"],
        "success_criteria": ["Configured local Ollama vision models are preferred when present and image attachments record processed or unavailable vision status truthfully"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"import json; from pathlib import Path; cfg=json.loads(Path('runtime/residents/alfred/vision_model_config.json').read_text()); assert cfg['provider']=='ollama'; assert cfg['cloud_allowed'] is False; assert cfg['fallback_behavior']=='vision_unavailable'\""),
            _cmd("python -c \"import json; from pathlib import Path; md=Path('operations/residents/alfred/WP-0130_local_vision_model_enablement_report.md'); js=Path('runtime/residents/alfred/WP-0130_local_vision_model_enablement_report.json'); assert md.is_file(); data=json.loads(js.read_text(encoding='utf-8')); required=['current_git_commit','detected_ollama_models','detected_vision_capable_models','selected_vision_model','configuration_path','adapter_behavior','example_image_prompt','fallback_behavior','tests_run','validation_commands_run','known_limitations','recommended_steward_install_command']; missing=[k for k in required if k not in data]; assert not missing, missing\""),
            _cmd("python -c \"from pathlib import Path; t=Path('src/estate/core/resident_interaction.py').read_text(encoding='utf-8'); required=['VISION_CONFIG_PATH','load_vision_config','is_vision_capable_model','api/show','cloud_allowed','vision_capable_models','Local image summaries']; missing=[x for x in required if x not in t]; assert not missing, missing\""),
            _cmd("python -c \"from pathlib import Path; t=Path('tests/test_resident_interaction.py').read_text(encoding='utf-8'); required=['test_wp0130_vision_capable_model_detection','test_wp0130_configured_vision_model_preference_and_no_cloud','test_wp0130_alfred_uses_vision_summary','test_wp0130_attachment_metadata_records_unavailable']; missing=[x for x in required if x not in t]; assert not missing, missing\""),
            _cmd('python -m pytest tests/test_resident_interaction.py tests/test_steward_command_center.py -q'),
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0130'); assert r['receipt_status']=='complete', r\""),
        ],
    },


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
    "WP-0116": {
        "recipe_id": "wp-0116-final-production-readiness-exception-closure",
        "title": "WP-0116 — Final Production-Readiness Exception Closure",
        "description": "Validates final exception closure reporting, Helen-path handling, placeholder quarantine, baseline package validations, production-readiness generation, and WP-0116 receipt completeness.",
        "required_checks": ["Final exception markdown report exists", "Final exception JSON report parses", "Initial 12 blockers are reported", "Before and after totals are present", "WP-0106, WP-0107, and WP-9999 are explicitly reported", "Production readiness executes", "Baseline packages remain passing", "WP-0116 completion receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/backlog_burn_down/WP-0116_final_exception_closure_report.md", "runtime/validation/backlog_burn_down/WP-0116_final_exception_closure_report.json", "collaboration/work_packages/completions/WP-0116_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "WP-9999 is falsely promoted"],
        "success_criteria": ["Required commands exit zero", "WP-9999 remains classified as intentionally invalid placeholder/test artifact"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from pathlib import Path; assert Path('operations/validation/backlog_burn_down/WP-0116_final_exception_closure_report.md').is_file()\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/backlog_burn_down/WP-0116_final_exception_closure_report.json').read_text(encoding='utf-8')); ids={'WP-0016','WP-0017','WP-0018','WP-0040','WP-0056','WP-0063','WP-0073','WP-0089','WP-0094','WP-0106','WP-0107','WP-9999'}; assert ids <= set(data.get('initial_blockers', [])); assert 'before_totals' in data and 'after_totals' in data; statuses=data.get('package_statuses', {}); assert all(wp in statuses for wp in ['WP-0106','WP-0107','WP-9999']); assert statuses['WP-9999'].get('production_readiness_status') != 'ready'\""),
            _cmd("python -m estate.cli.main validation-production-readiness --json"),
            _cmd("python -m estate.cli.main validate-work-package --id WP-0102 --json"),
            _cmd("python -m estate.cli.main validate-work-package --id WP-0105 --json"),
            _cmd("python -m estate.cli.main validate-work-package --id WP-0111 --json"),
            _cmd("python -m estate.cli.main validate-work-package --id WP-0114 --json"),
            _cmd("python -m estate.cli.main validate-work-package --id WP-0115 --json"),
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0116'); assert r['receipt_status']=='complete', r\""),
        ],
    },
    "WP-0117": {
        "recipe_id": "wp-0117-office-snapshot-export-button",
        "title": "WP-0117 — Office Snapshot Export Button",
        "description": "Self-validates the local-only Office Snapshot export control, browser ZIP implementation, manifest/schema metadata, source artifact context, privacy boundary, tests, and completion receipt.",
        "required_checks": ["Office Snapshot button is rendered", "Browser ZIP export implementation exists", "Snapshot manifest/schema behavior exists", "Source artifacts are represented", "Local-only/no-upload notice exists", "Tests cover button and manifest", "Receipt is complete"],
        "observational_checks": ["Screenshot support is documented as a limitation"],
        "expected_artifacts": ["src/estate/core/steward_command_center.py", "tests/test_steward_command_center.py", "collaboration/work_packages/completions/WP-0117_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "Snapshot export code references external upload behavior"],
        "success_criteria": ["Required commands exit zero", "Office UI can create a local snapshot ZIP without an external service"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.steward_command_center import generate_command_center, render_command_center_html; h=render_command_center_html(generate_command_center(write=False)); assert 'id=\\\"office-snapshot-button\\\"' in h and 'Office Snapshot' in h and 'exportOfficeSnapshot' in h and 'function makeZip' in h\""),
            _cmd("python -c \"from estate.core.steward_command_center import generate_command_center, build_office_snapshot_manifest; m=build_office_snapshot_manifest(generate_command_center(write=False)); assert m['schema_version']=='office-snapshot-v1'; assert m['local_only'] is True; assert {'snapshot_manifest.json','dom_state.json','ui_metadata.json','source_artifacts.json','README.md'} <= set(m['package_contents']); assert m['source_artifact_count'] >= 1\""),
            _cmd("python -c \"from pathlib import Path; t=Path('src/estate/core/steward_command_center.py').read_text(encoding='utf-8'); assert 'No upload is performed' in t and 'privacy_notice' in t and 'fetch(' not in t[t.index('async function exportOfficeSnapshot'):t.index('document.addEventListener(\\\'click\\\', event => { if(event.target.closest(\\\'#office-snapshot-button\\\'))')]\""),
            _cmd("python -c \"from pathlib import Path; t=Path('tests/test_steward_command_center.py').read_text(encoding='utf-8'); assert 'test_office_snapshot_button_manifest_and_local_zip_export_are_rendered' in t; assert 'office-snapshot-button' in t; assert 'build_office_snapshot_manifest' in t\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('collaboration/work_packages/completions/WP-0117_codex_done.json').read_text(encoding='utf-8')); assert data.get('work_package_id')=='WP-0117'; assert data.get('ready_for_ca_review') is True; assert data.get('merge_authority')=='ca_verified_auto_merge_allowed'; assert data.get('screenshot_support_status')\""),
        ],
    },
    "WP-0118": {
        "recipe_id": "wp-0118-office-steward-verb-surface-control-backlog",
        "title": "WP-0118 — Office of the Steward Verb Surface Audit and Control Backlog",
        "description": "Validates the Office verb-surface backlog, reusable action template, current tab inventory, action classification model, follow-up package plan, and completion receipt.",
        "required_checks": ["Backlog exists", "Template exists", "Current Office tabs inventoried", "Noun/status and verbs/actions distinguished", "Action classification model exists", "Per-tab verb matrix exists", "Follow-up work packages recommended", "Receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["docs/operations/Office_of_the_Steward_Verb_Surface_Control_Backlog_v1.md", "docs/templates/Office_Action_Surface_Work_Package_Template.md", "collaboration/work_packages/completions/WP-0118_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero", "Backlog covers every implemented Office tab", "Template requires authority classification and validation behavior"],
        "continue_on_failure": True,
        "commands": [
            _cmd('python -c "from pathlib import Path; p=Path(\'docs/operations/Office_of_the_Steward_Verb_Surface_Control_Backlog_v1.md\'); assert p.is_file(); t=p.read_text(encoding=\'utf-8\'); required=[\'Current Noun Surface Inventory\',\'Verb Surface Philosophy\',\'Action Classification\',\'Per-Tab Verb Matrix\',\'Immediate Implementation Breakdown\',\'Control Safety Rules\',\'Validation Recipe for WP-0118\']; missing=[x for x in required if x not in t]; assert not missing, missing"'),
            _cmd('python -c "from pathlib import Path; import ast; src=Path(\'src/estate/core/steward_command_center.py\').read_text(encoding=\'utf-8\'); tree=ast.parse(src); tabs=[]; [tabs.extend([elt.value for elt in node.value.elts if isinstance(elt, ast.Dict) for key, elt in []]) for node in []]; office=[]\nfor node in tree.body:\n    if isinstance(node, ast.Assign) and any(getattr(target, \'id\', None)==\'OFFICE_TABS\' for target in node.targets):\n        office=[d for d in ast.literal_eval(node.value)]\nlabels=[item[\'label\'] for item in office]; text=Path(\'docs/operations/Office_of_the_Steward_Verb_Surface_Control_Backlog_v1.md\').read_text(encoding=\'utf-8\'); missing=[label for label in labels if label not in text]; assert len(labels)>=19, labels; assert not missing, missing"'),
            _cmd('python -c "from pathlib import Path; t=Path(\'docs/operations/Office_of_the_Steward_Verb_Surface_Control_Backlog_v1.md\').read_text(encoding=\'utf-8\').lower(); required=[\'noun surfaces show state\',\'verb surfaces let the steward act\',\'safe read-only\',\'safe local generated-artifact update\',\'steward-confirmed local mutation\',\'authority-gated institutional action\',\'prohibited until future governance/tooling exists\']; missing=[x for x in required if x not in t]; assert not missing, missing"'),
            _cmd("python -c 'from pathlib import Path; t=Path(\"docs/operations/Office_of_the_Steward_Verb_Surface_Control_Backlog_v1.md\").read_text(encoding=\"utf-8\"); assert \"| Tab/workspace | Current noun/status surface | Proposed verbs/actions |\" in t; assert t.count(\"WP-0118-F\") >= 9; assert \"Buttons must not silently execute pending work packages\" in t'"),
            _cmd('python -c "from pathlib import Path; p=Path(\'docs/templates/Office_Action_Surface_Work_Package_Template.md\'); assert p.is_file(); t=p.read_text(encoding=\'utf-8\').lower(); required=[\'target tab/workspace\',\'current noun/status surface\',\'new verbs/actions\',\'authority classification\',\'confirmation behavior\',\'local command/api surface\',\'source artifacts read\',\'artifacts written\',\'ui placement\',\'failure handling\',\'tests\',\'validation recipe\',\'completion receipt\']; missing=[x for x in required if x not in t]; assert not missing, missing"'),
            _cmd('python -c "from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt(\'WP-0118\'); assert r[\'receipt_status\']==\'complete\', r"'),
        ],
    },

    "WP-0119": {
        "recipe_id": "wp-0119-windows-resident-runtime-test-stabilization",
        "title": "WP-0119 — Windows Resident Runtime Test Stabilization",
        "description": "Validates Windows-local resident runtime stabilization for command-center artifact generation and canonical duty runtime artifact paths.",
        "required_checks": ["Repair markdown report exists", "Repair JSON report parses", "Failure causes are reported", "Repaired resident packages validate", "Production readiness executes", "WP-9999 remains not promoted", "Alfred/Helen path status is reported", "Completion receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/backlog_burn_down/WP-0119_windows_resident_runtime_test_stabilization_report.md", "runtime/validation/backlog_burn_down/WP-0119_windows_resident_runtime_test_stabilization_report.json", "collaboration/work_packages/completions/WP-0119_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "WP-9999 is falsely promoted", "Any repaired resident runtime validation is not passed"],
        "success_criteria": ["Required commands exit zero", "WP-0106 through WP-0110 and WP-0116 through WP-0118 validate successfully", "WP-9999 remains quarantined/not promoted"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from pathlib import Path; assert Path('operations/validation/backlog_burn_down/WP-0119_windows_resident_runtime_test_stabilization_report.md').is_file()\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/backlog_burn_down/WP-0119_windows_resident_runtime_test_stabilization_report.json').read_text(encoding='utf-8')); required=['wp_0106_failure_cause','wp_0108_failure_cause','wp_0110_failure_cause']; missing=[k for k in required if not data.get(k)]; assert not missing, missing; validation_keys=['wp_0106_validation_result_after_repair','wp_0107_validation_result_after_repair','wp_0108_validation_result_after_repair','wp_0109_validation_result_after_repair','wp_0110_validation_result_after_repair','wp_0116_validation_result_after_repair','wp_0117_validation_result_after_repair','wp_0118_validation_result_after_repair']; assert all(data.get(k, {}).get('validation_status') == 'passed' for k in validation_keys); assert data.get('production_readiness_after'); assert data.get('wp_9999_quarantine_status') in {'quarantined_not_promoted','not_promoted'}; assert data.get('alfred_helen_runtime_path_status')\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/work_packages/WP-0106_validation.json').read_text(encoding='utf-8')); assert data.get('validation_status') == 'passed', data.get('validation_status')\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/work_packages/WP-0107_validation.json').read_text(encoding='utf-8')); assert data.get('validation_status') == 'passed', data.get('validation_status')\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/work_packages/WP-0108_validation.json').read_text(encoding='utf-8')); assert data.get('validation_status') == 'passed', data.get('validation_status')\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/work_packages/WP-0109_validation.json').read_text(encoding='utf-8')); assert data.get('validation_status') == 'passed', data.get('validation_status')\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/work_packages/WP-0110_validation.json').read_text(encoding='utf-8')); assert data.get('validation_status') == 'passed', data.get('validation_status')\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/work_packages/WP-0116_validation.json').read_text(encoding='utf-8')); assert data.get('validation_status') == 'passed', data.get('validation_status')\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/work_packages/WP-0117_validation.json').read_text(encoding='utf-8')); assert data.get('validation_status') == 'passed', data.get('validation_status')\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/work_packages/WP-0118_validation.json').read_text(encoding='utf-8')); assert data.get('validation_status') == 'passed', data.get('validation_status')\""),
            _cmd("python -m estate.cli.main validation-production-readiness --json"),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/production_readiness_report.json').read_text(encoding='utf-8')); assert all(item.get('work_package_id') != 'WP-9999' for key in ['blocking_work_packages', 'ready_for_chief_architect_production_readiness_acceptance'] for item in data.get(key, []))\""),
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0119'); assert r['receipt_status']=='complete', r\""),
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
            _cmd("python -c \"import sys; sys.path.insert(0, 'src'); import pytest; raise SystemExit(pytest.main(['tests/test_resident_presence.py', 'tests/test_resident_cards.py', 'tests/test_steward_command_center.py']))\""),
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
            _cmd("python -c \"import sys; sys.path.insert(0, 'src'); import pytest; raise SystemExit(pytest.main(['tests/test_alfred_duty.py', 'tests/test_resident_presence.py', 'tests/test_resident_cards.py']))\""),
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
            _cmd("python -c \"import sys; sys.path.insert(0, 'src'); import pytest; raise SystemExit(pytest.main(['tests/test_helen_duty.py', 'tests/test_resident_presence.py', 'tests/test_resident_cards.py']))\""),
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
            _cmd("python -c \"import sys; sys.path.insert(0, 'src'); import pytest; raise SystemExit(pytest.main(['tests/test_resident_conversation_sessions.py', 'tests/test_resident_conversations.py']))\""),
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
            _cmd("python -c \"import sys; sys.path.insert(0, 'src'); import pytest; raise SystemExit(pytest.main(['tests/test_resident_authority.py', 'tests/test_alfred_duty.py', 'tests/test_helen_duty.py', 'tests/test_resident_conversation_sessions.py', 'tests/test_resident_cards.py']))\""),
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

    "WP-0113": {
        "recipe_id": "wp-0113-helen-next-batch-recommendation",
        "title": "WP-0113 — Helen Next-Batch Recommendation",
        "description": "Validates the WP-0113 recommendation artifacts and confirms it did not falsely close the Helen implementation backlog.",
        "required_checks": ["Recommendation markdown exists", "Recommendation JSON parses", "Helen backlog packages remain pending", "Completion receipt is complete"],
        "observational_checks": ["Production-readiness report is locally executable"],
        "expected_artifacts": ["operations/validation/backlog_burn_down/WP-0113_helen_next_batch_recommendation.md", "runtime/validation/backlog_burn_down/WP-0113_helen_next_batch_recommendation.json", "collaboration/work_packages/completions/WP-0113_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "WP-0106 through WP-0110 are falsely marked complete"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from pathlib import Path; paths=['operations/validation/backlog_burn_down/WP-0113_helen_next_batch_recommendation.md','runtime/validation/backlog_burn_down/WP-0113_helen_next_batch_recommendation.json']; missing=[p for p in paths if not Path(p).is_file()]; assert not missing, missing\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/backlog_burn_down/WP-0113_helen_next_batch_recommendation.json').read_text(encoding='utf-8')); text=json.dumps(data).lower(); required=['wp-0106','wp-0107','wp-0108','wp-0109','wp-0110']; missing=[wp for wp in required if wp.lower() not in text]; assert not missing, missing\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/backlog_burn_down/WP-0113_helen_next_batch_recommendation.json').read_text(encoding='utf-8')); completed=set(data.get('packages_newly_production_ready', [])) | set(data.get('packages_repaired', [])); pending={f'WP-{i:04d}' for i in range(106,111)}; assert not (completed & pending), sorted(completed & pending)\""),
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0113'); assert r['receipt_status']=='complete', r\""),
            _cmd('python -m estate.cli.main validation-production-readiness --json', required=False),
        ],
    },

    "WP-0114": {
        "recipe_id": "wp-0114-historical-production-readiness-sweep",
        "title": "WP-0114 — Historical Production-Readiness Sweep",
        "description": "Validates the WP-0114 sweep reports, repaired-package validation evidence, pending-package safety checks, and completion receipt.",
        "required_checks": ["Sweep reports exist", "Sweep JSON parses", "Before and after totals are present", "At least one package was classified or repaired", "Pending implementation packages were not falsely completed", "Production-readiness validation executes", "WP-0102/WP-0105/WP-0111 remain passing", "WP-0114 receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/backlog_burn_down/WP-0114_historical_sweep_report.md", "runtime/validation/backlog_burn_down/WP-0114_historical_sweep_report.json", "collaboration/work_packages/completions/WP-0114_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero", "A known pending implementation package is falsely marked complete"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from pathlib import Path; paths=['operations/validation/backlog_burn_down/WP-0114_historical_sweep_report.md','runtime/validation/backlog_burn_down/WP-0114_historical_sweep_report.json']; missing=[p for p in paths if not Path(p).is_file()]; assert not missing, missing\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/backlog_burn_down/WP-0114_historical_sweep_report.json').read_text(encoding='utf-8')); assert data.get('production_readiness_totals_before') and data.get('production_readiness_totals_after'), data.keys()\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/backlog_burn_down/WP-0114_historical_sweep_report.json').read_text(encoding='utf-8')); count=len(data.get('packages_scanned', []))+len(data.get('packages_repaired_by_recipe_addition', []))+len(data.get('packages_repaired_by_receipt_normalization', [])); assert count > 0, data\""),
            _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/backlog_burn_down/WP-0114_historical_sweep_report.json').read_text(encoding='utf-8')); completed=set(data.get('packages_repaired_by_receipt_creation', [])); pending={f'WP-{i:04d}' for i in range(106,111)}; assert not (completed & pending), sorted(completed & pending)\""),
            _cmd('python -m estate.cli.main validation-production-readiness --json'),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0102 --json'),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0105 --json'),
            _cmd('python -m estate.cli.main validate-work-package --id WP-0111 --json'),
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0114'); assert r['receipt_status']=='complete', r\""),
        ],
    },

}


# WP-0115 generated conservative historical receipt/artifact recipes.
# These recipes intentionally use local, cross-platform Python checks only.
VALIDATION_RECIPES.update({
    "WP-0014": {
        "recipe_id": "wp-0014-historical-receipt-artifact-presence",
        "title": "WP-0014 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0014.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0014_validation.md", "runtime/validation/work_packages/WP-0014_validation.json", "collaboration/work_packages/completions/WP-0014_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0014'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0014_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0022": {
        "recipe_id": "wp-0022-historical-receipt-artifact-presence",
        "title": "WP-0022 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0022.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0022_validation.md", "runtime/validation/work_packages/WP-0022_validation.json", "collaboration/work_packages/completions/WP-0022_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0022'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0022_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0023": {
        "recipe_id": "wp-0023-historical-receipt-artifact-presence",
        "title": "WP-0023 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0023.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0023_validation.md", "runtime/validation/work_packages/WP-0023_validation.json", "collaboration/work_packages/completions/WP-0023_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0023'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0023_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0024": {
        "recipe_id": "wp-0024-historical-receipt-artifact-presence",
        "title": "WP-0024 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0024.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0024_validation.md", "runtime/validation/work_packages/WP-0024_validation.json", "collaboration/work_packages/completions/WP-0024_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0024'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0024_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0025": {
        "recipe_id": "wp-0025-historical-receipt-artifact-presence",
        "title": "WP-0025 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0025.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0025_validation.md", "runtime/validation/work_packages/WP-0025_validation.json", "collaboration/work_packages/completions/WP-0025_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0025'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0025_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0026": {
        "recipe_id": "wp-0026-historical-receipt-artifact-presence",
        "title": "WP-0026 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0026.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0026_validation.md", "runtime/validation/work_packages/WP-0026_validation.json", "collaboration/work_packages/completions/WP-0026_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0026'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0026_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0028": {
        "recipe_id": "wp-0028-historical-receipt-artifact-presence",
        "title": "WP-0028 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0028.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0028_validation.md", "runtime/validation/work_packages/WP-0028_validation.json", "collaboration/work_packages/completions/WP-0028_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0028'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0028_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0030": {
        "recipe_id": "wp-0030-historical-receipt-artifact-presence",
        "title": "WP-0030 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0030.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0030_validation.md", "runtime/validation/work_packages/WP-0030_validation.json", "collaboration/work_packages/completions/WP-0030_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0030'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0030_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0031": {
        "recipe_id": "wp-0031-historical-receipt-artifact-presence",
        "title": "WP-0031 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0031.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0031_validation.md", "runtime/validation/work_packages/WP-0031_validation.json", "collaboration/work_packages/completions/WP-0031_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0031'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0031_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0032": {
        "recipe_id": "wp-0032-historical-receipt-artifact-presence",
        "title": "WP-0032 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0032.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0032_validation.md", "runtime/validation/work_packages/WP-0032_validation.json", "collaboration/work_packages/completions/WP-0032_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0032'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0032_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0033": {
        "recipe_id": "wp-0033-historical-receipt-artifact-presence",
        "title": "WP-0033 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0033.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0033_validation.md", "runtime/validation/work_packages/WP-0033_validation.json", "collaboration/work_packages/completions/WP-0033_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0033'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0033_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0034": {
        "recipe_id": "wp-0034-historical-receipt-artifact-presence",
        "title": "WP-0034 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0034.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0034_validation.md", "runtime/validation/work_packages/WP-0034_validation.json", "collaboration/work_packages/completions/WP-0034_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0034'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0034_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0035": {
        "recipe_id": "wp-0035-historical-receipt-artifact-presence",
        "title": "WP-0035 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0035.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0035_validation.md", "runtime/validation/work_packages/WP-0035_validation.json", "collaboration/work_packages/completions/WP-0035_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0035'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0035_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0039": {
        "recipe_id": "wp-0039-historical-receipt-artifact-presence",
        "title": "WP-0039 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0039.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0039_validation.md", "runtime/validation/work_packages/WP-0039_validation.json", "collaboration/work_packages/completions/WP-0039_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0039'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0039_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0041": {
        "recipe_id": "wp-0041-historical-receipt-artifact-presence",
        "title": "WP-0041 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0041.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0041_validation.md", "runtime/validation/work_packages/WP-0041_validation.json", "collaboration/work_packages/completions/WP-0041_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0041'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0041_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0042": {
        "recipe_id": "wp-0042-historical-receipt-artifact-presence",
        "title": "WP-0042 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0042.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0042_validation.md", "runtime/validation/work_packages/WP-0042_validation.json", "collaboration/work_packages/completions/WP-0042_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0042'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0042_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0043": {
        "recipe_id": "wp-0043-historical-receipt-artifact-presence",
        "title": "WP-0043 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0043.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0043_validation.md", "runtime/validation/work_packages/WP-0043_validation.json", "collaboration/work_packages/completions/WP-0043_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0043'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0043_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0044": {
        "recipe_id": "wp-0044-historical-receipt-artifact-presence",
        "title": "WP-0044 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0044.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0044_validation.md", "runtime/validation/work_packages/WP-0044_validation.json", "collaboration/work_packages/completions/WP-0044_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0044'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0044_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0045": {
        "recipe_id": "wp-0045-historical-receipt-artifact-presence",
        "title": "WP-0045 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0045.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0045_validation.md", "runtime/validation/work_packages/WP-0045_validation.json", "collaboration/work_packages/completions/WP-0045_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0045'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0045_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0046": {
        "recipe_id": "wp-0046-historical-receipt-artifact-presence",
        "title": "WP-0046 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0046.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0046_validation.md", "runtime/validation/work_packages/WP-0046_validation.json", "collaboration/work_packages/completions/WP-0046_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0046'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0046_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0047": {
        "recipe_id": "wp-0047-historical-receipt-artifact-presence",
        "title": "WP-0047 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0047.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0047_validation.md", "runtime/validation/work_packages/WP-0047_validation.json", "collaboration/work_packages/completions/WP-0047_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0047'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0047_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0048": {
        "recipe_id": "wp-0048-historical-receipt-artifact-presence",
        "title": "WP-0048 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0048.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0048_validation.md", "runtime/validation/work_packages/WP-0048_validation.json", "collaboration/work_packages/completions/WP-0048_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0048'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0048_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0049": {
        "recipe_id": "wp-0049-historical-receipt-artifact-presence",
        "title": "WP-0049 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0049.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0049_validation.md", "runtime/validation/work_packages/WP-0049_validation.json", "collaboration/work_packages/completions/WP-0049_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0049'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0049_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0050": {
        "recipe_id": "wp-0050-historical-receipt-artifact-presence",
        "title": "WP-0050 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0050.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0050_validation.md", "runtime/validation/work_packages/WP-0050_validation.json", "collaboration/work_packages/completions/WP-0050_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0050'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0050_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0051": {
        "recipe_id": "wp-0051-historical-receipt-artifact-presence",
        "title": "WP-0051 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0051.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0051_validation.md", "runtime/validation/work_packages/WP-0051_validation.json", "collaboration/work_packages/completions/WP-0051_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0051'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0051_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0054": {
        "recipe_id": "wp-0054-historical-receipt-artifact-presence",
        "title": "WP-0054 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0054.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0054_validation.md", "runtime/validation/work_packages/WP-0054_validation.json", "collaboration/work_packages/completions/WP-0054_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0054'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0054_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0055": {
        "recipe_id": "wp-0055-historical-receipt-artifact-presence",
        "title": "WP-0055 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0055.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0055_validation.md", "runtime/validation/work_packages/WP-0055_validation.json", "collaboration/work_packages/completions/WP-0055_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0055'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0055_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0061": {
        "recipe_id": "wp-0061-historical-receipt-artifact-presence",
        "title": "WP-0061 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0061.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0061_validation.md", "runtime/validation/work_packages/WP-0061_validation.json", "collaboration/work_packages/completions/WP-0061_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0061'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0061_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0062": {
        "recipe_id": "wp-0062-historical-receipt-artifact-presence",
        "title": "WP-0062 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0062.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0062_validation.md", "runtime/validation/work_packages/WP-0062_validation.json", "collaboration/work_packages/completions/WP-0062_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0062'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0062_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0064": {
        "recipe_id": "wp-0064-historical-receipt-artifact-presence",
        "title": "WP-0064 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0064.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0064_validation.md", "runtime/validation/work_packages/WP-0064_validation.json", "collaboration/work_packages/completions/WP-0064_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0064'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0064_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0069": {
        "recipe_id": "wp-0069-historical-receipt-artifact-presence",
        "title": "WP-0069 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0069.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0069_validation.md", "runtime/validation/work_packages/WP-0069_validation.json", "collaboration/work_packages/completions/WP-0069_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0069'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0069_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0071": {
        "recipe_id": "wp-0071-historical-receipt-artifact-presence",
        "title": "WP-0071 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0071.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0071_validation.md", "runtime/validation/work_packages/WP-0071_validation.json", "collaboration/work_packages/completions/WP-0071_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0071'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0071_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0072": {
        "recipe_id": "wp-0072-historical-receipt-artifact-presence",
        "title": "WP-0072 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0072.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0072_validation.md", "runtime/validation/work_packages/WP-0072_validation.json", "collaboration/work_packages/completions/WP-0072_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0072'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0072_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0082": {
        "recipe_id": "wp-0082-historical-receipt-artifact-presence",
        "title": "WP-0082 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0082.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0082_validation.md", "runtime/validation/work_packages/WP-0082_validation.json", "collaboration/work_packages/completions/WP-0082_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0082'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0082_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0083": {
        "recipe_id": "wp-0083-historical-receipt-artifact-presence",
        "title": "WP-0083 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0083.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0083_validation.md", "runtime/validation/work_packages/WP-0083_validation.json", "collaboration/work_packages/completions/WP-0083_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0083'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0083_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0084": {
        "recipe_id": "wp-0084-historical-receipt-artifact-presence",
        "title": "WP-0084 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0084.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0084_validation.md", "runtime/validation/work_packages/WP-0084_validation.json", "collaboration/work_packages/completions/WP-0084_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0084'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0084_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0100": {
        "recipe_id": "wp-0100-historical-receipt-artifact-presence",
        "title": "WP-0100 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0100.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0100_validation.md", "runtime/validation/work_packages/WP-0100_validation.json", "collaboration/work_packages/completions/WP-0100_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0100'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0100_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
    "WP-0104": {
        "recipe_id": "wp-0104-historical-receipt-artifact-presence",
        "title": "WP-0104 — Historical receipt and artifact presence",
        "description": "Conservatively validates completion receipt completeness and repository artifact presence for WP-0104.",
        "required_checks": ["Completion receipt is complete", "Receipt-listed artifacts exist"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/reports/WP-0104_validation.md", "runtime/validation/work_packages/WP-0104_validation.json", "collaboration/work_packages/completions/WP-0104_codex_done.json"],
        "failure_criteria": ["Receipt is incomplete", "Receipt-listed repository artifacts are missing"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0104'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"import json; from pathlib import Path; receipt=Path('collaboration/work_packages/completions/WP-0104_codex_done.json'); data=json.loads(receipt.read_text(encoding='utf-8')); files=data.get('files_changed') or []; assert files, 'receipt has no files_changed'; missing=[p for p in files if not Path(p).is_file()]; assert not missing, missing\""),
        ],
    },
})


VALIDATION_RECIPES["WP-0133"] = {
    "recipe_id": "wp-0133-ai-services-post-launch-health-repair",
    "title": "WP-0133 — AI Services Post-Launch Health Verification and Process Tracking Repair",
    "description": "Validates lifecycle-aware AI service execution semantics, WP-0133 reports, completion receipt, and production-readiness compatibility.",
    "required_checks": ["AI services control-plane tests pass", "WP-0133 artifacts exist", "Receipt is complete", "Health lifecycle implementation is present"],
    "observational_checks": [],
    "expected_artifacts": ["operations/ai_services/WP-0133_ai_services_post_launch_health_repair_report.md", "runtime/ai_services/WP-0133_ai_services_post_launch_health_repair_report.json", "collaboration/work_packages/completions/WP-0133_codex_done.json"],
    "failure_criteria": ["Any required command exits non-zero"],
    "success_criteria": ["Required commands exit zero"],
    "continue_on_failure": True,
    "commands": [
        _cmd("PYTHONPATH=src pytest tests/test_ai_services_control_plane.py -q"),
        _cmd("python -c \"import json; from pathlib import Path; paths=['operations/ai_services/WP-0133_ai_services_post_launch_health_repair_report.md','runtime/ai_services/WP-0133_ai_services_post_launch_health_repair_report.json','collaboration/work_packages/completions/WP-0133_codex_done.json']; missing=[p for p in paths if not Path(p).is_file()]; assert not missing, missing; data=json.loads(Path('runtime/ai_services/WP-0133_ai_services_post_launch_health_repair_report.json').read_text(encoding='utf-8')); assert data.get('work_package_id')=='WP-0133'; assert data.get('ready_for_ca_review') is True\""),
        _cmd("python -c \"from pathlib import Path; t=Path('src/estate/ai_services/execution.py').read_text(encoding='utf-8'); required=['health_check_started','health_check_succeeded','health_check_failed','process_exited_before_health','http://127.0.0.1:5000/v1/models']; missing=[x for x in required if x not in t]; assert not missing, missing\""),
        _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0133'); assert r['receipt_status']=='complete', r\""),
    ],
}

VALIDATION_RECIPES["WP-0115"] = {
    "recipe_id": "wp-0115-historical-validation-recipe-bootstrap-sweep",
    "title": "WP-0115 — Historical Validation Recipe Bootstrap Sweep",
    "description": "Validates the WP-0115 recipe bootstrap reports, safety guardrails, dependent validations, production-readiness execution, and completion receipt.",
    "required_checks": ["Bootstrap reports exist", "Bootstrap report JSON parses", "Before and after totals are present", "At least one package was considered", "Skipped packages include reasons", "Do-not-promote packages were not falsely completed", "Prior critical packages remain passing", "Production-readiness validation executes", "WP-0115 receipt is complete"],
    "observational_checks": [],
    "expected_artifacts": ["operations/validation/backlog_burn_down/WP-0115_recipe_bootstrap_report.md", "runtime/validation/backlog_burn_down/WP-0115_recipe_bootstrap_report.json", "collaboration/work_packages/completions/WP-0115_codex_done.json"],
    "failure_criteria": ["Any required command exits non-zero", "A do-not-promote package is reported as selected or validated by WP-0115"],
    "success_criteria": ["Required commands exit zero"],
    "continue_on_failure": True,
    "commands": [
        _cmd("python -c \"from pathlib import Path; paths=['operations/validation/backlog_burn_down/WP-0115_recipe_bootstrap_report.md','runtime/validation/backlog_burn_down/WP-0115_recipe_bootstrap_report.json']; missing=[p for p in paths if not Path(p).is_file()]; assert not missing, missing\""),
        _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/backlog_burn_down/WP-0115_recipe_bootstrap_report.json').read_text(encoding='utf-8')); assert data.get('production_readiness_totals_before') and data.get('production_readiness_totals_after'), data.keys(); assert data.get('packages_considered'), data; assert all(x.get('reason') for x in data.get('packages_skipped', [])), data.get('packages_skipped')\""),
        _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('runtime/validation/backlog_burn_down/WP-0115_recipe_bootstrap_report.json').read_text(encoding='utf-8')); deny={'WP-0016','WP-0017','WP-0018','WP-0056','WP-0073','WP-0094','WP-0106','WP-0107','WP-9999'}; completed=set(data.get('packages_selected_for_recipe_generation', [])) | set(data.get('packages_successfully_validated', [])); assert not (deny & completed), sorted(deny & completed)\""),
        _cmd('python -m estate.cli.main validate-work-package --id WP-0102 --json'),
        _cmd('python -m estate.cli.main validate-work-package --id WP-0105 --json'),
        _cmd('python -m estate.cli.main validate-work-package --id WP-0111 --json'),
        _cmd('python -m estate.cli.main validate-work-package --id WP-0114 --json'),
        _cmd('python -m estate.cli.main validation-production-readiness --json'),
        _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0115'); assert r['receipt_status']=='complete', r\""),
    ],
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



VALIDATION_RECIPES.update({
    "WP-0131": {
        "recipe_id": "wp-0131-ai-services-control-plane",
        "title": "WP-0131 — AI Services Control Plane",
        "description": "Validates the local AI services control plane manifests, CLI hooks, reports, and completion receipt.",
        "required_checks": ["AI services tests pass", "Rediscovery CLI works", "Report artifacts exist", "Receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["src/estate/ai_services", "runtime/ai_services/registry.json", "operations/ai_services/WP-0131_ai_services_control_plane_report.md", "runtime/ai_services/WP-0131_ai_services_control_plane_report.json", "collaboration/work_packages/completions/WP-0131_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("PYTHONPATH=src pytest tests/test_ai_services_control_plane.py -q"),
            _cmd("PYTHONPATH=src python -m estate.cli.main ai-services rediscover --json"),
            _cmd("python -c \"import json; from pathlib import Path; paths=['operations/ai_services/WP-0131_ai_services_control_plane_report.md','runtime/ai_services/WP-0131_ai_services_control_plane_report.json','runtime/ai_services/registry.json','runtime/ai_services/state.json']; missing=[p for p in paths if not Path(p).exists()]; assert not missing, missing; reg=json.loads(Path('runtime/ai_services/registry.json').read_text(encoding='utf-8')); assert {'ollama','open_webui','textgen','comfyui','sillytavern'} <= {s['service_id'] for s in reg['services']}\""),
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0131'); assert r['receipt_status']=='complete', r\""),
        ],
    },
    "WP-0132": {
        "recipe_id": "wp-0132-ai-services-execution-adapters",
        "title": "WP-0132 — AI Services Execution Adapters and Steward Approval",
        "description": "Validates mock-tested execution adapters, approval artifacts, reports, and completion receipt.",
        "required_checks": ["AI services execution tests pass", "Report artifacts exist", "Receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["src/estate/ai_services/execution.py", "operations/ai_services/WP-0132_ai_services_execution_adapters_report.md", "runtime/ai_services/WP-0132_ai_services_execution_adapters_report.json", "collaboration/work_packages/completions/WP-0132_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("PYTHONPATH=src pytest tests/test_ai_services_control_plane.py -q"),
            _cmd("python -c \"import json; from pathlib import Path; paths=['src/estate/ai_services/execution.py','operations/ai_services/WP-0132_ai_services_execution_adapters_report.md','runtime/ai_services/WP-0132_ai_services_execution_adapters_report.json']; missing=[p for p in paths if not Path(p).exists()]; assert not missing, missing; data=json.loads(Path('runtime/ai_services/WP-0132_ai_services_execution_adapters_report.json').read_text(encoding='utf-8')); assert data.get('work_package_id')=='WP-0132'; assert data.get('ready_for_ca_review') is True\""),
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0132'); assert r['receipt_status']=='complete', r\""),
        ],
    }
})

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

# WP-0120 final historical exception cleanup recipes.
# Conservative, local-first checks only; these do not weaken readiness semantics.
VALIDATION_RECIPES.update({
    "WP-0018": {
        "recipe_id": "wp-0018-codex-handoff-generator-historical-presence",
        "title": "WP-0018 — Codex Handoff Generator historical artifact presence",
        "description": "Validates receipt completeness and local implementation artifacts for the historical Codex handoff generator.",
        "required_checks": ["Completion receipt is complete", "Implementation artifacts exist", "Handoff tests pass"],
        "observational_checks": [],
        "expected_artifacts": ["src/estate/core/work_package_handoff.py", "docs/operations/Codex_Handoff_Generator_v1.md", "collaboration/work_packages/completions/WP-0018_codex_done.json"],
        "failure_criteria": ["Receipt incomplete", "Required artifact missing", "Required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0018'); assert r['receipt_status']=='complete', r\""),
            _cmd("python -c \"from pathlib import Path; paths=['src/estate/core/work_package_handoff.py','docs/operations/Codex_Handoff_Generator_v1.md','tests/test_work_package_handoff.py']; missing=[p for p in paths if not Path(p).is_file()]; assert not missing, missing\""),
            _cmd("pytest -q tests/test_work_package_handoff.py"),
        ],
    },
    "WP-0040": {
        "recipe_id": "wp-0040-assignment-queue-v1-historical-smoke",
        "title": "WP-0040 — Assignment Queue v1 historical smoke validation",
        "description": "Validates assignment queue artifacts and read-only CLI JSON generation.",
        "required_checks": ["Receipt is complete", "Assignment queue CLI emits JSON", "Assignment queue tests pass"],
        "observational_checks": [],
        "expected_artifacts": ["src/estate/core/assignment_queue.py", "runtime/work_packages/assignment_queue.json", "operations/work_packages/assignment_queue.md"],
        "failure_criteria": ["Required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [_cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0040'); assert r['receipt_status']=='complete', r\""), _cmd("python -m estate.cli.main assignment-queue --json"), _cmd("pytest -q tests/test_assignment_queue.py")],
    },
    "WP-0063": {
        "recipe_id": "wp-0063-autonomous-work-queue-scheduler-historical-smoke",
        "title": "WP-0063 — Autonomous Work Queue Scheduler historical smoke validation",
        "description": "Validates scheduler receipt, implementation artifacts, CLI JSON generation, and focused tests.",
        "required_checks": ["Receipt is complete", "Scheduler CLI emits JSON", "Scheduler tests pass"],
        "observational_checks": [],
        "expected_artifacts": ["src/estate/core/autonomous_work_queue_scheduler.py", "runtime/work_packages/autonomous_work_queue_scheduler.json", "runtime/activity_console/work_queue_scheduler.json"],
        "failure_criteria": ["Required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [_cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0063'); assert r['receipt_status']=='complete', r\""), _cmd("python -m estate.cli.main autonomous-work-queue-scheduler --json"), _cmd("pytest -q tests/test_autonomous_work_queue_scheduler.py")],
    },
    "WP-0120": {
        "recipe_id": "wp-0120-final-historical-exception-cleanup",
        "title": "WP-0120 — Final Historical Exception Cleanup",
        "description": "Self-validates the final cleanup reports, residual classifications, VO-0001 status, quarantine preservation, resident-runtime readiness, and WP-0120 receipt completeness.",
        "required_checks": ["Reports exist and parse", "All initial blockers classified", "Remaining blockers have next actions", "VO-0001 status reported", "Alfred/Helen path remains ready", "WP-9999 remains not promoted", "Readiness command executes", "Recent resident-runtime packages pass", "Receipt is complete"],
        "observational_checks": [],
        "expected_artifacts": ["operations/validation/backlog_burn_down/WP-0120_final_historical_exception_cleanup_report.md", "runtime/validation/backlog_burn_down/WP-0120_final_historical_exception_cleanup_report.json", "collaboration/work_packages/completions/WP-0120_codex_done.json"],
        "failure_criteria": ["Any required command exits non-zero"],
        "success_criteria": ["Required commands exit zero"],
        "continue_on_failure": True,
        "commands": [
            _cmd("python -c \"import json; from pathlib import Path; md=Path('operations/validation/backlog_burn_down/WP-0120_final_historical_exception_cleanup_report.md'); js=Path('runtime/validation/backlog_burn_down/WP-0120_final_historical_exception_cleanup_report.json'); assert md.is_file(); data=json.loads(js.read_text(encoding='utf-8')); ids={'WP-0016','WP-0017','WP-0018','WP-0040','WP-0056','WP-0063','WP-0073','WP-0089','WP-0094'}; assert ids <= set(data.get('initial_blockers', [])); assert 'before_totals' in data and 'after_totals' in data; assert ids <= set(data.get('classifications', {})); assert all(v.get('validation_result') for v in data.get('repaired_packages', {}).values()); assert all(v.get('next_action') for v in data.get('packages_left_blocked', {}).values()); assert data.get('vo_0001', {}).get('status') in {'closed','open','preserved'}; assert data.get('alfred_helen_runtime_path_status', {}).get('ready') is True; assert data.get('wp_9999_quarantine_status', {}).get('promoted') is False\""),
            _cmd("python -m estate.cli.main validation-production-readiness --json"),
            _cmd("python -c \"import json; from pathlib import Path; p=Path('runtime/validation/work_packages/WP-0116_validation.json'); data=json.loads(p.read_text(encoding='utf-8')); assert data.get('validation_status') in {'passed','passed_with_findings'}, data.get('validation_status')\""),
            _cmd("python -c \"import json; from pathlib import Path; p=Path('runtime/validation/work_packages/WP-0117_validation.json'); data=json.loads(p.read_text(encoding='utf-8')); assert data.get('validation_status') in {'passed','passed_with_findings'}, data.get('validation_status')\""),
            _cmd("python -c \"import json; from pathlib import Path; p=Path('runtime/validation/work_packages/WP-0118_validation.json'); data=json.loads(p.read_text(encoding='utf-8')); assert data.get('validation_status') in {'passed','passed_with_findings'}, data.get('validation_status')\""),
            _cmd("python -c \"import json; from pathlib import Path; p=Path('runtime/validation/work_packages/WP-0119_validation.json'); data=json.loads(p.read_text(encoding='utf-8')); assert data.get('validation_status') in {'passed','passed_with_findings'}, data.get('validation_status')\""),
            _cmd("python -c \"from estate.core.production_readiness_validation import validate_receipt; r=validate_receipt('WP-0120'); assert r['receipt_status']=='complete', r\""),
        ],
    },
})

VALIDATION_RECIPES["WP-0213"] = {
    "recipe_id": "wp-0213-office-command-surface-real-verbs",
    "title": "WP-0213 — Office of the Steward Command Surface",
    "description": "Validates that WP-0213 installed real Office controls, action result model tests, audit/report artifacts, and completion receipt.",
    "required_checks": ["Office command surface tests pass", "Office payload exposes action controls", "Audit/report artifacts exist", "Completion receipt exists"],
    "observational_checks": ["Existing Office tests pass"],
    "expected_artifacts": [
        "src/estate/core/office_command_surface.py",
        "operations/steward/WP-0213_office_command_surface_verb_audit.md",
        "operations/steward/WP-0213_office_command_surface_report.md",
        "collaboration/work_packages/completions/WP-0213_codex_done.json",
    ],
    "failure_criteria": ["Any required command exits non-zero"],
    "success_criteria": ["Required commands exit zero"],
    "continue_on_failure": True,
    "commands": [
        _cmd("python -m pytest tests/test_office_command_surface.py"),
        _cmd("python -c \"import json, subprocess, sys; p=json.loads(subprocess.check_output([sys.executable,'-m','estate.cli.main','steward-command-center','--json'])); actions=p.get('office_actions') or {}; required=['ai-services-models','validation','work-packages','notifications','alfred','mission-control','daily-board']; missing=[tab for tab in required if not actions.get(tab)]; assert not missing, missing; assert all(c.get('availability') in {'available','gated'} for cs in actions.values() for c in cs)\""),
        _cmd("python -c \"from pathlib import Path; required=['operations/steward/WP-0213_office_command_surface_verb_audit.md','operations/steward/WP-0213_office_command_surface_report.md','collaboration/work_packages/completions/WP-0213_codex_done.json']; missing=[p for p in required if not Path(p).is_file()]; assert not missing, missing\""),
        _cmd("python -m pytest tests/test_steward_command_center.py", required=False),
    ],
}
