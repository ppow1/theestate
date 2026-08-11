# PL-0045 — Operator Deck Quadrant Snip Selection

Status: Captured
Priority: Medium
Category: Operator UX / Stream Deck / Screenshot Workflow
Originator: Pat / Steward
Date Captured: 2026-08-11
Target Milestone: After current Codex Desk / Grace parallelism work is stabilized

## Idea

Add a `SNIP` control to the Operator Deck, placed beneath the existing `CLEAR` control, that reuses the existing 4x4 monitor-quadrant button grid as a rectangle-selection surface for screenshots.

The goal is to make common monitor-region screenshots deterministic and one-button-driven without requiring mouse drag selection.

This should extend the existing Operator Deck monitor/quadrant model rather than introduce a new monitor geometry subsystem.

## Proposed Interaction

The interaction is a two-stage toggle:

1. Press `SNIP` to arm screenshot-selection mode.
2. Press one or more existing quadrant buttons on the left-side Operator Deck monitor grid.
3. Press `SNIP` again to capture the resulting rectangular region and place the image on the Windows clipboard.

The screenshot must remain within a single physical monitor because the intended workflow should not span monitor boundaries.

## Selection Semantics

The selected quadrant buttons define the smallest axis-aligned rectangle containing all selected quadrants on that monitor.

Examples for one monitor's four quadrant buttons:

- one quadrant selected -> capture only that quarter of the monitor;
- top-left + top-right -> capture the top half;
- bottom-left + bottom-right -> capture the bottom half;
- top-left + bottom-left -> capture the left half;
- top-right + bottom-right -> capture the right half;
- all four quadrants -> capture the whole monitor;
- diagonal pair (top-left + bottom-right OR top-right + bottom-left) -> the bounding rectangle is the entire monitor;
- any other multi-button combination -> capture the smallest rectangular region whose corners encompass the selected quadrants.

Selection must remain on one monitor. If buttons from more than one monitor are selected, the implementation should reject the selection or require the operator to clear/re-arm rather than silently create a cross-monitor capture.

## Operator Deck Integration

Preferred placement:

- `SNIP` button directly beneath the existing `CLEAR` button on the Operator Deck page, if the current geometry still has a suitable free slot.

Reuse the current monitor/quadrant controls as the selection surface. Do not duplicate the 4x4 grid or create another monitor map.

While SNIP mode is armed, the existing quadrant actions should temporarily mean `add/remove this quadrant from snip selection` rather than execute their normal window-placement action.

Outside SNIP mode, all existing quadrant controls must retain their current behavior unchanged.

## State / Feedback

When SNIP mode is armed, provide lightweight visual state if the existing Stream Deck plugin can absorb it safely:

- SNIP button visibly armed;
- selected quadrants visibly distinguishable;
- second SNIP press performs capture and returns the deck to normal mode;
- CLEAR while SNIP mode is armed may be considered as a natural way to clear the current screenshot selection, but only if that can be added without changing CLEAR's normal behavior outside SNIP mode.

Do not broaden this into a new general selection-state framework if the existing Operator Deck armed-selection machinery can absorb it.

## Capture Contract

When the second SNIP press confirms the selection:

1. Resolve the selected physical monitor and quadrants through the existing Operator Deck monitor topology.
2. Compute the bounding rectangle inside that monitor only.
3. Capture exactly that rectangular screen region.
4. Place the resulting bitmap/image directly onto the Windows clipboard.
5. Return SNIP/selection state to idle.

No file save is required for the initial implementation unless an existing screenshot utility already persists captures as a side effect.

The feature should complement, not replace, Pat's existing mouse-button screenshot workflow.

## Guardrails

- Do not allow a screenshot rectangle to cross physical monitor boundaries.
- Do not change normal Operator Deck quadrant/window-placement behavior when SNIP is not armed.
- Do not rewrite monitor topology or create another geometry registry.
- Do not interfere with UNDO / CLEAR / SELECT / CODEX DESK / Voice / navigation controls.
- Prefer extending the existing Operator Deck armed-selection and monitor-layout code.
- Do not scope-creep into OCR, annotation, image editing, file organization, or automatic upload/share behavior.

## Acceptance Examples

Given a monitor represented by four buttons:

```text
TL | TR
---+---
BL | BR
```

Expected:

- SNIP -> TL -> SNIP = top-left quarter to clipboard.
- SNIP -> TL -> TR -> SNIP = top half to clipboard.
- SNIP -> TL -> BL -> SNIP = left half to clipboard.
- SNIP -> TL -> BR -> SNIP = full monitor to clipboard.
- SNIP -> TL -> TR -> BL -> BR -> SNIP = full monitor to clipboard.

After capture, normal Operator Deck behavior must be restored automatically.

## Promotion Condition

Promote after current Codex Desk acceptance and Grace/parallel execution work are stable enough to return to Operator Deck ergonomics.

When promoted, first inspect the existing Operator Deck selection/armed-state implementation, monitor topology, and any current Windows screenshot helpers. Extend existing mechanisms before adding anything new.

## Explicit Non-Action

This item is parked.

Do not interrupt current CODEX DESK button acceptance, Grace integration, or parallelism work to implement it now.
