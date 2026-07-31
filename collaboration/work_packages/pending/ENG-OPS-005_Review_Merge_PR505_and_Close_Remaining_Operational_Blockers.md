# ENG-OPS-005 — Review, Merge PR #505, and Close Remaining Engineering Operational Blockers

Status: **AUTHORIZED FOR CODEX EXECUTION**  
Owner: Office of the Steward  
Repository: `ppow1/theestate`  
Execution environment: `A:\theestate-wp4233`  
Date authorized: 2026-07-31

## Steward intent

ENG-OPS-003 proved that bounded Qwen documentation work can complete repeatedly through the governed Engineering lifecycle, but broader Engineering Department acceptance remains blocked by three operational gaps:

1. Codex technical routing is blocked by prompt-source/profile policy.
2. The Steward-facing Grace CLI cannot complete a technical Engineering handoff without manual record construction.
3. There is no safe production-supported provider-failure injection seam for deterministic operational testing.

This work package is intentionally broader than another narrow one-field repair. Its objective is to review and merge PR #505 if safe, then close all three remaining blockers and prove the resulting department through fresh governed operational tests.

The campaign is complete only when:

- PR #505 has received a blocking review and, if clean or corrected, is merged normally;
- Codex can be selected and invoked through the governed path for one bounded repository task without bypassing prompt, profile, PTM, Dispatch, or adapter authority;
- the Steward-facing command surface can accept a realistic technical request and drive the complete Grace → Helen → PTM → Engineering → Dispatch → provider lifecycle without manual record surgery;
- a safe deterministic provider-failure injection mechanism exists and proves truthful failure handling without altering shared Ollama state or weakening production authority;
- fresh end-to-end success and failure evidence is durable, correlated, schema-valid, and replay-safe;
- the final report gives an evidence-backed acceptance recommendation for bounded Qwen and Codex Engineering use.

## Starting foundation

- PR #504 merged at `35d52c6520ffd7c5051b82a02402d19bf1f49460`.
- PR #505 is open, draft, mergeable, targets `main`, and currently points to `8c5fa87f85bdcc75f34901470dd3f1fc21528b9b`.
- PR #505 reports 236 passing tests, two fresh successful Qwen tasks, truthful negative scenarios, and conditional Qwen-only acceptance.
- Institutional acceptance remains `not_granted`.

## Phase 1 — Blocking review and disposition of PR #505

Perform a complete blocking review of PR #505.

Review every changed source, schema, test, runtime record, generated artifact, and report. Attempt to disprove:

- the two successful Qwen lifecycle claims;
- the replay/idempotency correction;
- provider-neutral authority preservation;
- truthful capability-gap, stale-PTM, prohibited-scope, and content-failure behavior;
- the claim that Codex, Steward CLI, and provider-failure injection remain the only material blockers.

Correct all in-scope defects on the PR #505 branch, add regression coverage, update durable reports, and rerun bounded validation.

If PR #505 is safe after review:

1. mark it ready for review;
2. merge it normally into `main` using an explicit merge commit;
3. synchronize local main and any installed Engineering runtime copy if needed;
4. run post-merge smoke validation.

Do not merge if a genuine unresolved blocker remains.

## Phase 2 — Codex governed routing closure

Trace and correct the production Codex path end to end.

Required outcome:

A fresh Grace technical request requiring bounded repository implementation or documentation selects `codex.execution.cli`, passes Helen and PTM authority, creates the Engineering commission and authorization, reaches Dispatch and the canonical adapter handoff, invokes the registered Codex CLI adapter exactly once, produces declared bounded outputs and receipt evidence, reconciles successfully, and returns a truthful Grace terminal state.

Requirements:

- preserve the canonical prompt source and digest;
- define the permitted prompt-source namespace explicitly rather than broadening to arbitrary runtime files;
- define and enforce the authorized Codex profile rather than accepting an implicit default;
- preserve exact read/write/output scopes;
- preserve sandbox and approval requirements;
- keep provider selection, adapter identity, health, capacity, and authorization evidence explicit;
- reject old or incomplete technical records;
- do not create a direct Grace-to-Codex bypass;
- do not weaken the Qwen path.

Use one harmless bounded task, such as creating or correcting one small validation Markdown file or one isolated test fixture, with fresh create-once paths.

## Phase 3 — Steward-facing complete technical intake

Extend the existing `estate grace-operations conduct` or the canonical Steward command surface so that a real operator request can supply or resolve all information needed for a governed technical handoff.

The command surface must support, directly or through a canonical referenced request file:

- requested outcome;
- required capabilities;
- exact authorized read paths;
- exact authorized write paths;
- exact expected outputs;
- artifact type;
- provider restrictions when explicitly authorized;
- classification and sandbox;
- validation criteria;
- prompt source and immutable digest;
- linkage to Grace objective/action;
- fresh Helen assessment;
- PTM readiness resolution;
- Engineering commission and authorization;
- Operations decision;
- Dispatch and adapter handoff.

The public command must fail closed when required information is missing or unsafe. It must never synthesize broad authority, skip PTM, manually force a provider, or grant institutional acceptance.

Prove the command using one fresh realistic Steward request that reaches a registered provider and completes without manual runtime record surgery.

## Phase 4 — Safe provider-failure injection

Implement a deterministic, production-safe test seam for provider failure behavior.

The seam must:

- be disabled by default;
- require explicit test/validation authority;
- be scoped to one commission or adapter request;
- never mutate shared Ollama service state, model state, provider catalog state, or global configuration;
- support at least transport failure, timeout, malformed response, and declared provider failure;
- remain inaccessible to normal production requests;
- produce truthful failure receipts and transaction states;
- prevent artifact acceptance, Engineering completion, and Grace success;
- preserve replay/idempotency and create-once evidence.

Prefer an injected transport/runtime seam already consistent with adapter architecture. Do not add a second provider registry or direct provider call path.

Run at least one governed failure scenario through the complete lifecycle and prove:

- provider invocation attempted exactly once;
- no successful artifact is accepted;
- failure receipt is durable and schema-valid;
- Engineering reconciliation records failure truthfully;
- Grace reaches the correct failed or blocked terminal state;
- institutional acceptance remains `not_granted`.

## Phase 5 — Final operational campaign

After implementing the three closures, run a fresh operational matrix with new IDs and paths:

1. Qwen bounded documentation success.
2. Codex bounded repository task success.
3. Realistic Steward command-surface request success.
4. Deterministic provider transport failure.
5. Provider timeout failure.
6. Capability gap.
7. Stale PTM evidence.
8. Prohibited scope.
9. Equivalent replay with no duplicate provider call.
10. Conflicting replay rejection.

Do not reuse prior artifacts, receipts, lifecycle IDs, or output paths.

## Source changes and correction authority

Codex is authorized to correct all defects necessary to complete this work package, provided it preserves the existing authority boundaries and does not introduce:

- a second scheduler or queue;
- a second provider catalog;
- direct Grace-to-provider invocation;
- automatic institutional acceptance;
- unrestricted repository access;
- hidden default authority;
- shared-service mutation for tests.

Continue through correctable blockers. Do not stop merely to report the next missing field.

Stop only when a required decision genuinely changes Steward authority, institutional acceptance policy, provider trust policy, or architecture outside these boundaries.

## Validation requirements

Run all affected tests, including:

- Grace, Helen, PTM, Engineering, Operations decision, Dispatch, queue, and handoff tests;
- Qwen and Codex adapter tests;
- provider catalog and provider runtime tests;
- Steward command-surface tests;
- failure injection tests;
- completion and reconciliation tests;
- replay/idempotency/concurrency tests;
- Draft 2020-12 schema validation with FormatChecker;
- Python compilation;
- tracked JSON parsing;
- `git diff --check`.

Reproduce known baseline failures on base and head before classifying them as unrelated.

## Durable reports

Create and commit:

- `docs/operations/reviews/ENG-OPS-005_PR505_Blocking_Review_20260731.md`;
- `docs/operations/reviews/ENG-OPS-005_Remaining_Blockers_Closure_20260731.md`;
- `docs/operations/validation/ENG-OPS-005_Final_Operational_Test_Results_20260731.md`;
- `docs/operations/reviews/ENG-OPS-005_Engineering_Department_Acceptance_Recommendation_20260731.md`.

Reports must contain exact commits, lifecycle IDs, paths, hashes, invocation counts, failures, corrections, tests, preservation checks, and the final acceptance recommendation.

Do not commit raw machine-local logs, caches, temporary worktrees, or unrestricted `A:\AI` evidence.

## Branching and PRs

- Review and correct PR #505 on its existing branch.
- After merging #505, create a fresh branch:
  `engineering/close-remaining-operational-blockers`
- Commit and push all Phase 2–5 work there.
- Open one draft PR against `main`.
- Keep it draft until blocking review is complete.
- Do not merge the final implementation PR without separate Steward authorization.

## Preservation

- Preserve all existing stashes.
- Leave `A:\theestate` untouched.
- Do not download, replace, or modify any model.
- Do not alter historical Qwen or Codex evidence.
- Do not grant institutional acceptance.
- Use the same Codex CLI session.

## Final completion criteria

Report:

- PR #505 review and merge disposition;
- post-merge main commit;
- Codex routing result and live invocation count;
- Steward command-surface result;
- failure-injection design and governed failure results;
- all fresh lifecycle IDs and evidence paths;
- Qwen and Codex artifact/receipt hashes;
- replay and scope results;
- complete test totals;
- final branch/HEAD and draft PR;
- worktree/stash/model/A:\theestate preservation;
- final Engineering Department acceptance recommendation;
- exact next Steward action.

Do not merge the final implementation PR.