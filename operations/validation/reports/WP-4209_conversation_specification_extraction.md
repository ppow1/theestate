# WP-4209 Validation Report

## Result

PASS — the extraction engine creates deterministic, non-canonical staging bundles
on complete coverage and review-blocked reports when coverage or safety validation
fails.

## Acceptance coverage

- Reuses the WP-4208 content-addressed MHTML ingestion entry point.
- Preserves structured message Markdown rather than extracting only normalized text.
- Classifies startup/continuation seeds, Steward instructions, automatic go messages,
  runtime-canons, completion/handoffs, and unrelated messages.
- Tests bounded ranges, multi-WP extraction, missing and duplicate WPs, malformed
  headings, collapsed formatting, ambiguous destinations, pending-definition
  overwrite attempts, truncated responses, tampering, and the checked-in realistic
  MHTML archive.
- Produces one staging file per uniquely mapped expected WP with complete provenance;
  it does not write to proposed repository destinations.

## Commands and results (2026-07-19)

`PYTHONPATH=src python -m pytest tests/test_conversation_archive_ingestion.py tests/test_conversation_specification_extraction.py -q`

Result: `12 passed in 2.40s`.

