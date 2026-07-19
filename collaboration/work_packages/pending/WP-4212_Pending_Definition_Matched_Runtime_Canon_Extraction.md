# WP-4212 — Pending-Definition-Matched Runtime-Canon Extraction

## Status

Pending

## Purpose

Implement conversation recovery around assistant-produced work-package outputs rather than around reconstructed conversational assignment scope.

The system must detect candidate runtime-canon or supporting-design documents in archived conversations, resolve each detected work-package identifier against the authoritative work-package files under `collaboration/work_packages/pending/`, compare the candidate output with the matching pending definition, and preserve qualifying material as a reviewable non-canonical supporting document.

Conversational assignment reconstruction remains useful for diagnostics, but it must not control whether a candidate work-package output is detected, extracted, validated, or preserved.

## Governing Principle

The authoritative relationship is:

```text
conversation output          = candidate evidence
pending work-package file    = authoritative definition
preserved supporting document = derived, non-canonical review material
```

The pending directory is the identification and validation authority. A conversational statement that a work package was assigned, completed, skipped, corrected, or out of scope is secondary evidence only.

## Problem Statement

Existing conversation validation can identify scope changes and execution errors, but real archived conversations contain historical references, copied seeds, corrections, examples, mistaken outputs, and repeated work-package numbers. Treating all such references as assignment declarations produces false scope conclusions.

The recovery objective is simpler and more concrete:

1. Find assistant output that appears to be a substantive work-package supporting document.
2. Identify the work-package number or named identifier associated with that output.
3. Confirm that a matching authoritative work-package definition exists.
4. Load that definition.
5. Determine whether the assistant output is complete and usable against the definition.
6. Preserve complete candidates as supporting documents with provenance.
7. Preserve incomplete or uncertain candidates only as review-blocked evidence.

## Scope

This work package covers:

- indexing authoritative pending work packages;
- detecting numbered and approved named work-package identifiers in assistant output;
- extracting complete candidate output blocks from parsed conversations;
- resolving candidates to authoritative pending definitions;
- evaluating candidate completeness and substantive coverage;
- grouping duplicate or competing candidates across multiple archives;
- producing deterministic manifests, reports, and proposed supporting documents;
- preserving provenance and hashes;
- integrating with the existing conversation-ingestion, extraction, validation, and promotion-blocking pipeline;
- maintaining assignment-scope analysis as a separate diagnostic surface.

This work package does not authorize automatic canonical promotion, modification of pending definitions, completion claims, or direct replacement of repository canon.

## Required Implementation Areas

### 1. Pending Work-Package Index

Create a deterministic index of files under:

```text
collaboration/work_packages/pending/
```

Each index record must include at least:

```json
{
  "work_package_id": "WP-4107",
  "canonical_identifier": "WP-4107",
  "title": "...",
  "path": "collaboration/work_packages/pending/WP-4107_....md",
  "content_sha256": "...",
  "filename_match": true,
  "internal_identifier_match": true,
  "index_status": "valid"
}
```

The indexer must detect and block:

- duplicate authoritative identifiers;
- malformed identifiers;
- filename/body identifier disagreement;
- ambiguous named work packages;
- unreadable files;
- multiple pending definitions resolving to the same normalized identifier.

The index must be stable across repeated runs against an unchanged repository.

### 2. Candidate Output Detection

Scan assistant-authored messages for evidence of a substantive work-package output.

Detection signals may include:

- `WP-####` in a title or leading heading;
- `Runtime Canon — WP-####`;
- `WP-#### Supporting Runtime Canon`;
- `Supporting Design for WP-####`;
- `Grounded in WP-####` followed by a substantial structured response;
- approved named work-package identifiers that resolve uniquely in the pending index.

A bare mention of a work-package identifier is not sufficient. The detector must distinguish substantive candidate documents from:

- conversational discussion;
- assignment lists;
- quoted instructions;
- copied work-package filenames;
- historical summaries;
- completion reports that do not contain the supporting document;
- examples and test fixtures embedded in prose;
- user-authored content unless explicitly configured for evidentiary capture.

Candidate detection must be independent of whether the work package was assigned in that conversation.

### 3. Candidate Boundary Extraction

For every detected candidate, extract the complete assistant-produced block.

The extractor must preserve:

- source archive identifier;
- parsed conversation identifier;
- source message sequence;
- source role;
- character and line boundaries where available;
- original text without semantic rewriting;
- normalized text for hashing and comparison;
- preceding and following message references;
- detector signals that caused selection.

A candidate generally ends at the end of the assistant message unless the ingestion format proves that one logical assistant output was split across adjacent records. Cross-message joining must be explicit, deterministic, and provenance-preserving.

### 4. Pending-Definition Resolution

Normalize the detected identifier and resolve it against the pending index.

Resolution outcomes must include:

```text
matched_unique
unmatched_identifier
ambiguous_identifier
malformed_identifier
named_identifier_not_approved
pending_definition_invalid
```

Only `matched_unique` candidates proceed to substantive completeness evaluation.

Unmatched output must remain visible in diagnostics. It must not be silently discarded, because it may indicate an incorrect number, a moved work package, or an output generated against a non-pending definition.

### 5. Definition Parsing

Parse the authoritative work-package definition into review dimensions where present:

- purpose or objective;
- governing principles;
- required implementation areas;
- required deliverables;
- schemas and persistent records;
- runtime behavior;
- decision and escalation logic;
- boundaries and prohibited behavior;
- integrations;
- audit and review surfaces;
- diagnostic handling;
- operator documentation;
- unit tests;
- integration tests;
- validation scenarios;
- anti-patterns;
- acceptance or completion criteria.

The parser must tolerate variations in heading names without inventing requirements absent from the authoritative definition.

### 6. Completeness and Usability Assessment

Assess substance, not heading presence alone.

Each candidate must receive:

```json
{
  "assessment": "complete_supporting_document",
  "confidence": "high",
  "required_dimensions": 14,
  "covered_dimensions": 14,
  "missing_dimensions": [],
  "partial_dimensions": [],
  "unsupported_claims": [],
  "truncation_status": "not_truncated",
  "review_required": true
}
```

Required assessment values:

```text
complete_supporting_document
substantially_complete_review_required
partial_supporting_document
truncated_candidate
identifier_only_false_positive
unrelated_content
cannot_assess_definition
```

A candidate may be classified as complete only when it materially responds to the authoritative definition and contains no unresolved truncation or major unsupported-completion defect.

No fixed percentage alone may authorize completeness. Coverage scoring is advisory; mandatory requirements and prohibited behavior take precedence.

### 7. Truncation Detection

Truncation detection must consider:

- abrupt sentence or section termination;
- unmatched fenced code blocks;
- unfinished numbered sequences;
- missing sections explicitly promised by the candidate;
- output ending in a transition phrase;
- archive/parser termination evidence;
- unusually short content relative to the authoritative definition;
- continuation markers without a following continuation.

Truncation must be reported separately from substantive incompleteness.

### 8. Duplicate and Competing Candidate Reconciliation

Group candidates by normalized work-package identifier across all supplied archives.

For each group, compute:

- exact normalized-hash duplicates;
- near duplicates;
- independently authored alternatives;
- complete versus partial versions;
- superseding continuations;
- conflicting substantive recommendations;
- provenance ordering.

The system may identify a preferred preservation candidate, but it must retain the full candidate set and explain the selection.

Preferred-candidate rules must prioritize:

1. unique match to the authoritative definition;
2. no truncation;
3. complete substantive coverage;
4. fewer unsupported claims;
5. stronger provenance;
6. later version only when it is demonstrably more complete or corrective.

Recency alone must not determine superiority.

### 9. Supporting-Document Preservation

A qualifying candidate must be rendered as a proposed non-canonical supporting document.

The preserved document must include a provenance preamble containing:

- work-package identifier;
- authoritative pending-definition path and hash;
- source archive and conversation identifiers;
- source message sequence;
- candidate content hash;
- extraction timestamp;
- assessment result;
- review status;
- explicit statement that the artifact is non-canonical until approved.

The assistant-produced body must remain verbatim except for clearly marked mechanical normalization such as newline normalization.

The implementation must not write supporting documents into `collaboration/work_packages/pending/` and must not overwrite the authoritative definition.

The final destination must follow an existing repository convention discovered during implementation. If no approved convention exists, the system must emit a promotion plan and block repository write rather than inventing a canonical destination.

### 10. Separation from Assignment Diagnostics

Assignment and scope reconstruction remains available for questions such as:

- Was this work package requested?
- Was it produced outside the stated range?
- Was a correction ignored?
- Was a requested work package omitted?

However:

```text
assignment status must not suppress candidate detection
assignment status must not prevent pending-definition resolution
assignment status must not determine completeness
assignment status must not delete or hide out-of-scope outputs
```

Assignment diagnostics must be attached as secondary metadata only.

## Persistent Records and Artifacts

The implementation must produce deterministic machine-readable artifacts, including:

### `pending_work_package_index.json`

Authoritative index and validation status for pending definitions.

### `runtime_canon_candidates.json`

All detected candidate blocks, including false positives and unresolved identifiers.

### `definition_match_report.json`

Resolution result for every candidate.

### `candidate_assessment_report.json`

Dimension-level completeness, truncation, unsupported claims, and review disposition.

### `candidate_reconciliation_report.json`

Duplicate groups, competing versions, preferred candidates, and selection reasons.

### `supporting_document_manifest.json`

Proposed preserved artifacts, destinations, hashes, provenance, and promotion status.

### `runtime_canon_recovery_report.md`

Human-readable summary organized by work-package identifier.

### `promotion_block_report.md`

All conditions preventing preservation or promotion.

Existing scope and execution artifacts may continue to be emitted, but they are not the primary index for this workflow.

## Runtime Pipeline

```text
conversation archives
→ existing archive ingestion and normalized message records
→ assistant-message candidate detection
→ candidate boundary extraction
→ pending-folder index resolution
→ authoritative definition loading and parsing
→ completeness and truncation assessment
→ cross-archive duplicate reconciliation
→ supporting-document rendering
→ review and promotion gate
```

Every stage must be restartable and deterministic from persisted inputs.

## Decision and Escalation Logic

### Preserve as proposed supporting document

Permitted only when:

- identifier resolves uniquely;
- pending definition is valid and readable;
- candidate is complete or explicitly approved under the substantially-complete review path;
- candidate is not truncated;
- provenance is complete;
- destination policy is known;
- no conflicting candidate requires human selection.

### Retain as review-blocked candidate

Required when:

- candidate is partial;
- completeness confidence is not high;
- multiple materially conflicting complete candidates exist;
- destination convention is unresolved;
- unsupported claims remain;
- definition parsing is incomplete.

### Block preservation

Required when:

- identifier has no unique pending match;
- pending index is ambiguous or invalid;
- source provenance is missing;
- extraction boundaries are unreliable;
- candidate is truncated;
- candidate is unrelated or only an identifier mention.

### Escalate to Steward review

Required for:

- competing complete candidates;
- proposed changes to repository destination policy;
- named identifiers without an approved mapping;
- a candidate that materially conflicts with the authoritative work package;
- any request to promote a supporting document into canon.

## Boundaries and Prohibited Behavior

The implementation must not:

- treat conversational assignment as the authority for extraction;
- create a work-package definition merely because a number appears in conversation;
- infer that a work package is complete because the assistant says it is complete;
- overwrite or edit the pending definition during extraction;
- silently discard out-of-scope but valid outputs;
- merge competing candidates into a synthetic document without explicit authorization;
- rewrite the candidate body while claiming it is verbatim;
- promote a derived artifact automatically;
- rely solely on heading counts or keyword frequency;
- hide unmatched or malformed identifiers;
- use recency as the sole duplicate-selection rule.

## Integration Requirements

Integrate with and preserve compatibility with:

- conversation archive ingestion from WP-4208;
- conversation specification extraction from WP-4209;
- specification validation and reconciliation from WP-4210;
- plain-text and diagnostic handling from WP-4211;
- existing repository promotion-blocking behavior;
- existing CLI patterns and validation-report locations.

WP-4212 changes the primary organizing principle for runtime-canon recovery. It does not remove the diagnostic value of WP-4211.

## Operator Interface

Provide a CLI entry point capable of accepting:

- one or more normalized conversation archives or derived conversation directories;
- repository root;
- pending work-package directory override for tests;
- output directory;
- optional identifier filter;
- dry-run mode;
- strict mode;
- machine-readable output mode.

The CLI must clearly report:

```text
archives processed
assistant messages scanned
candidates detected
unique pending matches
unmatched identifiers
complete candidates
partial candidates
truncated candidates
duplicate groups
conflicting groups
proposed supporting documents
blocked promotions
```

A non-zero exit status is required when blocking conditions exist in strict mode.

## Diagnostics

At minimum, support these diagnostic codes:

```text
pending_index_duplicate_identifier
pending_filename_body_identifier_mismatch
candidate_identifier_unmatched
candidate_identifier_ambiguous
candidate_false_positive
candidate_boundary_uncertain
candidate_truncated
candidate_partial
candidate_missing_required_dimension
candidate_unsupported_completion_claim
candidate_conflicts_with_definition
duplicate_candidate_exact
duplicate_candidate_near
competing_complete_candidates
supporting_destination_unknown
provenance_incomplete
promotion_blocked
```

Diagnostics must include source pointers and remediation guidance.

## Unit Tests

Unit coverage must include:

- numbered identifier normalization;
- named identifier normalization and rejection;
- pending index duplicate detection;
- filename/body mismatch detection;
- substantive candidate versus bare mention;
- quoted seed and historical-summary rejection;
- complete single-message extraction;
- deterministic adjacent-message joining;
- unmatched and ambiguous resolution;
- dimension parsing across heading variations;
- substantive completeness evaluation;
- truncation signals;
- exact and near-duplicate grouping;
- preferred-candidate selection;
- provenance rendering;
- assignment metadata not suppressing extraction;
- stable hashes and deterministic artifact ordering.

## Integration Tests

Integration tests must include:

1. A conversation containing an assigned and complete WP output.
2. A conversation containing a complete output for an unassigned WP.
3. A conversation containing many historical WP references but only one substantive output.
4. Multiple archives containing exact duplicate outputs.
5. Multiple archives containing partial and complete versions of the same output.
6. Multiple materially conflicting complete candidates.
7. A named work package with a unique approved pending definition.
8. An identifier with no pending match.
9. A truncated output caused by archive termination.
10. A pending directory containing duplicate identifiers.
11. A dry run that produces no repository mutation.
12. Repeated runs producing byte-identical machine-readable reports for unchanged inputs.

## Production Validation Scenarios

The implementation must be validated against the real conversation archives previously used for WP-4211, including the available four-file set.

The validation must demonstrate that:

- assistant outputs are enumerated by detected work-package identifier;
- historical and assignment references do not become authoritative output records;
- every candidate is matched or explicitly reported unmatched;
- complete outputs are distinguishable from partial or truncated outputs;
- duplicate candidates across files are grouped;
- no pending definition is overwritten;
- proposed supporting documents preserve provenance;
- assignment diagnostics remain available but do not control extraction.

The production validation report must list the actual work-package identifiers found and the disposition of each candidate.

## Anti-Patterns

- Building the candidate list from the final assignment scope.
- Treating every `WP-####` mention as an output.
- Declaring completeness from section-count thresholds alone.
- Dropping a valid output because it was produced by mistake.
- Selecting the newest duplicate without comparing substance.
- Combining two outputs into a new synthetic canon during recovery.
- Saving a candidate into the pending directory.
- Reporting success without testing against the real multi-file archives.

## Deliverables

1. Pending work-package index implementation.
2. Runtime-canon candidate detector and boundary extractor.
3. Pending-definition resolver and parser.
4. Completeness and truncation assessment engine.
5. Duplicate and competing-candidate reconciler.
6. Supporting-document renderer and manifest generator.
7. CLI integration.
8. Machine-readable and human-readable reports.
9. Unit and integration tests.
10. Production four-file validation report.
11. Operator documentation.
12. Completion record identifying exact files, tests, commands, and observed results.

## Acceptance Criteria

WP-4212 is complete only when all of the following are demonstrated:

- The pending directory is indexed deterministically and invalid definitions block resolution.
- Substantive assistant work-package outputs are detected independently of assignment scope.
- Every candidate identifier is resolved against the authoritative pending index.
- Complete, partial, truncated, false-positive, and unmatched candidates are distinguishable.
- Completeness is evaluated against the actual matching pending definition.
- Valid out-of-scope outputs remain visible and eligible for preservation.
- Duplicate and competing outputs across multiple archives are reconciled without silent loss.
- Qualifying outputs are rendered as non-canonical supporting documents with complete provenance.
- No pending definition or canonical artifact is automatically modified.
- Assignment diagnostics remain separate and secondary.
- The real four-file archive trial produces a trustworthy identifier-by-identifier recovery report.
- Tests and repeated production runs are deterministic.
- All blocking conditions are surfaced with actionable diagnostics.
