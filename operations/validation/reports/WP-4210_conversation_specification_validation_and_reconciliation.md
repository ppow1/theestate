# WP-4210 Conversation Specification Validation and Reconciliation

Date: 2026-07-26  
Branch: `codex/seat1-wp4210-reconciliation`  
Campaign-authorized base: `8f527a872a76b14d3938242bf230a232fc3e8839`

## Result

PASS for the WP-4210 implementation and its end-to-end integration. The review
layer consumes WP-4209 bundles, integrity-checks candidate and provenance records,
compares candidates to exactly matched pending definitions, assesses substantive
runtime-canon areas, classifies duplicates, optionally stages compatible drafts,
validates destinations, reports range coverage, and emits deterministic,
content-addressed review bundles.

All generated results are non-canonical and review-required. No pending definition,
canonical destination, archive, WP-4208 bundle, or WP-4209 bundle is modified.
Material conflicts remain unresolved and cannot generate a merged draft.

## Test and validation evidence

- `PYTHONPATH=src python -m pytest tests/test_conversation_specification_reconciliation.py tests/test_conversation_specification_reconciliation_integration.py -q`
  — `14 passed in 0.42s`.
- `PYTHONPATH=src python -m pytest tests/test_conversation_specification_extraction.py -q`
  — `9 passed in 2.41s`.
- `python -m py_compile src/estate/core/conversation_specification_reconciliation.py`
  — passed.
- `git diff --check` — passed.
- `PYTHONPATH=src python -m pytest tests/test_conversation_archive_ingestion.py -q`
  — `12 passed, 1 failed in 0.28s`. The pre-existing WP-4208 charset-label
  assertion expects `windows-1252`, while the current authorized baseline reports
  Python's normalized alias `cp1252`. WP-4210 does not modify the prohibited
  dependency implementation; ingestion itself completed and the WP-4210 end-to-end
  ingestion/extraction/reconciliation test passed.

## Acceptance and boundaries

The tests cover a valid single candidate; absent and substantively empty areas;
unsupported completion claims; identical, compatible, materially conflicting, and
three-candidate duplicates; expected-range missing/unexpected/invalid members;
hash tampering; provenance mismatch; ambiguous, pending-overwrite, existing, and
cross-candidate destination collisions; deterministic reruns; review-only drafts;
conflict merge refusal; artifact tampering; and WP-4208 → WP-4209 → WP-4210 flow.

The implementation did not touch PR 437's MHTML/runtime-canon recovery boundary,
resident-restoration or Open WebUI files, Local Compute paths, Evelyn paths,
WP-4208/WP-4209 implementation files, pending definitions, or canonical artifacts.
No automatic promotion, approval, overwrite, or conflict winner selection exists.

## Infrastructure limitation

This execution used the campaign-authorized repository snapshot. Outbound GitHub
fetch was unavailable because the environment proxy returned HTTP 403. Final remote
synchronization remains required before integration. No integration or merge has
occurred.
