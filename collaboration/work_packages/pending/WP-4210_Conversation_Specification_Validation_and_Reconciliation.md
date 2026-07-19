# WP-4210 — Conversation Specification Validation and Reconciliation

Status: Pending
Owner: Institutional Ingestion Implementation Stream
Execution Target: Codex
Depends On: WP-4208, WP-4209, src/estate/core/conversation_archive_ingestion.py, src/estate/core/conversation_specification_extraction.py
Classification: Estate Internal

## Objective

Build the validation and reconciliation layer that reviews specification candidates produced from archived ChatGPT design conversations before any candidate is promoted into the Estate repository.

The system must compare each extracted candidate against its authoritative pending work-package definition, detect missing sections and incomplete outputs, reconcile duplicate candidates for the same work package, identify material disagreements, verify repository destinations, and produce deterministic review artifacts without silently selecting a winner or promoting chat output into canon.

The initial operational scenario includes independently generated specifications for overlapping ranges, including duplicate candidate sets for WP-4127 through WP-4130, alongside single-source candidate ranges such as WP-4107 through WP-4117 and WP-4118 through WP-4126.

## Required Implementation

### 1. Candidate Bundle Intake

Consume one or more WP-4209 staging bundles and their validation reports.

Validate before comparison:

- schema version;
- source archive hash;
- extraction run identifier;
- candidate content hash;
- work-package identifier;
- source message provenance;
- proposed destination;
- non-canonical review status.

Reject or review-block tampered, incomplete, unsupported, or internally inconsistent bundles.

### 2. Authoritative Work-Package Comparison

For every candidate, load the matching pending work-package definition from:

`collaboration/work_packages/pending/`

Compare the candidate against the authoritative definition without modifying the pending file.

Verify that the candidate:

- addresses the stated objective;
- covers every required implementation area;
- includes required deliverables;
- respects boundaries and prohibited behavior;
- addresses acceptance criteria;
- preserves defined terminology and distinctions;
- does not claim implementation, testing, validation, or closure without evidence;
- does not silently introduce global Estate redesign outside the work package.

### 3. Runtime-Canon Structural Validation

Validate expected runtime-canon coverage, including where applicable:

- policy and governing principles;
- schemas and persistent records;
- runtime behavior;
- decision and escalation logic;
- boundaries and prohibited behavior;
- Estate-system integrations;
- audit and review surfaces;
- diagnostics and failure handling;
- operator documentation;
- unit tests;
- integration tests;
- validation scenarios;
- anti-patterns;
- completion criteria.

The validator must distinguish:

- absent section;
- present but substantively empty section;
- partial coverage;
- complete coverage;
- unsupported implementation claim;
- ambiguous or contradictory requirement.

Do not rely only on heading names. Use deterministic rules plus explicit diagnostics for uncertain mappings.

### 4. Duplicate Detection and Reconciliation

Group candidates by WP identifier across all supplied bundles.

For duplicate candidates:

- retain every source and provenance record;
- compare normalized structure and exact content hashes;
- identify identical, near-identical, and materially divergent candidates;
- produce section-level and statement-level differences;
- identify content unique to each candidate;
- detect direct contradictions;
- distinguish wording differences from substantive differences;
- never silently discard or select a candidate.

Produce a reconciliation record with one of these statuses:

- `single_candidate`;
- `duplicate_identical`;
- `duplicate_compatible_merge_possible`;
- `duplicate_material_conflict`;
- `review_blocked`.

### 5. Reconciled Candidate Generation

For compatible duplicates, the system may generate a deterministic reconciled draft, but only as non-canonical review material.

A reconciled draft must:

- preserve all source provenance;
- identify which source contributed each merged section;
- avoid inventing new requirements;
- avoid resolving substantive contradictions automatically;
- mark unresolved conflicts inline and in metadata;
- receive a new content hash and reconciliation run identifier;
- remain review-required.

For material conflicts, produce no merged candidate unless an explicit human-authored resolution input is supplied.

### 6. Repository Destination Validation

Verify proposed destinations against current repository conventions.

The implementation must:

- inspect established specification/runtime-canon destinations;
- reject any destination under `collaboration/work_packages/pending/`;
- detect existing destination collisions;
- distinguish create-new-file, exact-duplicate, replacement-proposed, and ambiguous-destination cases;
- never write directly to canonical destinations during validation or reconciliation;
- generate a reviewable promotion plan only.

### 7. Coverage Validation Across Assigned Ranges

Accept explicit expected ranges and cross-bundle range sets.

Support examples such as:

- `WP-4107 through WP-4116`;
- `WP-4117 through WP-4126`;
- `WP-4127 through WP-4130`;
- combined `WP-4107 through WP-4130`.

The report must enumerate:

- expected;
- found;
- missing;
- duplicated;
- unexpected;
- invalid;
- blocked;
- ready for human review.

No missing or duplicate package may be silently ignored.

### 8. Review Artifacts

Produce a deterministic, content-addressed reconciliation bundle containing at least:

- `reconciliation_manifest.json`;
- `coverage_report.json`;
- `candidate_assessments.jsonl`;
- `duplicate_comparisons.json`;
- `reconciliation_report.md`;
- `promotion_plan.json`;
- optional reconciled candidate Markdown files;
- diagnostics and validation evidence.

Every artifact must carry source hashes and run identifiers.

### 9. CLI and Operator Workflow

Provide a CLI that can:

- accept one or more WP-4209 staging bundle paths;
- accept expected ranges;
- locate authoritative pending work packages;
- run validation only;
- run duplicate comparison;
- generate compatible reconciled drafts;
- emit machine-readable and human-readable reports;
- return non-zero status for review-blocking conditions.

Document exact operator commands and expected outputs.

### 10. Safety and Authority Boundaries

The implementation must never:

- modify immutable MHTML archives;
- modify WP-4208 or WP-4209 source bundles;
- overwrite pending work-package definitions;
- promote a candidate into canon automatically;
- choose between conflicting duplicates without explicit human authority;
- report a work package implemented, tested, validated, closed, or complete merely because a design candidate exists;
- erase provenance during reconciliation.

## Deliverables

- Validation and reconciliation runtime module under `src/estate/core/`.
- JSON schemas for reconciliation manifests and reports.
- CLI entry point and operator documentation.
- Deterministic comparison and reconciliation outputs.
- Unit tests.
- Integration tests spanning WP-4208, WP-4209, and WP-4210.
- Synthetic fixtures for identical, compatible, and conflicting duplicates.
- A realistic duplicate-range test for WP-4127 through WP-4130 when archives are available.
- Validation report under `operations/validation/reports/`.
- Completion artifact under `collaboration/work_packages/completions/`.

## Required Tests

Test at minimum:

- one valid candidate and matching pending definition;
- missing required runtime-canon section;
- substantively empty section;
- unsupported completion claim;
- identical duplicate candidates;
- compatible duplicates with complementary sections;
- materially conflicting duplicates;
- three or more candidates for one WP;
- missing work package in an expected range;
- unexpected work package outside the range;
- candidate hash tampering;
- source bundle provenance mismatch;
- ambiguous repository destination;
- attempted pending-definition overwrite;
- existing destination collision;
- deterministic rerun identity;
- safe generation of a review-only reconciled draft;
- refusal to merge unresolved material conflicts;
- end-to-end MHTML ingestion, extraction, validation, and reconciliation.

## Acceptance Criteria

WP-4210 is complete only when:

1. Multiple WP-4209 bundles can be ingested and validated together.
2. Every candidate is checked against its authoritative pending work package.
3. Required runtime-canon sections are assessed substantively, not merely by heading presence.
4. Duplicate candidates are classified as identical, compatible, conflicting, or blocked.
5. Section-level differences and unique contributions are reported with provenance.
6. Compatible reconciliation drafts can be generated without inventing requirements.
7. Material conflicts remain explicitly unresolved pending human judgment.
8. Expected range coverage is complete and explicit.
9. Proposed destinations are validated without writing to them.
10. No pending definition or canonical artifact is modified automatically.
11. Outputs are deterministic, content-addressed, auditable, and idempotent.
12. Unit and integration tests pass.
13. Validation evidence and the WP completion JSON are committed.
14. The completion artifact states that all outputs remain non-canonical and review-required.

## Codex Handoff

Implement this work package end to end. Reuse WP-4208 and WP-4209 rather than duplicating ingestion or extraction logic. Preserve every source and provenance record. Treat duplicate WP-4127 through WP-4130 specification candidates as the principal real-world reconciliation scenario when suitable archives become available. Do not automatically promote, overwrite, approve, or select between materially conflicting candidates.