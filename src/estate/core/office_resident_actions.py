"""Installed staged Office control metadata; installed metadata runtime code."""
from __future__ import annotations

STAGED_WORK_IS_INSTALLED = True
LOCAL_ONLY_NO_UPLOAD = True
ACTION_IDS = ['alfred.start_alfred_conversation', 'alfred.inspect_alfred_surface', 'alfred.copy_alfred_duty_status_commands', 'alfred.queue_alfred_request', 'alfred.inspect_alfred_job_request', 'alfred.cancel_retry_job_design', 'helen.inspect_helen_surface', 'helen.copy_helen_duty_status_authority_commands', 'helen.start_helen_conversation', 'helen.draft_hr_onboarding_request', 'resident_conversations.start_session', 'resident_conversations.open_transcript', 'resident_conversations.export_transcript', 'resident_conversations.redact_forget_with_audit_design', 'resident_conversations.draft_promotion_of_outcome', 'resident_conversations.inspect_authority_boundary']

def staged_action_ids():
    return ACTION_IDS.copy()
