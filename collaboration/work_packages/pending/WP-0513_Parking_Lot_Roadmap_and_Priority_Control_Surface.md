# WP-0513 - Parking Lot, Roadmap, and Priority Control Surface

Status: Proposed
Priority: High
Owner: Chief Architect #5
Classification: Estate Internal

## Mission

Turn the Parking Lot and Roadmap pages into real planning control surfaces. Every actionable element must invoke a canonical Estate handler, update the canonical planning artifacts, and refresh the Office immediately.

## Required Controls

- Create item
- Edit item
- Move up
- Move down
- Drag/reorder when practical
- Change priority
- Accept item
- Reject/archive item
- Restore archived item
- Promote item into an existing governed destination
- Assign owner
- Add/update notes
- Open source artifact
- Filter
- Search
- Safe undo of the most recent local order/status change

## Control Contracts

Each control must define:

- action ID;
- required inputs;
- canonical handler;
- artifacts read/written;
- runtime state changed;
- confirmation requirements;
- completed, blocked, and failed results.

Promotion must not create a new queue or bypass existing planning, assignment, or work-package authority. It must call the canonical destination runtime.

## UI Requirements

- Controls must be adjacent to the item they affect.
- Move Up/Down must update visible order immediately.
- Primary actions must be keyboard accessible.
- Enter submits focused single-action forms; Shift+Enter remains available for multiline notes.
- Duplicate submission must be blocked.
- Failed writes must leave the prior visible state intact and show diagnostics.
- Selected item and filters should survive targeted refresh.

## Expected Implementation

Inspect and reuse existing parking-lot, roadmap, planning, assignment, and work-package modules. Modify the Office command surface and `steward_command_center.py` as required. Add a focused runtime adapter only if no canonical callable seam exists.

Create:

```text
tests/test_office_parking_lot_controls.py
docs/integration/office_parking_lot_control_surface.md
collaboration/work_packages/completions/WP-0513_codex_done.json
```

Register a WP-0513 validation recipe.

## Tests

Tests must prove:

- create/edit persists;
- move up/down changes canonical order and rendered order;
- reorder survives reload;
- priority and owner changes persist;
- accept/archive/restore update real state;
- promote calls the canonical destination handler exactly once;
- invalid promotion remains blocked;
- undo restores the prior safe local state;
- search/filter return correct visible items;
- no decorative or permanently disabled controls are counted as delivered.

## Acceptance Criteria

1. The Parking Lot is fully operable from the Office.
2. Roadmap ordering and prioritization are serviceable.
3. Promotion uses existing governed pathways.
4. Every control changes real state or evidence.
5. Browser state refreshes immediately and persists after reload.
6. Focused tests and WP-0513 validation pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0513_Parking_Lot_Roadmap_and_Priority_Control_Surface.md and do exactly what it says.
```
