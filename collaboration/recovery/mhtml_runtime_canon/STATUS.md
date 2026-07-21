# Estate MHTML Recovery Implementation Status — V2

## Complete

1. Proven dependency-free MHTML message-boundary repair.
2. Proven all-representation MIME scanning and exact deduplication design.
3. Proven 102-message / 25-assistant real-archive baseline.
4. Implemented multi-candidate runtime-canon segmentation design.
5. Implemented separate-line title plus canon-marker recognition.
6. Implemented matching explicit-closure boundaries.
7. Preserved quoted/startup-seed rejection.
8. Added compatibility `detect()` wrapper while the pipeline migrates to `detect_all()`.
9. Added unit-test changes for multiline headings, multiple canons in one message, explicit closure, and quoted-seed rejection.

## Remaining before merge

1. Apply both patches to the source files on this branch.
2. Run focused repository tests.
3. Run the five real archives through the patched repository pipeline.
4. Verify deterministic output across two clean output roots.
5. Keep the PR in draft until the source and private-archive gates pass.

## Promotion boundary

Recovered supporting documents remain non-canonical review material. No automatic promotion is introduced.
