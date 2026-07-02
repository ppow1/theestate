# ADR-0002: Estate Work Package Registry Proposal

## Status
Proposed — pending Chief Architect review

## Context

Work packages currently exist primarily as files under `collaboration/work_packages/`, prompts, or board references. This makes them useful for local delegation but weak as institutional objects because their authoritative state, review history, dependencies, and completion markers are distributed across transient execution records.

The Estate architecture already treats conversation as an interface rather than state, and expects persistent state to answer what is running, blocked, owned, waiting, and complete. A Work Package Registry should extend that principle to delegated work packages without changing existing governance or lifecycle states before Chief Architect approval.

## Decision Drivers

- Work packages must become durable, auditable Estate objects.
- The registry must reference existing documents rather than replace them prematurely.
- Registry state must support Chief Architect review gates for architecture/governance-adjacent work.
- Codex workers need enough metadata to determine suitability, merge risk, dependencies, and validation requirements before execution.
- The model must relate work packages to missions and operations boards while avoiding a direct governance-state change in this proposal.

## Proposed Registry Model

This ADR proposes the following conceptual fields for Chief Architect review. Field names are descriptive and not a final schema contract.

| Field | Purpose |
|---|---|
| Work Package ID | Stable identifier such as `WP-0016`; must remain unique across the Estate. |
| Title | Human-readable work package name. |
| Status | Current existing work package status using approved lifecycle language only; this ADR does not create new states. |
| Mode | Execution/review mode, such as architecture-first, implementation, validation, or operations, using approved mode vocabulary. |
| Owner | Accountable Estate role, resident, or worker lane. |
| Source Request | Link or citation to the originating prompt, board item, message, mission order, or executive request. |
| Dependencies | Other work packages, decisions, board items, ADRs, validations, or external prerequisites required before execution or merge. |
| Codex Suitability | Assessment of whether Codex may execute directly, needs human/CA review first, or is unsuitable without decomposition. |
| Merge Class | Merge risk class, including whether CA review is required before implementation or merge. |
| Validation State | Current validation posture and required checks, without redefining validation lifecycle terminology. |
| Completion Marker | Canonical completion artifact path or event proving the package reached an accepted terminal condition. |
| CA Review Record | Review request, reviewer, decision, date, conditions, and references to review messages or ADR approvals. |
| Mission Relation | Parent mission, program, or strategic effort that gives the package authority and context. |
| Board Relation | Operations board rows or active-work entries where the package appears. |

## Object Boundary

A registered work package should be treated as a small institutional record that points to supporting artifacts rather than embedding every artifact directly. The registry record should answer:

1. What is the work package?
2. Who owns it?
3. Why does it exist?
4. What must happen before it can proceed?
5. Is Codex allowed to execute it?
6. What review gate applies?
7. What proves completion?
8. Which mission or board is it part of?

The canonical work instructions may remain in `collaboration/work_packages/`. The registry should index and govern those instructions rather than replace them in the first implementation.

## CA Review Requirements

Before implementation, the Chief Architect should decide:

- Whether the registry belongs in `data/registry/`, `collaboration/work_packages/registry/`, another persistent-state location, or a future database-backed store.
- Whether status and mode values should be controlled by existing documents or by a new enum owned elsewhere.
- Whether completion markers should be JSON files, event records, board updates, promotion records, or a combination.
- Whether CA review records are embedded in the registry entry or linked as separate collaboration messages.
- How strict dependency validation should be during early adoption.
- How the registry relates to operations boards without making boards a second source of truth.

## Non-Decisions

This proposal does not:

- Implement a registry schema.
- Add or change governance lifecycle states.
- Migrate existing work packages.
- Create validation tooling.
- Change board formats.
- Authorize Codex implementation of the registry before CA review.

## Follow-on Codex Implementation Package Outline

After Chief Architect approval, a separate Codex work package should be created with the approved model. That implementation package should include:

1. The approved registry storage location.
2. The approved record format and required fields.
3. Migration or seed entries for active/pending work packages if authorized.
4. Validation checks for required fields and unique IDs.
5. Documentation updates describing registry use.
6. Completion criteria that include tests or structural validation.

The follow-on package should not be executed until the CA review record explicitly authorizes implementation.

## Consequences

### Positive

- Work packages gain stable identity and auditability.
- Codex can be routed more safely based on suitability and merge class.
- Architecture-first packages can be blocked from implementation until review is recorded.
- Missions, boards, and package files can be connected without making prompts the source of truth.

### Risks

- A registry can become bureaucratic if too many fields are mandatory too early.
- Boards and registry records may diverge unless source-of-truth rules are explicit.
- Validation tooling may accidentally create lifecycle semantics before governance approval.

## Recommendation

Approve the conceptual model with a minimal first implementation after CA review: one durable registry record per work package, linked to existing work-package files and board rows, with CA review metadata required for Class B or higher work. Keep lifecycle terms unchanged and defer automation beyond structural validation until the registry has been used on several packages.
