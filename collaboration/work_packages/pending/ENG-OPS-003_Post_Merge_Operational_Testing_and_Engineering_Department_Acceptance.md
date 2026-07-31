# ENG-OPS-003 — Post-Merge Operational Testing and Engineering Department Acceptance

Status: **AUTHORIZED AFTER PR #504 MERGE**  
Owner: Office of the Steward  
Execution environment: `A:\theestate-wp4233`  
Repository: `ppow1/theestate`  
Date authored: 2026-07-31

## Purpose

PR #504 and ENG-OPS-001 prove that one real governed Engineering task can complete through the full production lifecycle. That is necessary, but it is not enough to declare the Engineering Department dependable.

This campaign tests repeatability, routing, failure truthfulness, authority preservation, idempotency, and operator usability after the ENG-OPS-001 implementation is merged into `main`.

The campaign is complete only when the merged production system demonstrates that it can:

1. complete multiple fresh authorized tasks;
2. select the correct worker for materially different work;
3. refuse work when capability or authority is absent;
4. fail truthfully when evidence, provider health, paths, or outputs are invalid;
5. avoid duplicate commissions, queue entries, provider calls, and completions;
6. preserve the complete Grace/Helen/PTM/Engineering/Dispatch/provider evidence chain;
7. operate from a realistic Steward request rather than a purpose-built fixture;
8. produce a durable acceptance report supporting an explicit Steward decision on broader governed use.

Institutional acceptance is not automatically granted by this campaign. The final decision remains with the Steward.

## Preconditions

Do not begin until all are true:

- PR #504 is merged into `main`;
- local `main` is fast-forwarded to `origin/main`;
- any separately installed Engineering Worker Runtime is synchronized from merged `main` when the repository contract requires it;
- the worktree is clean;
- all existing stashes are preserved;
- `A:\theestate` remains untouched;
- `qwen3:8b` is still available through the configured loopback endpoint;
- the historical Qwen demonstration and ENG-OPS-001 evidence remain unchanged;
- no test reuses lifecycle IDs, artifact paths, receipt paths, authorization records, decisions, or Dispatch records from earlier runs.

If PR #504 is not merged, stop without performing tests.

## Branch

Create a fresh branch from updated `main`:

`operations/engineering-department-operational-test-campaign`

Do not run the campaign from an old implementation or validation branch.

## Production-only rule

Use the actual merged production construction and registered provider paths.

Do not use:

- fake PTM resolvers;
- fake providers for live scenarios;
- test-only adapter injection;
- always-ready fixtures;
- direct Ollama generation calls;
- direct Codex invocation as a substitute for Dispatch;
- manually edited readiness, authorization, decision, Dispatch, completion, or Grace records;
- broad repository read or write authority.

Fake providers may be used only in automated regression tests that accompany a proven source correction. They do not satisfy a live operational scenario.

## Runtime synchronization and preflight

Before the first scenario:

1. record merged `main` HEAD;
2. identify every installed runtime copy used by Engineering execution;
3. synchronize only through canonical repository scripts;
4. verify source/destination hashes when synchronization occurs;
5. verify Grace, Residential Gateway, Ollama, and any required local service endpoints without modifying them;
6. confirm the provider catalog, provider configuration, schemas, and installed runtime agree on provider and adapter identities;
7. confirm `qwen3:8b` is present without downloading or updating it;
8. run the focused post-merge automated matrix before live execution;
9. record all pre-existing failures separately and reproduce them against merged `main` before labeling them unrelated.

## Scenario set

Each scenario must use fresh identifiers and fresh create-once paths. Every live provider call must be counted. No scenario may silently retry with the same paths.

### Scenario 1 — Repeated Qwen documentation success

Submit a new realistic Steward request through Grace for a bounded documentation task materially different from the ENG-OPS-001 artifact.

The task should require:

- `documentation_draft`;
- `text_generation`;
- bounded reads of two exact repository files;
- one exact Markdown artifact;
- one exact provider receipt.

Required result:

- Helen selects `qwen.local.text` based on fresh evidence;
- PTM returns `ready`;
- Engineering, authorization, Operations decision, Dispatch, handoff, provider invocation, artifact, receipt, completion, reconciliation, and Grace closure all succeed;
- actual model is `qwen3:8b`;
- exactly one live provider call occurs;
- institutional acceptance remains `not_granted`.

### Scenario 2 — Provider routing to Codex

Submit a bounded repository implementation or code-review task whose required capability is not authorized for Qwen but is authorized for `codex.execution.cli`.

Use a harmless, isolated task such as creating or correcting a small test fixture or documentation validator in a fresh bounded branch/worktree.

Required result:

- Helen does not select Qwen;
- the provider catalog and Engineering select `codex.execution.cli`;
- exact read/write scope is preserved;
- the registered Codex adapter executes once;
- artifact/receipt or implementation result is validated according to the Codex contract;
- no Qwen invocation occurs;
- no merge occurs during the test campaign.

If a safe live Codex test cannot be performed without consuming unrelated user work or broad authority, stop this scenario and record the exact authority needed. Do not substitute a fake provider and call the live scenario passed.

### Scenario 3 — Capability gap and enabling-project proposal

Submit a request requiring a capability that no registered, qualified, healthy, available, and authorized provider currently possesses.

Use a clearly bounded synthetic capability that does not accidentally match Qwen or Codex.

Required result:

- Helen returns a truthful capability gap;
- no Engineering execution commission for the original task is created;
- no Dispatch or provider invocation occurs;
- the lifecycle produces the canonical worker-specification or enabling-project proposal path already established by the capability-enablement architecture;
- Grace receives the correct waiting/proposal state;
- no adapter is automatically invented or registered.

### Scenario 4 — Stale evidence blocks before execution

Create or use a controlled test setup where otherwise valid provider health, availability, authorization, or PTM readiness evidence is expired under the canonical freshness policy.

Required result:

- the stale evidence is detected by the canonical authority owner;
- no provider invocation occurs;
- no artifact or receipt is published;
- the exact stale field, timestamp, policy, and rejection stage are durably recorded;
- retry requires newly generated evidence and fresh output paths.

Do not alter the canonical freshness policy merely to manufacture this result.

### Scenario 5 — Prohibited scope fails closed

Submit a technical request containing one intentionally prohibited scope condition, such as:

- repository-root read scope;
- parent-directory write scope;
- absolute path;
- traversal path;
- output path outside the authorized namespace;
- mismatched provider receipt path.

Required result:

- the earliest responsible authority boundary rejects it;
- no queue item capable of execution is published;
- no provider is invoked;
- no partial artifact or receipt exists;
- rejection evidence is create-once, bounded, schema-valid, and correlated.

### Scenario 6 — Provider failure and truthful evidence

Run one authorized Qwen request through a controlled, reversible provider-failure condition that does not modify the model or service installation. Examples include a deliberately unreachable per-request endpoint only if the adapter contract safely permits a test override, or a bounded request configuration guaranteed to fail before generation.

Do not stop or reconfigure the shared Ollama service in a way that disrupts unrelated work.

Required result:

- authority validation succeeds up to the provider boundary;
- the provider execution fails truthfully;
- no false artifact is accepted;
- failure receipt or retained staging evidence follows the merged Qwen transaction contract;
- Engineering completion is not falsely granted;
- Grace receives the correct failed or blocked state;
- the service is left unchanged after the test.

If no safe production-supported failure injection exists, record that as a testability gap rather than adding an ad hoc bypass during the campaign.

### Scenario 7 — Idempotency and replay

Repeat an equivalent previously successful request through the canonical operational entry point using the same idempotency identity where the contract calls for replay, without manually reusing create-once output paths outside the contract.

Required result:

- no duplicate Grace objective/action where canonical replay requires reuse;
- no duplicate Engineering commission;
- no duplicate authorization or Operations decision;
- no duplicate Dispatch queue item;
- no second provider invocation;
- no duplicate artifact, receipt, completion, or Grace terminal receipt;
- equivalent replay returns the existing truthful result;
- conflicting replay fails closed.

### Scenario 8 — Realistic Steward-to-Grace request

Run one end-to-end request using the actual Steward-facing Grace command or natural-language intake surface intended for routine use, not a developer fixture assembled record by record.

The task should be a useful, bounded repository documentation request.

Required result:

- the request is interpreted by Grace;
- Helen and PTM operate through canonical production construction;
- Engineering and Dispatch require no manual record surgery;
- a registered provider executes once;
- the result is placed at the location directed by Grace;
- Grace reports completion through the intended operator surface;
- the entire evidence chain is traceable.

If the Estate does not yet expose a usable Steward-facing entry point for this path, that is a blocking operational finding. Identify the exact missing public entry point and smallest correction required.

## Continuous checks across all scenarios

For every scenario record:

- objective and requested outcome;
- exact runtime entry point;
- all lifecycle IDs;
- capability requirements;
- Helen assessment and fresh evidence;
- PTM resolution, high-watermark, policy, registry, and expiry;
- Engineering commission and authorization;
- Operations decision;
- Dispatch and queue result;
- provider and adapter selection;
- configured and actual model where applicable;
- provider invocation count;
- artifact and receipt paths and SHA-256 values;
- validation and reconciliation result;
- Grace final state;
- institutional acceptance state;
- local evidence paths;
- source changes, if any;
- preservation checks.

After each scenario confirm:

- worktree changes are understood;
- no historical evidence changed;
- no model was downloaded or modified;
- `A:\theestate` remains untouched;
- stashes remain preserved;
- no background process or test runner was accidentally left running;
- any generated tracked timestamp/readiness artifacts are either canonical evidence or restored.

## Source-correction authority

This campaign is primarily testing, but it is authorized to correct genuine production defects exposed by the scenarios when all are true:

- the defect is within the merged Engineering execution lifecycle;
- the correction preserves existing authority boundaries;
- the correction does not create a second scheduler, queue, registry, readiness resolver, or execution system;
- a regression test is added;
- the failed scenario is rerun with fresh lifecycle IDs and fresh output paths;
- no institutional acceptance is granted by code.

Do not stop merely to report a correctable missing field or missing propagation seam.

Stop and request Steward authority only when correction would require:

- a new institutional policy;
- materially broader provider authority;
- registration of a new provider or adapter;
- destructive service or model modification;
- a new external dependency or credential;
- an architectural replacement rather than connection or repair;
- access to user data or repositories outside the authorized Estate scope.

## Retry budget

Each failed live scenario may be retried up to three times after source correction.

Every retry must use:

- fresh lifecycle IDs;
- fresh create-once artifact and receipt paths;
- fresh evidence timestamps;
- a clear link to the failed attempt and correction commit.

Do not overwrite or rewrite failed operational evidence.

## Automated validation

Run a bounded but comprehensive changed-scope matrix including:

- Grace lifecycle and natural-language intake tests;
- Helen capability and capability-gap tests;
- PTM readiness, freshness, waiver, replay, and high-watermark tests;
- Engineering commission, authorization, completion, and reconciliation tests;
- Dispatch authorization, queue, rejection, and idempotency tests;
- adapter handoff and authority-schema tests;
- provider catalog and health tests;
- Qwen adapter tests without duplicating live calls;
- Codex adapter tests without duplicating live calls;
- runtime synchronization tests where applicable;
- Draft 2020-12 schema validation with FormatChecker;
- Python compilation;
- tracked JSON parsing;
- `git diff --check`.

The full suite may be attempted, but timeout is neither pass nor failure. Record progress and restore unrelated generated artifacts.

## Required durable reports

Create and commit:

1. `docs/operations/reviews/ENG-OPS-003_Operational_Test_Plan_and_Traceability_<date>.md`
2. `docs/operations/validation/ENG-OPS-003_Operational_Test_Results_<date>.md`
3. `docs/operations/reviews/ENG-OPS-003_Engineering_Department_Acceptance_Recommendation_<date>.md`

The acceptance recommendation must distinguish:

- implementation correctness;
- operational repeatability;
- governance correctness;
- provider-routing correctness;
- failure truthfulness;
- operator usability;
- known limitations;
- institutional acceptance recommendation.

Do not commit unrestricted raw machine-local logs, caches, temporary worktrees, staging directories, secrets, or model data.

## Completion criteria

ENG-OPS-003 is complete when:

- every safely executable scenario has a durable pass/fail result;
- all in-scope correctable blockers have been corrected and retested;
- at least two separate live successful tasks have completed after PR #504 merge;
- at least one non-execution capability-gap scenario passed;
- at least one stale/authority/scope rejection passed without provider invocation;
- idempotency proves no duplicate provider execution;
- the realistic Steward-facing request either completes or yields a precisely documented public-entry-point blocker;
- all evidence is committed and pushed;
- a draft PR is opened against `main`;
- the final recommendation clearly states whether broader governed Engineering use should be accepted, conditionally accepted, or rejected.

## Merge boundary

Do not merge the ENG-OPS-003 PR.

Do not enable auto-merge.

Do not grant institutional acceptance automatically.

Return the final recommendation and PR to the Steward for decision.

## Final report

Report:

- merged starting main HEAD;
- branch and final HEAD;
- runtime synchronization result;
- each scenario and disposition;
- all live provider invocation counts;
- all lifecycle IDs and evidence paths;
- source corrections and commits;
- complete automated validation totals;
- pre-existing failures and base/head reproduction;
- historical evidence preservation;
- model preservation;
- stash count;
- worktree state;
- confirmation `A:\theestate` remained untouched;
- draft PR number;
- acceptance recommendation;
- exact next Steward action.
