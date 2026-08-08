# Living Diagnostics developer workflow

Canonical knowledge is stored in `checkpoints.json`; it is explicitly `VALIDATED` or
`REVALIDATION_REQUIRED`. Developer text is retained separately in reconciliation
output as `CANDIDATE`/`PROPOSED`, with `canonical_promotion: false`. Rejected packet
metadata is listed under `rejected_packets` and never covers a change.

1. Make the authorized code change and run focused tests.
2. Describe intent in a small request JSON, then emit the canonical packet:
   `python tools/estate_diagnostics.py impact create --input request.json --output diagnostics/impact/my-change.json`.
3. Run deterministic reconciliation with the accepted baseline and packet.
4. Inspect `affected_checkpoints`, then run `candidates --reconciliation result.json`.
5. Publish code and packet together. A later local-AI/validation process reviews,
   but cannot promote, the candidate. Generate its bounded input with
   `local-ai-delta --reconciliation result.json --output delta.json`.

Minimal valid request (the command captures hashes, Git blobs, revision, and dirty
or untracked state rather than trusting the author):

```json
{"packet_id":"WP-EXAMPLE","component":"living-diagnostics","intended_behavior":"Keep ingestion deterministic","changed_files":["src/estate/diagnostics/impact.py"],"dependencies":["git"],"invariants":["candidate is not canonical"],"failure_seams":["invalid provenance"],"probes":["pytest -q tests/test_living_diagnostics_ingestion.py"],"evidence":["tests/test_living_diagnostics_ingestion.py"],"boundaries":["reconcile after packet creation"],"affected_checkpoints":["LD-DEVELOPER-INGESTION"],"proposed_knowledge":[{"state":"CANDIDATE","text":"Check rejected_packets before review."}],"confidence":"HIGH","source":{"kind":"human","actor":"developer"}}
```

Invalid example: change `confidence` to `CERTAIN`, omit `source.actor`, or use a
path such as `../secret`. Creation exits 2. If malformed files are supplied to
reconciliation they appear in `rejected_packets`; the changed artifact remains in
`uncovered_changes` with `CHANGE_WITHOUT_DIAGNOSTIC_IMPACT_METADATA`.
