# Repository Boundary and Local Runtime State v1

## Boundary statement

GitHub is an external crossing for the Estate. It is appropriate for source code, authored institutional contracts, governance documents, tests, install manifests, staged workstream artifacts, work packages, completion receipts, and deliberate evidence approved for sharing.

GitHub is not the default transport for live Estate state. Normal Office operation can generate dashboards, search indexes, validation rollups, assignment queues, resident interactions, approvals, attachment references, local model inventory, worker heartbeats, and other environment-specific state. Those artifacts are local-first and should not be casually committed as source.

## Ingrid posture

Ingrid's future office should own and approve the Estate's external-sharing posture for runtime data, privacy, clearance, boundaries, and external crossings. Until Ingrid is fully operational, the repository defaults to local-only treatment for live runtime projections and sensitive resident or operational state.

## Working rule until Ingrid owns the office

1. Keep authored source, governance, tests, install manifests, staged workstream content, work packages, completion receipts, and deliberate evidence tracked.
2. Keep regenerated runtime projections, resident conversations, approvals, local attachment references, local AI/model inventory, current dashboards, and validation rollups out of Git by default.
3. If a runtime artifact is needed as evidence, create or move a deliberate evidence artifact under the appropriate completion or operations evidence path instead of committing live local state wholesale.
4. If classification is unclear, use `review_required` and ask for Steward/Ingrid review before publishing externally.
