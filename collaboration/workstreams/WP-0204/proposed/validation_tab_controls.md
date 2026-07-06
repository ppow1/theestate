# WP-0204 Validation Tab Controls

WP-0200 staged vocabulary available and used: action classes, authority classes, confirmation requirements, local-only posture, read/write artifacts, command hooks, output paths, failure behavior, and disabled/prohibited semantics.

Safety rules: UI state is evidence, not acceptance; copy controls do not execute; recipes require explicit confirmation and report output paths; production readiness never overrides blockers; observations are drafts until approved transitions; bulk export summarizes affected items and includes sensitivity warnings.

## Controls
- **Open validation report** (`validation.open_report`): Read validation markdown reports and related runtime JSON. Authority: safe read-only. Confirmation: none. Local only. Validation evidence is not institutional acceptance.
- **Copy validation command** (`validation.copy_command`): Copy validate-work-package command text only. Authority: safe read-only. Confirmation: none. Local only. Copied command grants no acceptance.
- **Run validation recipe** (`validation.run_recipe`): Design for confirmed local validation recipe execution with output paths. Authority: safe local generated-artifact update. Confirmation: explicit Steward confirmation. Local only. Generated evidence is not acceptance.
- **Run production readiness** (`validation.run_production_readiness`): Design for confirmed production readiness refresh. Authority: safe local generated-artifact update. Confirmation: explicit Steward confirmation. Local only. Readiness output does not override blockers.
- **Inspect blocker/failure detail** (`validation.inspect_blocker`): Open source artifacts behind warning/error. Authority: safe read-only. Confirmation: none. Local only. Failure inspection is evidence only.
- **Copy failing command** (`validation.copy_failing_command`): Copy failing command text from report. Authority: safe read-only. Confirmation: none. Local only. Copied command does not execute or accept.
- **Create validation observation draft** (`validation.create_observation_draft`): Draft observation without closing failure. Authority: Steward-confirmed local mutation. Confirmation: explicit Steward confirmation. Local only. Observation draft does not close failure.
- **Export validation evidence bundle** (`validation.export_evidence_bundle`): Design local bundle export with sensitivity warning. Authority: safe local generated-artifact update. Confirmation: explicit confirmation for generated bundle. Local only. Evidence bundle is not acceptance.
