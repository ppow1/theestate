# Engineering Department Canonical Reuse Map

**Purpose:** binding baseline for downstream CAMPAIGN-0670 design. “Extend” means add references, validation, or an adapter at the named seam—not copy its state into a new Engineering subsystem.

## 1. Required reuse map

| Need | Canonical mechanism to reuse | Permitted extension seam | Must not be created |
|---|---|---|---|
| Approved intake | PTM/orchestrator intake records and decision runtime in `src/estate/core/orchestrator_intake*.py` | Engineering campaign adapter validating approved source and stable IDs | Engineering approval inbox or second intake queue |
| Campaign definition | `collaboration/campaigns/*.md` plus PTM campaign contracts | Versioned machine-readable projection referencing path/digest | Competing campaign document or hidden chat-only plan |
| Package definition/identity | `collaboration/work_packages/*`, work-package template, PTM identity/dependency contracts | Readiness validator and shared cross-record identifiers | Engineering task type that replaces work packages |
| Dependencies/readiness/schedule | PTM schedule/readiness contract and orchestrator schedule runtime | Department policy constraints and read-only eligibility projection | Second Engineering scheduler or dependency graph |
| Staffing/qualification | `HelenWorkforceStore`, requests and assessments | Campaign/package references and qualification requirements | Engineering worker registry or hiring workflow |
| Operational momentum | `GraceOperationsRuntime` objectives/actions/checkpoints/closures | Campaign/package-linked status, reminders and escalation | Architecture approval or a Grace execution queue |
| Communication | mailbox index/control/sync and Alfred routing | Structured notices carrying canonical record references | Engineering mailbox bus or message-as-state system |
| Provider identity/capability | provider catalog and capability registry | Engineering-required-capability query | Engineering provider registry |
| Provider health/capacity | canonical health/capacity records and Engineering aggregate views | Time-bounded routing evidence | Copied health database |
| Provider recommendation | provider-routing recommendation and Engineering routing runtimes | Explainable policy constraints and evidence references | Recommendation treated as authorization |
| Provider reservation | governed provider scheduler, only after Gate-B reconciliation with PTM | Reservation linked to an eligible assignment/Dispatch attempt | Work queue or sequencing authority inside reservation system |
| Execution handoff | `execution_dispatch.py` and adapter handoff runtime | Campaign/package/attempt metadata and bounded-path validation | Second dispatch queue or direct provider bypass |
| Codex/local AI execution | provider-neutral adapter, Codex bridge adapter, external Engineering Worker Runtime | Lane-specific adapter mappings | Codex/local AI office, authority, or direct merge path |
| External worktree/run evidence | `A:\AI\EngineeringWorktrees`, `A:\AI\EngineeringRuns`, Estate references/hashes | Evidence manifest links and immutable digests | Raw external execution corpus committed into Estate |
| Validation | registered work-package recipes, production readiness, post-merge pipeline and reconciliation | Evidence manifest and phase-specific verdict projection | Engineering validation runner or self-acceptance shortcut |
| Integration | Git commit/branch/PR and Chief Architect review | Branch ownership and acceptance metadata | Automatic merge or validation-equals-acceptance rule |
| Post-merge readiness | Operational Readiness Closure Controller | Campaign/package/PR linkage and status projection | Engineering activation/publication controller |
| Reports/metrics | existing runtime records and generated operations reports | Read-only campaign-keyed aggregation with timestamps | Parallel evidence database or manually asserted metrics |
| Reflection/continuity | existing reflection process/templates and `operations/continuity/*` | Engineering notebook index referencing canonical artifacts | Chat transcript as sole continuity or duplicate archive |
| Completion/archive | existing completion receipts, validation evidence, campaign report conventions | Deterministic receipt schema/status interpretation and campaign acceptance package | Third receipt directory or self-marked acceptance |

## 2. Identifier and reference rules for downstream packages

1. Preserve the campaign’s literal ID and the work package’s literal ID across staffing, Grace, scheduling, Dispatch, provider, evidence, validation, PR, readiness and continuity records.
2. Reference canonical artifact paths and content digests; do not embed mutable copies of their full state.
3. Every execution attempt receives its own attempt/run/Dispatch identity and links to its predecessor when retried or superseded.
4. A routing recommendation identifies evidence time and policy version. A provider selection/reservation, Dispatch authorization and live-execution confirmation are separate events.
5. A branch/commit identifies the code validated. Any material change after validation requires new evidence.
6. Status projections disclose source records, observation time and conflicts. They never overwrite canonical source state.
7. Acceptance records identify the actor and authority basis. Absence of an explicit Chief Architect decision is “awaiting acceptance,” never implicit acceptance.

## 3. Explicit prohibition list

Downstream CAMPAIGN-0670 packages must not implement:

- a second scheduler, dependency resolver, assignment queue, Dispatch queue, validation path, provider registry, capability registry, health/capacity store, mailbox bus, personnel system, readiness controller, evidence archive, or acceptance authority;
- direct Engineering execution from a campaign/notebook/chat record without an eligible bounded Dispatch handoff;
- direct provider routing that bypasses recommendation evidence, capability constraints, health/capacity policy, or required confirmation;
- any automatic merge or equation of execution completion, test pass, validation pass, Grace closure, Dispatch completion, or readiness closure with Chief Architect acceptance;
- campaign or package state held only in conversational memory, filename location, a generated dashboard, or an unversioned mutable report;
- relabeling Codex, local AI, Helen, Grace, Alfred, PTM, Dispatch, or Validation as an Engineering approval authority;
- raw external worktrees/runs in the Estate repository when hashes and canonical external references suffice;
- mutation of historical receipts/snapshots to simulate current truth; supersede them with linked records;
- inference that a pending EOC/CME design is implemented behavior;
- routine Steward scheduling disguised as a required confirmation. Escalate only authority, safety, priority, exception, and irreconcilable evidence questions.

## 4. Gate-specific freeze

- **Gate A (this package):** the systems named above are the baseline. No downstream package may invent replacements.
- **Gate B:** WP-0671 and WP-0672 must jointly freeze IDs, readiness, scheduling authority, routing/selection/reservation, branch ownership, and minimum evidence before either can integrate.
- **Gate C:** WP-0673 and WP-0674 must use the identical identifiers and source references for validation, acceptance, metrics, notebook, communications and continuity.
- **Gate D:** WP-0675 must demonstrate the composed existing mechanisms; a demonstration that uses a parallel shortcut does not satisfy readiness.

## 5. Unresolved questions reserved for Chief Architect / Gate B

1. Which exact PTM/orchestrator record is the authoritative machine-readable eligibility decision for an Engineering package?
2. Is `governed_provider_scheduler.py` retained solely as a provider reservation implementation, or superseded for Engineering by PTM/orchestrator scheduling?
3. What deterministic precedence resolves package Markdown status, directory placement, JSON receipt, Markdown receipt, validation verdict and PR state?
4. Which actor may create the campaign projection, and which actor may release each integration gate?
5. Where is branch ownership recorded, and what event releases it after rejection, interruption or merge?
6. Which evidence classes are mandatory per lane, and which require repository content hashes versus external canonical references?
7. How is Steward final institutional authority represented without making the Steward the routine scheduler or overriding Campaign 0670’s Chief Architect Engineering-acceptance rule?

Until these are accepted, downstream packages may document alternatives but must fail closed rather than choose silently.

