# WP-4024 Resident Context Assembly Contract

This staged contract defines an uninstalled resident context assembly pipeline for WP-4031 integration.

## Inputs

- `resident_id` and the current task/blocker statement.
- Existing Estate registries, especially `data/registry/residents.json` and `data/registry/personnel.json`.
- Caller-provided existing-source snapshots for communications, approved continuity artifacts, knowledge-index hits, and citations.

## Guarantees

- Privacy and classification checks run before prompt assembly.
- The assembler does not persist memory and does not create a second memory store.
- Every included section has a source citation object.
- Empty, unavailable, unrelated, cross-resident, unapproved, over-clearance, or prohibited private sources are omitted with explicit reasons.
- Context budgeting is deterministic and never partially truncates a source silently.
- Stale source warnings are explicit metadata on included sections.

## Install handoff

WP-4031 should move the staged module into the resident runtime, replace caller-provided snapshots with live retrieval adapters, and wire the packet into resident chat/task prompt construction after preserving the same filtering order.
