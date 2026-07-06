# WP-0213 Office Command Surface Report

## Steward objective
The Office of the Steward must be an operational cockpit, not merely a dashboard. WP-0213 implements a first governed local command surface so Office controls invoke real handlers and display action results.

WP-0200 through WP-0212 were foundational. They added action vocabulary, metadata, staged definitions, manifests, and backend structure, but they were not completion of the nouns-to-verbs objective because they did not provide enough meaningful Office UI controls that execute local Estate operations.

## Real verbs implemented
- AI Services / Models: Refresh local AI service inventory.
- Validation: Run production readiness refresh.
- Work Packages: Refresh assignment queue; validate selected work package.
- Notifications: Refresh notification center; acknowledge notification locally.
- Residents / Alfred: Request Alfred briefing.
- Mission Control: Refresh Mission Control payload.
- Daily Board: Generate morning briefing.

## Tabs affected
`ai-services-models`, `validation`, `work-packages`, `notifications`, `alfred`, `mission-control`, and `daily-board`.

## Handlers invoked
All controls dispatch through `estate.core.office_command_surface.execute_office_action`, which records action results under `runtime/steward/office_command_surface_action_results.jsonl`.

Specific handlers reused or wrapped:
- `estate.core.service_status_board.generate_service_status_board`
- `estate.core.provider_sync.sync_ollama_providers`
- `estate.core.production_readiness_validation.generate_production_readiness_report`
- `estate.core.work_package_validation.validate_work_package`
- `estate.core.assignment_queue.generate_assignment_queue`
- `estate.core.operations_notification_center.generate_operations_notification_center`
- `estate.core.operations_notification_center.acknowledge_operations_notification`
- `estate.core.alfred_duty.run_alfred_duty`
- `estate.core.mission_control_workspace.build_mission_control_workspace`
- `estate.core.daily_board_integration.generate_daily_board_integration`
- `estate.core.morning_briefing.generate_morning_briefing`

## Artifacts read/written/generated
- AI services: reads service/provider registries and writes service status board plus possible provider registry changes.
- Validation: writes production readiness JSON/Markdown artifacts.
- Work packages: reads collaboration work package folders and writes assignment queue and validation evidence.
- Notifications: writes notification center artifacts and local acknowledgement state.
- Alfred: writes duty state, duty run log, duty summary, and resident presence.
- Mission Control: writes Mission Control workspace payload.
- Daily Board: writes Daily Board integration and morning briefing artifacts.

## Gated verbs and reasons
- Start/stop/load AI service is visibly gated. Reason: the Office does not yet expose a governed process-control approval path, so service lifecycle control must remain unavailable rather than fake-operational.
- Validate selected work package blocks until a work package id is supplied.
- Local notification acknowledgement blocks until a notification id is supplied.

## Failed/deferred verbs and reasons
- Executing pending work packages is deferred because no governed Office execution authority is exposed.
- Notification follow-up draft creation is deferred until a governed draft schema/path is selected.
- Parking lot or warning promotion to proposal draft is deferred until proposal draft authority/schema is selected.
- Validation evidence bundle export is deferred to a later evidence packaging verb.

## Tests run
- `PYTHONPATH=src python -m pytest tests/test_office_command_surface.py -q`
- `PYTHONPATH=src python -m estate.cli.main steward-command-center --json`

## Manual verification instructions
1. Start served Office mode: `PYTHONPATH=src python -m estate.cli.main steward-command-center --serve --host 127.0.0.1 --port 8765`.
2. Open `http://127.0.0.1:8765/`.
3. AI Services / Models: click **Refresh local AI service inventory**. Expected outcome: `completed` or `failed`; completed lists service board/provider artifacts. Confirm by checking `runtime/services/service_status_board.json`.
4. Validation: click **Run production readiness refresh**. Expected outcome: `completed`; message states evidence is not institutional acceptance. Confirm `runtime/validation/production_readiness.json` changed.
5. Work Packages: click **Refresh assignment queue**. Expected outcome: `completed`. Confirm `runtime/work_packages/assignment_queue.json` changed.
6. Work Packages: enter `WP-0213` in the work package id input and click **Validate selected work package**. Expected outcome: `completed` if validation attempts and creates evidence, or `failed` if a recipe command fails; blocked only if no id is supplied.
7. Notifications: click **Refresh notification center**. Expected outcome: `completed`. Confirm `runtime/notifications/operations_notification_center.json` changed.
8. Notifications: enter a notification id from the notification table and click **Acknowledge notification locally**. Expected outcome: `completed`; confirm local-only state in `runtime/notifications/operations_notification_center_acknowledgements.json`.
9. Alfred: click **Request Alfred briefing**. Expected outcome: `completed`; confirm `operations/alfred/duty_summary.md` changed. Alfred does not approve or execute privileged actions.
10. Mission Control: click **Refresh Mission Control payload**. Expected outcome: `completed`; confirm `runtime/steward/mission_control_workspace.json` changed.
11. Daily Board: click **Generate morning briefing**. Expected outcome: `completed`; confirm `operations/briefings/morning_briefing.md` changed.
12. Static file verification: open `runtime/steward/command_center.html` directly and click a control. Expected outcome: deterministic blocked message because served local mode is required for POST handlers.

## Known limitations
- The first command surface uses JSON result panels rather than rich per-control result cards.
- Served mode is required for actual UI POST execution; static HTML blocks safely.
- Service lifecycle and institutional actions remain gated until authority/process-control paths are implemented.

## Recommended next verbs
- Governed service lifecycle request/approval controls.
- Notification follow-up draft creation.
- Parking lot promotion to proposal draft.
- Validation evidence bundle export.
- Rich selected-row binding for work package and notification controls.
