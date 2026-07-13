# WP-4130 — Measurement Variant Matrix

**Series:** Visual Estate Initiative — Campaign 03

**Status:** Pending

## Objective

Create a resident-specific measurement comparison system that allows the Steward to review nearby physical variants without turning one resident's specification into a universal template.

## Dependencies

- WP-4109 — Canonical Physical Specification Standard
- WP-4111 — Height, Proportion, and Scale Reference System
- WP-4112 — Measurement Variant Review Workflow
- WP-4128 — 360° Capture Standard
- WP-4129 — Vertical Comparison Sheet Standard

## Required Work

1. Define a machine-readable measurement matrix schema for each resident.
2. Support at least three comparison variants when refinement is required:
   - lower variant
   - proposed/candidate variant
   - upper variant
3. Permit the Steward to vary top, middle, and bottom measurements independently when the character design requires it.
4. Require a narrative reason for each changed dimension.
5. Preserve all fixed variables during comparison:
   - face
   - height
   - age presentation
   - pose
   - camera
   - lighting
   - wardrobe
   - footwear unless footwear is the variable under test
6. Record whether each difference is visually discernible at normal review size.
7. Require regeneration when differences cannot be distinguished without opening separate windows or relying on memory.
8. Store selected, rejected, and superseded variants with provenance.
9. Support narrow-tolerance residents and broad-tolerance residents.
10. Prevent accidental propagation of one resident's measurements into another resident's Visual Bible.

## Evelyn Calibration Example

Evelyn's narrow review range may include:

- 33B–20–30
- 33B–21–31
- 33B–22–32

Her likely canonical target remains 33B–21–31 unless the Steward changes it. This is an example of a tightly constrained resident and must not be treated as the Estate-wide default.

## Deliverables

- Measurement matrix schema
- Resident variant manifest template
- Comparison selection record
- Rejection reason record
- Visual discernibility checklist
- Example populated Evelyn matrix

## Acceptance Criteria

- Three nearby variants can be compared in one vertically aligned review artifact.
- A reviewer can identify the intended differences without changing windows.
- Variant ranges are resident-specific.
- The selected canonical variant and rationale are recorded.
- Rejected variants remain traceable but cannot be mistaken for canonical data.
