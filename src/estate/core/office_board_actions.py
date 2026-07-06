"""Installed staged Office control metadata; installed metadata runtime code."""
from __future__ import annotations

STAGED_WORK_IS_INSTALLED = True
LOCAL_ONLY_NO_UPLOAD = True
ACTION_IDS = ['daily_board.refresh_daily_board', 'daily_board.open_source_item', 'daily_board.mark_locally_reviewed', 'daily_board.draft_daily_note', 'daily_board.promote_blocked_review_to_request_draft', 'parking_lot.inspect_parking_lot_item', 'parking_lot.promote_to_proposed_work_package_draft', 'parking_lot.archive_local_duplicate_design', 'parking_lot.request_review', 'parking_lot.export_parking_lot_snapshot']

def staged_action_ids():
    return ACTION_IDS.copy()
