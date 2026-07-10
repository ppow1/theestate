# WP-0528 Rollback Notes

WP-0528 is staged-only. Rollback before WP-0531 installation is removal of:

- `collaboration/workstreams/WP-0528/install_manifest.json`;
- `collaboration/workstreams/WP-0528/staged/office_operational_timeline.py`;
- `collaboration/workstreams/WP-0528/staged/test_office_operational_timeline.py`;
- `collaboration/workstreams/WP-0528/operational_timeline_contract.md`;
- `collaboration/workstreams/WP-0528/validation_notes.md`;
- `collaboration/workstreams/WP-0528/rollback_notes.md`;
- `collaboration/work_packages/completions/WP-0528_codex_done.json`.

No shared active Office files are modified by this staged package. If WP-0531 later installs the timeline, rollback must follow WP-0531's active-file install plan.
