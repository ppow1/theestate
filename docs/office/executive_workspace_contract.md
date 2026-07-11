# WP-0522 Executive Workspace Contract

## Scope
This is an installed executive workspace for answering two Steward-facing questions:

1. What requires Steward attention now?
2. Is the Estate safe to leave unattended for a short period?

## Inputs
The workspace inspects existing Estate evidence only, including work-package directories, operations boards, service/provider health artifacts, validation evidence, readiness artifacts, and review/completion areas.

## Outputs
- Deterministic prioritized attention queue.
- Readiness verdict for short unattended operation: `ready`, `conditional`, or `not_ready`.
- Recommended next governed action with explanation and evidence links.
- Drill-down paths to source artifacts and controlling workspaces.
- Missing-evidence and uncertainty disclosures.
- Explicit authority boundaries.

## Ranking Contract
Attention items sort by descending numeric `priority_score`, then stable item id. Current blockers and failed validation outrank reviews, unresolved decisions, provider/runtime health, stale work, and missing evidence.

## Authority Boundary
Recommendations are evidence, not decisions. The staged workspace never approves work, rejects work, installs work, executes commands on behalf of the Steward, or mutates shared active Office files.

## Install Boundary
Shared Office integration is deferred to WP-0531 INSTALL-HANDOFF. Expected future targets may include a dedicated installed module, Office tab registration, command-surface registration, tests, and documentation.
