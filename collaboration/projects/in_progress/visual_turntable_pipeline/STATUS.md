# Status

## Completed

- Confirmed Qwen Image Edit can generate useful multi-angle resident candidates.
- Established the eight target angle names and degree convention.
- Tested direct, long-prompt, sequential, relative-rotation, and candidate-pool approaches.
- Identified parallel absolute-angle generation as the strongest current method.
- Generated two timestamped 24-image pools with three candidates per angle.
- Confirmed usable candidates exist for all eight target viewpoints.
- Built and tested BiRefNet background removal.
- Verified a true transparent RGBA PNG using checkerboard display.
- Preserved the complete project package in the Estate repository under `collaboration/projects/in_progress/visual_turntable_pipeline/`.
- Committed the project as commit `d2e11d56` with message `Preserve visual turntable pipeline as in-progress project`.
- Published branch `feature/evelyn-multimodel-tpose-pipeline` to GitHub and established upstream tracking.
- Clarified that transparent RGBA PNGs are to be the primary reusable runtime assets for 360 capture ingestion, while opaque source renders remain preserved as provenance.
- Confirmed the first canon run is a pipeline-health test using `TEMP_EVELYN_CANON_TEST_FIXTURE`, not acceptance of final Evelyn appearance.

## Current best artifacts

- `workflows/TPose_24_Absolute_ViewPool_Timestamped_v1.1_workflow.json`
- `workflows/BiRefNet_Transparent_Background_v1.0_workflow.json`
- `samples/source_archives/2026-07-24_HH-43-27.zip`
- `samples/contact_sheets/2026-07-24_HH-43-27.jpg`
- `samples/contact_sheets/2026-07-24_HH-50-46.jpg`
- `samples/transparency_tests/checkerboard_verification.png`

## Current execution point

The next action is candidate selection, not additional workflow experimentation:

1. Select the strongest single image for each required angle.
2. Preserve those eight opaque selections as immutable source/provenance assets.
3. Run all eight selections through BiRefNet.
4. Verify genuine RGBA transparency and edge integrity.
5. Hand the eight transparent PNGs to the governed WP-4128 360 capture ingestion and validation pipeline.
6. Stop at review state unless the Steward later issues explicit acceptance.

## Known issue

The timestamp workflow produced folder names containing the literal text `HH` rather than substituting the hour. This is cosmetic and should be corrected before formal adoption.

## Not yet completed

- Select and record the strongest single image for each of the eight angles.
- Run all eight selected images through background removal.
- Verify alpha-channel quality, including hair, fingers, footwear, halos, and residual background.
- Create the governed original/transparent asset pairing and provenance records.
- Validate the resulting eight transparent images through the Estate WP-4128 visual canon.
- Record validation pass/failure diagnostics and Steward review status.
- Decide whether the workflow becomes a formal Estate capability.
