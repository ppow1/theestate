# WP-4045 — Resident Registry Synchronization

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Runtime Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Start Condition

Execute only after WP-4044 is merged to `main`.

## Objective

Make the Estate resident, employee, office, authority, lifecycle, mailbox, and active-runtime registries a synchronized source of truth for resident cognition so no resident can deny an active colleague, invent an appointment, misstate an office, or rely on stale prompt memory for institutional identity facts.

## Problem Statement

Live testing after WP-4042 exposed conflicting resident beliefs:

- Helen and Grace denied that Evelyn existed.
- Alfred reported incomplete or unspecified relationships.
- Residents disagreed about Grace's appointment state.
- Conference-room participants produced mutually inconsistent descriptions of the active cast.
- Mailbox and communication availability were guessed rather than read from canonical Estate state.

The runtime currently exposes fragments of resident identity, but it does not provide a deterministic, validated, current registry snapshot before each resident inference.

## Architectural Requirements

Implement a canonical `ResidentRegistrySnapshot` and synchronization service that reconciles, at minimum:

- `data/registry/residents.json`
- employee/personnel registry records
- office and organizational assignments
- appointment and activation state
- authority and delegation records
- resident surface definitions
- mailbox and message-endpoint availability
- active gateway model exposure
- candidate versus appointed versus active lifecycle status

The synchronized snapshot must be read-only to resident inference and must not become a second registry.

## Required Behavior

1. Build one deterministic snapshot from canonical Estate artifacts.
2. Detect duplicate IDs, conflicting office assignments, stale activation state, missing mailbox bindings, and gateway/registry drift.
3. Fail closed on unresolved contradictions and expose a diagnostic rather than selecting an arbitrary truth.
4. Inject the synchronized snapshot into the runtime identity-composition path created by WP-4043.
5. Make current registry state visible to single-resident and conference-room requests.
6. Ensure updates become visible without hand-editing prompts or duplicating metadata.
7. Preserve privacy boundaries: directory-level facts may be shared; protected relationship-layer content may not.

## Resident Answer Rules

When asked about another resident, a resident shall answer from the synchronized snapshot and distinguish:

- active resident
- appointed but inactive resident
- candidate
- former/retired resident
- unknown/unverified person

Residents shall not:

- deny a registered active resident
- claim a candidate is active
- invent an office, employee ID, mailbox, or appointment
- infer lifecycle state from old conversation history
- expose protected continuity or private relationship-layer content

## Diagnostics

Provide a machine-readable diagnostic surface containing:

- snapshot timestamp
- source artifacts consulted
- record counts
- detected conflicts
- stale or missing bindings
- gateway exposure drift
- snapshot hash/version

Do not include protected message bodies or restricted continuity content in diagnostics.

## Validation

Add tests proving at least the following:

1. Helen, Grace, Ingrid, Alfred, and Evelyn all recognize each active resident.
2. Candidate and inactive states are described correctly.
3. Conflicting registry records fail closed with an explicit diagnostic.
4. A registry update is reflected in the next runtime composition without prompt edits.
5. Conference-room participants receive the same synchronized institutional cast.
6. Evelyn's protected relationship-layer data is not included in the shared registry snapshot.
7. Gateway model exposure and registry state are checked for drift.
8. No duplicate registry or alternate source of truth is introduced.

## Deliverables

- canonical registry synchronization module
- typed/read-only resident registry snapshot
- integration with resident identity composition
- conflict and drift diagnostics
- single-resident and conference-room tests
- documentation of source precedence
- completion receipt

## Constraints

- Strengthen existing registries; do not create a new department or parallel registry.
- Derived indexes must be regenerated from canonical artifacts, not manually edited.
- No privileged Estate action may be executed by resident inference.
- Keep implementation bounded to registry synchronization and runtime consumption.

## Completion Criteria

This package is complete when all current residents agree on the active cast, offices, lifecycle states, and public authority facts using one synchronized Estate snapshot, and contradictory registry state produces a visible failure instead of a hallucinated answer.
