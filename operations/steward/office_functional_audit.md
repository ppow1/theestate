# Office Functional Audit

Generated: 2026-07-10T05:03:32+00:00

## Summary

{
  "broken": 3,
  "functional": 72,
  "missing_required_capability": 2,
  "partially_functional": 4
}

## Records

- **navigation:home** — functional (low): Navigation entry audited against rendered tab controls.
- **navigation:mission-control** — functional (low): Navigation entry audited against rendered tab controls.
- **navigation:alfred** — functional (low): Navigation entry audited against rendered tab controls.
- **navigation:helen** — functional (low): Navigation entry audited against rendered tab controls.
- **navigation:resident-conversations** — functional (low): Navigation entry audited against rendered tab controls.
- **navigation:ai-services-models** — functional (low): Navigation entry audited against rendered tab controls.
- **navigation:daily-board** — functional (low): Navigation entry audited against rendered tab controls.
- **navigation:operational-activity** — functional (low): Navigation entry audited against rendered tab controls.
- **navigation:execution-control** — functional (low): Navigation entry audited against rendered tab controls.
- **navigation:active-projects** — broken (high): Navigation entry audited against rendered tab controls.
- **navigation:expansion-roadmap** — broken (high): Navigation entry audited against rendered tab controls.
- **navigation:parking-lot** — broken (high): Navigation entry audited against rendered tab controls.
- **navigation:work-packages** — functional (low): Navigation entry audited against rendered tab controls.
- **navigation:mailboxes** — functional (low): Navigation entry audited against rendered tab controls.
- **navigation:recalls** — functional (low): Navigation entry audited against rendered tab controls.
- **navigation:notifications** — functional (low): Navigation entry audited against rendered tab controls.
- **navigation:validation** — functional (low): Navigation entry audited against rendered tab controls.
- **navigation:search** — functional (low): Navigation entry audited against rendered tab controls.
- **navigation:settings** — functional (low): Navigation entry audited against rendered tab controls.
- **navigation:help** — functional (low): Navigation entry audited against rendered tab controls.
- **navigation:about** — functional (low): Navigation entry audited against rendered tab controls.
- **tab:home** — functional (low): Panel must exist for each visible tab.
- **tab:mission-control** — functional (low): Panel must exist for each visible tab.
- **tab:alfred** — functional (low): Panel must exist for each visible tab.
- **tab:helen** — functional (low): Panel must exist for each visible tab.
- **tab:resident-conversations** — functional (low): Panel must exist for each visible tab.
- **tab:ai-services-models** — functional (low): Panel must exist for each visible tab.
- **tab:daily-board** — functional (low): Panel must exist for each visible tab.
- **tab:operational-activity** — functional (low): Panel must exist for each visible tab.
- **tab:execution-control** — functional (low): Panel must exist for each visible tab.
- **tab:projects** — functional (low): Panel must exist for each visible tab.
- **tab:roadmap** — functional (low): Panel must exist for each visible tab.
- **tab:parking** — functional (low): Panel must exist for each visible tab.
- **tab:work-packages** — functional (low): Panel must exist for each visible tab.
- **tab:mailboxes** — functional (low): Panel must exist for each visible tab.
- **tab:recalls** — functional (low): Panel must exist for each visible tab.
- **tab:notifications** — functional (low): Panel must exist for each visible tab.
- **tab:validation** — functional (low): Panel must exist for each visible tab.
- **tab:search** — functional (low): Panel must exist for each visible tab.
- **tab:settings** — functional (low): Panel must exist for each visible tab.
- **tab:help** — functional (low): Panel must exist for each visible tab.
- **tab:about** — functional (low): Panel must exist for each visible tab.
- **action:execution_session.preview** — functional (low): No provider call; writes preview/session evidence.
- **action:execution_session.start** — functional (low): Requires explicit confirmation and existing authorization evidence.
- **action:execution_session.resume** — functional (low): Preserves duplicate-provider-call protection.
- **action:execution_session.status** — functional (low): Audited from rendered HTML and action registry.
- **action:execution_session.report** — functional (low): Audited from rendered HTML and action registry.
- **action:execution_attempt.cancel_request** — functional (low): Records request; does not claim provider stopped.
- **action:execution_attempt.inspect_recovery** — functional (low): Audited from rendered HTML and action registry.
- **action:execution_attempt.retry_eligibility** — functional (low): Does not authorize or start a retry.
- **action:execution_attempt.release_stale** — functional (low): Requires explicit confirmation and stale-safe evidence.
- **action:execution_result.inspect_reconciliation** — functional (low): Audited from rendered HTML and action registry.
- **action:execution_result.reconcile** — functional (low): Idempotent; never grants institutional acceptance.
- **action:execution_result.report** — functional (low): Audited from rendered HTML and action registry.
- **action:settings.load_current** — functional (low): Audited from rendered HTML and action registry.
- **action:settings.save_apply** — functional (low): Persists atomically and reloads Office payload.
- **action:settings.reset_defaults** — functional (low): Audited from rendered HTML and action registry.
- **action:settings.export** — functional (low): Audited from rendered HTML and action registry.
- **action:settings.import** — functional (low): Audited from rendered HTML and action registry.
- **action:ai_services.refresh_local_inventory** — partially_functional (medium): Audited from rendered HTML and action registry.
- **action:validation.run_production_readiness** — functional (low): Evidence is not institutional acceptance.
- **action:work_packages.refresh_assignment_queue** — functional (low): Audited from rendered HTML and action registry.
- **action:work_packages.validate_selected** — partially_functional (medium): Audited from rendered HTML and action registry.
- **action:notifications.refresh_center** — functional (low): Audited from rendered HTML and action registry.
- **action:notifications.local_acknowledge** — partially_functional (medium): Local state only; authoritative closure is unchanged.
- **action:alfred.request_briefing** — functional (low): Audited from rendered HTML and action registry.
- **action:mission_control.refresh_payload** — functional (low): Audited from rendered HTML and action registry.
- **action:daily_board.generate_morning_briefing** — partially_functional (medium): Audited from rendered HTML and action registry.
- **action:orchestrator_intake.record_decision** — functional (low): Records a durable decision artifact; does not schedule or execute work.
- **action:operations_control.record_decision** — functional (low): Writes an operations-control decision artifact; does not execute providers.
- **action:operations_control.run_provider** — missing_required_capability (medium): Provider execution is intentionally outside the Office traffic-controller panel.
- **action:ai_services.start_stop_load** — missing_required_capability (medium): Process-control approval workflow is not implemented for Office controls; use existing governed service approval path first.
- **control:settings-theme** — functional (low): WP-0511 settings control.
- **control:settings-accent** — functional (low): WP-0511 settings control.
- **control:settings-density** — functional (low): WP-0511 settings control.
- **control:settings-startup-tab** — functional (low): WP-0511 settings control.
- **control:settings-nav-order** — functional (low): WP-0511 settings control.
- **control:settings-refresh-enabled** — functional (low): WP-0511 settings control.
- **control:settings-refresh-seconds** — functional (low): WP-0511 settings control.
- **control:settings-global-verbosity** — functional (low): WP-0511 settings control.
- **control:settings-json** — functional (low): WP-0511 settings control.
