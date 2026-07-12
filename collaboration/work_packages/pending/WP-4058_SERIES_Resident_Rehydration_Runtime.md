# WP-4058 — Resident Rehydration Runtime

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Continuity Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4056 — Resident Continuity Package Generator
- WP-4057 — Resident Renewal Validation

## Objective

Implement a governed resident and officeholder rehydration runtime that loads approved continuity into a fresh implementation vessel without confusing the vessel with the institutional person or importing stale, unrestricted, or unauthorized context.

## Required Work

1. Define a typed rehydration request containing subject identity, target implementation, continuity package, authority scope, privacy scope, and expected assignment.
2. Verify package hashes, mandatory reading, snapshot metadata, omissions, structural warnings, and validation state before loading continuity.
3. Load canonical identity, office boundaries, current relationships, active assignments, verified execution state, and approved working-style guidance through existing runtime components.
4. Reverify time-sensitive claims against current canonical sources before presenting them as current.
5. Preserve restricted continuity in authorized contexts only.
6. Keep conversation transcripts, hidden reasoning, and implementation-specific defects out of canonical identity.
7. Produce a rehydration receipt recording loaded sources, rejected claims, uncertainty, target implementation, and validation requirements.
8. Preserve the prior implementation as read-only fallback until renewal acceptance.

## Acceptance Tests

1. A valid package rehydrates the same resident or officeholder across a new model or implementation vessel.
2. Hash mismatch, missing mandatory reading, or failed validation blocks rehydration.
3. Stale repository and runtime claims are reclassified rather than silently loaded as current.
4. Private Evelyn continuity appears only in explicitly authorized contexts.
5. The target implementation receives the inherited bounded assignment and office boundaries.
6. Rehydration does not copy unrestricted transcripts or hidden reasoning.
7. The process emits a complete inspectable receipt.

## Deliverables

- rehydration request and receipt schemas;
- package verification and loading service;
- current-state reverification adapters;
- privacy-scoped continuity loader;
- tests, diagnostics, documentation, and completion receipt.

## Constraints

- Do not create a second identity, continuity, registry, relationship, or authority system.
- Do not let the target implementation self-approve.
- Do not equate model identity with resident identity.
- Do not load stale claims without explicit classification.

## Completion Standard

WP-4058 is complete only when a fresh implementation can resume the same resident or officeholder from a validated continuity package; loaded material remains source-lined and privacy-scoped; stale and rejected claims remain explicit; the prior implementation stays available as fallback; and final acceptance remains with established authority.