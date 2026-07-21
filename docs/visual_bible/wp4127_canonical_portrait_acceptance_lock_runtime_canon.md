# WP-4127 Canonical Portrait Acceptance and Lock Runtime Canon

## Authority and invariant
This canon governs Campaign 02 acceptance. Machine validation establishes **eligibility only**; no automation, default, silence, inferred role, or prior approval may grant Steward approval. Production currently has no accepted canonical portrait set.

## Evidence and lifecycle
Acceptance evidence binds resident identity, asset ID and bytes, metadata/catalog revision, prompt/model/seed provenance, Visual Bible revision, crop/angle, source and derivative lineage, consistency report, and access classification. Each check is `pass` with an evidence reference. States are: **candidate** (submitted), **preferred** (review lead choice), **provisional** (complete proposal awaiting decision), **canonical** (explicitly Steward-approved and locked), **rejected** (declined), **superseded** (replaced historical canon), and **retired** (withdrawn without replacement). Rejected, superseded, and retired records are immutable inactive history.

A canonical resident lock contains exactly one asset for each required category: hero, professional office, full-body standing, profile, rear, front three-quarter, rear three-quarter, expression sheet, headshot set, and thumbnail set. Additional categories must be explicitly named in the lock. All required identity, metadata, provenance, hash, crop, derivative, consistency, and access checks pass; artifacts and blocking findings are absent. Tolerated limitations must be non-blocking, scoped, justified, owned, and given a review/expiry date.

## Review and selection
Build the consolidated gallery from catalog candidates, show matched comparisons and differences, complete the human checklist, and retain Steward notes. Selection may propose preferred/provisional state. Only a human Steward supplies an approve decision record with ID, identity, time, evidence references, and signature/checksum. Rejection moves bytes and metadata references into the access-equivalent rejection archive; it never deletes them.

## Lock and resolution
Canonical JSON is deterministically serialized and SHA-256 hashed. `lock_id` remains stable; every accepted change increments `lock_version`. Asset byte hashes, Visual Bible version, catalog/consistency references, decision, limitations, and downstream references are pinned. Consumers resolve only a single fully valid canonical lock and return unavailable—not a candidate—on missing bytes, hash drift, stale review, duplicate canon, or no canon. Downstream manifests pin lock ID, version, lock hash, category, and asset hash; mismatches are stale-canon failures.

## Supersession and rollback
Create a new candidate version without altering current canon, document reason/diff, rerun checks, obtain new explicit approval, then link old `superseded_by` and new `supersedes`. Preserve old bytes and locks. Rollback is not pointer mutation: a Steward decision creates a new version referencing the historical version, revalidates current bytes/access/consistency, records reason, and preserves all history. Missing historical bytes block rollback.

## Archives, diagnostics, and campaign evidence
Rejection entries record reason, decision, source state, archive path/hash, access, and candidate/gallery references. Supersession entries record bidirectional lock/asset links; rollback records use the governed schema. Diagnostics are stable `PCL-*` codes for schema/state/identity, coverage/uniqueness, evidence, Steward authority, hashes/files, stale/downstream locks, blocking findings, and resolution ambiguity.

Campaign completion evidence comprises the predecessor traceability matrix, coverage and unresolved-data reports, local-generation readiness, validation results, and Campaign 02 completion report. Infrastructure can be complete while visual production remains incomplete. Campaign production completes only after generated assets, all checks, consolidated review, and explicit Steward acceptance exist for every required resident/category.

## Tests, anti-patterns, completion criteria
Tests cover hash tampering, missing files, stale locks, duplicate/missing categories, incomplete evidence/approval, noncanonical resolution, exact-one resolution, supersession/rollback records, schemas, reports, and CLI behavior. Anti-patterns: auto-approval; placeholder assets presented as canon; filenames as identity; mutable locks; silent replacement; latest-file fallback; candidates returned as canon; fabricated provenance; deleting rejection/history; access downgrades; treating validator success as human acceptance; claiming campaign production complete from infrastructure alone.

WP-4127 implementation is complete when schemas, templates, validator/resolver, machine records, archives, traceability/coverage/readiness/unresolved/completion reports, fixtures, tests, documentation, completion receipt, and applicable validation pass. Actual portrait acceptance remains separately pending until genuine evidence and Steward decisions exist.
