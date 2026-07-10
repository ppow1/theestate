# Office Shell Action Transport

WP-0512 establishes one browser action endpoint: `POST /api/office/actions/execute`.
Every browser action sends an allow-listed `action_id`, browser-generated `request_id`, and current `payload_version`. The server dispatches only through `execute_office_action`; unknown or gated actions return structured `blocked` results rather than invoking arbitrary code.

The browser renders `running`, `completed`, `blocked`, and `failed` results in the relevant `.office-action-result` element. Failed handler exceptions include a diagnostics artifact path. State-changing actions request targeted payload refresh from `GET /api/office/payload?tab=<tab>` rather than forcing a full page reload.

Navigation is deterministic: tabs map to rendered `workspace-<tab>` panels, direct hashes activate tabs, and browser back/forward is handled via `popstate`. Settings startup tabs are validated by the settings manager; unavailable values fall back to Settings.

Duplicate submits are blocked in-browser with an in-flight action set. Static-file or unavailable-server failures render recoverable local errors.

## WP-0512 Validation Recipe

Run:

```bash
pytest tests/test_office_shell_functional.py tests/test_office_command_surface.py tests/test_steward_command_center.py
```

Evidence expected:

- all configured tabs render real workspace panels;
- invalid startup tabs fall back safely;
- hash/history navigation and duplicate-submit protection exist in the rendered runtime;
- request IDs, diagnostics, artifacts, stale warnings, malformed-response recovery, and targeted refresh are visible in browser transport;
- unregistered action IDs return structured `blocked` results.
