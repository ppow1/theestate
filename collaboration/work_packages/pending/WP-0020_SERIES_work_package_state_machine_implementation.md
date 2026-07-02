# SERIES TASK WP-0020 — Work Package State Machine Implementation

## Status
Blocked — pending Chief Architect approval of ADR-0003.

## Mission
After Chief Architect approval, implement the approved Estate work package state machine as a structural model for registry-backed work packages.

## Dependency
Do not start this package until `Architecture/ADR/ADR-0003-Work-Package-State-Machine-Proposal.md` is reviewed and implementation is explicitly authorized by the Chief Architect or Steward.

## Expected Scope After Approval
- Add the approved state vocabulary to the chosen work package registry or documentation location.
- Add structural validation that rejects unknown states and unauthorized transition records if a registry schema exists.
- Preserve the distinction between `codex_done`, `ca_verified`, `merge_authorized`, `merged`, and `operationally_validated`.
- Update operator or collaboration documentation to explain how state changes are recorded.
- Add tests or validation fixtures for allowed and disallowed transitions.

## Out of Scope
- Autonomous scheduling.
- Automatic merging.
- Automatic state transitions without explicit recorded authority.
- Redefining Estate lifecycle states beyond work package status.

## Completion Criteria
- Approved state vocabulary is documented in the implementation location.
- Transition authority rules are represented in the chosen schema or validation layer.
- Tests or structural checks cover representative valid and invalid transitions.
- A completion marker is created with ready-for-CA-review status.
