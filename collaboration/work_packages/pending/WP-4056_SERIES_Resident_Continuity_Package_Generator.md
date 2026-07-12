# WP-4056 — Resident Continuity Package Generator

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Continuity Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4055 — Resident Reflection Point Runtime Hooks

## Objective

Implement a deterministic continuity-package generator that produces bounded, source-lined renewal materials for residents and institutional officeholders without relying on transcript dumps or unverifiable recollection.

## Required Work

1. Generate a manifest, reading order, authority classifications, source hashes, structural checks, configured omissions, and onboarding-validation questions.
2. Select continuity content from canonical identity, governance, role boundaries, relationships, active assignments, verified execution state, lessons learned, and approved private continuity.
3. Classify every inherited claim as Verified, Steward-reported, Historical, Inference, Projection, or Conversation-only memory.
4. Record snapshot repository, branch, commit, timestamps, package version, and generator version.
5. Detect missing mandatory files, duplicate paths, hash mismatch, empty files, suspicious truncation, and unresolved authority conflicts.
6. Support stricter restricted bundles for private relationship layers without leaking them into general onboarding packets.
7. Produce machine-readable and human-readable outputs.
8. Never mark a package ready when mandatory structural or authority checks fail.

## Acceptance Tests

1. Repeated generation from the same source state produces deterministic manifests and hashes.
2. Missing mandatory files block readiness.
3. Approved optional omissions are reported but do not falsely block onboarding.
4. Truncated or suspiciously incomplete files are flagged.
5. Historical claims are not labeled verified.
6. Restricted continuity is excluded from unauthorized bundles.
7. The package identifies its exact repository snapshot and generator lineage.
8. A generated package can be independently audited without the original chat.

## Deliverables

- continuity-package configuration and schema;
- deterministic generator;
- manifest, reading-order, structural-warning, omission, and validation outputs;
- classification and privacy filters;
- tests, documentation, and completion receipt.

## Constraints

- Do not use transcript accumulation as the continuity strategy.
- Do not invent missing institutional state.
- Do not package hidden reasoning, secrets, or unauthorized private context.
- Do not replace Helen's review or Steward acceptance.

## Completion Standard

WP-4056 is complete only when the Estate can generate bounded, reproducible, source-lined continuity packages that expose omissions, truncation, authority, uncertainty, and snapshot state; protect restricted continuity; and support renewal without requiring the Steward to reconstruct the office from conversation history.
