# PROD-PTM-001B — Read-only adapter contract fixtures

Status: Pending Gate PTM-PROD-G1  
Owner: Chief Architect  
Execution lane: Codex  
Campaign: PTM-PROD-01  
Depends on: PROD-PTM-001A

## Objective

Build deterministic, non-production fixtures and integration tests that prove
the frozen adapter boundary is safe against the real repository source shapes.

## Scope and evidence

- Create sanitized fixtures for the bounded Parking Lot/work-package, Dispatch,
  validation, and acceptance source slices.
- Cover absent files, partial records, conflicting status, invalid hashes,
  staleness, path escape, size bounds, and private-field redaction.
- Assert zero writes and no source-state normalization in place.
- Register the targeted test command in the repository's existing testing
  conventions and document exact expected outcomes.
- Produce a completion receipt and Gate G2 evidence references.

## Boundaries

Fixtures do not become a registry or authoritative dataset. Do not change the
Gate G1 interface, production sources, governance semantics, or acceptance
state. Stop/replan if a fixture reveals a frozen-contract defect.

## Delivery

Open a PR for Chief Architect review and merge before PROD-PTM-001C at Gate G2.
