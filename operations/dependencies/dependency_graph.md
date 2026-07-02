# Estate Dependency Graph

Machine-readable output: `runtime/dependencies/dependency_graph.json`.

## Summary
- Generated: 2026-07-02T21:04:16+00:00
- Nodes: 65
- Edges: 0
- Orphaned items: 65
- Warnings: 64

## Supported dependency sources
- JSON fields: `dependencies`, `depends_on`, `dependency_ids`, `dependency_id`, `blocked_by`, `requires`, `required_capabilities`, `required_services`, `work_package_dependencies`.
- Markdown front matter or lines using those same field names.
- Markdown sections clearly headed `Dependencies`, `Depends On`, `Blocked By`, `Requires`, `Required Capabilities`, or `Required Services`.

## Graph schema
- `nodes`: `{id, type, label, source_artifact}`.
- `edges`: `{source, target, dependency_type, source_artifact}`.
- `warnings`: missing optional inputs, malformed JSON, malformed references, and artifacts without explicit dependency fields.
- `orphaned_items`: nodes with no incoming or outgoing explicit dependency edges.

## CLI usage
- `python -m estate.cli.main dependency-graph` writes JSON and Markdown and prints a summary.
- `python -m estate.cli.main dependency-graph --json` writes outputs and prints the JSON graph.

## Limitations
- Only explicit fields and clearly labelled dependency sections are captured.
- The generator does not infer hidden dependencies from wording, similarity, order, or proximity.
- Missing inputs produce warnings rather than failures.

## Edges
- No explicit dependency edges found.

## Orphaned items
- `ARCHITECTURE-FIRST TASK WP-0016 — Work Package Registry` (work_package) — collaboration/work_packages/pending/WP-0016_ARCHITECTURE_FIRST_work_package_registry.md
- `ARCHITECTURE-FIRST TASK WP-0017 — Work Package State Machine` (work_package) — collaboration/work_packages/pending/WP-0017_ARCHITECTURE_FIRST_work_package_state_machine.md
- `Active Work Board` (operation) — operations/boards/active_work.md
- `Active Work Item Template` (operation) — operations/templates/active_work_item.md
- `Alfred Operational Briefing` (operation) — operations/alfred/operational_briefing.md
- `CA3 Review Brief: Check for Updates Synchronization Mechanism` (operation) — operations/briefings/CA3_Check_For_Updates_PR12_Review.md
- `CAP-000001` (capability) — runtime/capabilities/capability_lifecycle_report.json
- `CAP-000002` (capability) — runtime/capabilities/capability_lifecycle_report.json
- `CAP-000003` (capability) — runtime/capabilities/capability_lifecycle_report.json
- `CAP-000004` (capability) — runtime/capabilities/capability_lifecycle_report.json
- `CAP-000005` (capability) — runtime/capabilities/capability_lifecycle_report.json
- `CAP-000006` (capability) — runtime/capabilities/capability_lifecycle_report.json
- `Check for Updates` (operation) — operations/updates/check_updates_latest.md
- `Continuous Operational Validation Report` (operation) — operations/validation/operational_validation_report.md
- `Daily Board Integration` (operation) — operations/boards/daily_board_integration.md
- `Daily Task Board` (operation) — operations/boards/daily_board.md
- `Daily Task Template` (operation) — operations/templates/daily_task.md
- `EC-000086: Add Estate Operations Board` (operation) — operations/history/EC-000086.md
- `Estate Capability Lifecycle Status` (capability) — operations/capabilities/lifecycle_status.md
- `Estate Operations Board` (operation) — operations/README.md
- `Estate Steward Dashboard` (operation) — operations/steward/dashboard.md
- `Local Operational Validation Run` (operation) — operations/validation/local_operational_validation_run.md
- `Mailbox Synchronization Duty` (operation) — operations/mailboxes/synchronization_duty.md
- `Operations Board Implementation Recommendation` (operation) — operations/implementation_recommendation.md
- `Parking Lot` (operation) — operations/boards/parking_lot.md
- `Parking Lot Item` (operation) — operations/templates/parking_item.md
- `Pending Codex Work Packages` (work_package) — collaboration/work_packages/pending/README.md
- `Review Cadence` (operation) — operations/boards/review_cadence.md
- `SERIES TASK WP-0014 — Mailbox Index Regeneration and Destination Coverage Fix` (work_package) — collaboration/work_packages/pending/WP-0014_SERIES_mailbox_destination_coverage.md
- `SERIES TASK WP-0015 — Message Acknowledgement and Reply Flow` (work_package) — collaboration/work_packages/pending/WP-0015_SERIES_message_acknowledgement_reply_flow.md
- `SERIES TASK WP-0018 — Codex Handoff Generator` (work_package) — collaboration/work_packages/pending/WP-0018_SERIES_codex_handoff_generator.md
- `SERIES TASK WP-0019 — Alfred Operational Activation` (work_package) — collaboration/work_packages/pending/WP-0019_SERIES_alfred_operational_activation.md
- `SERIES TASK WP-0020 — Helen HR Operational Onboarding` (work_package) — collaboration/work_packages/pending/WP-0020_SERIES_helen_hr_operational_onboarding.md
- `SERIES TASK WP-0020 — Work Package State Machine Implementation` (work_package) — collaboration/work_packages/pending/WP-0020_SERIES_work_package_state_machine_implementation.md
- `SERIES TASK WP-0021 — Personnel Identity and Mailbox Resolver` (work_package) — collaboration/work_packages/pending/WP-0021_SERIES_personnel_identity_mailbox_resolver.md
- `SERIES TASK WP-0022 — Check for Updates v2 Mailbox Integration` (work_package) — collaboration/work_packages/pending/WP-0022_SERIES_check_for_updates_v2_mailbox_integration.md
- `SERIES TASK WP-0023 — Mailbox Synchronization Duty Runtime` (work_package) — collaboration/work_packages/pending/WP-0023_SERIES_mailbox_synchronization_duty_runtime.md
- `SERIES TASK WP-0024 — Daily Board and Parking Lot Integration` (work_package) — collaboration/work_packages/pending/WP-0024_SERIES_daily_board_parking_lot_integration.md
- `SERIES TASK WP-0025 — Local Operational Validation Runner` (work_package) — collaboration/work_packages/pending/WP-0025_SERIES_local_operational_validation_runner.md
- `SERIES TASK WP-0026 — Generated Artifact Policy` (work_package) — collaboration/work_packages/pending/WP-0026_SERIES_generated_artifact_policy.md
- `SERIES TASK WP-0027 — Institutional Search v1` (work_package) — collaboration/work_packages/pending/WP-0027_SERIES_institutional_search_v1.md
- `SERIES TASK WP-0028 — Document Registry and Stable Document IDs` (work_package) — collaboration/work_packages/pending/WP-0028_SERIES_document_registry_stable_ids.md
- `SERIES TASK WP-0029 — Artifact Provenance Model` (work_package) — collaboration/work_packages/pending/WP-0029_SERIES_artifact_provenance_model.md
- `SVC-000001` (service) — data/registry/services.json
- `SVC-000002` (service) — data/registry/services.json
- `SVC-000003` (service) — data/registry/services.json
- `Strategic Roadmap` (operation) — operations/boards/roadmap.md
- `Work Package WP-LEAP-001` (work_package) — collaboration/work_packages/open/WP-LEAP-001_Audit_Worker_v1_Local_Ollama.md
- `msg_20260701_000000_example_routing` (message) — collaboration/messages/example_alfred_routing_engine_v1.json
- `msg_ca2_20260701_0001_mailbox_index_validation` (message) — collaboration/messages/msg_ca2_20260701_0001_mailbox_index_validation.json
- `msg_ca2_20260701_0002_mailbox_infrastructure_verification_to_ca3` (message) — collaboration/messages/msg_ca2_20260701_0002_mailbox_infrastructure_verification_to_ca3.json
- `msg_ca3_20260701_0001_alfred_capability_brief` (message) — collaboration/messages/msg_ca3_20260701_0001_alfred_capability_brief.json
- `msg_ca3_20260701_0002_audit_malformed_json_review` (message) — collaboration/messages/msg_ca3_20260701_0002_audit_malformed_json_review.json
- `msg_ca3_20260701_0003_operations_board_review` (message) — collaboration/messages/msg_ca3_20260701_0003_operations_board_review.json
- `msg_ca3_20260701_0004_capability_lifecycle_review` (message) — collaboration/messages/msg_ca3_20260701_0004_capability_lifecycle_review.json
- `msg_ca3_20260701_0005_steward_dashboard_review` (message) — collaboration/messages/msg_ca3_20260701_0005_steward_dashboard_review.json
- `msg_ca3_20260701_0006_collaboration_event_framework_review` (message) — collaboration/messages/msg_ca3_20260701_0006_collaboration_event_framework_review.json
- `msg_ca3_20260701_0007_dependency_graph_review` (message) — collaboration/messages/msg_ca3_20260701_0007_dependency_graph_review.json
- `msg_ca3_20260701_0008_operational_validation_review` (message) — collaboration/messages/msg_ca3_20260701_0008_operational_validation_review.json
- `msg_ca3_20260701_0009_check_updates_review_to_ca2` (message) — collaboration/messages/msg_ca3_20260701_0009_check_updates_review_to_ca2.json
- `msg_ca3_20260701_0010_check_updates_review_to_ca4` (message) — collaboration/messages/msg_ca3_20260701_0010_check_updates_review_to_ca4.json
- `msg_ca3_20260701_0011_meeting_request_to_ca4` (message) — collaboration/messages/msg_ca3_20260701_0011_meeting_request_to_ca4.json
- `msg_ca3_20260701_0012_roadmap_rebaseline_draft_to_ca4` (message) — collaboration/messages/msg_ca3_20260701_0012_roadmap_rebaseline_draft_to_ca4.json
- `msg_ca4_20260701_0001_reply_to_ca3_mailbox_check` (message) — collaboration/messages/msg_ca4_20260701_0001_reply_to_ca3_mailbox_check.json
- `msg_ca4_20260702_0001_roadmap_rebaseline_response_to_ca3` (message) — collaboration/messages/msg_ca4_20260702_0001_roadmap_rebaseline_response_to_ca3.json

## Warnings
- missing_dependency_field: collaboration/messages/example_alfred_routing_engine_v1.json — msg_20260701_000000_example_routing has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca2_20260701_0001_mailbox_index_validation.json — msg_ca2_20260701_0001_mailbox_index_validation has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca2_20260701_0002_mailbox_infrastructure_verification_to_ca3.json — msg_ca2_20260701_0002_mailbox_infrastructure_verification_to_ca3 has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca3_20260701_0001_alfred_capability_brief.json — msg_ca3_20260701_0001_alfred_capability_brief has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca3_20260701_0002_audit_malformed_json_review.json — msg_ca3_20260701_0002_audit_malformed_json_review has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca3_20260701_0003_operations_board_review.json — msg_ca3_20260701_0003_operations_board_review has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca3_20260701_0004_capability_lifecycle_review.json — msg_ca3_20260701_0004_capability_lifecycle_review has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca3_20260701_0005_steward_dashboard_review.json — msg_ca3_20260701_0005_steward_dashboard_review has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca3_20260701_0006_collaboration_event_framework_review.json — msg_ca3_20260701_0006_collaboration_event_framework_review has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca3_20260701_0007_dependency_graph_review.json — msg_ca3_20260701_0007_dependency_graph_review has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca3_20260701_0008_operational_validation_review.json — msg_ca3_20260701_0008_operational_validation_review has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca3_20260701_0009_check_updates_review_to_ca2.json — msg_ca3_20260701_0009_check_updates_review_to_ca2 has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca3_20260701_0010_check_updates_review_to_ca4.json — msg_ca3_20260701_0010_check_updates_review_to_ca4 has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca3_20260701_0011_meeting_request_to_ca4.json — msg_ca3_20260701_0011_meeting_request_to_ca4 has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca3_20260701_0012_roadmap_rebaseline_draft_to_ca4.json — msg_ca3_20260701_0012_roadmap_rebaseline_draft_to_ca4 has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca4_20260701_0001_reply_to_ca3_mailbox_check.json — msg_ca4_20260701_0001_reply_to_ca3_mailbox_check has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca4_20260702_0001_roadmap_rebaseline_response_to_ca3.json — msg_ca4_20260702_0001_roadmap_rebaseline_response_to_ca3 has no explicit dependency field.
- missing_optional_artifact: runtime/operations/operations_board.json — Optional input artifact is unavailable.
- missing_dependency_field: runtime/capabilities/capability_lifecycle_report.json — CAP-000001 has no explicit dependency field.
- missing_dependency_field: runtime/capabilities/capability_lifecycle_report.json — CAP-000002 has no explicit dependency field.
- missing_dependency_field: runtime/capabilities/capability_lifecycle_report.json — CAP-000003 has no explicit dependency field.
- missing_dependency_field: runtime/capabilities/capability_lifecycle_report.json — CAP-000004 has no explicit dependency field.
- missing_dependency_field: runtime/capabilities/capability_lifecycle_report.json — CAP-000005 has no explicit dependency field.
- missing_dependency_field: runtime/capabilities/capability_lifecycle_report.json — CAP-000006 has no explicit dependency field.
- missing_dependency_field: collaboration/work_packages/open/WP-LEAP-001_Audit_Worker_v1_Local_Ollama.md — Work Package WP-LEAP-001 has no clearly labelled dependency section or field.
- missing_dependency_field: collaboration/work_packages/pending/README.md — Pending Codex Work Packages has no clearly labelled dependency section or field.
- missing_dependency_field: collaboration/work_packages/pending/WP-0014_SERIES_mailbox_destination_coverage.md — SERIES TASK WP-0014 — Mailbox Index Regeneration and Destination Coverage Fix has no clearly labelled dependency section or field.
- missing_dependency_field: collaboration/work_packages/pending/WP-0015_SERIES_message_acknowledgement_reply_flow.md — SERIES TASK WP-0015 — Message Acknowledgement and Reply Flow has no clearly labelled dependency section or field.
- missing_dependency_field: collaboration/work_packages/pending/WP-0016_ARCHITECTURE_FIRST_work_package_registry.md — ARCHITECTURE-FIRST TASK WP-0016 — Work Package Registry has no clearly labelled dependency section or field.
- missing_dependency_field: collaboration/work_packages/pending/WP-0017_ARCHITECTURE_FIRST_work_package_state_machine.md — ARCHITECTURE-FIRST TASK WP-0017 — Work Package State Machine has no clearly labelled dependency section or field.
- missing_dependency_field: collaboration/work_packages/pending/WP-0018_SERIES_codex_handoff_generator.md — SERIES TASK WP-0018 — Codex Handoff Generator has no clearly labelled dependency section or field.
- missing_dependency_field: collaboration/work_packages/pending/WP-0019_SERIES_alfred_operational_activation.md — SERIES TASK WP-0019 — Alfred Operational Activation has no clearly labelled dependency section or field.
- missing_dependency_field: collaboration/work_packages/pending/WP-0020_SERIES_helen_hr_operational_onboarding.md — SERIES TASK WP-0020 — Helen HR Operational Onboarding has no clearly labelled dependency section or field.
- missing_dependency_field: collaboration/work_packages/pending/WP-0020_SERIES_work_package_state_machine_implementation.md — SERIES TASK WP-0020 — Work Package State Machine Implementation has no clearly labelled dependency section or field.
- missing_dependency_field: collaboration/work_packages/pending/WP-0021_SERIES_personnel_identity_mailbox_resolver.md — SERIES TASK WP-0021 — Personnel Identity and Mailbox Resolver has no clearly labelled dependency section or field.
- missing_dependency_field: collaboration/work_packages/pending/WP-0022_SERIES_check_for_updates_v2_mailbox_integration.md — SERIES TASK WP-0022 — Check for Updates v2 Mailbox Integration has no clearly labelled dependency section or field.
- missing_dependency_field: collaboration/work_packages/pending/WP-0023_SERIES_mailbox_synchronization_duty_runtime.md — SERIES TASK WP-0023 — Mailbox Synchronization Duty Runtime has no clearly labelled dependency section or field.
- missing_dependency_field: collaboration/work_packages/pending/WP-0024_SERIES_daily_board_parking_lot_integration.md — SERIES TASK WP-0024 — Daily Board and Parking Lot Integration has no clearly labelled dependency section or field.
- missing_dependency_field: collaboration/work_packages/pending/WP-0025_SERIES_local_operational_validation_runner.md — SERIES TASK WP-0025 — Local Operational Validation Runner has no clearly labelled dependency section or field.
- missing_dependency_field: collaboration/work_packages/pending/WP-0026_SERIES_generated_artifact_policy.md — SERIES TASK WP-0026 — Generated Artifact Policy has no clearly labelled dependency section or field.
- missing_dependency_field: collaboration/work_packages/pending/WP-0027_SERIES_institutional_search_v1.md — SERIES TASK WP-0027 — Institutional Search v1 has no clearly labelled dependency section or field.
- missing_dependency_field: collaboration/work_packages/pending/WP-0028_SERIES_document_registry_stable_ids.md — SERIES TASK WP-0028 — Document Registry and Stable Document IDs has no clearly labelled dependency section or field.
- missing_dependency_field: collaboration/work_packages/pending/WP-0029_SERIES_artifact_provenance_model.md — SERIES TASK WP-0029 — Artifact Provenance Model has no clearly labelled dependency section or field.
- missing_dependency_field: operations/README.md — Estate Operations Board has no clearly labelled dependency section or field.
- missing_dependency_field: operations/alfred/operational_briefing.md — Alfred Operational Briefing has no clearly labelled dependency section or field.
- missing_dependency_field: operations/board/latest.md — Estate Operations Board has no clearly labelled dependency section or field.
- missing_dependency_field: operations/boards/active_work.md — Active Work Board has no clearly labelled dependency section or field.
- missing_dependency_field: operations/boards/daily_board.md — Daily Task Board has no clearly labelled dependency section or field.
- missing_dependency_field: operations/boards/daily_board_integration.md — Daily Board Integration has no clearly labelled dependency section or field.
- missing_dependency_field: operations/boards/parking_lot.md — Parking Lot has no clearly labelled dependency section or field.
- missing_dependency_field: operations/boards/review_cadence.md — Review Cadence has no clearly labelled dependency section or field.
- missing_dependency_field: operations/boards/roadmap.md — Strategic Roadmap has no clearly labelled dependency section or field.
- missing_dependency_field: operations/briefings/CA3_Check_For_Updates_PR12_Review.md — CA3 Review Brief: Check for Updates Synchronization Mechanism has no clearly labelled dependency section or field.
- missing_dependency_field: operations/capabilities/lifecycle_status.md — Estate Capability Lifecycle Status has no clearly labelled dependency section or field.
- missing_dependency_field: operations/history/EC-000086.md — EC-000086: Add Estate Operations Board has no clearly labelled dependency section or field.
- missing_dependency_field: operations/implementation_recommendation.md — Operations Board Implementation Recommendation has no clearly labelled dependency section or field.
- missing_dependency_field: operations/mailboxes/synchronization_duty.md — Mailbox Synchronization Duty has no clearly labelled dependency section or field.
- missing_dependency_field: operations/steward/dashboard.md — Estate Steward Dashboard has no clearly labelled dependency section or field.
- missing_dependency_field: operations/templates/active_work_item.md — Active Work Item Template has no clearly labelled dependency section or field.
- missing_dependency_field: operations/templates/daily_task.md — Daily Task Template has no clearly labelled dependency section or field.
- missing_dependency_field: operations/templates/parking_item.md — Parking Lot Item has no clearly labelled dependency section or field.
- missing_dependency_field: operations/updates/check_updates_latest.md — Check for Updates has no clearly labelled dependency section or field.
- missing_dependency_field: operations/validation/local_operational_validation_run.md — Local Operational Validation Run has no clearly labelled dependency section or field.
- missing_dependency_field: operations/validation/operational_validation_report.md — Continuous Operational Validation Report has no clearly labelled dependency section or field.
