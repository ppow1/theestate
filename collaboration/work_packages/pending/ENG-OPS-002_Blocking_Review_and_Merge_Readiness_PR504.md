# ENG-OPS-002 — Blocking Review, Correction, and Merge Readiness for PR #504

Status: **AUTHORIZED FOR CODEX EXECUTION**  
Owner: Office of the Steward  
Execution environment: `A:\theestate-wp4233`  
Repository: `ppow1/theestate`  
Date authorized: 2026-07-31

## Purpose

PR #504 claims that the Estate Engineering Department has completed its first full governed live task through:

`Grace → Helen → PTM → Engineering → Dispatch → canonical adapter handoff → registered qwen.local.text provider → artifact and receipt → Engineering completion/reconciliation → Grace terminal completion`.

This work package is the final blocking review and correction campaign for that claim.

This is not a summary pass. Codex must attempt to disprove the implementation, evidence chain, and completion claim. If a blocking defect exists inside PR #504 scope, Codex is authorized to correct it on the same branch, add regression coverage, rerun the bounded validation matrix, update the durable reports, and continue until the PR is genuinely merge-ready.

The campaign is complete only when either:

1. PR #504 is proven merge-ready with no remaining blocking finding and is marked ready for review, but not merged; or
2. a genuine Steward-only authority or architecture decision outside the boundaries below prevents a safe correction.

Do not stop merely to report a correctable defect.

## Current state

Pull request: `#504`  
Branch: `engineering/complete-governed-engineering-first-live-task`  
Expected starting HEAD: `c85801c37a2501cb304472adf15417aea8d0e2d7`  
Base main at campaign start: `c3d5f3990e86123d5623462c03e5c39be3d50aec`

Claimed successful lifecycle:

- Grace objective: `grace-obj-fe51924664ec`
- Grace action: `grace-act-62204acc9560`
- Capability inquiry: `capreq-49d95aa6f603`
- Helen assessment: `heldet-7141829d2859`
- PTM resolution: `res_01KYX0K9FCK79MNY9MNGRXCHJM`
- Engineering commission: `engcom-abe0b75fc0e0`
- Engineering authorization: `engauth-630a7485650d`
- Operations decision: `opdec-630a7485650d5e196eb753ac`
- Dispatch: `dispatch-5e196eb753ac`
- Adapter request: `adapter-dispatch-5e196eb753ac`
- Engineering completion: `engcomp-8b4124134893`
- Grace receipt: `gracereceipt-5bbae355f02a`
- Provider: `qwen.local.text`
- Adapter: `qwen-local-ollama-text-adapter@1.0.0`
- Configured and actual model: `qwen3:8b`
- Live invocation count: exactly one
- Grace final state: `completed`
- Institutional acceptance: `not_granted`

Claimed outputs:

- Artifact: `docs/operations/validation/Qwen_First_Live_Task_6561985c223d405c8c9b1d41562af5fb.md`
- Artifact SHA-256: `8a859cdd6767ee64d88ab2836faf684e5f1469541a11af5b341806b29bdfc93b`
- Provider receipt SHA-256: `82bc18bd3119917f18a561222e8c03c78271bf88a147ea4cb1ddef5b03545677`

Durable reports:

- `docs/operations/reviews/ENG-OPS-001_Source_of_Truth_Matrix_20260731.md`
- `docs/operations/reviews/ENG-OPS-001_Implementation_Closure_20260731.md`
- `docs/operations/validation/Qwen_First_Live_Task_6561985c223d405c8c9b1d41562af5fb_20260731.md`

## Preparation

1. Fetch origin.
2. Confirm the active worktree is `A:\theestate-wp4233`.
3. Switch to `engineering/complete-governed-engineering-first-live-task`.
4. Pull or fast-forward from the matching remote branch.
5. Confirm HEAD is the current PR #504 head.
6. Confirm the worktree is clean.
7. Confirm all 16 stashes remain.
8. Confirm `A:\theestate` is not modified by this work.
9. Confirm PR #504 remains open, draft, unmerged, and targets `main` before review starts.

## Review standard

Review the complete diff, all changed production files, all changed schemas, all changed tests, every durable report, all live lifecycle records, the generated artifact, provider receipt, Engineering completion, reconciliation record, and Grace terminal receipt.

Do not accept a claim merely because a report says it passed.

Recalculate hashes, reload canonical records, validate schemas, retrace correlations, and inspect the actual production call graph.

## Blocking review areas

### 1. Production-path authenticity

Prove that the live execution used the real production path and not a test seam, fixture, direct Ollama generation, arbitrary injected adapter, manually fabricated record, or bypass.

Trace the exact call chain through:

- `GraceHelenEngineeringComposition`;
- `governed_commission_and_dispatch()`;
- PTM production resolver and projection;
- Engineering authorization writer;
- Operations decision writer;
- canonical Dispatch queue;
- `prepare_handoff()`;
- registered provider lookup;
- `run_registered_handoff_adapter()` or canonical equivalent;
- `qwen.local.text` adapter;
- result validation;
- reconciliation;
- Engineering completion;
- Grace completion receipt.

Search for alternate production entry points that could bypass any authority stage.

### 2. Live invocation proof

Prove exactly one real Qwen generation request occurred.

Validate available durable evidence for:

- endpoint identity;
- provider identity;
- adapter identity and version;
- configured model;
- actual model returned;
- request identity;
- Dispatch identity;
- invocation count;
- timing;
- provider result;
- receipt publication.

Ensure no direct Ollama generation was used outside the adapter and no second invocation occurred during retries, validation, or report generation.

### 3. Canonical metadata and source-of-truth ownership

Audit every field in `ENG-OPS-001_Source_of_Truth_Matrix_20260731.md` against actual production code and records.

Verify the canonical owner and propagation path for:

- requested capability;
- qualification;
- availability;
- capacity;
- authorization;
- provider health;
- provider identity;
- adapter identity/version;
- model identity;
- prompt source/type/digest;
- exact read scope;
- exact write scope;
- exact expected outputs;
- artifact path;
- provider receipt path;
- PTM readiness and digest;
- Engineering commission;
- Engineering authorization;
- Operations decision;
- Dispatch;
- adapter request;
- provider receipt;
- completion and reconciliation.

Any field derived from arbitrary caller metadata rather than canonical authority is blocking.

### 4. Qwen execution extension

Review the closed Qwen execution extension and every consumer.

Confirm it binds at minimum:

- requested capability;
- evidence observed time;
- evidence expiry time;
- provider-health evidence reference and digest;
- authorized model identity;
- provider receipt path;
- provider ID;
- adapter ID/version;
- exact artifact path;
- exact read/write/output scopes;
- Grace/Helen/PTM/Engineering/Dispatch correlations.

Confirm:

- schemas are closed;
- no arbitrary additional metadata can broaden authority;
- unsupported provider-specific metadata fails closed;
- extension identity/version is required;
- stale or mismatched evidence fails closed;
- receipt path is an exact authorized output;
- model identity cannot be changed downstream;
- historical incomplete technical records remain non-executable.

### 5. Prompt and scope integrity

Recalculate the canonical Grace action digest and verify the final adapter request used those exact bytes.

Confirm:

- only authorized read files were exposed;
- no directory-wide or repository-wide read was granted;
- only exact artifact and receipt paths were writable;
- expected outputs match the governed request;
- all paths are repository-relative;
- absolute, traversal, symlink, and reparse escapes are rejected;
- scopes did not broaden between Grace, commission, authorization, decision, Dispatch, and adapter request.

### 6. PTM readiness integrity

Reload and validate the exact PTM readiness resolution and projection.

Confirm:

- ledger chain is valid;
- source high-watermark matches;
- policy identity/version/digest match canonical policy;
- waiver registry identity/version/digest match canonical registry;
- readiness was `ready`, not inferred from provider availability;
- evidence was fresh at commission and Dispatch boundaries;
- final handoff revalidated current readiness;
- no waiver was fabricated;
- no changed or contradictory event invalidated the resolution before execution.

### 7. Authorization and Operations decision

Validate the exact Engineering authorization and Operations decision using their closed Draft 2020-12 schemas and `FormatChecker`.

Recalculate canonical digests.

Confirm complete correlation across:

- Grace objective/action;
- Helen assessment;
- PTM resolution;
- Engineering commission;
- authorization;
- Operations decision;
- Dispatch;
- provider;
- adapter;
- prompt digest;
- read/write/output scopes;
- Qwen extension;
- expiry;
- institutional acceptance state.

Any missing, copied-but-unverified, stale, or contradictory authority is blocking.

### 8. Dispatch and queue integrity

Confirm:

- Dispatch was authorized only after PTM readiness;
- Engineering authorization was durable before Dispatch referenced it;
- Operations decision was durable before handoff;
- queue insertion occurred exactly once;
- no duplicate or conflicting queue item exists;
- final revalidation occurred at the authorization boundary;
- queue evidence binds the exact PTM, authorization, decision, scopes, provider, adapter, and extension;
- retries cannot silently reuse stale evidence;
- concurrent replay remains idempotent and conflict-safe.

### 9. Adapter handoff integrity

Load the durable adapter request.

Validate:

- schema identity/version;
- complete closed authority structures;
- exact request ID;
- exact Dispatch ID;
- provider/adapter match;
- prompt digest;
- scope arrays;
- expected outputs;
- Qwen extension;
- authorization and decision references/digests;
- PTM reference/digest;
- create-once publication;
- no partial or stale prior request was reused.

Confirm the registered adapter runtime, not an arbitrary injected adapter, consumed the request.

### 10. Artifact quality and truthfulness

Review the generated Markdown artifact itself, not only its hash.

Confirm it satisfies the commission exactly and does not contain misleading or unauthorized claims.

Specifically examine:

- whether `Generated by: Grace` is truthful or falsely attributes provider output to Grace;
- whether `Owner: Operations` is authorized and accurate;
- whether references to a “provided JSON structure” or “proposal” misstate the actual prompt context;
- whether the closing phrase `Let me know if further adjustments are needed!` is acceptable in a governed artifact or indicates uncontrolled conversational residue;
- whether the artifact accurately states capabilities, restrictions, model identity, and institutional acceptance;
- whether it exposes hidden prompt content or unrelated repository material;
- whether formatting, content, and classification meet the requested output contract.

A technically successful invocation with materially misleading output is not a successful Engineering completion.

If content defects are correctable only by rerunning the live commission, do not silently edit the generated artifact. Preserve historical evidence, create a fresh governed retry with new IDs and output paths, and validate the new result. Do not exceed two additional live invocations during this review campaign.

### 11. Artifact and receipt integrity

Recalculate the artifact SHA-256 and provider receipt SHA-256.

Validate the provider receipt against its contract and confirm:

- artifact path and digest match actual bytes;
- provider, adapter, model, request, Dispatch, Grace, Helen, PTM, Engineering, authorization, and decision references match;
- success status is truthful;
- no full prompt or secret is retained;
- timestamps are coherent;
- output paths were create-once;
- no collision or orphan state occurred;
- staging/publication state is truthful;
- receipt itself was not modified after publication.

### 12. Completion and reconciliation integrity

Reload Engineering validation, reconciliation, completion, and Grace receipt records.

Confirm:

- completion required both artifact and valid provider receipt;
- artifact existed at validation time;
- receipt hash matched;
- reconciliation references the same Dispatch and readiness evidence;
- completion was created once;
- conflicting replay fails closed;
- Grace completed only after Engineering completion;
- institutional acceptance remained `not_granted`;
- no component retroactively granted readiness or authority;
- a later source change would not rewrite historical truth.

### 13. Persistence and concurrency safety

Review every new write path introduced by PR #504.

Confirm use of canonical create-once and durable persistence behavior:

- complete writes;
- short-write handling;
- flush;
- fsync;
- close;
- parent-directory durability where supported;
- repository-root bounding;
- symlink/reparse protection;
- no unsafe overwrite;
- no unsafe rollback;
- equivalent replay idempotency;
- conflicting replay rejection;
- deterministic concurrent-writer tests.

### 14. Schema integrity

Validate all authority schemas with Draft 2020-12 and `FormatChecker`.

Confirm:

- unique `$id` values;
- complete `$ref` resolution from repository and installed-package roots;
- closed authority-bearing objects;
- strict digest patterns;
- safe path patterns;
- required non-null production fields;
- timestamps and expiry;
- no open generic metadata can carry hidden authority;
- Qwen extension is provider-specific without weakening provider-neutral contracts.

### 15. Regression and compatibility

Confirm:

- Codex provider behavior remains valid;
- Qwen historical evidence remains readable and unchanged;
- historical incomplete technical Dispatch remains blocked;
- nontechnical Dispatch remains compatible;
- existing provider-neutral handoff remains usable;
- no duplicate registry, queue, scheduler, readiness engine, or authorization system was introduced;
- no hard-coded live validation IDs or paths remain in production code;
- no test-only hook is reachable through production construction.

### 16. Durable reports

Audit all three ENG-OPS-001 reports for factual accuracy against final repository and runtime evidence.

Correct stale commit references, PR state, paths, hashes, lifecycle IDs, test totals, or claims.

Do not create self-referential report-head correction loops. Use wording that distinguishes the implementation head from later report-only commits.

Create a final blocking-review report:

`docs/operations/reviews/ENG-OPS-002_PR504_Blocking_Review_20260731.md`

The report must include:

- reviewed starting head;
- final head;
- findings;
- corrections;
- live retry count, if any;
- artifact-content assessment;
- evidence-chain assessment;
- tests and validation;
- inherited baseline failures;
- preservation checks;
- PR state;
- exact next Steward action.

## Required deterministic tests

Add regression tests for every corrected defect.

At minimum ensure coverage for:

- canonical Qwen extension propagation;
- arbitrary metadata override rejection;
- stale evidence rejection;
- model mismatch;
- receipt-path mismatch;
- provider-health evidence mismatch;
- final handoff extension revalidation;
- registered-provider-only execution;
- exact invocation count;
- result-evidence schema validity after reconciliation;
- artifact and receipt hash correlation;
- completion gating;
- Grace terminal gating;
- idempotent replay;
- conflicting replay;
- historical technical record blocking;
- test-only adapter seam isolation;
- artifact content contract where deterministic validation is possible.

## Validation matrix

Run a bounded but complete changed-scope matrix covering:

- all ENG-OPS-001 tests;
- Grace/Helen composition;
- PTM production readiness;
- Engineering commission and authorization;
- Operations decisions;
- Dispatch and queue;
- adapter handoff;
- registered provider runtime;
- Qwen adapter without unnecessary extra live invocation;
- Codex adapter regressions;
- result validation;
- completion and reconciliation;
- Grace terminal receipt;
- schema registry;
- Draft 2020-12 and `FormatChecker`;
- Python compilation;
- tracked JSON parsing;
- `git diff --check`;
- worktree status.

Reproduce known baseline failures on base and head before classifying them as unrelated:

- Windows path-separator assertion in `tests/test_execution_result_reconciliation_runtime.py`;
- two malformed JSON fixtures previously identified.

Do not treat a timeout as a pass. Record progress and use a bounded changed-scope matrix if the complete suite is impractical.

## Correction authority

Codex is authorized to correct any blocking defect inside PR #504 scope, including:

- production metadata propagation;
- schemas;
- persistence;
- idempotency;
- validation;
- reconciliation;
- reports;
- provider-neutral runtime compatibility;
- Qwen extension behavior;
- a fresh governed retry if artifact content or execution evidence is invalid.

For every correction:

1. Add regression coverage.
2. Commit on `engineering/complete-governed-engineering-first-live-task`.
3. Push normally without force.
4. Keep PR #504 draft until the final audit passes.
5. Continue the review after correction.

Do not stop to ask the Steward about a correctable implementation defect.

## Steward-stop conditions

Stop only if a required correction would demand one of the following new decisions:

- granting institutional acceptance;
- changing Estate authority ownership;
- adding a new scheduler, queue, provider registry, readiness authority, or authorization system;
- broadening Qwen to shell execution, source implementation, unrestricted reads, arbitrary writes, or merge authority;
- downloading or replacing a model;
- modifying `A:\theestate`;
- exceeding two additional live Qwen invocations during this review campaign.

If stopped, produce a durable report that identifies the exact decision required and why no existing authority resolves it.

## Preservation requirements

- Preserve all 16 stashes.
- Leave `A:\theestate` untouched.
- Do not download, update, or replace any model.
- Do not modify historical Qwen evidence.
- Do not rewrite PR #503 history.
- Do not grant institutional acceptance.
- Do not merge PR #504.
- Do not enable auto-merge.
- Do not open unrelated PRs.
- Do not commit raw machine-local logs, caches, staging directories, or unrestricted `A:\AI` evidence.

## Completion behavior

If no blocking finding remains after corrections and validation:

1. Push the final branch head.
2. Update PR #504 body with final evidence and correct commit/report references.
3. Mark PR #504 ready for review.
4. Do not merge.
5. Return control to the Steward for explicit merge authorization.

## Final report requirements

Report:

- starting and final heads;
- commits added;
- blocking and non-blocking findings;
- corrections made;
- live retry count;
- production-path authenticity;
- exact provider invocation evidence;
- source-of-truth result;
- PTM result;
- authorization/decision result;
- Dispatch/queue result;
- adapter-handoff result;
- artifact content assessment;
- artifact and receipt hashes;
- completion/reconciliation result;
- Grace terminal result;
- institutional acceptance state;
- schema and persistence results;
- regression totals;
- baseline-failure reproduction;
- report path;
- PR status;
- worktree status;
- stash count;
- model preservation;
- historical-evidence preservation;
- `A:\theestate` preservation;
- whether PR #504 was marked ready;
- exact next Steward action.

Do not merge.