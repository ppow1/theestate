# WP-0692 — Campaign and Work-Package Momentum Observer

Status: Pending  
Priority: High  
Owner: Chief Architect  
Execution lane: Codex  
Primary campaign: CAMPAIGN-0681 — Estate Operationalization  
Depends on: WP-0688, WP-0689  
Integration gate: G2 — Observation Truth

## Objective

Implement a repository-grounded observer that can determine the truthful momentum state of campaigns and work packages without becoming a dispatcher, scheduler, acceptance authority, or duplicate state registry.

The observer shall reconcile canonical campaign definitions, work-package dependencies, readiness evidence, completion receipts, blockers, review gates, health inputs, and campaign-execution checkpoints into a concise operational view suitable for Grace, Engineering, the Chief Architect, and the Steward.

## Constitutional Precedence

Accepted Estate campaign, work-package, Engineering, PTM, Dispatch, readiness, validation, evidence, acceptance, communication, mailbox, reflection, and continuity standards remain authoritative.

If this package conflicts with an accepted canonical artifact, the accepted canonical artifact prevails.

WP-0692 may observe, normalize, reconcile, and explain campaign momentum. It may not redefine campaign state, package state, dependency rules, readiness, validation, acceptance, dispatch authority, or office authority.

## Required Inputs

Before implementation, discover and read the canonical successors of at least:

- CAMPAIGN-0681 and its execution manifest;
- WP-0688 and WP-0689 deliverables;
- CAMPAIGN-0670 accepted campaign and work-package lifecycle artifacts;
- WP-0678 campaign-level execution capability and completion evidence, when available;
- canonical campaign, work-package, readiness, validation, evidence, acceptance, PTM, Dispatch, and completion-receipt schemas;
- current campaign dashboards, notebooks, indexes, and reporting surfaces;
- existing dependency and status calculation code;
- CAMPAIGN-0680 decision-support outputs where overlap exists.

A moved path is not permission to invent a replacement. Discover the canonical successor through repository evidence.

## Scope

Implement or extend canonical seams needed to provide:

1. campaign discovery from authoritative repository artifacts;
2. package discovery and primary-campaign association;
3. dependency graph reconstruction from canonical definitions;
4. package-state reconciliation from authoritative evidence;
5. campaign-level momentum calculation;
6. detection of eligible, active, waiting, blocked, degraded, failed, review-gated, protected, and complete work;
7. stale, contradictory, missing, and partial-evidence detection;
8. critical-path and next-eligible-work views where supported by authoritative inputs;
9. concise explanations for every derived momentum state;
10. machine-readable and human-readable observation outputs;
11. deterministic repeated observation of unchanged repository state;
12. tests covering normal, partial, contradictory, stale, and failed campaign conditions.

## Required Momentum Model

The observer must distinguish at least:

- **Unready** — required launch or package readiness evidence is absent or unsatisfied;
- **Waiting** — work is valid but dependencies or authorized prerequisites are incomplete;
- **Eligible** — all observable prerequisites are satisfied and work may proceed through its proper execution lane;
- **Active** — canonical evidence shows execution has begun and has not reached a terminal or paused state;
- **Review gated** — work has reached a required non-protected review checkpoint;
- **Protected gated** — continuation requires an office or Steward decision that the observer cannot supply;
- **Blocked** — a known blocker prevents progression;
- **Degraded** — progression may be affected by resident, service, staffing, evidence, or environment degradation;
- **Failed** — authoritative evidence records execution or validation failure requiring recovery or decision;
- **Paused** — a canonical pause or safe checkpoint prevents continued execution;
- **Complete pending acceptance** — implementation evidence exists but protected acceptance has not occurred;
- **Accepted/closed** — canonical acceptance and closure evidence exists;
- **Indeterminate** — available evidence is missing, contradictory, stale, or insufficient for a truthful conclusion.

These labels are observational classifications only. They shall not silently mutate authoritative campaign or package state.

## Evidence Precedence

The implementation must define and test a deterministic precedence order among authoritative evidence sources.

At minimum:

1. protected acceptance and closure records outrank inferred completion;
2. explicit failure, pause, cancellation, or supersession records outrank optimistic progress inference;
3. current canonical package and campaign artifacts outrank discovery indexes and dashboards;
4. signed or schema-valid receipts outrank prose summaries;
5. repository-backed authoritative records outrank transient runtime claims;
6. stale or contradictory evidence results in an `Indeterminate`, `Blocked`, or `Degraded` observation rather than fabricated certainty.

The observer must expose which evidence produced each conclusion.

## Dependency and Eligibility Rules

The observer shall:

- reconstruct declared dependencies without inventing implicit dependency edges;
- recognize approved parallel groups only from canonical campaign evidence;
- account for required integration gates and review checkpoints;
- refuse to mark work eligible when required evidence is missing or contradictory;
- distinguish a dependency blocker from a staffing, health, validation, authority, or execution failure blocker;
- avoid treating file existence alone as proof of package completion;
- avoid treating a commit alone as acceptance or closure;
- avoid treating a recommendation as dispatch authorization.

## Required Outputs

Provide a stable observation object containing at least:

- campaign ID and canonical reference;
- observation timestamp;
- repository/base identity and relevant digest or commit;
- campaign momentum state;
- package-by-package observed state;
- dependency satisfaction summary;
- current critical path or limiting chain, when determinable;
- eligible package set;
- active package set;
- blocker and degraded-condition summary;
- pending review and protected-decision set;
- stale, missing, or contradictory evidence warnings;
- evidence references supporting each classification;
- concise human explanation;
- recommended destination for follow-up, without performing dispatch.

The output format must be suitable for later consumption by WP-0693, WP-0694, WP-0697, WP-0698, WP-0700, and WP-0703.

## Non-Goals and Protected Surfaces

WP-0692 shall not:

- dispatch, assign, start, pause, resume, retry, merge, deploy, accept, close, cancel, or supersede work;
- create a second campaign or work-package status registry;
- replace PTM, Dispatch, campaign manifests, completion receipts, readiness, validation, or acceptance records;
- infer acceptance from implementation completion;
- infer authority from technical capability;
- alter office charters or institutional boundaries;
- convert Grace into a scheduler or execution authority;
- write status back to canonical artifacts merely because an observation was calculated;
- conceal contradictory or stale evidence;
- build the Continuous Momentum Engine decision loop assigned to WP-0700.

## Implementation Requirements

- Reuse existing schemas, parsers, indexes, and repository services wherever possible.
- Keep observation calculation side-effect free by default.
- Make ordering and results deterministic for the same repository state.
- Preserve source references and evidence lineage.
- Fail closed when authoritative evidence cannot be reconciled.
- Provide clear extension seams for health integration from WP-0691 and blocker classification from WP-0693.
- Avoid adding a new persistent database unless a separately approved architectural decision proves canonical repository state cannot support the requirement.

## Validation

Tests must prove at least:

1. a simple sequential campaign is observed correctly;
2. an approved parallel group is represented without false serialization;
3. an unmet dependency prevents eligibility;
4. completed implementation without acceptance is not reported as accepted;
5. a failed validation overrides optimistic progress evidence;
6. a protected decision gate halts eligible continuation;
7. stale or contradictory evidence produces a truthful warning and fail-closed state;
8. a paused campaign remains paused across repeated observations;
9. a partially completed campaign identifies the correct remaining eligible work;
10. identical repository state produces identical normalized output;
11. the observer performs no dispatch or authoritative state mutation;
12. outputs can be consumed by the next CAMPAIGN-0681 integration packages.

## Deliverables

1. implementation in the canonical repository seam;
2. machine-readable observation schema or documented reuse of an existing schema;
3. human-readable campaign momentum view;
4. dependency and evidence precedence documentation;
5. automated tests and fixtures;
6. conflict/reuse report identifying canonical systems extended;
7. completion receipt with changed paths, commands, results, limitations, and unresolved blockers.

## Acceptance Criteria

WP-0692 is complete only when the Estate can observe a real campaign and truthfully explain:

- where the campaign is;
- which packages are complete, active, eligible, waiting, blocked, degraded, failed, paused, review-gated, protected-gated, or indeterminate;
- which evidence supports each conclusion;
- what dependency or gate limits progress;
- which office or existing mechanism should receive the next follow-up;
- and why no observation has been misrepresented as dispatch, authority, or acceptance.

Completion requires Chief Architect review and independently readable evidence. It does not launch CAMPAIGN-0681 or authorize execution of any observed package.