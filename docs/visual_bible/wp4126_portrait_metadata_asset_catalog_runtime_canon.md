# WP-4126 Portrait Metadata and Asset Catalog Runtime Canon

## Authority and scope

This document is the authoritative runtime contract for still resident portraits. The catalog at `data/visual_bibles/catalog/` is authoritative; folders and filenames are not. It extends, and never replaces, resident identity, Visual Bible, Steward review, canonical-lock, and WP-4125 consistency evidence. Group and motion assets have extension points but are out of scope. No example or reserved slot asserts that an approved production portrait exists.

## Identity and records

A resident identifier resolves to the Estate resident registry and is distinct from the mutable display name. A portrait asset ID is `pa_` plus the first 24 lowercase hexadecimal characters of SHA-256 over the UTF-8 sequence `v1 NUL resident_id NUL portrait_type NUL revision NUL file_sha256`. IDs therefore bind identity, semantic type, revision, and bytes—not paths or timestamps. Re-minting with identical inputs is idempotent; a different result for the same inputs is a collision and blocks admission. Imported and generated material use the same rule.

Every materialized asset records type, angle, crop/framing, expression, wardrobe, footwear, environment, camera and lighting; file path, media type, dimensions/size where applicable, and SHA-256; access, review, canonical and slot lifecycle; timestamps and revision; prompt and negative-prompt IDs and versions; and lineage. Generation receipts distinguish generated, imported, and derived work and preserve generator, model/version, model hash, workflow/hash, seed, sampler, scheduler, settings, adapters, and reference inputs where applicable. Unavailable historical values are explicitly `null` or `unknown`, never invented.

The schema supports hero, professional office, full-body, front/side/rear, three-quarter, expression sheet, headshot, thumbnail, black-and-white, photorealistic, comparison, and rejected/superseded records. Binary data is never embedded.

## Catalog and lookup

The Estate catalog is a versioned array plus append-only audit records. The runtime sorts by resident ID, portrait type, angle, canonical state, revision, and asset ID. It produces an Estate-wide ordered view, sorted per-resident views, and lookup keys `resident|portrait_type|angle|canonical_state`. Consumers must use these indexes and exact enum values, not directory scans or fuzzy filename matching. Access filtering happens before results leave a trust boundary; derivatives inherit the most restrictive source tier unless an evidenced declassification decision exists.

Only `materialized` records may claim a path or hash. `reserved` and `pending` are explicit planning slots and must claim neither. A missing materialized file is a blocking orphaned record; a scanned portrait file with no record is an orphaned file warning and cannot become canon. Hash mismatch blocks use. Records older than `stale_after_days` warn and require review; staleness never silently removes historical evidence.

## Review, canon, and lifecycle

Review state (`pending`, `in_review`, `approved`, `rejected`) is independent from canonical state (`candidate`, `canonical`, `superseded`, `retired`, `rejected`). Canon requires approved review plus a Steward decision ID, Steward identity, approval time, and evidence hash. Exactly one canonical record may occupy a resident/type/angle slot. A derivative does not inherit approval. Rejected, superseded, or retired assets are immutable historical records, not approved/current results.

Supersession creates a new revision and bidirectional lineage update; it never overwrites bytes. Rejection records reason and evidence. Retirement removes resolution eligibility while preserving the record. Rollback creates an audited transition to an eligible prior hash and never deletes intervening history. A replacement needs its own WP-4125 and Steward evidence. `source_asset_ids`, `derivative_asset_ids`, and `supersedes` must resolve and must not self-reference. Production tooling should additionally reject longer lineage cycles in transaction validation.

Audit events record reserve/create/review/approve/reject/supersede/retire/rollback/migrate, actor, UTC time, target, before/after record hashes, and reason. Provenance receipts are part of the asset record; external references are immutable IDs, paths and versions rather than pasted content.

## Validation and diagnostics

Validation is fail closed for schema/version errors, required fields, deterministic-ID mismatch/collision, invalid enum state, missing bytes, hash mismatch, undeclared duplicate bytes, broken/self lineage, conflicting canon, missing approval evidence, and invalid timestamps. Duplicate bytes require an explicit `duplicate_of` declaration and still remain separately reviewable. Warnings report stale metadata and orphaned files. Diagnostics are deterministically sorted and carry stable `PAC-*` codes and asset context. A failed catalog must not publish new indexes.

The CLI is:

```bash
PYTHONPATH=src python -m estate.portraits.catalog CATALOG.json --root . --output REPORT.json --scan-root PATH
```

`PAC-FILE-MISSING-001` means restore the exact bytes, retire/supersede the record, or correct an uncommitted record; never change the hash to fit unknown bytes. `PAC-HASH-001` means quarantine and investigate. `PAC-ID-COLLISION-001` or `PAC-ID-MISMATCH-001` stops ingestion. `PAC-ORPHAN-FILE-001` requires cataloging, quarantine, or deletion under retention policy. `PAC-STALE-001` requires metadata review, not automatic canon loss.

## Schema evolution and migration

Schema version is explicit. Additive optional fields may remain v1; enum, ID, required-field, or semantic changes require a new schema and migration. Migrations are deterministic, retain the source record hash, produce an audit `migrate` event, validate both input and output, and are reversible until accepted. Readers must reject unsupported major versions rather than guess.

For legacy images: inventory bytes read-only; resolve resident/type and access; calculate SHA-256; preserve unknown provenance; mint the deterministic ID; link prompts and sources only when evidenced; start as candidate/pending review; validate; then seek fresh Steward approval. Do not infer canon from `final`, `approved`, or a directory. Missing legacy files may only become reserved/pending slots with no path/hash, not materialized claims. v1 remains compatible with existing WP-4118–4125 sidecars through references; it does not rewrite them.

## Tests, anti-patterns, and completion

Unit tests cover stable ID minting, indexing, hashes, missing files, reserved slots, duplicate IDs/bytes, canonical uniqueness, approval, stale records, and lineage. Integration tests load the example, resolve real fixture bytes, build resident/Estate views, and execute the CLI. Fixtures explicitly say they are test evidence, not production approvals.

Forbidden patterns include filename-as-canon, mutable IDs, binary JSON, fabricated provenance, path-only integrity, approving derivatives by inheritance, publicizing restricted thumbnails, overwriting/deleting rejected history, silent migrations, circular lineage, nondeterministic set ordering, and catalog claims for absent files outside reserved/pending slots.

WP-4126 is complete only when schemas parse, validators and CLI pass, deterministic views reproduce, positive and adversarial tests pass, traceability is published, no production claim references nonexistent bytes, migration compatibility is documented, and unresolved limitations are reported. Steward visual approval and creation of final resident images remain outside this implementation.
