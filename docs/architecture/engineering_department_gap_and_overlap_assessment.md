# Engineering Department Gap and Overlap Assessment

**Baseline:** WP-0670 repository observation on 2026-07-16.  
**Rule:** findings are observed; remedies labeled “Proposed” are constraints for later work packages, not production changes in WP-0670.

## 1. Critical gaps

| ID | Observed gap and repository evidence | Consequence | Minimum downstream change (proposed) |
|---|---|---|---|
| G-01 | Campaigns are Markdown contracts in `collaboration/campaigns/`; `operational_campaign_runtime.py` is not an Engineering campaign registry and CAMPAIGN_0550 is hard-coded in `local_engineering_department.py`. | No durable, machine-readable source ties campaign ID, package graph, gate, authority and acceptance state together. | WP-0671 should define a versioned projection/contract referencing the canonical Markdown, not a second campaign queue. |
| G-02 | PTM specifies dependencies/readiness, but current Engineering helpers construct WP-0552 or WP-0649 records directly. | Package identity, readiness, staffing, Dispatch and evidence can drift. | Require the same `campaign_id` and `work_package_id` on all derived records and fail closed on mismatch. |
| G-03 | `governed_provider_scheduler.py`, orchestrator scheduling, PTM scheduling, operations schedulers, and autonomous queue code coexist. | Engineering could accidentally acquire a second scheduler/queue. | Gate B must name one scheduling authority and treat every other surface as an adapter, view, legacy path, or bounded reservation mechanism. |
| G-04 | Provider catalog, routing recommendations, Engineering routing, and scheduler reservations are separate records. | A recommendation can be mistaken for authorization, or health can go stale between routing and dispatch. | WP-0672 must distinguish recommendation, reservation, Dispatch authorization, and live-execution confirmation, with evidence timestamps. |
| G-05 | Package definitions commonly remain under `pending/` while completion receipts exist under both `completed/` and `completions/`. | Directory location and document `Status` are not truthful lifecycle state. | Define a computed status precedence and an immutable transition ledger/reference; do not create another package store. |
| G-06 | Validation recipes, runtime reports, external evidence hashes, PR review, Grace closure and operational readiness cases exist but no campaign evidence manifest binds them. | A reviewer must manually discover whether all evidence belongs to the same package/commit/provider run. | WP-0673 should define a manifest of references and hashes keyed by campaign/package/commit, leaving evidence in canonical stores. |
| G-07 | `operational_readiness_closure.py` begins after merge, while Engineering acceptance is pre-merge and Campaign 0670 forbids merge by Codex. | “Validation passed,” “package accepted,” “merged,” and “operationally ready” can be conflated. | Freeze distinct verdicts and authorities: execution result, validation verdict, integration approval, merge, readiness closure, campaign acceptance. |
| G-08 | Grace records objectives and closures, but campaign gates and dependency unlocks are manual prose. | Routine progress depends on direct Steward/architect prompting even when evidence is already sufficient. | WP-0674 should project next eligible actions from PTM/Dispatch/validation evidence while preserving explicit Chief Architect gates. |
| G-09 | Existing reflection and continuity templates are worker-centric and not keyed to Engineering campaign/package state. | Context, decisions and recovery instructions are lost between execution sessions. | Add an Engineering notebook/continuity view that references existing records and renews at gates; do not create a new mailbox or evidence archive. |
| G-10 | No recovery contract says how to resume after stale reservation, interrupted provider run, invalid evidence, rejected PR, merge conflict, or readiness failure. | Operators may retry unsafely, lose provenance, or bypass Dispatch. | Later contracts must define idempotency keys, retry ownership, preserved attempts, supersession, and escalation for each seam. |
| G-11 | No single status surface explains next action, blocker owner, gate, dependency, provider state, validation state, PR state and continuity link. | Momentum coordination requires repository archaeology. | Produce a read-only aggregated status/notebook view from existing stores; it must never become a second authority. |
| G-12 | Campaign and work-package templates do not require all authority, branch ownership, evidence, provider, and recovery fields. | Different campaigns rely on unwritten conventions. | WP-0671/WP-0672 should define required/optional fields and readiness validation while retaining work packages as the execution unit. |

## 2. Direct Steward-prompt dependency

### Necessary human decisions (must remain)

- approve intent, priority exceptions, and constitutional exceptions;
- provide explicit confirmation where a live provider boundary requires it;
- resolve escalations assigned to Steward authority;
- merge or authorize merge according to repository governance;
- exercise any final institutional authority retained above the Chief Architect.

### Routine prompting that should be removed

- asking someone to rediscover which package is dependency-ready;
- manually copying campaign/package identity between Helen, Grace, Dispatch and validation records;
- asking which provider is healthy/capable when canonical evidence already answers it;
- prompting for evidence collection that can be projected from existing artifact paths;
- prompting Grace to report unchanged status or remind the next accountable office;
- reconstructing an interrupted package from chat instead of a durable continuity record.

The removal mechanism must be deterministic evaluation and governed notifications through PTM/orchestrator, Grace and mailbox seams—not autonomous architecture approval or provider execution.

## 3. Authority conflicts and resolutions required at Gate B

| Conflict | Observed wording/behavior | Gate-B baseline resolution |
|---|---|---|
| Steward vs Chief Architect acceptance | The Engineering charter says Steward retains final institutional authority; Campaign 0670 says Chief Architect retains Engineering architecture and acceptance authority. | For this campaign, Chief Architect owns Engineering package/gate acceptance. Steward retains constitutional/priority/exception and any final institutional authority, not routine Engineering acceptance. Record escalation points explicitly. |
| Grace “objective intake” vs approved Engineering intake | CAMPAIGN_0550 assigns objective intake to Grace; Campaign 0670 says Grace coordinates momentum and cannot approve architecture. | Grace may receive and operationalize an already approved objective. She cannot establish technical readiness, package architecture, or gate acceptance. |
| Helen assignment vs Grace assignment | Helen workforce records can name a worker; Grace objectives also name an owner. | Helen certifies/assigns available personnel to the staffed pool/team; Grace assigns governed operational work only to eligible personnel. |
| Alfred routing vs execution | Alfred runtime offers routing/actions; the charter limits Alfred to coordination. | Alfred may transmit or summarize an authorized action but never becomes package executor, scheduler, or approver. |
| PTM schedule vs Engineering scheduler | PTM plans dependency/readiness; `engineering-scheduler` queues provider reservations. | PTM/orchestrator owns work eligibility and sequencing. Provider reservation may only implement an already eligible assignment and may not enqueue a second work lifecycle. |
| Dispatch completion vs validation/acceptance | Dispatch can be marked complete with a result reference. | Dispatch completion means provider handoff execution ended. It never means validation passed, PR accepted, merge occurred, readiness closed, or campaign accepted. |
| Validation pass vs acceptance | Validation produces pass/fail evidence; closure/controller can advance state. | Validation is an independent verdict. Chief Architect acceptance remains an explicit separate decision. |

## 4. Duplication and overlap register

| Overlap | Classification | Required treatment |
|---|---|---|
| Execution Dispatch vs orchestrator dispatch records vs Grace dispatch requests | Intentional layered seams with duplication risk | Grace requests; orchestrator may create a governed request; `execution_dispatch` remains the executable queue. Use shared IDs/references, not copies of state. |
| PTM/orchestrator scheduling vs Engineering provider scheduler vs operations/autonomous schedulers | Unresolved authority overlap | Freeze source of eligibility at Gate B. No downstream package may add a scheduler. |
| Provider catalog vs Engineering provider reports | Canonical source plus derived views | Catalog/capability/health/capacity remain source records; Engineering reports may cache only provenance and observation time. |
| `completed/` vs `completions/` and Markdown status | Existing duplicate status representations | Preserve for compatibility; define deterministic interpretation and validation rather than a third directory. |
| Work-package validation vs production readiness vs post-merge validation | Complementary gates often conflated | Document phase and verdict type; reuse all applicable gates. |
| Operational campaigns vs Markdown Engineering campaigns | Partial semantic overlap | Adapt/reference operational campaign checkpoints only if they can preserve Engineering authority and identifiers; do not create competing definitions. |
| Local Engineering closed loop vs generic Dispatch/provider adapter | Demonstration plus canonical generic path | Treat `run_closed_loop()` as historical demonstration; use the Dispatch bridge/provider-neutral path for general packages. |
| Mailbox messages vs Grace actions vs notebook | Communication, operations state, and continuity | Link them; do not use a message or notebook entry as authoritative queue state. |

## 5. Stale and partial records

- WP-0125 readiness totals, Git hash, and runtime department status are historical snapshots and must not be presented as current.
- CAMPAIGN_0550’s completion evidence is durable, but its fixed IDs and one-PR exception do not generalize to CAMPAIGN_0670.
- `cuemastery_execution_handoff.md` is an initial handoff, not a department-wide priority backlog.
- Work packages WP-0650 through WP-0662 demonstrate receipts coexisting with definitions still labeled or located as pending.
- EOC/CME packages WP-0663 through WP-0669 are pending designs and cannot be treated as implemented operational automation.
- Generated files under `operations/engineering_capacity/`, `operations/readiness/`, and runtime snapshots are derived views whose observation time must be shown.

## 6. Missing durable record fields

Later work packages should minimally standardize references for: schema version; campaign ID; work-package ID; canonical definition path and digest; dependency/gate; authority owner; operational owner; branch/worktree and base commit; allowed paths; staffing assessment; routing recommendation and observation time; selected provider/reservation; Dispatch/handoff/run IDs; validation recipe/report/verdict; evidence hashes; PR/integration identity; acceptance decision and actor; readiness case; attempt/supersession; blocker and escalation owner; notebook/continuity link; and timestamps.

These fields belong in a contract/projection. Raw provider, validation, mailbox, staffing, Dispatch, and readiness evidence must remain in their existing stores.

## 7. Recovery requirements

Downstream design must explicitly cover:

1. **intake mismatch:** quarantine and request correction; never guess campaign/package identity;
2. **dependency or gate closed:** remain not-ready and identify the accepting authority;
3. **staffing unavailable:** Helen records missing qualification/capacity; Grace records operational blocker;
4. **provider unhealthy/reservation stale:** preserve recommendation/reservation evidence, reevaluate through existing routing, never silently switch;
5. **dispatch interrupted:** resume/retry through Dispatch with a new attempt linked to the original;
6. **validation failure:** preserve raw output and return to implementation without marking Dispatch execution incomplete if execution actually ended;
7. **PR conflict/rejection:** retain validation evidence against its exact commit and require revalidation after changes;
8. **post-merge readiness failure:** use the closure controller’s blocker/acknowledgement/remediation lifecycle;
9. **session loss:** resume from the campaign notebook/continuity reference, not conversational memory;
10. **record divergence:** fail closed and escalate rather than overwriting one source with another.

## 8. Gate A disposition

Gate A is ready for Chief Architect review because canonical assets, active seams, duplication risks, stale records, authority conflicts, missing records, recovery requirements and prohibited replacements are explicitly identified. This document does **not** release Gate A and does not authorize WP-0671 or WP-0672; only Chief Architect acceptance can do so.

