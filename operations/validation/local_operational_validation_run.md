# Local Operational Validation Run

Generated: 2026-07-02T21:04:16+00:00

## Summary
- Step Count: 9
- Failed Steps: 0
- Warning Count: 76
- Ok: True

## Source Boundary

### Authoritative Sources
- data/registry/**/*.json
- collaboration/messages/*.json
- collaboration/work_packages/**/*.md
- collaboration/work_packages/completions/*.json
- operations/boards/*.md
- docs/**/*.md

### Generated Projections
- collaboration/mailboxes/index.json
- collaboration/status/worker_inbox_summary.json
- runtime/collaboration/routing/latest.json
- runtime/updates/check_updates_latest.json
- operations/updates/check_updates_latest.md
- operations/alfred/operational_briefing.md
- runtime/operations/daily_board_integration.json
- operations/boards/daily_board_integration.md
- runtime/capabilities/capability_lifecycle_report.json
- runtime/dependencies/dependency_graph.json
- runtime/validation/operational_validation_report.json
- operations/validation/operational_validation_report.md
- runtime/validation/local_operational_validation_run.json
- operations/validation/local_operational_validation_run.md

## Steps
- mailbox_index: ok (Regenerate mailbox index and worker mailbox surfaces.)
- routing_decisions: ok (Regenerate collaboration routing decisions.)
- worker_inbox_summary: ok (Regenerate worker inbox summaries.)
- check_updates: ok (Regenerate Check for Updates briefing.)
- alfred_operational_briefing: ok (Regenerate Alfred operational briefing.)
- daily_board_integration: ok (Regenerate Operations/Daily Board integration.)
- capability_lifecycle: ok (Regenerate capability lifecycle report.)
- dependency_graph: ok (Regenerate dependency graph.)
- operational_validation: ok (Regenerate operational validation report.)

## Warnings
- identity_resolution:  — unresolved actor: steward
- unresolved_identity:  — Actor identity could not be resolved to a mailbox or worker.
- missing_input: runtime/operations/operations_board.json — Optional update source not present.
- mailbox_index_warning: collaboration/messages/example_alfred_routing_engine_v1.json — unresolved destination: queue
- missing_artifact: runtime/operations/operations_board.json — 
- missing_artifact: runtime/steward/dashboard.json — 
- missing_optional_artifact: runtime/operations/operations_board.json — Optional input artifact is unavailable.
- missing_optional_artifact: runtime/audit/latest.json — Optional input artifact is unavailable.
- missing_optional_artifact: collaboration/audit/results/*.json — Optional input artifact is unavailable.
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
- missing_input: runtime/operations/operations_board.json — Input artifact is unavailable.
- missing_input: runtime/audit/latest.json — Input artifact is unavailable.
- missing_input: collaboration/audit/results/*.json — Input artifact is unavailable.
