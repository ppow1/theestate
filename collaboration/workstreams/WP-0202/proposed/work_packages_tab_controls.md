# WP-0202 Work Packages Tab Controls

All controls align with WP-0200 vocabulary and explicitly prevent silent pending work-package execution. Validation output is evidence, not institutional acceptance; review requests are not approvals.

## Inspect work package
- Action ID: `work_packages.inspect`
- Authority: `safe_read_only`
- Confirmation: `none`
- Safety: open/read pending, completion, validation artifacts; never execute pending packages

## Open source artifact
- Action ID: `work_packages.open_source`
- Authority: `safe_read_only`
- Confirmation: `none`
- Safety: open known source paths only

## Copy Codex command
- Action ID: `work_packages.copy_codex_command`
- Authority: `safe_read_only`
- Confirmation: `none`
- Safety: copy one-line command; execution_allowed false

## Copy validation command
- Action ID: `work_packages.copy_validation_command`
- Authority: `safe_read_only`
- Confirmation: `none`
- Safety: copy validation command; not executable in Wave 1

## Run validation recipe (design only)
- Action ID: `work_packages.run_validation_recipe_design`
- Authority: `safe_local_generated_artifact_update`
- Confirmation: `confirm_generated_artifact`
- Safety: future confirmed validation run produces evidence, not acceptance

## Request Chief Architect review
- Action ID: `work_packages.request_ca_review`
- Authority: `authority_gated_institutional_action`
- Confirmation: `explicit_authority_route`
- Safety: draft/queue request; does not mark review complete

## Create blocker note
- Action ID: `work_packages.create_blocker_note`
- Authority: `steward_confirmed_local_mutation`
- Confirmation: `preview_before_write`
- Safety: draft local blocker note; no canonical state transition

## Prepare sequential batch manifest
- Action ID: `work_packages.prepare_batch_manifest`
- Authority: `authority_gated_institutional_action`
- Confirmation: `explicit_authority_route`
- Safety: draft manifest only; does not submit or execute batch

## Inspect parallel workstream manifest
- Action ID: `work_packages.inspect_parallel_workstream_manifest`
- Authority: `safe_read_only`
- Confirmation: `none`
- Safety: read manifest only; does not install staged work
