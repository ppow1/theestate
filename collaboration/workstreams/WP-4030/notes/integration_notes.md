# WP-4030 Integration Notes

WP-4030 is intentionally staged and local-only. Later WP-4031 installation work
should register a CLI wrapper, Office status panels, service supervision hooks,
and lifecycle reporting only after these staged tests are re-run.

Do not add cloud targets or unrestricted host-path backup configuration. Any
production scope must be declared as relative paths rooted inside the approved
resident runtime data root.
