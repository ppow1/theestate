# Estate Operations Center UI Principles v1

Status: Draft Design Contract  
Classification: Estate Internal  
Owner: Steward / Operations  
Architectural Oversight: Chief Architect  
Work Package: WP-0046

## 1. Purpose

The Estate Operations Center is the local operational interface for monitoring, steering, and reviewing Estate activity. This document defines the foundational UI architecture principles for future Operations Center work packages. It is a design contract, not an implementation package.

Future UI work must preserve these principles unless a later Chief Architect-approved architecture document supersedes them.

## 2. Scope

This specification covers:

- Primary layout principles for the Operations Center shell.
- Navigation, workspace, status, activity, command, settings, and about surfaces.
- Refresh and update behavior for local operational data.
- Verbosity controls for global and resident-specific views.
- Interface-adapter boundaries for voice integrations.
- The path for gradually aligning the UI with the Estate Visual Manifest.

This specification does not build UI components, select a frontend framework, or require network services.

## 3. Architectural Posture

### 3.1 Local-first operation

The Operations Center must be usable from local Estate artifacts before relying on remote services. It should read from repository-local documents, generated operational reports, local registries, and local runtime outputs wherever possible.

Required posture:

- Local files are the initial source of truth for operational state.
- Remote services, if added later, are adapters rather than hard dependencies.
- The UI must tolerate missing, stale, or partial local artifacts.
- Any displayed state derived from generated files must expose freshness and provenance.
- No future UI package may require full remote connectivity merely to render the shell.

### 3.2 Functional before visual polish

The first implementation must be deliberately plain and reliable. Usability, traceability, and operational clarity take precedence over animation, branding, or advanced visual treatment.

Minimum acceptable first implementation:

- Clear page structure.
- Readable tables, lists, panels, and controls.
- Explicit empty, loading, stale, warning, and error states.
- Keyboard-reachable controls.
- Text labels before icon-only controls.
- Stable layout regions that future work can refine without replacing the architecture.

### 3.3 Progressive enhancement

Future work packages should enhance individual panels and adapters without rewriting the whole shell. The shell must support incremental addition of tabs, panels, refresh sources, status indicators, and command handlers.

## 4. Canonical Shell Layout

The Operations Center shell consists of five persistent regions:

1. Collapsible navigation panel.
2. Tabbed workspace.
3. Persistent bottom status bar.
4. Collapsible live activity / SCADA console.
5. Command palette / console overlay.

These regions are architectural expectations even if the first implementation renders them with minimal styling.

## 5. Collapsible Navigation Panel

The left navigation panel is the primary orientation and routing surface.

Required behavior:

- It can expand to show labels and collapse to a compact state.
- It preserves the current active tab or route when collapsed.
- It must remain navigable by keyboard.
- It must expose stable destinations for operational domains such as dashboard, work packages, residents, validation, mailboxes, decisions, settings, and about.
- It should visually distinguish live operational views from reference or configuration views.

First implementation guidance:

- A simple vertical list is sufficient.
- Icons are optional.
- Collapsed state may use initials or short labels if icons are not available.

## 6. Tabbed Workspace

The main workspace is tabbed to support concurrent operational review without forcing full context switches.

Required behavior:

- Tabs represent open operational views or documents.
- Users can switch tabs without resetting global shell state.
- Refreshes must update tab content in place rather than redraw the entire page shell.
- A default dashboard tab should be available.
- Future packages may add closable, pinned, or deep-linked tabs, but must not require them for first use.

Recommended initial tabs:

- Overview.
- Work Package Pipeline.
- Validation and Estate Health.
- Residents.
- Decision Queue.
- Mailboxes / Communications.
- Settings.
- About.

## 7. Persistent Bottom Status Bar

The bottom status bar provides always-visible operational context.

Required content categories:

- Current local time and last refresh time.
- Overall Estate health indicator.
- Validation state or most recent validation result.
- Active warnings or blocked item count.
- Runtime / worker heartbeat summary when available.
- Data freshness and source-status indicator.
- Current global verbosity mode.

Required behavior:

- The bar persists across tabs and navigation changes.
- It must be compact and not obscure primary work content.
- It should provide drill-in affordances to relevant tabs or console entries.
- It must clearly show stale or unavailable data rather than implying healthy state.

## 8. Collapsible Live Activity / SCADA Console

The Operations Center should include a collapsible console inspired by network operations and SCADA monitoring. It is not limited to industrial telemetry; it is the live operational activity surface for the Estate.

Required behavior:

- The console can collapse, expand, and remain available across the shell.
- It displays time-ordered operational events, warnings, worker activity, validation events, mailbox activity, and command results when available.
- It supports filtering by severity, source, resident, subsystem, and freshness where data permits.
- It must distinguish observed events from inferred summaries.
- It must never be the only location for critical state; critical items must also surface in durable panels or reports.

First implementation guidance:

- A static or locally refreshed event list is acceptable.
- Live streaming is not required for the first version.
- The UI should reserve the interaction pattern so future streaming adapters can attach without redesign.

## 9. Command Palette / Console

The Operations Center must define a command surface for fast navigation and future operational actions.

Required behavior:

- The command palette can search views, resident records, work packages, documents, and supported commands.
- Commands are explicit, named, and auditable.
- Destructive or state-changing commands require confirmation and clear provenance.
- The command surface must be able to report command output to the activity console.
- The first implementation may be navigation-only.

Recommended command categories:

- Navigate to view.
- Open local artifact.
- Filter current panel.
- Refresh data source.
- Show resident.
- Show work package.
- Open settings.
- Show about / component inventory.

## 10. Dynamic Refresh Without Full-page Redraws

The UI must refresh operational data without rebuilding the entire shell.

Required behavior:

- Each panel declares its data dependencies.
- Refreshes update the smallest practical region: status bar, active tab, console, or specific panel.
- The shell remains stable during refresh.
- Loading, stale, failed, and partial-refresh states are visible.
- User context such as selected tab, collapsed panels, filters, and scroll position should be preserved where practical.

Local refresh sources may include generated JSON, Markdown-derived summaries, registries, validation reports, mailbox files, and runtime heartbeat artifacts.

## 11. Verbosity Controls

The Operations Center must support both global and per-resident verbosity controls.

### 11.1 Global verbosity

Global verbosity determines the default detail level across the shell.

Recommended levels:

- Quiet: only critical status, blockers, and required actions.
- Normal: concise operational summaries and warnings.
- Detailed: expanded provenance, timestamps, source paths, and intermediate status.
- Diagnostic: implementation-oriented details, raw records, and adapter diagnostics.

The current global verbosity level should appear in the status bar and be configurable from settings.

### 11.2 Per-resident verbosity

Per-resident verbosity allows specific resident, worker, or office views to display more or less detail than the global default.

Required behavior:

- A resident-specific override can inherit from the global level.
- Overrides must be visible when active.
- Resident cards or profiles should respect the effective verbosity level.
- Diagnostic details for a resident should not flood unrelated panels.

## 12. Settings Page

The Operations Center must include a settings page for user-facing configuration.

Required settings categories:

- Theme: plain, system, high-contrast, and future Estate Visual Manifest-inspired themes.
- Refresh: manual, interval, and source-specific refresh preferences.
- Filters: default severity, subsystem, resident, work-package, and freshness filters.
- Layout: navigation collapsed state, console collapsed state, tab behavior, density, and panel ordering where supported.
- Notifications: local notification preferences, warning thresholds, and quiet modes.
- Verbosity: global default and resident-specific overrides.

Settings must be local-first and should be serializable so they can later be stored in a local config file or browser-local persistence layer.

## 13. About Page and Component / Version Inventory

The Operations Center must include an About page that inventories the running interface and its data sources.

Required inventory categories:

- Operations Center shell version.
- Build or package version when available.
- UI architecture specification version.
- Data adapters and their versions.
- Local source artifacts used by visible panels.
- Last refresh time per adapter.
- Known unavailable adapters or missing artifacts.
- Repository branch and commit when available.

The About page must help operators answer: "What am I looking at, where did it come from, and how fresh is it?"

## 14. Voice Integration Hooks

Voice integrations are interface adapters only. This specification does not authorize embedding speech systems directly into business logic or making any voice provider mandatory.

Required adapter boundaries:

- Speech-to-text adapter: converts local or user-approved audio input into command-palette text or annotated notes.
- Text-to-speech adapter: reads selected status, summaries, alerts, or resident-focused information from UI state.
- SillyTavern adapter: bridges Estate conversation surfaces only through explicit interface contracts and local policy controls.

Required constraints:

- Voice adapters must be optional.
- The UI must work fully without voice adapters.
- Voice input must route through the same command validation, confirmation, and audit paths as typed commands.
- Voice output must respect verbosity, privacy, quiet-mode, and notification settings.
- Adapter failures must degrade gracefully and appear as adapter status, not shell failure.

## 15. Visual Manifest Alignment

The Operations Center should gradually reflect the Estate Visual Manifest while preserving a simple first implementation. The canonical visual onboarding entry point is `docs/onboarding/visual_manifest.md`, which points workers to the Estate master-plan and organization-overview visuals.

Progression model:

1. Foundation: plain, accessible, functional shell with stable regions and clear labels.
2. Alignment: introduce visual hierarchy that reflects the Estate's organizational model, operational layers, and command-center metaphor.
3. Theming: add Estate-inspired color, spacing, typography, and iconography as selectable themes rather than hard requirements.
4. Atmosphere: refine the interface toward the Estate's bridge / operations-center identity with tasteful visual depth, panel framing, and live-status treatments.
5. Steward-grade polish: mature dashboards, resident cards, and command surfaces while retaining local-first traceability.

Guardrails:

- Visual polish must not obscure provenance, freshness, warnings, or controls.
- Simple theme must remain available.
- High-contrast and readable modes must remain available.
- Future image or motif usage must reference the Visual Manifest rather than hard-code assumptions from individual assets.

## 16. Accessibility and Operator Safety

Future implementations must treat the Operations Center as an operational tool, not a decorative website.

Required expectations:

- Keyboard access for navigation, tabs, command palette, console, and settings.
- Visible focus states.
- Readable text contrast.
- Non-color-only warning indicators.
- Confirmations for destructive commands.
- Clear distinction among healthy, warning, failed, stale, unknown, and unavailable states.

## 17. Data Provenance and State Semantics

Every operational panel should be able to explain its source.

Required panel metadata where practical:

- Source artifact or adapter name.
- Last loaded timestamp.
- Last successful refresh timestamp.
- Staleness threshold.
- Error or partial-load state.
- Whether content is observed, generated, inferred, or manually configured.

## 18. Future Work Package Compliance Checklist

Future Operations Center UI work packages should confirm that they:

- Preserve the shell layout regions defined here.
- Remain local-first.
- Avoid full-page redraws for ordinary refreshes.
- Respect global and per-resident verbosity.
- Surface source freshness and provenance.
- Add settings when behavior becomes configurable.
- Add About-page inventory entries when new components or adapters are introduced.
- Treat voice integrations as optional adapters.
- Progress toward the Visual Manifest without blocking simple functional use.
