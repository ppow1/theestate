# WP-4213 Runtime-Canon Recovery Production Activation Validation

## Repository archive search

The repository was searched by filename and by available normalized-bundle manifests. One real archive was available:

- `ingestion/conversations/Chief_Architect_Renewal_Verification_2026-07-19.mhtml`, SHA-256 `3107d96b21f2cd16429fadfc2c54a76cefe088761fc15a2299ee9de7e9e285b` (repository-safe filename equivalent of **Chief Architect Renewal Verification.mhtml**).

The following named archives and equivalent normalized bundles were not present; no counts are fabricated for them:

- `127-130 #1.mhtml`
- `127-130 #1(1).mhtml`
- `Estate work-package continuation2.mhtml`

Search scope was the complete connected repository (`find . -type f` plus case-insensitive name matching for each target and normalized manifests). No workstation path was assumed.

## Real archive production run

Run identifier: `6d3ab4d515de6382`.

- archives processed: 1
- messages parsed: 23
- assistant messages scanned: 4
- substantive candidates: 0
- complete / substantially complete / partial / truncated / false positive: 0 / 0 / 0 / 0 / 0
- matched / unmatched: 0 / 0
- duplicate / competing groups: 0 / 0
- supporting documents staged: 0
- candidate review blocks: 0
- pending-index review conditions: 16 affected duplicate identifiers; global fatal diagnostics: 0

The absence of candidates is the pipeline result for this available renewal-verification archive, not a claim about the three unavailable archives.

## Deterministic rerun

Two clean output roots produced the same run identifier and byte-identical required reports after output-root paths were removed from artifact content. Input and pending-definition hashes participate in run identity; stable ordering and the declared stable generation timestamp make reruns reproducible.

## Safety and authority

Candidate extraction scans every assistant message independently of assignment reconstruction. Pending definitions are read-only authority. Supporting documents can only be staged as `canonical: false`; the manifest prohibits automatic promotion, and the pipeline never writes a proposed destination or any file below the pending root.

## Tests

- WP-4208 through WP-4213 focused integration: 43 passed.
- Broad repository suite: 1,586 passed and 4 unrelated pre-existing failures. The failures are three OpenWebUI Campaign 02 expectation mismatches (`placeholder`/`uncommissioned` states and absent `voice.alfred`) and the historical reflection handoff's expected final sentence. None exercises conversation ingestion or runtime-canon recovery.
