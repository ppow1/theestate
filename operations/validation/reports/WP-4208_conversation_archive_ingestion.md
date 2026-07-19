# WP-4208 Conversation Archive Ingestion Validation

Date: 2026-07-19

## Result

PASS. The engine ingested the committed acceptance archive without changing it.
The content-addressed run `3107d96b21f2cd16` records the complete source SHA-256
`3107d96b21f2cd16c0ec4ba0ca1ec545dfaaa0964fca9b921be91452f716162f`
and extracted 23 ordered messages (19 user and 4 assistant).

## Provenance and governance controls

- Every message records the archive hash, source message identifier, DOM selector,
  MIME content location, sequence, role, and normalized-text hash.
- The source archive is read only; generated files use a separate content-addressed path.
- Verbatim extraction and derived review are separate artifacts.
- Derived interpretations and institutional candidates are deliberately empty and
  have `review_required` status. The bundle is explicitly non-canonical.
- Atomic replacement and a source-derived run identifier make repeated runs
  deterministic and idempotent.
- Validation checks source and message integrity, ordering, counts, roles, and contract version.

## Commands and evidence

```text
PYTHONPATH=src python -m pytest tests/test_conversation_archive_ingestion.py -q
3 passed

PYTHONPATH=src python -m estate.core.conversation_archive_ingestion ingestion/conversations/Chief_Architect_Renewal_Verification_2026-07-19.mhtml
{"message_count": 23, "output": "ingestion/conversations/derived/Chief_Architect_Renewal_Verification_2026-07-19/3107d96b21f2cd16", "run_id": "3107d96b21f2cd16", "valid": true}
```

The automated tests additionally demonstrate byte-for-byte source preservation,
stable re-ingestion output, non-canonical defaults, and rejection of tampered or
non-conversation input.
