# WP-0525 Rollback Notes

WP-0525 is staged and not installed. To roll back this staged package before WP-0531 installation, remove:

- `collaboration/workstreams/WP-0525/install_manifest.json`
- `collaboration/workstreams/WP-0525/staged/office_resident_presence.py`
- `collaboration/workstreams/WP-0525/staged/test_office_resident_presence.py`
- `collaboration/workstreams/WP-0525/resident_presence_contract.md`
- `collaboration/workstreams/WP-0525/validation_notes.md`
- `collaboration/workstreams/WP-0525/rollback_notes.md`
- `collaboration/work_packages/completions/WP-0525_codex_done.json`

No shared active Office file rollback is required because WP-0525 does not install into active Office surfaces.
