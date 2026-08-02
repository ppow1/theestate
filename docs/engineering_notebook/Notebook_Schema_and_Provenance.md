# Schema and Provenance Guide

Schemas:

- `schemas/notebook/engineering_notebook_state_v1.schema.json`
- `schemas/notebook/notebook_update_proposal_v1.schema.json`
- `schemas/notebook/notebook_verification_receipt_v1.schema.json`
- `schemas/notebook/notebook_handoff_v1.schema.json`

All are closed objects with `additionalProperties: false` at their governed
boundaries. References are repository-relative safe paths; absolute paths,
parent traversal, placeholders, and secret-like values are rejected by runtime
validation. Digests are SHA-256 identities of source records or verified state.

Provenance is mandatory for material claims. `worker_proposed` is not evidence
until the harness observes it. Validator and repository facts outrank narrative.
The Markdown renderer redacts secret-like patterns and explicitly labels the
notebook as subordinate to authoritative records.
