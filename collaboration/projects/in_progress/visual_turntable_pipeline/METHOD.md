# Method

## Generation

1. Load the desired full-body source image into ComfyUI.
2. Run `TPose_24_Absolute_ViewPool_Timestamped_v1.1_workflow.json`.
3. The workflow requests eight absolute viewpoints three times, yielding 24 candidates.
4. Review candidates by target angle rather than assuming each labeled output is correct.
5. Select one best candidate for each target angle.

## Selection criteria

For each angle, prefer the candidate with:

- correct viewpoint;
- strongest identity match to the source;
- complete body visible from head to feet;
- upright portrait orientation;
- consistent hairstyle, dress, footwear, and body proportions;
- minimal anatomy distortion;
- neutral framing and camera height.

## Background removal

1. Load the selected candidate into `BiRefNet_Transparent_Background_v1.0_workflow.json`.
2. Use `birefnet.safetensors` from the ComfyUI background-removal model directory.
3. Run the workflow.
4. Open the saved PNG in an alpha-aware editor.
5. Confirm the area around the figure displays a checkerboard.
6. Inspect hair, white fabric, fingers, legs, and footwear for lost edges or halos.

## Canon validation

Use the resulting eight transparent images as a temporary non-canonical fixture. Run the established visual-canon process and record:

- accepted fields;
- rejected fields;
- missing required views;
- identity consistency findings;
- manifest or schema output;
- any required correction pass.
