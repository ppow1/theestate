# Office Parking Lot Control Surface

WP-0513 turns the Office Parking Lot and Roadmap panels into local planning control surfaces backed by canonical Estate handlers.

## Canonical handlers

- `parking_lot.control` calls `estate.core.office_parking_lot_controls.parking_action` and writes `operations/boards/parking_lot.md` plus runtime audit/undo artifacts.
- `roadmap.control` calls `estate.core.office_parking_lot_controls.roadmap_action` and writes `operations/boards/roadmap.md` plus runtime audit/undo artifacts.
- `planning.undo_last_local_change` calls `estate.core.office_parking_lot_controls.planning_undo` and restores the most recent safe local planning change.
- `planning.filter` calls `estate.core.office_parking_lot_controls.filter_items` and returns visible items without mutating canonical artifacts.
- Parking Lot promotion calls `estate.core.operations_control_runtime.OperationsControlRuntime.record_decision` for an existing governed operations-control destination; it does not create a new queue.

## Control contracts

| Control | Action ID | Required inputs | Canonical handler | Artifacts read/written | Runtime state | Confirmation | Results |
|---|---|---|---|---|---|---|---|
| Create item | `parking_lot.control` / `roadmap.control` | `planning_action=create`; item fields | `parking_action` / `roadmap_action` | Reads/writes board markdown; writes audit and undo | Board row appended; Office refresh requested | None | completed/failed |
| Edit item | same | `planning_action=edit`, `item_id` | same | Reads/writes board markdown; writes audit and undo | Row fields updated | None | completed/blocked/failed |
| Move up/down | same | `planning_action=move_up|move_down`, `item_id` | same | Reads/writes board markdown; writes audit and undo | Visible/canonical order changes | None | completed/blocked at boundary/failed |
| Drag/reorder | same | `planning_action=reorder`, complete `order` list | same | Reads/writes board markdown; writes audit and undo | Canonical order replaces previous order | Complete-order validation | completed/blocked/failed |
| Change priority | `parking_lot.control` | `planning_action=set_priority`, `item_id`, `priority` | `parking_action` | Parking Lot markdown; audit and undo | Priority persists | Priority enum validation | completed/blocked/failed |
| Roadmap priority/status | `roadmap.control` | `planning_action=set_priority`, `item_id`, `priority` or `status` | `roadmap_action` | Roadmap markdown; audit and undo | Status/priority planning marker persists | None | completed/blocked/failed |
| Accept/reject/archive/restore | `parking_lot.control` | `planning_action=accept|reject|archive|restore`, `item_id` | `parking_action` | Parking Lot markdown; audit and undo | Status persists | None | completed/blocked/failed |
| Promote item | `parking_lot.control` | `planning_action=promote`, `item_id`, governed `destination` | `parking_action` → `OperationsControlRuntime.record_decision` | Parking Lot markdown and operations-control decision artifacts | Status becomes Promoted; governed decision recorded | Destination allow-list | completed/blocked/failed |
| Assign owner | `parking_lot.control` edit | `item_id`, `owner` | `parking_action` | Parking Lot markdown; audit and undo | Originator/owner field persists | None | completed/blocked/failed |
| Add/update notes | edit controls | `item_id`, `notes` | planning adapter | Board markdown; audit and undo | Notes/future initiative persists | None | completed/blocked/failed |
| Open source artifact | rendered artifact links | source path | Office static/source link rendering | Reads source artifact | Browser opens source | N/A | source available/unavailable |
| Filter/search | `planning.filter` | `surface`; optional query/status/priority/owner | `filter_items` | Reads board markdown only | Browser visible list can change | None | completed/failed |
| Undo | `planning.undo_last_local_change` | none | `planning_undo` | Reads undo; writes board markdown and audit | Last safe change restored | Only last local change is eligible | completed/blocked/failed |

## UI behavior

The Office renders item-adjacent controls for Parking Lot and Roadmap rows, including move, edit, priority/status, Parking Lot lifecycle, and promotion buttons. The existing Office action runtime blocks duplicate submissions per action, supports Enter-submitted single-action forms through standard button/form behavior, keeps Shift+Enter available in textareas, reports failed writes in the action result panel, and requests targeted refresh after completed state-changing actions.

Selected tab, filters, and browser layout preferences remain local browser state and survive targeted refresh because the Office runtime preserves active tab preferences and returns fresh payload metadata without replacing the whole page.
