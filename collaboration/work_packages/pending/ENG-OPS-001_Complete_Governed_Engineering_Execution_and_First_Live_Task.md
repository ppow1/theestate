# ENG-OPS-001 — Complete Governed Engineering Execution and Prove the First Live Task

Status: **AUTHORIZED FOR CODEX EXECUTION**  
Owner: Office of the Steward  
Execution environment: `A:\theestate-wp4233`  
Repository: `ppow1/theestate`  
Date authorized: 2026-07-31

## Steward intent

This is not another narrow one-field repair.

The Estate has spent the day building and validating the pieces of a governed Engineering execution lifecycle, but Engineering still cannot complete a simple live task from Grace through a registered worker and return a truthful completion.

This work package authorizes a bounded but comprehensive operational-closure campaign whose required outcome is:

> A fresh Grace request successfully traverses Grace → Helen → PTM → Engineering → Dispatch → canonical adapter handoff → registered local Qwen provider → artifact and provider receipt → Engineering completion and reconciliation → Grace terminal completion, without bypasses, false authority, or institutional acceptance.

The work is not complete merely because another missing field is identified, another preflight report is written, or another individual seam passes a unit test.

The work is complete only when the full production lifecycle performs one real bounded task successfully and the result is backed by durable evidence.

## Current foundation

The following merged work is the starting foundation:

- PR #499 — governed `qwen.local.text` provider;
- PR #500 — production PTM readiness authority;
- PR #501 — Grace/PTM/Engineering/Dispatch readiness integration;
- PR #502 — governed authority propagation into the Dispatch adapter handoff.

Current main includes PR #502 merge commit:

`4526cd52f933bf02f1b402e00d6507414f4a77a0`

The latest operational preflight is recorded in draft PR #503 and:

`docs/operations/validation/Qwen_Governed_Live_Validation_021142e6f4914ee2ae1a09444d91203a_FAILED_20260731.md`

That preflight established that the local Ollama endpoint is reachable and `qwen3:8b` is installed, but the production path still drops Qwen-required execution metadata before the registered adapter is invoked.

The currently identified missing fields are:

- `requested_capability`;
- `evidence_observed_at`;
- `evidence_expires_at`;
- `authorized_model_identity`;
- `provider_receipt_path`.

These are the known symptoms, not necessarily the complete defect set.

## Campaign authorization

Codex is authorized to inspect, design, implement, test, and operationally validate every remaining correction within the existing governed Engineering execution path that is necessary to achieve the required end-to-end outcome.

This includes corrections across:

- Grace request and action records;
- Helen capability evidence;
- PTM readiness bindings;
- Engineering commission authority;
- Engineering authorization records;
- Operations execution decisions;
- Dispatch request and queue records;
- adapter handoff construction and validation;
- provider-neutral adapter request contracts;
- provider-specific request metadata;
- provider catalog and registered adapter resolution;
- provider receipt paths and receipt validation;
- artifact validation;
- Engineering completion and reconciliation;
- Grace terminal receipts and lifecycle state;
- related schemas, persistence, tests, operator documentation, and validation reports.

Codex does **not** need to stop and request a separate Steward authorization for each additional missing field, schema mismatch, correlation defect, persistence defect, or production wiring gap discovered inside this exact lifecycle.

Codex must continue correcting in-scope blockers until either:

1. the full live governed task succeeds; or
2. a blocker requires a genuine authority or architectural decision outside the boundaries below.

When an in-scope correction is required, implement it, add regression coverage, and continue the campaign. Do not return after merely diagnosing the next missing field.

## Non-negotiable boundaries

This campaign does not authorize:

- a second scheduler, queue, provider catalog, PTM system, Engineering department, or authority registry;
- bypassing Grace, Helen, PTM, Engineering, Dispatch, handoff validation, provider registration, or completion reconciliation;
- an always-ready PTM resolver;
- arbitrary caller metadata becoming execution authority;
- direct Ollama generation as a substitute for the governed adapter path;
- shell authority or repository implementation authority for Qwen;
- broad repository read or write access;
- changing the configured Qwen model without a separately documented necessity;
- downloading or updating a model;
- granting institutional acceptance;
- automatically merging a pull request;
- rewriting historical evidence;
- modifying `A:\theestate`;
- deleting or altering the existing 16 stashes.

Institutional acceptance must remain `not_granted` throughout this campaign.

## Required branch and repository preparation

1. Work in the same existing Codex CLI session.
2. Use repository worktree:

   `A:\theestate-wp4233`

3. Fetch origin.
4. Switch to `main`.
5. Fast-forward to `origin/main`.
6. Confirm main includes merge commit:

   `4526cd52f933bf02f1b402e00d6507414f4a77a0`

7. Confirm this work package exists at:

   `collaboration/work_packages/pending/ENG-OPS-001_Complete_Governed_Engineering_Execution_and_First_Live_Task.md`

8. Confirm the worktree is clean.
9. Confirm 16 stashes remain.
10. Confirm `A:\theestate` is not modified.
11. Preserve draft PR #503 and its report as historical failed-preflight evidence.
12. Create a fresh branch:

   `engineering/complete-governed-engineering-first-live-task`

Do not continue implementation on the PR #503 validation branch.

## Phase 1 — Production-path reconciliation

Before editing, trace the actual production call path end to end.

At minimum inspect:

- `GraceOperationsRuntime`;
- `GraceHelenEngineeringComposition`;
- `governed_commission_and_dispatch()`;
- capability inquiry and Helen assessment creation;
- `PtmProductionReadinessResolver` and integration adapter;
- Engineering commission creation;
- Engineering authorization persistence;
- Operations decision persistence;
- `authorize_dispatch()`;
- canonical Dispatch queue insertion;
- `prepare_handoff()` and final handoff validation;
- `from_dispatch_record()`;
- `run-dispatch-bridge` and local Engineering worker paths;
- execution-provider adapter runtime;
- provider catalog resolution;
- `qwen.local.text` adapter request construction and `_metadata_errors()`;
- Qwen artifact and provider receipt publication;
- Engineering result validation and completion;
- reconciliation;
- Grace terminal closure.

Produce a single source-of-truth matrix showing, for every execution-critical field:

- canonical owner;
- record where created;
- schema governing it;
- path through each lifecycle stage;
- final consumer;
- freshness or expiry rule;
- digest or identity binding;
- whether it is provider-neutral or provider-specific.

The matrix must cover at least:

- requested capability;
- qualified capability evidence;
- evidence observation and expiration timestamps;
- provider health evidence;
- authorized provider identity;
- authorized adapter identity;
- authorized model identity;
- prompt source and digest;
- exact read paths;
- exact write paths;
- expected outputs;
- exact artifact path;
- exact provider receipt path;
- PTM resolution and digest;
- Engineering commission;
- Engineering authorization;
- Operations decision;
- Dispatch identity;
- adapter request identity;
- provider receipt identity;
- completion and reconciliation references.

Do not solve this by copying arbitrary provider metadata through every record. Define the correct provider-neutral execution contract and a bounded provider-specific extension where genuinely necessary.

## Phase 2 — Complete the execution contract

Implement a coherent production contract that carries every required value from its canonical authority to the registered provider adapter.

### Provider-neutral authority

The provider-neutral lifecycle must carry and validate:

- requested capability or capabilities;
- evidence observation timestamp;
- evidence expiry timestamp;
- provider identity;
- adapter identity;
- model or implementation identity when the selected provider requires one;
- prompt source/type/digest;
- exact read scope;
- exact write scope;
- exact expected outputs;
- exact provider receipt path;
- all Grace/Helen/PTM/Engineering/Operations/Dispatch correlations.

### Provider-specific requirements

Provider-specific fields must be represented through a closed, versioned extension contract owned by the registered provider/adapter definition, not through an unconstrained metadata dictionary.

For `qwen.local.text`, the production request must authoritatively supply and validate:

- `requested_capability` supported by the provider catalog;
- fresh `evidence_observed_at`;
- valid `evidence_expires_at`;
- `authorized_model_identity = qwen3:8b`;
- exact `provider_receipt_path`;
- exact artifact output path;
- endpoint and loopback policy from canonical provider configuration;
- provider and adapter version identity.

The adapter must not infer missing authority, select another model, invent a receipt destination, or broaden paths.

### Canonical ownership

Determine and enforce the correct owners:

- Grace owns requested outcome and action prompt;
- Helen owns capability qualification, availability, capacity, and workforce evidence;
- PTM owns readiness;
- Engineering owns commission and bounded execution authority;
- Operations decision records authorize the specific execution decision;
- Dispatch owns execution authorization and queue insertion;
- provider catalog owns provider capability and adapter declarations;
- provider configuration owns model and endpoint policy;
- adapter owns execution behavior but not authority creation.

Do not allow duplicate authorities to disagree silently.

## Phase 3 — Schemas, persistence, replay, and validation

Add or revise closed Draft 2020-12 schemas for every new or changed authority-bearing record.

Use `Draft202012Validator` and `FormatChecker`.

Requirements include:

- `additionalProperties: false` for authority-bearing objects;
- strict ID and SHA-256 patterns;
- repository-relative bounded paths;
- exact output and receipt paths;
- unique path arrays;
- explicit enums and const values;
- non-null production authority fields;
- explicit schema versions;
- provider-extension schema identity;
- freshness timestamps and expiry;
- institutional acceptance fixed at `not_granted`;
- closed cross-record references.

All durable authority records must use canonical create-once persistence with:

- complete writes;
- short-write handling;
- flush;
- fsync;
- close;
- parent-directory durability where supported;
- deterministic idempotent replay;
- conflicting replay rejection;
- path bounding;
- symlink/reparse-point escape rejection;
- no truncating overwrite;
- no unsafe pathname rollback.

Final adapter handoff must reload and revalidate the canonical source records and digests, not merely compare copied metadata.

## Phase 4 — Production construction and bypass closure

Ensure the completed contract is active in the real production path.

Search all technical provider execution entry points, including:

- Dispatch bridge;
- local Engineering worker;
- direct adapter runtime calls;
- provider selection paths;
- CLI entry points;
- handoff test seams;
- any older technical Dispatch execution path.

Requirements:

- no technical provider can execute without a valid PTM-bound commission, Engineering authorization, Operations decision, Dispatch queue item, and final validated handoff;
- test-only adapter injection remains test-only;
- historical incomplete technical Dispatch remains non-executable;
- nontechnical Dispatch compatibility remains intact;
- retries require fresh unexpired evidence and fresh create-once output paths where prior publication was attempted;
- one governed request can produce at most one provider invocation and one completion.

## Phase 5 — Comprehensive automated validation

Add deterministic regression coverage for the complete field chain and all newly discovered blockers.

At minimum test:

### Positive production path

- Grace request creates action and inquiry;
- Helen emits qualified, available, capacity, authorization, and provider-health evidence;
- PTM returns ready;
- Engineering commission contains complete execution authority;
- Engineering authorization validates;
- Operations decision validates;
- Dispatch revalidation passes;
- queue insertion occurs once;
- final handoff validates every canonical source;
- registered fake adapter is invoked once;
- artifact and receipt evidence reconcile;
- Engineering completion is produced;
- Grace reaches completed state;
- institutional acceptance remains not granted.

### Required metadata

- requested capability missing/mismatched/unsupported;
- evidence observed timestamp missing or malformed;
- evidence expiry missing, stale, or before observed time;
- provider health stale;
- authorized model missing or mismatched;
- provider receipt path missing, broad, colliding, or outside scope;
- artifact path missing, broad, colliding, or outside scope;
- provider extension schema missing or unknown;
- arbitrary caller metadata attempting to override authority.

### Correlation and authority

- Grace mismatch;
- Helen mismatch;
- PTM mismatch or expiry;
- commission mismatch;
- Engineering authorization mismatch;
- Operations decision mismatch;
- Dispatch mismatch;
- provider mismatch;
- adapter mismatch;
- model mismatch;
- prompt digest mismatch;
- read/write/output mismatch;
- receipt-path mismatch;
- policy or registry drift;
- high-watermark change.

### Persistence and concurrency

- equivalent replay;
- conflicting replay;
- concurrent authorization;
- concurrent Dispatch;
- concurrent handoff creation;
- concurrent output collision;
- partial write, flush, fsync, and close failure;
- no duplicate provider invocation;
- no false completion after a failed publication.

Run the broadest practical bounded matrix covering all changed modules and direct consumers.

Run:

- Python compilation;
- tracked JSON parsing;
- schema-registry uniqueness and `$ref` resolution;
- Draft 2020-12 validation with FormatChecker;
- `git diff --check`;
- worktree status;
- base-versus-head checks for known unrelated failures.

A broad-suite timeout is not automatically a failure, but it must be documented truthfully and replaced with a complete changed-scope matrix.

## Phase 6 — Real live governed task

After the implementation and fake-adapter production-path tests pass, perform one real live Qwen task through the exact production path.

### Local provider

- Provider: `qwen.local.text`
- Adapter: `qwen-local-ollama-text-adapter@1.0.0`
- Endpoint: `http://127.0.0.1:11434`
- Model: `qwen3:8b`

Verify model presence read-only before the run. Do not download or update it.

### Task

Create one small Markdown document describing:

1. the authorized Qwen capabilities:
   - `documentation_draft`;
   - `text_generation`;
   - `bounded_repository_read`;
2. prohibited authorities:
   - no shell execution;
   - no repository implementation;
   - no arbitrary writes;
   - no merge authority;
   - no institutional acceptance authority;
3. configured and actual model identity `qwen3:8b`;
4. successful execution does not grant institutional acceptance.

Authorized reads are limited to:

- `docs/operations/Governed_Qwen_Local_Text_Provider.md`;
- `config/providers/qwen_local_text.json`.

Use entirely fresh lifecycle IDs and entirely fresh exact create-once artifact and provider receipt paths.

The run must traverse:

Steward request → Grace objective/action → capability inquiry → Helen assessment → PTM ready → Engineering commission → Engineering authorization → Operations decision → Dispatch revalidation → canonical queue → final handoff → registered Qwen adapter → live model → artifact → provider receipt → validation → Engineering completion → reconciliation → Grace terminal receipt.

### Live-run retry authority

If the first live attempt exposes another **in-scope production defect**, preserve the failure evidence, correct the defect on the same campaign branch, add regression tests, and retry using entirely new lifecycle IDs and new exact output paths.

Do not stop the campaign solely because the next in-scope defect appears.

No more than three live provider invocations are authorized for this campaign. Each attempt must have fresh IDs and paths and a durable attempt report.

Stop before another live invocation if the failure is caused by model behavior rather than production wiring, or if a safe correction requires authority outside this work package.

## Phase 7 — Durable reports and PR

Create durable repository reports under:

- `docs/operations/reviews/` for implementation and blocking-review evidence;
- `docs/operations/validation/` for each live attempt and final successful validation.

Reports must include:

- starting main commit;
- branch and commits;
- production path reconciled;
- source-of-truth matrix;
- defects found and corrections made;
- schemas and public symbols;
- lifecycle IDs;
- exact authority and decision references;
- exact PTM resolution and digest;
- Dispatch and handoff results;
- configured and actual provider/model;
- provider invocation count;
- artifact and receipt paths and hashes;
- completion, reconciliation, and Grace final state;
- institutional acceptance state;
- tests and validation totals;
- local evidence paths without committing raw machine-local evidence;
- preservation checks;
- remaining limitations;
- exact next Steward action.

Do not commit raw `A:\AI` runtime directories, caches, temporary worktrees, staging directories, secrets, or unrestricted logs.

Commit implementation, tests, schemas, documentation, and appropriate canonical evidence on:

`engineering/complete-governed-engineering-first-live-task`

Push normally without force.

Open one draft PR against `main` for the complete campaign.

Keep it draft and unmerged.

Do not enable auto-merge.

PR #503 remains a historical failed-preflight report. Do not rewrite it to represent the successful campaign.

## Completion criteria

This work package is complete only when all of the following are true:

1. the provider-neutral and Qwen-specific execution contracts are complete and closed;
2. every required field has a canonical owner and traceable path;
3. no arbitrary caller metadata can create authority;
4. production construction uses the corrected path;
5. no technical execution bypass remains;
6. automated fake-adapter end-to-end execution succeeds exactly once;
7. one real governed `qwen3:8b` invocation succeeds;
8. the exact Markdown artifact is published create-once;
9. the exact provider receipt is published create-once;
10. artifact and receipt hashes validate;
11. Engineering completion and reconciliation succeed;
12. Grace reaches completed terminal state;
13. institutional acceptance remains `not_granted`;
14. source, schemas, tests, and durable reports are committed and pushed;
15. draft PR is open and ready for blocking review;
16. worktree is clean;
17. all 16 stashes remain;
18. `A:\theestate` remains untouched;
19. no model was downloaded or changed;
20. historical Qwen evidence and failed validation evidence remain unchanged.

A report that merely identifies the next missing field does not satisfy this work package.

## Conditions that require a Steward stop

Stop and return for a new Steward decision only if the required correction would:

- create or replace a canonical authority owner;
- change institutional acceptance policy;
- add a second queue, scheduler, provider registry, or PTM authority;
- grant Qwen shell, coding, merge, or broad repository authority;
- require downloading or changing a model;
- require modifying `A:\theestate`;
- require destructive migration or rewriting historical canonical records;
- require more than three live provider invocations;
- reveal that the intended lifecycle architecture itself cannot support the required task without redesign outside this package.

Otherwise, continue the campaign to a successful first live task.

## Final Codex response

Return one consolidated final report containing:

- starting and final HEAD;
- all commits;
- draft PR number;
- files changed;
- source-of-truth matrix path;
- defects corrected;
- schemas and contracts added or changed;
- production path and bypass-search result;
- automated test totals;
- live attempt count;
- all final lifecycle IDs;
- configured and actual model;
- artifact and receipt paths and SHA-256 values;
- Engineering completion and reconciliation result;
- Grace terminal receipt and final state;
- institutional acceptance state;
- remaining limitations;
- worktree state;
- stash count;
- model preservation;
- historical-evidence preservation;
- confirmation `A:\theestate` was untouched;
- exact next Steward action.

Do not merge.