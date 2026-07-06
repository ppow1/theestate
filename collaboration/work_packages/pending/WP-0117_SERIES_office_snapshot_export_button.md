# SERIES TASK WP-0117 — Office Snapshot Export Button

## Codex Command
Read collaboration/work_packages/pending/WP-0117_SERIES_office_snapshot_export_button.md and do exactly what it says.

## Mode
SERIES

## Mission
Implement a local-only Office Snapshot export feature in the Office of the Steward so the Steward can click one button in the local web UI and download a portable ZIP package containing the current Office page state for drag-and-drop AI-assisted debugging and review.

This promotes Parking Lot item PL-0017 into active implementation.

## Background
The Office of the Steward web surface is becoming the primary local interface for Estate operations. Debugging visual/UI issues through chat is currently painful because the Steward must describe the current page, which panels are open, what tabs are active, what CSS is applied, and what runtime artifacts are being rendered.

The Steward needs a one-click snapshot button that captures the current interface state and downloads a ZIP file that can be dragged back into ChatGPT or another AI assistant for offline analysis.

The snapshot must be local-first. It must not transmit Estate data to any external service. The browser should assemble and download the debug package locally from the currently rendered page and locally served assets/artifacts where feasible.

Parking Lot item PL-0017 describes this need as:

Office Snapshot Export: add a one-click Office Snapshot button to the Office of the Steward that exports the current page/interface into a portable review package containing rendered HTML, CSS, JavaScript, visible panels, navigation structure, active workspace, DOM state, UI metadata, and future screenshot/runtime artifact support for drag-and-drop AI-assisted UI review.

The Steward has now clarified that the snapshot should also expand or record menus/panels where possible, include everything necessary to troubleshoot the current Steward web page, ZIP it into one file, and trigger an automatic download.

## Scope
Implement the first practical Office Snapshot export feature for the local Office of the Steward UI.

In scope:

1. Add a visible Office Snapshot button to the Office of the Steward UI.
2. Capture the currently rendered HTML/DOM state.
3. Capture active workspace/tab/navigation state.
4. Capture visible panels and collapsed/expanded panel state.
5. Capture CSS required to understand the rendered page.
6. Capture JavaScript required to understand the UI behavior where feasible.
7. Capture UI metadata such as timestamp, current URL/path, viewport size, user agent, active tab, active navigation item, and snapshot schema version.
8. Capture relevant local runtime/source artifact references used to render the page.
9. Package the snapshot into a ZIP file in the browser or through a local endpoint.
10. Trigger an automatic browser download of the ZIP.
11. Include a manifest file inside the ZIP describing contents and limitations.
12. Add tests for snapshot export support where feasible.
13. Add or update validation recipe for WP-0117.
14. Create a WP-0117 completion receipt.

## Out of Scope
Do not transmit snapshots externally.

Do not add cloud services, external APIs, telemetry SaaS, or remote debugging endpoints.

Do not capture secrets intentionally.

Do not capture arbitrary local files beyond the known local Office artifacts required to render/debug the current Office page.

Do not implement a general browser automation system.

Do not require Playwright, Selenium, or other heavyweight browser automation unless the repository already uses it and the dependency is justified.

Do not redesign the Office UI.

Do not change Steward, Chief Architect, Resident, validation, governance, or merge authority.

Do not make snapshot export a substitute for validation.

Do not edit estate_ledger/ledger.md or development/devlog.md unless current repository standards require it.

## Required Behavior
The implementation must provide a useful debug package even if some advanced capture features are not available.

### 1. Snapshot Button
Add a clear button or command in the Office of the Steward UI labeled one of:

- Office Snapshot
- Export Snapshot
- Debug Snapshot

The button should be accessible from a stable location such as the header, toolbar, status bar, Help/About area, or developer tools area.

The button must not disrupt normal Office navigation.

### 2. Snapshot ZIP Contents
The downloaded ZIP should include, where feasible:

- `snapshot_manifest.json`
- `page.html` or `dom.html`
- `dom_state.json`
- `ui_metadata.json`
- `styles.css` or captured inline/external stylesheet contents
- `scripts.js` or captured inline/external script references/content where feasible
- `source_artifacts.json`
- `README.md`

If screenshots are feasible without large dependencies, include:

- `screenshot.png`

If screenshot capture is not feasible in this package, record it as a known limitation and future enhancement.

### 3. DOM / HTML Capture
Capture the current rendered page state after the Office has loaded.

The capture should include current DOM content, active tab/workspace state, visible panels, and collapsed/expanded states where those states are represented in DOM attributes/classes.

The implementation should prefer actual current DOM capture over only regenerating server-side HTML.

### 4. Menu and Panel State
Where feasible, before capture either:

- record current collapsed/expanded state for all known menus/panels; or
- temporarily expand debug-relevant collapsible panels for capture and then restore their previous state; or
- include both the current state and a list of collapsed sections that were not expanded.

Do not break user navigation state permanently.

### 5. CSS and JavaScript Capture
Capture enough CSS and JavaScript context for an AI assistant to understand layout and behavior.

At minimum:

- include inline styles from the current document;
- include stylesheet hrefs and script src references;
- include local stylesheet/script contents when available and safe to fetch from the local Office server;
- record any assets that could not be fetched.

### 6. Runtime / Source Artifact Context
Include metadata about the local Estate artifacts used to render the Office where the command center already knows those artifact paths.

At minimum, include known panel/source artifact paths and availability state if those are already present in the generated page data.

Do not read unrelated local files.

### 7. Local-Only Download
The feature must create the ZIP locally and trigger a browser download.

Acceptable implementations include:

- browser-side ZIP creation using a small vendored or minimal local implementation if already available or acceptable;
- server-side local endpoint that returns a ZIP assembled from current Office state and artifacts;
- hybrid model where browser posts DOM state to a local endpoint and receives a ZIP.

If adding a ZIP library dependency is too large or not appropriate, implement a first-pass snapshot bundle format using a `.json` or `.html` download and document ZIP packaging as a follow-up. However, the preferred acceptance target is ZIP download.

### 8. Failure Handling
If snapshot export fails, show a clear local UI error or downloaded error manifest.

The failure should explain:

- which part failed;
- whether the DOM was captured;
- whether CSS/JS capture failed;
- whether ZIP packaging failed;
- what the Steward can do next.

### 9. Privacy / Safety
The snapshot package may contain Estate operational state visible on the page. The UI should indicate that the downloaded ZIP may contain internal Estate information and is intended for deliberate Steward-controlled sharing.

Do not automatically upload or send the snapshot anywhere.

## Required CLI / Command Surface
If useful and low-risk, add a local command to generate a server-side snapshot from the current generated Office artifact:

```bash
PYTHONPATH=src python -m estate.cli.main office-snapshot export --json
```

This is optional. The priority is the one-click UI export.

If a CLI command is not implemented, record the not-applicable reason in the completion receipt.

## Required Artifacts
Expected artifacts may include:

- updates to `src/estate/core/steward_command_center.py` or related Office UI modules
- optional snapshot helper module
- optional local endpoint handler for snapshot ZIP export
- optional browser-side JavaScript for DOM capture and download
- tests for snapshot metadata, endpoint behavior, or generated UI button presence
- validation recipe for WP-0117
- `collaboration/work_packages/completions/WP-0117_codex_done.json`

## Required Tests
Add or update tests to verify:

- the Office Snapshot button is rendered in the Office UI
- snapshot export code produces a package or manifest with required files/keys
- snapshot manifest includes timestamp, schema version, active UI state, and source artifact information where available
- CSS/JS references or captured content are represented
- export behavior is local-only and does not reference external upload endpoints
- failure cases are reported clearly where helper functions are added
- WP-0117 validation recipe is registered and does not return `no_recipe`

Run relevant existing tests, including command center tests if present:

```bash
PYTHONPATH=src pytest tests/test_steward_command_center.py -q
```

Also run validation tests if recipe code is changed:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
```

## Required Validation Commands
Run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0117 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If a CLI snapshot command is implemented, run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main office-snapshot export --json
```

## Required Outputs
Update or create as applicable:

- Office UI snapshot button implementation
- snapshot export helper/module if needed
- tests
- validation report for WP-0117 under `operations/validation/reports/`
- runtime validation JSON for WP-0117 under `runtime/validation/work_packages/`
- updated production-readiness artifacts if required
- `collaboration/work_packages/completions/WP-0117_codex_done.json`

## WP-0117 Self-Validation Recipe
Add a recipe for WP-0117 that verifies:

- the Office Snapshot UI control exists in generated Office HTML or related UI artifact
- snapshot export implementation exists
- snapshot manifest/schema behavior is represented by code or tests
- local-only/no-upload constraint is represented in code or documentation
- tests cover the snapshot button and package/manifest output
- WP-0117 completion receipt is complete

Use cross-platform Python checks only.

## Completion Artifact
Create:

`collaboration/work_packages/completions/WP-0117_codex_done.json`

It must include:

- `work_package_id = WP-0117`
- `codex_status = done`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- `summary`
- snapshot button location
- snapshot package contents implemented
- screenshot support status
- CLI command surface or not-applicable reason
- files changed
- tests run
- validation commands run
- known limitations
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria
WP-0117 is complete when:

1. The Office of the Steward exposes a clear one-click Office Snapshot export control.
2. The export produces a downloadable local package, preferably ZIP.
3. The package contains the current rendered page/DOM state or a documented equivalent.
4. The package contains CSS/JS context or references sufficient for UI debugging.
5. The package records active workspace/navigation/panel state.
6. The package includes a manifest and README/metadata explaining contents and limitations.
7. The implementation is local-only and does not upload data externally.
8. Tests and validation recipe cover the feature.
9. WP-0117 has a complete completion receipt.

## Merge Class
Class A if this adds a local-only debug/export feature without changing authority or production semantics.

Escalate to Class B if the implementation adds new dependencies, server endpoints, file-access behavior, or packaging behavior that materially changes Office runtime risk.
