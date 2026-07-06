# WP-0208 — Daily Board and Parking Lot Controls

## Alignment
WP-0200 staged vocabulary was available and used for action classes, authority classes, confirmation requirements, fail-closed behavior, and local-only guarantees.

## Staged Controls

### Daily Board
- `daily_board.refresh_daily_board` — see `action_metadata.json`; local-only; staged, not installed.
- `daily_board.open_source_item` — see `action_metadata.json`; local-only; staged, not installed.
- `daily_board.mark_locally_reviewed` — see `action_metadata.json`; local-only; staged, not installed.
- `daily_board.draft_daily_note` — see `action_metadata.json`; local-only; staged, not installed.
- `daily_board.promote_blocked_review_to_request_draft` — see `action_metadata.json`; local-only; staged, not installed.

### Parking Lot
- `parking_lot.inspect_parking_lot_item` — see `action_metadata.json`; local-only; staged, not installed.
- `parking_lot.promote_to_proposed_work_package_draft` — see `action_metadata.json`; local-only; staged, not installed.
- `parking_lot.archive_local_duplicate_design` — see `action_metadata.json`; local-only; staged, not installed.
- `parking_lot.request_review` — see `action_metadata.json`; local-only; staged, not installed.
- `parking_lot.export_parking_lot_snapshot` — see `action_metadata.json`; local-only; staged, not installed.

## Safety Notes
- Staged work is not installed into active Office runtime files.
- Review requests are not approvals; promotion creates drafts/proposals only.
- No deletion, cloud calls, telemetry, resident authority expansion, service startup, or model load is introduced.
- Exports include sensitivity warnings and remain local-only.
