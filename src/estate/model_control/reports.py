import json, subprocess
from pathlib import Path
from .registry import now, load_registry
from .assignments import load_assignments

def write_reports(tests_run=None, validation_commands_run=None, root=None):
    r=Path(root) if root else Path.cwd()
    payload={'work_package_id':'WP-0218','generated_at':now(),'root_cause':'Model selection lived inside adapters/resident defaults rather than an Estate-governed model-control layer.','paths':['src/estate/model_control','runtime/model_control','operations/model_control'],'registry_schema_summary':['model_id','provider','service_id','model_name','endpoint','capabilities','capability_confidence','context_length','size_bytes','discovered_at','available','local_only','cloud_allowed'],'assignment_schema_summary':['estate_defaults','residents','workers','authority'],'authority_policy_summary':'Actor capability authority plus model capability validation; cloud disallowed by default; Steward approval required for assignment changes.','office_ui_changes':'AI Services / Models panel now includes Estate model-control registry, assignments, authority, diagnostics, and audit artifacts.','cli_commands_added':['model-control rediscover','model-control list-models','model-control assignments','model-control set-default','model-control assign','model-control validate-assignments'],'alfred_integration_changes':'Alfred resolves text selection through model_control assignments/policy before adapter invocation and labels bootstrap fallback explicitly.','tests_run':tests_run or [],'validation_commands_run':validation_commands_run or [],'known_limitations':['Runtime Ollama fetching is opt-in and mocked in tests; no models are installed or downloaded.'],'recommended_next_action':'CA review and Steward selection of production preferred vision/code models when local models are available.','ready_for_ca_review':True,'registry':load_registry(r),'assignments':load_assignments(r)}
    (r/'runtime/model_control').mkdir(parents=True, exist_ok=True); (r/'operations/model_control').mkdir(parents=True, exist_ok=True)
    (r/'runtime/model_control/WP-0218_estate_model_control_plane_report.json').write_text(json.dumps(payload, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    md='# WP-0218 Estate Model Control Plane Report\n\n'+'\n'.join(f'- **{k}**: {v}' for k,v in payload.items() if k not in {'registry','assignments'})+'\n'
    (r/'operations/model_control/WP-0218_estate_model_control_plane_report.md').write_text(md, encoding='utf-8')
    return payload
