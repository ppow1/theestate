# ESTATE-CAP-002 — Blocking Review and Merge Readiness for PR #507

## Objective

Perform a complete blocking review of PR #507, correct any in-scope defects, and determine whether the Estate Capability Onboarding Standard is safe to merge.

This is a documentation-first architecture and operational-standard review with one small resident capability manifest schema and bounded validator support. It is not authorization to implement Qwen Coder, Whisper, ComfyUI live execution, Historian tools, Legal tools, or any new provider.

## Current PR

- PR: #507
- Branch: `architecture/estate-capability-onboarding-standard`
- Expected head: `628101a82d7b4b3b76b348826709070c054f4cd8`
- Base: `main`
- State: open, draft, unmerged, mergeable

## Review goals

Attempt to disprove that the package is sufficiently complete, executor-neutral, Estate-wide, and safe for Grace, Helen, Codex CLI, Qwen Coder, another qualified worker, or a human engineer to use without hidden context.

Correct all in-scope blockers found during review. Keep the PR draft until the final audit passes.

## Required review areas

### 1. Executor neutrality

Confirm the standard, template, runbook, checklist, schema, validator, and worked examples do not depend on Codex-specific behavior, undocumented oral context, hidden repository knowledge, or one implementation worker.

Verify an unfamiliar qualified worker can determine:

- what must be discovered before implementation;
- which canonical registries and lifecycle surfaces to reuse;
- which decisions require Steward or Chief Architect authority;
- how Helen specifies a missing worker capability;
- how Grace resumes after an enabling project;
- how to prove maturity transitions;
- how to stop safely rather than invent policy.

### 2. Estate-wide applicability

Confirm the three-layer model is clear and consistently applied:

1. Estate core capability contract;
2. resident overlay;
3. provider/tool overlay.

Verify the framework covers both executable providers and resident-owned non-execution tools, including legal research, historical retrieval, source comparison, transcription, media generation, classification, audit, and advisory tools.

### 3. Maturity model

Review Levels 0 through 5 for:

- unambiguous entry and exit evidence;
- current availability separate from historical maturity;
- explicit transition authority;
- no inference of operational status from registration;
- no inference of institutional acceptance from successful execution;
- regression, expiry, suspension, deprecation, and requalification behavior.

Confirm Grace and Helen can report maturity, availability, dispatchability, authority requirements, and enabling-project state distinctly.

### 4. Canonical source-of-truth reuse

Verify every named canonical surface exists and is described accurately, including:

- `config/providers/catalog.json`;
- `data/registry/capabilities.json`;
- resident manifests and readiness surfaces;
- Helen capability assessment;
- PTM readiness;
- Engineering commission and authorization;
- Operations decision;
- Dispatch and adapter request;
- provider receipts;
- reconciliation and Grace terminal evidence;
- service manifests and adapter registries.

Confirm no second provider catalog, capability registry, PTM system, Dispatch path, personnel system, or receipt authority is introduced.

### 5. Resident capability manifest schema

Review `schemas/residents/resident_capability_manifest_v1.schema.json` completely.

Confirm it is:

- closed and versioned;
- compatible with the provider catalog rather than replacing it;
- sufficient for resident discovery;
- explicit about owner, capability binding, provider/tool binding, adapter identity, maturity, current status, classification ceiling, authority, evidence sources, limitations, inputs, and outputs;
- strict on IDs, versions, timestamps, and repository-relative references where applicable;
- unable to smuggle hidden authority through open metadata;
- clear about the difference between maturity and current availability.

Add positive and negative schema tests for missing, malformed, conflicting, duplicate, overbroad, or extra authority-bearing fields.

### 6. Implementation template completeness

Review the implementation template as if commissioning each of these from scratch:

- Qwen Coder repository implementation;
- Whisper transcription;
- ComfyUI image generation;
- Historian archival research;
- Legal Expert source analysis.

Confirm the template forces complete treatment of:

- ownership;
- taxonomy;
- duplicate discovery;
- worker requirements;
- bootstrap dependencies;
- authority;
- exact I/O and provenance;
- classification and network boundaries;
- credentials;
- schemas and records;
- health, capacity, qualification, authorization, and freshness;
- persistence;
- failure, cancellation, collision, and replay;
- tests and live acceptance;
- rollback, deprecation, and removal;
- institutional acceptance separation.

No section may depend on the capability being created to bootstrap itself.

### 7. Runbook usability

Walk the runbook from a natural-language Steward request to an operational capability.

Confirm the decision tables answer when:

- a catalog entry is sufficient;
- a provider configuration is sufficient;
- an adapter is required;
- a resident wrapper is sufficient;
- PTM is required;
- Dispatch is required;
- a receipt is required;
- live acceptance is mandatory;
- designed or registered maturity is the safe stopping point.

Confirm the runbook explains exactly what Grace, Helen, Engineering, the resident owner, and the Steward do at each phase.

### 8. Worked examples

Verify each example is a faithful application of the same standard rather than a separate mini-architecture.

The examples must expose their materially different requirements:

- Qwen Coder: worktree/write/output authority and receipts;
- Whisper: media identity, transcript timestamps, language/model evidence, no repository implementation authority;
- ComfyUI: workflow/model/node provenance, health/capacity, image metadata, no automatic media acceptance;
- Historian/Legal: citation and source evidence, read-only default, uncertainty/conflict reporting, jurisdiction/effective-date boundaries, no substitution of model inference for source evidence.

Examples must remain designs only and must not imply live authorization.

### 9. Grace and Helen paper exercises

Perform at least these paper exercises and record the results:

1. Grace receives a request for Whisper transcription and asks Helen for capability status.
2. Helen finds the model installed but no governed adapter and reports the correct maturity and enabling project.
3. Grace receives a request for Qwen Coder repository implementation and distinguishes provider availability from dispatchability.
4. Historian requests a read-only archival search wrapper with conflicting sources.
5. Legal Expert requests a jurisdiction-bound research tool with stale authority evidence.
6. A worker cannot implement an adapter because the required bootstrap capability is absent.

For each exercise, identify:

- owner;
- current maturity;
- current availability;
- required authority;
- next lifecycle record;
- safe stop condition;
- whether Grace may resume automatically after the enabling dependency is satisfied.

### 10. Validator and lint behavior

Review all changes to the work-package validator and onboarding lint.

Confirm:

- ordinary existing work packages are not broken;
- onboarding validation applies only when appropriate;
- required sections cannot be satisfied by empty placeholders;
- executor-neutral completeness is testable without overfitting exact prose;
- false positives and false negatives are bounded;
- template files themselves validate;
- malformed or incomplete onboarding packages fail with actionable diagnostics.

### 11. Documentation consistency

Confirm terminology, maturity levels, file paths, schema IDs, authority boundaries, and lifecycle order agree across all deliverables.

Fix stale, contradictory, ambiguous, or circular language.

### 12. Failure and stop behavior

Confirm the standard fails closed for unresolved:

- ownership;
- classification;
- credentials;
- endpoint/network policy;
- protected data;
- authority;
- worker qualification;
- health/capacity/freshness;
- bootstrap capability;
- schema ownership;
- registry precedence;
- live service access;
- institutional acceptance.

A worker must return a bounded gap or authority request rather than silently broaden scope.

## Correction authority

You may correct all blocking defects within PR #507’s existing scope.

For each correction:

1. add or update regression validation;
2. preserve executor neutrality;
3. reuse existing canonical surfaces;
4. do not implement any example provider;
5. commit on the existing branch;
6. push normally without force;
7. keep PR #507 draft until the final audit passes.

Stop for a genuine unresolved architecture or authority decision that cannot be answered by existing Estate canon.

## Validation

Run at minimum:

- all onboarding standard, template, runbook, checklist, and example tests;
- resident manifest schema tests with Draft 2020-12 and FormatChecker;
- work-package validator and onboarding lint tests;
- provider catalog and capability registry tests;
- relevant Grace/Helen capability lifecycle tests;
- relevant PTM, Dispatch, handoff, receipt, and reconciliation tests sufficient to validate referenced contracts;
- Markdown/link/reference checks available in the repository;
- Python compilation;
- tracked JSON parsing;
- `git diff --check`;
- `git status`.

Reproduce the two reported temporary-root CLI failures on base and head and document whether they are truly unrelated.

## Durable review report

Create:

`docs/operations/reviews/ESTATE-CAP-002_PR507_Blocking_Review_20260731.md`

Record:

- starting head;
- findings;
- corrections;
- paper exercises;
- schema and validator results;
- base/head status of inherited failures;
- test totals;
- final head;
- PR state;
- unresolved decisions;
- exact next Steward action.

## Final action

If all blocking findings are resolved and validation passes:

1. mark PR #507 ready for review;
2. do not merge;
3. return control to the Steward for explicit merge authorization.

If a blocker remains:

- keep the PR draft;
- report the exact blocker and required decision or correction.

Do not merge.
