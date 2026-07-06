"""Installed staged Office control metadata; installed metadata runtime code."""
from __future__ import annotations

STAGED_WORK_IS_INSTALLED = True
LOCAL_ONLY_NO_UPLOAD = True
ACTION_IDS = ['ai_services_models.inspect_service_model_manifest', 'ai_services_models.refresh_rediscovery_design', 'ai_services_models.sync_local_model_provider_inventory_design', 'ai_services_models.copy_start_stop_load_commands', 'ai_services_models.request_service_model_approval', 'ai_services_models.inspect_approval_audit_history', 'ai_services_models.inspect_resident_model_assignment_state', 'ai_services_models.export_ai_services_snapshot']

def staged_action_ids():
    return ACTION_IDS.copy()
