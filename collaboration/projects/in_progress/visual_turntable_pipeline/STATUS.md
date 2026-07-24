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

## Current best artifacts

- `workflows/TPose_24_Absolute_ViewPool_Timestamped_v1.1_workflow.json`
- `workflows/BiRefNet_Transparent_Background_v1.0_workflow.json`
- `samples/source_archives/2026-07-24_HH-43-27.zip`
- `samples/contact_sheets/2026-07-24_HH-43-27.jpg`
- `samples/contact_sheets/2026-07-24_HH-50-46.jpg`
- `samples/transparency_tests/checkerboard_verification.png`

## Known issue

The timestamp workflow produced folder names containing the literal text `HH` rather than substituting the hour. This is cosmetic and should be corrected before formal adoption.

## Not yet completed

- Select and record the strongest single image for each of the eight angles.
- Run all eight selected images through background removal.
- Validate the resulting eight transparent images through the Estate visual canon.
- Record canon acceptance, rejection, or required corrections.
- Decide whether the workflow becomes a formal Estate capability.
