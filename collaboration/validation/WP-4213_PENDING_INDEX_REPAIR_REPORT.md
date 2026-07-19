# WP-4213 Pending Index Repair Report

## Before

The WP-4212 index reported 42 fatal conditions: 25 malformed filenames (24 PTM institutional identifiers plus `README.md`), one approved named work package whose heading used a historical form, and 16 duplicate numbered identifiers.

## Repairs

- `README.md` is excluded because it is directory documentation, not a definition.
- the 24 `*-PTM-*` identifiers are supported as approved historical named packages; their content and filenames are preserved.
- `WP-Operator-Deck-Prototype.md` is handled through an explicit approved exception; its institutional heading and filename are preserved.
- record-local malformed/mismatch conditions and duplicate identifiers now block only the affected identifier instead of the entire corpus.

## After

The production index contains 494 definitions and no global fatal diagnostic. Sixteen historically duplicated identifiers remain explicitly review-blocked because repository evidence does not authorize selecting or renaming one definition:

- `WP-0020`
- `WP-0079`
- `WP-0101`
- `WP-0103`
- `WP-0105`
- `WP-0116`
- `WP-0117`
- `WP-0118`
- `WP-0125`
- `WP-0136`
- `WP-0548`
- `WP-0627`
- `WP-0628`
- `WP-0629`
- `WP-0630`
- `WP-0697`

No pending definition was renamed, rewritten, overwritten, merged, or deleted.
