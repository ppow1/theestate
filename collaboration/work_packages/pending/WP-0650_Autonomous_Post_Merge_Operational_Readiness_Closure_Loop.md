# WP-0650 — Autonomous Post-Merge Operational Readiness Closure Loop

## Status

Pending implementation.

## Owner

Office of Chief Architect, implemented through Engineering and the existing Estate Operations Runtime.

## Objective

Implement one canonical, production-ready autonomous closure system that carries an approved merged work package from merge detection through deployment, activation, live validation, bounded remediation, observation, and an evidence-backed operational-readiness verdict.

This is not an MVP, prototype, advisory dashboard, or first installment in a sequence of replacement systems. The implementation delivered under this work package must establish the durable production architecture. Future work may add supported remediation handlers or target adapters to this same subsystem, but must not create a second operational-readiness engine.

The Estate can currently implement, merge, discover, audit, and validate work, but it does not reliably finish the operational journey without repeated manual intervention by the Steward. The resulting system must not stop at reporting that a merged capability is unready. It must determine the exact blockers, perform every authorized safe correction, revalidate, and continue until either:

1. the capability is operationally ready; or
2. a specific bounded condition requires Steward authority or manual intervention.

## Institutional Placement

Implement this capability inside the existing Estate Operations Runtime as the canonical Operational Readiness Closure Controller.

It must coordinate existing institutions and surfaces rather than duplicate them:

- Merge Discovery identifies merged work and associated commits.
- Work-package and completion receipts define intended scope, expected artifacts, validation recipes, and declared affected subsystems.
- Validation produces behavioral evidence.
- Post-Merge Audit evaluates merged work and evidence.
- The Estate Feature Activation Ledger records reachability and activation state.
- Existing deployment, bootstrap, host, Scheduled Task, and runtime controls perform operational actions.
- The Office of the Steward exposes current state, blockers, actions, and evidence.
- Audit may review the resulting record.
- The Steward or other named authority retains institutional acceptance authority.

Do not create another Office, scheduler, validation engine, audit engine, deployment registry, activation inventory, provider router, queue, authority hierarchy, or dashboard.

## Required Outcome

For every eligible merged work package, the Estate must automatically create or resume one durable operational-readiness case and drive it through the complete post-merge lifecycle.

A case is complete only when all applicable conditions are proven:

- merge commit identified;
- affected target and capability identified;
- production or managed runtime checkout contains the required commit;
- required deployment, reload, restart, or activation completed;
- capability is reachable through its canonical surface;
- live validation passed against the deployed target;
- no unresolved blocking findings remain;
- required observation criteria passed;
- Activation Ledger and Office evidence are current;
- operational-readiness verdict is written;
- institutional acceptance remains separate unless explicitly granted by the proper authority.

## Canonical State Model

Implement a durable, resumable state machine supporting at least:

- `merged`
- `assessment_required`
- `deployment_required`
- `deployment_in_progress`
- `deployed`
- `activation_required`
- `activation_in_progress`
- `live_validation_required`
- `live_validation_in_progress`
- `live_validation_failed`
- `remediation_required`
- `remediation_in_progress`
- `observation_required`
- `observation_in_progress`
- `operationally_ready`
- `blocked_authority_required`
- `blocked_manual_intervention`
- `blocked_unsafe_action`
- `failed_bounded_retries`
- `rejected`

State transitions must be deterministic, evidence-backed, idempotent, restart-safe, and recoverable after host interruption or power loss.

The controller must never infer completion merely because a state file, completion receipt, branch, merge, or validation report exists.

## Eligibility and Intake

The controller must consume canonical Merge Discovery and post-merge evidence.

For each merge, determine:

- work-package ID;
- merge commit;
- base branch;
- repository and operational target;
- completion receipt;
- affected files and declared subsystems;
- validation recipe;
- deployment and restart requirements;
- activation requirements;
- observation requirements;
- acceptance authority;
- whether the case is already known, active, completed, superseded, or ineligible.

Duplicate merges, repeated runtime cycles, and restarts must not create duplicate readiness cases.

Historical packages and merges must not be silently promoted as new current work.

## Assessment Contract

Before acting, produce a structured readiness assessment containing:

- current merged revision;
- current target revision;
- repository cleanliness;
- branch and upstream state;
- runtime process and host state;
- Scheduled Task or service state where applicable;
- activation and canonical reachability state;
- latest validation result and evidence paths;
- current operational-readiness blockers;
- available deterministic remediation handlers;
- actions requiring authority;
- actions prohibited by policy;
- retry history;
- next action.

The assessment must distinguish:

- implementation failure;
- validation failure;
- deployment failure;
- activation failure;
- configuration failure;
- runtime infrastructure failure;
- stale repository or stale runtime checkout;
- incorrect test or validation recipe;
- missing prerequisite;
- observation incomplete;
- authority required;
- manual intervention required;
- unknown or unclassified failure.

## Authorized Deterministic Remediation

Implement a policy-controlled remediation registry inside the existing controller. It must contain explicit handlers, preconditions, evidence, rollback or safe-stop behavior, bounded retry limits, and post-action validation.

The initial production implementation must support all of the following where the target configuration declares them applicable:

### Repository and runtime synchronization

- fetch the configured upstream;
- fast-forward a clean managed checkout;
- refresh or rebuild the existing isolated runtime checkout through the canonical bootstrap mechanism;
- verify local revision equals the intended remote or merged revision;
- refuse dirty, divergent, detached, ambiguous, or unauthorized checkouts;
- never force-reset, force-push, discard local work, or rewrite history.

### Runtime lifecycle

- restart or reload an existing declared service, host, or Scheduled Task;
- verify the expected executable, command, root, PID, lock, heartbeat, and revision;
- recover from a dead-process stale lock through existing safe lock rules;
- refuse unknown processes, mismatched roots, uncertain ownership, or undeclared lifecycle actions.

### Configuration and prerequisites

- create declared runtime directories;
- materialize tracked or generated prerequisites through approved existing mechanisms;
- apply approved non-secret configuration already defined by canonical target metadata;
- detect missing credentials or secrets and escalate rather than fabricate them;
- refuse unregistered or speculative configuration changes.

### Activation and reachability

- connect implemented capability through an existing declared canonical surface;
- refresh existing registrations, projections, or generated Office artifacts;
- verify the capability can be reached through the canonical caller;
- update the existing Estate Feature Activation Ledger with evidence;
- refuse creation of parallel surfaces or duplicate activation inventories.

### Validation and evidence

- invoke the canonical work-package validation recipe;
- invoke target-specific live checks where required;
- retain stdout, stderr, exit code, revision, environment, and evidence paths;
- classify failures;
- invoke an approved deterministic remediation when classification and policy permit;
- revalidate after every remediation;
- suppress repeated identical validations when no relevant state changed;
- avoid infinite repair loops.

### Observation

- observe a configurable but explicit number of production cycles, elapsed duration, restart events, or health checks as required by target policy;
- preserve observation evidence across runtime restarts;
- reset observation only when a relevant regression occurs;
- distinguish a single successful check from sustained operational readiness.

## Repair-Loop Behavior

The controller must execute this loop without Steward intervention when actions are authorized:

1. Assess current state.
2. Identify all current blockers.
3. Select the next deterministic permitted action.
4. Record the decision and preconditions.
5. Execute exactly one bounded action.
6. Record stdout, stderr, exit status, changed state, and evidence.
7. Reassess.
8. Revalidate when relevant.
9. Continue until operationally ready or genuinely blocked.

The controller must not merely recommend a safe action that it is already authorized to perform.

When several blockers exist, choose an order that minimizes risk and avoids validating stale or undeployed code.

## Escalation Contract

Stop and escalate only when at least one of the following is true:

- repository contains uncommitted or divergent work;
- destructive operation would be required;
- governance or acceptance authority is required;
- credentials, secrets, hardware access, or physical intervention are required;
- no approved deterministic remediation exists;
- failure classification confidence is insufficient;
- bounded retry limit is exhausted;
- a repair causes a new regression;
- target identity or ownership is ambiguous.

Escalation must be concise and actionable. It must state:

- exact blocked state;
- exact blocker;
- evidence paths;
- actions already attempted;
- why autonomous action stopped;
- exact decision or manual action required;
- what the controller will do automatically after the blocker is cleared.

Do not return broad checklists when only one decision is required.

## Operational-Readiness Verdict

Write a durable canonical verdict containing at least:

- readiness case ID;
- work-package ID;
- repository and target ID;
- merge commit;
- deployed revision;
- activation state;
- validation status and evidence;
- observation status and evidence;
- remediations attempted;
- unresolved findings;
- final state;
- `operationally_ready` boolean;
- `institutional_acceptance_granted` boolean;
- acceptance authority;
- generated timestamp;
- evidence root.

The controller may declare operational readiness only when every applicable required gate is satisfied.

The controller must never grant institutional acceptance unless an existing canonical mechanism records an explicit decision by the authorized officeholder.

## Office of the Steward Surface

Expose the controller through the existing Office command surface.

The Office must provide accessible controls and evidence for:

- list readiness cases;
- inspect one case;
- show current stage and next action;
- show blockers and exact escalation requirement;
- show deployed and remote revisions;
- show activation state;
- show live-validation evidence;
- show observation progress;
- request or resume closure processing;
- pause and resume an individual case;
- acknowledge a manual blocker resolution;
- open evidence artifacts;
- filter by ready, active, blocked, or failed.

Controls must invoke the canonical controller directly. Do not build decorative controls or a second readiness implementation inside the Office.

The surface must be usable with large display scaling, keyboard navigation, predictable focus order, readable status text, and minimal visual hunting.

## Operations Runtime Integration

Integrate processing into the existing Operations Runtime cycle.

Requirements:

- no second scheduler or resident host;
- bounded work per cycle;
- configurable active-case limit;
- fair progress across cases;
- idempotent claim and lease behavior;
- crash-safe and restart-safe case persistence;
- no provider execution unless separately authorized by an existing provider policy;
- metrics included in existing runtime status and Office projections;
- no repeated creation of equivalent cases or actions;
- no starvation behind permanently blocked cases.

Required cycle metrics include:

- cases discovered;
- cases assessed;
- cases advanced;
- remediations attempted;
- remediations succeeded;
- remediations failed;
- validations executed;
- cases entering observation;
- cases declared operationally ready;
- cases blocked for authority;
- cases blocked for manual intervention;
- retry limits reached;
- current active cases;
- oldest active case age.

## Target and Policy Configuration

Use or extend existing operational-target metadata rather than creating a separate target registry.

Each target must be able to declare:

- managed checkout path;
- base branch and upstream;
- deployment mechanism;
- lifecycle action identifiers;
- canonical reachability probes;
- validation recipes;
- allowed remediation handlers;
- observation policy;
- acceptance authority;
- classification and evidence location.

Default posture is deny. A remediation handler may execute only when both the handler and target policy authorize it.

## Safety Requirements

The implementation must not:

- force-push;
- force-reset a dirty or divergent user checkout;
- delete branches or history;
- overwrite unrelated work;
- merge pull requests;
- grant itself new authority;
- expose credentials;
- execute arbitrary generated shell commands;
- perform open-ended AI-generated repair;
- create new governance institutions;
- mark a capability ready based only on isolated tests;
- mark a capability ready while production runs an older revision;
- silently ignore failed actions or stale evidence.

Every mutation must be attributable to a named deterministic handler and recorded before and after execution.

## Required Implementation Artifacts

Implement at minimum:

- canonical readiness case and verdict models;
- controller and state-transition logic;
- deterministic remediation registry and handlers;
- persistence, leasing, retry, and recovery behavior;
- Operations Runtime integration;
- operational-target metadata integration;
- Validation and Post-Merge Audit integration;
- Activation Ledger integration;
- Office command actions and accessible surface;
- CLI inspection and controlled-processing commands;
- structured JSON status and evidence;
- human-readable operational report;
- documentation;
- focused unit tests;
- integration tests;
- isolated-workspace tests;
- live local acceptance procedure;
- work-package validation recipe;
- completion receipt.

Suggested canonical implementation paths may follow existing repository conventions, but Engineering must inspect current structures before selecting exact filenames. Do not create duplicate modules when an existing Operations Runtime or Office module can absorb a responsibility cleanly.

## CLI Requirements

Provide canonical CLI commands equivalent to:

- list readiness cases;
- show case;
- process one case;
- run one bounded controller cycle;
- pause case;
- resume case;
- acknowledge cleared manual blocker;
- show controller status;
- render report.

Commands must support JSON output and must not perform hidden provider or dispatch execution.

## Testing Requirements

Testing must prove the complete production flow, not only model serialization.

Required deterministic scenarios include:

1. A merged work package whose clean managed runtime is behind remote is fast-forwarded, restarted when required, validated, observed, and declared operationally ready.
2. A dirty checkout is not modified and produces an exact manual escalation.
3. A missing declared runtime directory is created, validation reruns, and the case advances.
4. A stale or dead runtime lock is recovered only under existing safe rules.
5. A live process with a valid lock is not duplicated.
6. An implemented but unreachable capability is activated through an existing canonical surface and recorded in the Activation Ledger.
7. A validation failure with an approved deterministic remediation is corrected and revalidated.
8. An implementation defect without an approved repair is escalated for a bounded work package rather than patched speculatively.
9. A case survives process termination and resumes without duplicate actions.
10. Repeated cycles do not duplicate cases, deployments, restarts, validations, or ledger entries.
11. Observation persists across cycles and only produces readiness after the declared threshold.
12. Institutional acceptance remains false after operational readiness unless explicitly granted through an existing authorized mechanism.
13. Blocked cases do not starve other cases.
14. Office controls invoke the canonical controller and remain keyboard accessible.
15. Runtime status truthfully reports activity, blockers, and readiness outcomes.

Tests must use temporary repositories, fake process and Scheduled Task adapters, deterministic clocks where needed, and fake validation outcomes. No test may alter the production Scheduled Task, active runtime, user repository, credentials, or live provider state.

## Live Acceptance Requirements

Before acceptance, execute a controlled local end-to-end demonstration against the Estate target using a deliberately selected merged work package or safe fixture.

The demonstration must prove:

- merge intake;
- deployment determination;
- managed runtime revision alignment;
- safe lifecycle action;
- live validation;
- blocker classification;
- at least one permitted automatic remediation;
- revalidation;
- observation progression;
- operational-readiness verdict;
- Office visibility;
- persistence after controller or host restart;
- institutional acceptance remains separate.

Do not mark WP-0650 complete based solely on mocks or isolated unit tests.

## Completion and Production-Readiness Criteria

WP-0650 is complete only when:

- one canonical controller exists and is integrated into the existing Operations Runtime;
- the complete state model is durable and restart-safe;
- authorized deterministic remediation is functioning;
- the Estate can autonomously carry an eligible merged work package to operational readiness without routine Steward commands;
- unsafe or unauthorized cases stop with exact bounded escalation;
- Office controls are functional and accessible;
- CLI and structured evidence are complete;
- unit, integration, recovery, idempotency, and live acceptance tests pass;
- a validation recipe exists and passes from a clean isolated workspace;
- completion receipt records exact files, tests, live demonstration, limitations, and safety assertions;
- production runtime deployment and observation prove the controller itself is operationally ready;
- no parallel institution or replacement readiness engine was created.

The implementation is not complete if it only:

- inventories blockers;
- recommends actions without executing authorized actions;
- validates isolated code without deploying it;
- adds a dashboard;
- handles only one hard-coded work package;
- requires the Steward to manually shepherd normal transitions;
- defers core lifecycle stages to later versions;
- declares readiness without live evidence.

## Required Completion Receipt Assertions

The completion receipt must explicitly state and support with evidence:

- `work_package_id = WP-0650`;
- `single_canonical_controller_created = true`;
- `parallel_readiness_engine_created = false`;
- `existing_operations_runtime_extended = true`;
- `deterministic_remediation_only = true`;
- `arbitrary_generated_shell_execution = false`;
- `force_push_or_destructive_reset_used = false`;
- `dirty_checkout_protection_verified = true`;
- `runtime_revision_alignment_verified = true`;
- `activation_ledger_integration_verified = true`;
- `office_controls_functional = true`;
- `accessibility_contract_verified = true`;
- `restart_recovery_verified = true`;
- `idempotency_verified = true`;
- `live_acceptance_completed = true`;
- `operational_readiness_declared_by_controller = true`;
- `institutional_acceptance_granted = false` unless separately and explicitly authorized;
- `provider_execution_performed = false` unless separately authorized and documented;
- `dispatch_execution_performed` truthfully reported;
- `ready_for_ca_review = true`.

## Scope Exclusions

Do not use this work package to:

- redesign Estate governance;
- create autonomous merge authority;
- create general-purpose self-modifying repair;
- replace Validation, Audit, Discovery, Activation Ledger, Office, or Operations Runtime;
- implement unrelated provider adjudication or Ring 2 work;
- activate unrelated capabilities merely because they are discovered during implementation;
- grant institutional acceptance;
- expand to unmanaged external targets without explicit canonical target configuration.

Unrelated defects discovered during implementation must be recorded separately and not absorbed unless they directly prevent WP-0650 from meeting its own production criteria.

## Engineering Execution Guidance

Engineering must begin by verifying current `main`, repository cleanliness, upstream synchronization, and the existing implementations of Merge Discovery, Post-Merge Audit, Validation, Operations Runtime, runtime host/bootstrap, operational targets, Office command surface, and Activation Ledger.

Prefer extending existing modules over adding new top-level systems. Use one durable readiness record per merged work package and target. Keep mutations deterministic and policy-gated.

Do not reduce the contract to a passive readiness report. The controller must actually finish authorized operational work.

## Final Deliverables

Return:

- exact files changed;
- architecture and integration summary;
- state-transition table;
- remediation-handler table with preconditions and safety behavior;
- CLI commands;
- Office actions;
- tests and results;
- live acceptance evidence;
- production deployment evidence;
- operational-readiness verdict for the demonstration case;
- known limitations;
- completion receipt;
- pull request URL.

## Codex Handoff

Implement this work package as one production-ready canonical Operational Readiness Closure Controller. Do not split the core lifecycle into later versions or create a parallel readiness engine. Integrate it with the existing Operations Runtime, Merge Discovery, Post-Merge Audit, Validation, operational targets, Activation Ledger, runtime host/bootstrap, and Office command surface. Implement deterministic policy-authorized remediation, live revalidation, observation, restart recovery, exact escalation, accessible Office controls, and the full test and live-acceptance contract. Preserve institutional acceptance as separate authority.

Work package filename:
`WP-0650_Autonomous_Post_Merge_Operational_Readiness_Closure_Loop.md`

Repository path:
`A:\theestate\collaboration\work_packages\pending\WP-0650_Autonomous_Post_Merge_Operational_Readiness_Closure_Loop.md`

Codex handoff command:
`Implement the instructions in A:\theestate\collaboration\work_packages\pending\WP-0650_Autonomous_Post_Merge_Operational_Readiness_Closure_Loop.md. Build one production-ready canonical Operational Readiness Closure Controller inside the existing Estate Operations Runtime. Do not split the core lifecycle into later versions, create a parallel readiness engine, redesign governance, or grant institutional acceptance. Complete all required code, Office and CLI integration, deterministic remediation handlers, tests, live acceptance, completion receipt, and production-readiness evidence.`