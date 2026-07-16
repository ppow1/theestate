# Engineering Execution Lane and Provider Routing Contract

Status: Gate B contract  
Campaign: CAMPAIGN_0670_ENGINEERING_DEPARTMENT_OPERATIONALIZATION  
Work package: WP-0672  
Authority owner: Chief Architect

## Purpose and governing boundary

This contract defines how an already-approved, PTM/orchestrator-eligible Engineering work package is matched to an execution lane and provider. It extends the existing provider catalog, capability, health, capacity, recommendation, governed reservation, Execution Dispatch, provider-neutral adapter, and validation seams. It creates no Engineering scheduler, queue, provider registry, approval path, or acceptance authority.

Work packages remain the unit of execution and campaigns the unit of coordination. PTM/orchestrator owns dependency eligibility and sequencing. A routing recommendation informs an authorized provider selection; a reservation holds capacity; Execution Dispatch authorizes a bounded handoff; an adapter submits it; and an execution confirmation proves what ran. None of those events approves architecture, merges a branch, validates the result, or accepts the package.

## Execution lanes

The lane is a package constraint, not a provider identity or institutional office. A package declares one preferred lane, permitted alternates, prohibited lanes, required capabilities, data/classification limits, write scope, validation needs, and human gates before readiness evaluation.

| Lane | Suitable work | Required controls | Must not do |
|---|---|---|---|
| `codex` | Bounded repository analysis or implementation needing reviewable branch/commit/PR output | Provider-neutral Dispatch handoff; Codex bridge profile/sandbox policy; exact read/write/blocked paths; validation commands | Approve architecture, broaden scope, bypass Dispatch, self-accept, or merge |
| `local_ai` | Bounded drafting, analysis, tests, or implementation supported by a registered local model/worker | Canonical provider/capability/health evidence; external Engineering Worker Runtime or accepted adapter; data-locality and output provenance | Become a worker registry, make protected decisions, silently switch models, or merge |
| `local_tool` | Deterministic scripts, compilers, linters, tests, generators, migrations, and reproducible transforms | Tool/version/environment identity; command, inputs, outputs, exit status and hashes; Dispatch when the tool performs assigned package execution | Infer approvals, mutate outside allowed paths, or convert a check into acceptance |
| `accepted_provider` | A future or external provider already admitted to canonical provider governance | Registered identity/capabilities; current health/capacity; accepted provider-neutral adapter; classification, cost and boundary approval | Use an ad hoc provider, direct network handoff, or create lane-specific authority |
| `human_authority` | Architecture, protected approvals, ambiguity resolution, review and acceptance | Named actor, authority basis, durable decision reference, scope and time | Be represented as an AI provider or routine execution fallback |

Hybrid packages enumerate stage order and evidence per stage. Every executing stage uses the same campaign and package IDs and its own attempt/run identity. A human gate does not erase provider provenance, and a provider result cannot stand in for a human decision.

## Gate-B identity and branch freeze

Every record from readiness through completion MUST preserve:

- literal `campaign_id` and `work_package_id` from the canonical definitions;
- `attempt_id`, plus `predecessor_attempt_id` and supersession reason for a retry;
- canonical definition paths and content digests;
- readiness/eligibility reference and its observation time;
- branch name, branch owner, base commit, allowed paths, prohibited paths, and release event;
- routing policy version, recommendation, selection, reservation, Dispatch, adapter request, provider run, and result references when applicable;
- delivered commit and evidence hashes.

One implementation branch belongs to one package and one owner. Ownership ends only on the package-declared `PR closed`, `merged`, `cancelled`, or explicit reassignment event. Provider failure, session loss, Dispatch completion, validation success, or PR creation does not release it. Any material change after validation creates a new delivered commit and requires new evidence.

## Routing inputs and lane capability requirements

Routing evaluates only source-backed evidence. The request MUST include:

1. a `ready` canonical PTM/orchestrator eligibility reference for the exact campaign/package and current source high-watermark;
2. package lane policy, risk/classification, required capabilities, expected outputs and validation recipe;
3. branch/base/ownership and bounded read, write and blocked paths;
4. staffing/assignment reference and authorized operational owner;
5. canonical provider candidates, capability versions, health/capacity observations and expiry;
6. environment, locality, secrets/PII, budget/cost ceiling, network and protected-approval constraints;
7. retry policy and previous-attempt references.

Minimum capability declarations by lane are:

- **Codex:** repository read/write mode, sandbox/approval policy, profile, context limits, tool/network availability, branch/commit support, and validation-command support.
- **Local AI:** model/runtime identity and version, host/GPU requirement, context limits, allowed tools, structured-output ability, repository-write ability, locality/classification ceiling, and evidence export.
- **Local tool:** executable and version, platform, deterministic/non-deterministic classification, input/output formats, side effects, exit semantics, and rollback behavior.
- **Accepted provider:** the common requirements above plus adapter version, authentication boundary, data egress/retention policy, cost/rate limit and provider-specific protected approval.

Missing, stale, conflicting, unhealthy, over-capacity, over-budget, unqualified, or classification-incompatible evidence excludes a candidate. An empty candidate set is a blocker, never permission to relax a constraint.

## Deterministic routing and authority sequence

1. **Eligibility:** PTM/orchestrator confirms the exact package is ready. Closed/unknown/stale eligibility stops routing.
2. **Candidate query:** the canonical catalog/capability registry supplies identities matching the declared lane and hard requirements.
3. **Safety filter:** classification, allowed/prohibited paths, locality, secrets, network, protected approvals and provider exclusions remove incompatible candidates.
4. **Fitness evidence:** canonical health/capacity, qualification, environment, cost and prior benchmark evidence are observed with timestamps and expiry.
5. **Recommendation:** the existing recommendation runtime produces ranked, explainable advisory evidence with policy version and excluded-candidate reasons.
6. **Selection:** the authorized Traffic Controller/Operations Manager records the selected provider, recommendation reference, constraint snapshot, rationale, decision time and any permitted override. A recommendation never selects itself.
7. **Reservation:** the governed provider scheduler may create one time-bounded capacity hold only for the eligible assignment. It does not enqueue work or alter dependency order.
8. **Dispatch authorization:** canonical Execution Dispatch records the selected provider, decision/readiness/reservation references, classification, bounded paths, expected outputs and validation requirements.
9. **Adapter handoff:** the provider-neutral adapter validates the Dispatch record and translates it through an accepted lane-specific adapter. No direct provider call may bypass this seam.
10. **Live confirmation:** execution starts only after a provider submission/acknowledgement records the exact request, provider identity/version, attempt/run ID and start time. A prepared or dry-run handoff is not live execution.
11. **Result reconciliation:** immutable result evidence records end state, output references/hashes, commands/tool calls as permitted, usage/cost, timestamps and failure details. Dispatch completion means only that the execution handoff ended.

Selection overrides may choose another still-eligible candidate, but MUST name the authorized actor, reason, policy basis and original recommendation. They may not waive architecture, readiness, classification, protected approval, path, or provider-admission constraints.

## Minimum evidence by event

| Event | Minimum durable evidence |
|---|---|
| Recommendation | IDs; attempt; policy/version; candidate and exclusion list; capability/health/capacity refs; observation and expiry; rationale |
| Selection | recommendation; selected canonical provider/lane; decision actor/authority; constraint snapshot; override rationale; decision time |
| Reservation | eligible assignment; provider/resource; lease ID; start/expiry; state; release/expiry record; `dispatch_required: true` |
| Dispatch authorization | Dispatch ID/state; readiness and selection refs; campaign/package/attempt; classification; exact scope; expected outputs; decision reference |
| Adapter handoff | adapter request/version; Dispatch ID; translated provider/profile; validation result; submission mode; request digest |
| Live confirmation | provider run/session ID; acknowledgement; provider/model/tool version; exact request digest; start time; `live_provider_called: true` |
| Execution result | terminal provider state; end time; output/evidence refs and hashes; delivered commit if any; usage/cost; errors; predecessor/supersession |

Dry runs MUST state `live_provider_called: false`. External worktrees and run corpora remain in their canonical external locations; Estate records references and immutable digests rather than copying raw corpora into the repository.

## Failure, retry, and recovery

- **Stale recommendation or changed health/capacity:** retain the old evidence, expire/release any lease, and reevaluate. Never silently substitute a provider.
- **Reservation expiry:** record expiry/release and return to selection/reservation for the still-eligible assignment; it does not change package readiness by itself.
- **Dispatch validation failure:** keep the rejected handoff evidence, correct the governed source, and create a new linked request/attempt where submission could have occurred.
- **Provider rejection or interruption:** preserve acknowledgement, logs/references and partial outputs; reconcile the attempt; release capacity; retry through a new Dispatch-linked attempt.
- **Provider becomes unhealthy during execution:** follow the provider/runtime safe-stop policy. A fallback provider requires fresh evidence, selection and Dispatch authorization.
- **Scope or branch mismatch:** stop and escalate to the branch/integration owner. Do not broaden allowed paths or change base silently.
- **Validation failure:** preserve the completed execution result and return to implementation with a linked attempt. Do not rewrite Dispatch history.
- **PR rejection/conflict or material edit:** retain commit-bound evidence, amend/rebase under branch ownership, and rerun applicable validation.
- **Evidence conflict or session loss:** fail closed and resume from canonical records and continuity references, not conversational memory.

Retries are idempotent only for the same immutable request and provider idempotency key. Otherwise they receive a new attempt, Dispatch and adapter/run identity linked to the predecessor. Historical records are never mutated to present a retry as the original run.

## Relationship to validation, integration, and acceptance

Lane evidence proves routing and execution provenance only. WP-0673 may reference it in the campaign evidence manifest, but must preserve separate verdicts for execution completion, validation, Chief Architect acceptance, merge and post-merge readiness. Codex, local AI, local tools, providers, Helen, Grace, Alfred, recommendation runtimes, reservations and Dispatch cannot accept Engineering work.

The Chief Architect owns Engineering architecture, package/gate acceptance and integration review for this campaign. The Steward retains constitutional, priority and exception authority but is not the routine scheduler. Grace may coordinate checkpoints, Helen may supply staffing evidence, and Alfred may route notices; none changes routing or execution state by message alone.

## Existing seams and prohibited replacements

Implementations of this contract MUST reuse:

- provider catalog/capability and health/capacity sources;
- provider-routing recommendation and Engineering routing views;
- `governed_provider_scheduler.py` only as the bounded reservation mechanism;
- `execution_dispatch.py` and the dispatch-to-adapter handoff;
- the provider-neutral execution adapter, Codex bridge adapter, and external Engineering Worker Runtime;
- canonical validation, Git/PR, completion receipt and continuity systems.

They MUST NOT add a provider registry, worker registry, scheduler, assignment queue, Dispatch queue, evidence archive, validation runner, mailbox bus, direct merge path, or automatic fallback executor. Generated dashboards and reports are timestamped projections and never canonical state.

## Gate-B alignment and unresolved decisions

This contract adopts WP-0671's literal IDs, readiness states, PTM/orchestrator eligibility authority, branch ownership, collision controls and commit-bound evidence. It resolves provider scheduling as capacity reservation only and freezes recommendation, selection, reservation, Dispatch authorization and live confirmation as distinct events.

Chief Architect acceptance is still required to release Gate B. The following implementation-policy choices must be named by that acceptance or a subsequent approved package before automation relies on them: the exact canonical PTM/orchestrator eligibility record, authorized selector role mapping, evidence expiry thresholds by lane/risk, approved-provider admission policy, and repository location/schema for the shared projection. Unknown choices fail closed; this document does not release a campaign gate.
