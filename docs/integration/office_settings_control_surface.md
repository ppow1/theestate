# Office Settings Control Surface

WP-0511 repairs Settings as a persistent browser-to-handler-to-artifact control surface. The Settings tab now renders enabled controls only for supported local preferences: theme, accent, startup tab, default workspace, visible tabs, navigation order, status bar visibility, action console visibility, auto-refresh state and interval, verbosity, topic/resident verbosity overrides, and layout density.

Settings actions use the existing Office action endpoint `/api/office/actions/execute` and existing settings artifact `runtime/steward/operations_center_settings.json`:

- `settings.load_current`
- `settings.save_apply`
- `settings.reset_defaults`
- `settings.export`
- `settings.import`

Writes are atomic. Imports validate the schema, reject unknown unsafe top-level fields, and back up the prior settings file before replacing it. Malformed stored settings are normalized to safe defaults with visible warnings rather than crashing the Office.
