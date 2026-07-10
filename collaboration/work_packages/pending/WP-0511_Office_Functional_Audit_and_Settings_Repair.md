# WP-0511 - Office Functional Audit and Settings Repair

Status: Proposed
Priority: High
Owner: Chief Architect #5
Classification: Estate Internal
Created: 2026-07-10

## Mission

Audit the entire Office of the Steward for real operational functionality and fully repair the Settings page as the first implementation wave.

This is not a cosmetic redesign and not another placeholder pass.

A control is complete only when:

```text
browser input
-> structured Office request
-> canonical Estate handler
-> durable state change
-> refreshed Office payload
-> visible effect after reload
-> deterministic test proof
```

## Codex Direction

```text
Read this work package and do exactly what it says.

Do not create a new web framework, Office, command bus, settings registry, queue, provider, or event system.

Do not claim a control is functional because it renders, is clickable, has a handler registered, or returns HTTP 200.

Repair Settings into a real persistent control surface and leave a machine-readable audit of the rest of the Office.
```

## Required Reading

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
docs/governance/Institutional_Operations_Doctrine.md
src/estate/core/steward_command_center.py
src/estate/core/office_command_surface.py
src/estate/core/operations_center_settings.py
src/estate/core/operations_center_workspace_profiles.py
src/estate/core/steward_presence.py
src/estate/core/mission_control_workspace.py
src/estate/cli/main.py
tests/test_steward_command_center.py
tests/test_office_command_surface.py
tests/test_operations_center_settings.py
```

Inspect the actual rendered HTML, JavaScript, tab routing, action endpoint, input handling, persistence paths, refresh behavior, and failure rendering.

## Part A - Functional Audit

Create a reusable audit implementation, preferably:

```text
src/estate/core/office_functional_audit.py
```

The audit must inventory every:

- navigation entry;
- tab and panel;
- visible button, selector, checkbox, input, link, form, and menu;
- Office action ID;
- handler registration;
- endpoint route;
- required input;
- artifact read/write;
- runtime state change;
- refresh and reload effect.

Classify each surface as exactly one of:

```text
functional
partially_functional
display_only
placeholder
broken
duplicative
missing_required_capability
```

Each audit record must include at least:

```text
surface_id
surface_type
tab_id
label
rendered
visible
enabled
action_id
handler
endpoint
required_inputs
input_controls_present
request_reaches_handler
runtime_state_changed
artifacts_read
artifacts_written
payload_changed_after_action
change_visible_after_refresh
change_persists_after_reload
failure_feedback_truthful
classification
severity
repair_wave
notes
```

The audit must detect:

- dead tabs and missing panels;
- visible controls with no handler;
- registered handlers with no reachable control;
- duplicate action IDs or duplicate tabs;
- permanently disabled placeholders;
- controls that report success without changing state;
- controls whose result is not reflected after refresh;
- artifact-only pages presented as command surfaces;
- CLI-only operational capabilities that belong in the Office.

Write:

```text
runtime/steward/office_functional_audit.json
runtime/steward/office_functional_audit_summary.json
runtime/steward/office_repair_waves.json
operations/steward/office_functional_audit.md
```

Create repair waves that prioritize:

```text
Wave 1 - deceptive or broken core controls
Wave 2 - Settings, navigation, refresh, and persistence
Wave 3 - CLI-only operational capabilities
Wave 4 - duplicate and low-value surfaces
Wave 5 - layout improvements after functionality is proven
```

## Part B - Real Settings Repair

The Settings page must stop being a placeholder.

Use and extend the existing settings subsystem rather than creating a parallel one.

Support only settings that can be applied truthfully. At minimum implement:

```text
theme
accent or highlight preference
startup tab
default workspace
visible tabs
navigation order
status bar visibility
action console visibility
auto-refresh enabled
auto-refresh interval
global verbosity
topic verbosity overrides
resident verbosity overrides
layout density
```

If a setting cannot be made operational in this package, do not render a fake enabled control. Show it as unsupported with a specific reason.

Implement real actions for:

```text
Load current settings
Save and apply settings
Reset to defaults
Export settings
Import settings
```

The persistence contract must include a versioned schema and atomic writes. Use the existing settings path where possible.

Required cycle:

```text
Change a setting in the browser
-> validate input
-> persist settings
-> apply to current Office state
-> refresh the affected UI
-> reload or restart the Office
-> setting remains active
```

Malformed settings must not crash the Office. Show a warning and offer Reset to Defaults.

## Functional Requirements

### Theme and appearance

- current theme is selected;
- changing theme visibly changes rendered CSS/classes/variables;
- reload preserves it;
- invalid themes are rejected;
- accent and density changes are measurable when supported.

### Navigation

- hidden tabs disappear from navigation;
- navigation order changes immediately and persists;
- invalid or duplicate tab IDs are rejected;
- Settings cannot hide itself without a recovery path;
- hiding the active tab falls back safely.

### Refresh

- enabled state and interval persist;
- browser timer starts and stops accordingly;
- duplicate timers are prevented;
- invalid intervals are blocked;
- current refresh state is visible.

### Verbosity

- global verbosity changes rendered detail;
- topic and resident overrides supersede the global value;
- preferences must affect actual output, not merely be stored.

### Import and export

- export produces valid settings JSON;
- import validates schema and allowed values;
- prior settings are backed up before import;
- unsafe or unknown executable fields are rejected;
- changed fields are reported truthfully.

## Office Integration

Likely files:

```text
src/estate/core/steward_command_center.py
src/estate/core/office_command_surface.py
src/estate/core/operations_center_settings.py
src/estate/core/operations_center_workspace_profiles.py
src/estate/cli/main.py
```

Create tests, preferably:

```text
tests/test_office_functional_audit.py
tests/test_office_settings_functional.py
```

Create docs:

```text
docs/integration/office_functional_audit.md
docs/integration/office_settings_control_surface.md
```

Create completion receipt:

```text
collaboration/work_packages/completions/WP-0511_codex_done.json
```

Register a WP-0511 validation recipe.

Optional CLI recovery and audit surfaces may include:

```text
python -m estate.cli.main office-functional-audit run --json
python -m estate.cli.main office-functional-audit status --json
python -m estate.cli.main office-settings show --json
python -m estate.cli.main office-settings apply --settings <path> --json
python -m estate.cli.main office-settings reset --json
```

The browser remains the primary Settings control surface.

## Test Requirements

Audit tests must prove:

- every navigation tab is inventoried;
- every registered action is inventoried;
- every rendered control is inventoried;
- missing handlers and duplicate IDs are detected;
- placeholder text and permanently disabled controls are classified honestly;
- enabled controls with no state change are not marked functional;
- repair waves are deterministic.

Settings tests must prove:

- persisted values render correctly;
- changing theme updates the artifact and rendered Office;
- reload preserves theme;
- visible tabs and navigation order change and persist;
- startup tab changes initial selection;
- auto-refresh settings alter the actual timer without duplication;
- verbosity changes actual rendered detail;
- reset restores defaults;
- export returns valid schema;
- valid import applies settings;
- malformed import is blocked;
- malformed stored settings produce a recoverable warning;
- completed, blocked, and failed action results are distinct;
- no live provider, network, GPU, Ollama, ChatGPT, or Codex CLI call occurs.

At least one end-to-end deterministic test must execute:

```text
open Settings payload
-> change theme and visible tabs
-> submit Save/Apply
-> verify settings artifact changed
-> reload Office payload
-> verify theme and navigation changed
-> recreate the Office against the same root
-> verify settings remain active
```

## Out of Scope

Do not:

- repair every Office tab in this package;
- redesign the whole visual language;
- migrate to another frontend framework;
- replace the local HTTP server;
- create another command bus;
- add remote authentication;
- perform live provider calls;
- auto-authorize, auto-retry, auto-merge, or grant institutional acceptance.

The audit identifies remaining defects. Settings is the page that must be fully repaired here.

## Acceptance Criteria

1. Every Office tab and visible control is inventoried and classified.
2. The audit distinguishes real functionality from rendering or registration.
3. Prioritized repair-wave artifacts exist.
4. Settings is no longer a placeholder page.
5. Supported Settings controls are enabled and operational.
6. Browser changes persist to durable settings state.
7. Reload and restart preserve settings.
8. Theme, navigation, refresh, and verbosity visibly affect the Office.
9. Reset, export, and import work safely.
10. Malformed settings do not crash the Office.
11. Browser-to-handler-to-artifact-to-render tests pass.
12. Remaining broken surfaces are reported honestly.
13. WP-0511 validation passes.
14. Completion receipt exists and is ready for Chief Architect review.
15. No parallel Office, settings registry, command bus, provider, queue, event system, or web framework is created.

## Completion Receipt Assertions

The completion receipt must explicitly include:

```text
settings_persistence_verified: true
settings_reload_verified: true
theme_application_verified: true
navigation_visibility_verified: true
navigation_order_verified: true
auto_refresh_verified: true
verbosity_application_verified: true
import_export_verified: true
live_provider_calls_made: false
new_web_framework_introduced: false
new_command_bus_introduced: false
```

## Steward / Chief Architect Note

WP-0510 adds real execution controls.
WP-0511 audits the entire Office honestly and makes Settings the first fully repaired page under the standard that a control must produce a real, persistent, visible effect.
