# WP-4220 staged validation report

- **Date:** 2026-07-26
- **Result:** pass
- **Environment:** offline repository checkout; Python/pytest recorded by command evidence
- **Fixture inventory:** 20 valid records plus one malformed record; no live records used
- **Example queue SHA-256:** `2b99cf2222b058b39fe92624d30a3b64754d12ea8646dd67abccdcd82f496d36`
- **Example report SHA-256:** `1cbc5cb3117bf2724e0fa696c8d4aadb7fa2314dda250dba73cd1704a1ee7f4e`
- **Logical generation ID:** `737344cc015fef47477e`

Validated discovery ordering, stable correlation, duplicates, supersession, evidence states,
dependencies/cycles, lanes, touch points, merge risk, parallel safety, blockers, staleness,
malformed input, ordering/hash stability, required fields, provenance, CLI success/failure,
read-only input preservation, output-boundary rejection, and repeated-run equivalence.

Known staging limitations: v1 reads governed JSON snapshots rather than parsing every live
Markdown dialect; it has no network/hosting adapter, institutional acceptance integration,
persistent audit publisher, production freshness clock, scheduler, UI, or installation.
