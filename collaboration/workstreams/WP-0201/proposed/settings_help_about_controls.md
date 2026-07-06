# WP-0201 Settings, Help, and About Utility Controls

Aligned with WP-0200 vocabulary. All controls are local-only/no-upload and staged only. Diagnostics exports must display a sensitivity warning because they may include internal paths and operational state.

## Inspect current local settings
- Action ID: `settings.inspect_payload`
- Tab: `settings`
- Authority: `safe_read_only`
- Confirmation: `none`
- Local-only/no-upload: true

## Export settings/profile snapshot
- Action ID: `settings.export_snapshot`
- Tab: `settings`
- Authority: `safe_local_generated_artifact_update`
- Confirmation: `confirm_generated_artifact`
- Local-only/no-upload: true

## Preview reset to defaults
- Action ID: `settings.preview_reset_defaults`
- Tab: `settings`
- Authority: `steward_confirmed_local_mutation`
- Confirmation: `preview_before_write`
- Local-only/no-upload: true

## Save active tab profile
- Action ID: `settings.save_active_tab_profile`
- Tab: `settings`
- Authority: `steward_confirmed_local_mutation`
- Confirmation: `preview_before_write`
- Local-only/no-upload: true

## Open local documentation links
- Action ID: `help.open_local_docs`
- Tab: `help`
- Authority: `safe_read_only`
- Confirmation: `none`
- Local-only/no-upload: true

## Copy support/debug command
- Action ID: `help.copy_support_command`
- Tab: `help`
- Authority: `safe_read_only`
- Confirmation: `none`
- Local-only/no-upload: true

## Export help document index snapshot
- Action ID: `help.export_doc_index`
- Tab: `help`
- Authority: `safe_local_generated_artifact_update`
- Confirmation: `confirm_generated_artifact`
- Local-only/no-upload: true

## Draft documentation feedback note
- Action ID: `help.draft_feedback_note`
- Tab: `help`
- Authority: `steward_confirmed_local_mutation`
- Confirmation: `preview_before_write`
- Local-only/no-upload: true

## Copy version manifest
- Action ID: `about.copy_version_manifest`
- Tab: `about`
- Authority: `safe_read_only`
- Confirmation: `none`
- Local-only/no-upload: true

## Export diagnostics manifest
- Action ID: `about.export_diagnostics_manifest`
- Tab: `about`
- Authority: `safe_local_generated_artifact_update`
- Confirmation: `confirm_generated_artifact`
- Local-only/no-upload: true

## Inspect component/source inventory
- Action ID: `about.inspect_source_inventory`
- Tab: `about`
- Authority: `safe_read_only`
- Confirmation: `none`
- Local-only/no-upload: true
