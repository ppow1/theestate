# PL-0035 — Visual Canon Candidate Selection Utility

Status: Captured
Priority: Normal
Category: Visual Canon Production / Operator Tooling
Originator: ChatGPT worker, confirmed by Pat / Steward
Date Captured: 2026-07-24
Target Milestone: After the manual eight-view selection and BiRefNet canon-validation workflow has been completed and repeated

## Idea

Create a small operator-facing selection utility for Estate visual-canon production. The utility would present generated candidate pools or contact sheets, allow the Steward or authorized reviewer to select one image for each required WP-4128 angle, and then produce the governed handoff artifacts automatically.

Potential behavior includes:

- select one primary candidate for each of the eight required viewpoints;
- optionally record runner-up candidates;
- copy the selected opaque source images into the governed selection directory;
- assign deterministic canonical filenames;
- generate `selection_manifest.json` with source run, source image, angle, and provenance;
- preserve the original candidate pools unchanged;
- hand the completed selection set to the existing BiRefNet transparency stage.

## Why It Is Parked

The current assignment is to choose and process the first eight-image canon-validation set. Building an interactive selection utility now would expand the active scope and delay completion of the proven manual workflow. The Estate should complete the current manual process before deciding whether repeated use justifies automation.

## Promotion Condition

Promote this idea only when:

1. The manual candidate-selection, naming, manifest, transparency, and WP-4128 validation process has completed successfully.
2. The same manual selection pattern is required for additional residents or repeated visual-canon runs.
3. The repeated operator burden and error risk are documented.
4. The Steward intentionally authorizes a tooling work package or bounded implementation task.

## Explicit Non-Action

Do not design, implement, prototype, or integrate the selection utility during the current eight-image preselection and BiRefNet batch work. Continue using direct visual review and the explicit selection manifest already established for the active run.

## Related Evidence

- `AI_COMMUNICATION_HINTS.md`
- `operations/boards/parking_lot.md`
- `collaboration/projects/in_progress/visual_turntable_pipeline/STATUS.md`
- `collaboration/projects/in_progress/visual_turntable_pipeline/canon_validation/selection_manifest.example.json`
- `docs/visual_bible/wp4128_360_capture_standard_runtime_canon.md`
