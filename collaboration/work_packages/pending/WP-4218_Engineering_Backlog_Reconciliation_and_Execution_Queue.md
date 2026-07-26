# WP-4218 — Engineering Backlog Reconciliation and Execution Queue

- **Status:** Pending
- **Source:** Estate Authored Backlog Implementation campaign assignment; no matching Parking Lot item
- **Mode:** isolated staged implementation
- **Implementation root:** `collaboration/workstreams/WP-4218/`
- **Install authority:** none; production installation requires a separate install package

## 1. Mission and authority

Implement a read-only, deterministic reconciliation process that inventories the Estate's Parking Lot, WIP, pending and completed work packages, open and merged pull requests, completion receipts, and validation reports, then emits one authoritative **engineering planning queue** with evidence, dependencies, readiness, and conflict information. It continuously identifies work that is duplicate, superseded, partial, completed, blocked, stale, or ready without becoming a runtime scheduler or dispatch authority.

Existing domain artifacts remain authoritative. WP-4218 produces a versioned projection and audit trail; it MUST NOT replace or mutate the canonical PTM ledger, execution dispatch queue, work-package directories, Parking Lot, WIP boards, Git history, PR state, receipts, or validation reports. A queue row is planning evidence, not authorization to claim, schedule, execute, merge, install, accept, or close work.

## 2. Mandatory isolation and reuse boundary

All future implementation, schemas, fixtures, tests, generated samples, reports, and implementation receipts MUST remain beneath `collaboration/workstreams/WP-4218/`. The implementation must consume sources through read-only adapters and reuse the Estate PTM source-reference model, existing provider-neutral execution dispatch boundary, and existing Engineering evidence/acceptance lifecycle. It MUST NOT create a second registry, operational dispatch queue, project-management system, scheduler, worker controller, or acceptance authority.

Do not modify production orchestrator logic, shared runtime, Open WebUI, Grace, Helen, Alfred, Local Compute, Evelyn, Git automation, merge automation, or production/shared files. Network and Git-host access are optional adapters: offline repository reconciliation must remain useful and must mark unavailable hosting facts `unknown`. Installation or shared integration requires a separately authorized install package with compatibility, migration, rollback, ownership, and validation gates.

## 3. Canonical sources and inventory contract

Each reconciliation run snapshots, without modifying:

1. `operations/boards/parking_lot.md` and structured Parking Lot records, if present;
2. active-work/WIP boards and `collaboration/workstreams/**` WIP manifests;
3. `collaboration/work_packages/pending/`, `open/`, `claimed/`, `completed/`, and recovered package records;
4. completion receipts in canonical completion/receipt locations;
5. validation reports and acceptance/verdict evidence;
6. local Git commits, branches, merge commits, and repository paths;
7. open and merged PR metadata only when an authorized, bounded provider snapshot is supplied;
8. campaign, roadmap, dependency, queue, and operational planning documents as contextual evidence.

Every adapter emits a normalized `source_record` with source kind, stable source locator, native identifier/status, content digest, observed revision/commit, observed-at time, authoritative-as-of time when known, adapter version, parse warnings, and raw reference (not an ungoverned copy). Missing, malformed, inaccessible, or conflicting sources stay visible. Provider absence never implies that a PR does not exist.

## 4. Reconciliation cycle and triggers

A cycle is: **discover → snapshot → normalize → correlate → classify → build dependency graph → assess risk/lanes/touch points → score readiness/priority → generate queue → validate invariants → publish immutable run artifacts**. Publication occurs only after validation succeeds; a failed candidate run leaves the last valid queue intact and publishes diagnostics.

Trigger a candidate run on an authorized manual request; Parking Lot/WIP/work-package lifecycle change; new or changed PR snapshot, commit, receipt, validation, or acceptance evidence; dependency/status change; configured freshness expiry; adapter/policy/schema version change; or correction of a source conflict. Coalesce identical events by source digest. Concurrent triggers use one immutable input cutoff and either serialize publication or discard a candidate based on an older cutoff.

Run identity is derived from normalized input snapshot digest plus schema, adapter, and policy versions. Identical logical inputs and configuration MUST produce byte-stable logical output and ordering; generated timestamps belong in a separable run envelope.

## 5. Correlation, duplicates, supersession, and partial work

Correlation uses, in order: exact WP/PL/PR/receipt/validation identifiers; explicit `implements`, `source`, `supersedes`, dependency, commit, and path references; then conservative normalized-title/scope/touch-point similarity as a **candidate only**. Fuzzy matches never auto-collapse records.

Duplicate classes are `exact_same_object`, `explicit_alias`, `probable_duplicate`, and `not_duplicate`. Exact/alias records form one queue candidate while preserving every source reference; probable duplicates remain separate, receive a review blocker, and expose reasons/scores. Conflicting terminal states can never be silently deduplicated.

Supersession requires an explicit link or independently reviewable evidence that a newer accepted package covers the same acceptance criteria. Classification records `superseded_by`, coverage (`full` or `partial`), rationale, and evidence. Full supersession removes readiness but retains an audit row; partial supersession subtracts only evidenced completed scope and produces residual acceptance criteria.

A package is `partially_implemented` only when commits/PRs or implementation artifacts map to some, but not all, acceptance criteria and terminal evidence is absent. Record criterion-level `implemented`, `validated`, `accepted`, `missing`, or `unknown`; never equate a branch, commit, PR, or generated file with completion.

## 6. Implementation evidence and reconciliation classifications

Evidence strength, highest first, is: accepted completion receipt linked to merged PR/commit and passing validation; acceptance verdict plus linked implementation and validation; completion receipt with coherent linked implementation; merged PR/commit with passing package-specific validation; open PR/branch/commit or implementation artifacts; authored package/planning statement only. Contradictions downgrade readiness and create review blockers rather than being overwritten.

Every candidate receives exactly one reconciliation classification:

- `not_started` — authorized scope exists with no implementation evidence;
- `authored_but_not_implemented` — implementation-ready package exists but no implementation evidence;
- `partially_implemented` — only a proven subset is implemented/validated;
- `implemented_but_not_validated` — implementation evidence exists without required validation/acceptance;
- `implemented_and_complete` — all acceptance criteria, validation, merge evidence, and required receipt/acceptance gates agree;
- `implemented_but_stale_or_defective` — completed/implemented work has failing, expired, contradicted, or defect evidence;
- `superseded_by_other_work` — scope is fully replaced with evidence;
- `ambiguous_requires_review` — identity, state, authority, or evidence conflicts prevent a safer classification.

`implemented_and_complete` is excluded from the actionable queue but included in the reconciliation ledger. A merged PR alone is not completion; a pending filename alone is not pending status.

## 7. Lifecycle reconciliation

### Parking Lot

Canonical lifecycle projection is `Captured → Promoted → Implementing → Validation → Complete → Closed`. The existing board may retain its narrower native vocabulary; intermediate states are derived, never written back by WP-4218. Promotion requires an implementing WP reference. Implementing requires implementation evidence and WP. Validation requires a PR/commit plus validation activity. Complete requires implementing WP, PR or equivalent merge evidence, completion receipt, and passing validation report. Closed additionally requires authorized lifecycle closure. Missing required references create blockers and stale findings.

### WIP

WIP states are `discovered → active → blocked | abandoned | validation → complete → archived`. Entry requires an implementing WP/attempt and owner or worker-class reference where authorized. Heartbeats are evidence changes, not wall-clock-only file touches. Stale thresholds are policy-versioned by lane; stale WIP is blocked for review, never auto-abandoned. Reassignment closes the prior attempt and links a new one. Abandonment requires an authorized reason, last evidence, residual scope, and release of file ownership.

### Work packages

Projected lifecycle is `draft → pending → ready → claimed → implementing → validation → accepted → complete → closed`, with side states `blocked`, `abandoned`, `superseded`, and `ambiguous`. Readiness requires resolved dependencies, implementation-ready acceptance criteria, touch points, lane, validation plan, no unresolved duplicate, and no conflicting file reservation. Receipt creation documents authoring or implementation but does not itself advance acceptance.

## 8. Dependency graph and blocked work

Generate a directed graph with candidate/WP nodes and typed edges: `requires`, `blocks`, `supersedes`, `implements`, `validates`, `installs`, `conflicts_with`, and `related_to`. Only `requires` participates in topological readiness. Every edge includes source evidence and confidence; inferred edges require review before blocking unless deterministic policy derives them from explicit scope gates.

Detect self-dependencies and strongly connected components. Any dependency cycle makes all affected candidates `blocked_dependency_cycle`, records the exact cycle, and excludes them from ready ordering. Other blockers include missing/failed/stale validation, unresolved duplicate/supersession review, missing acceptance criteria, unavailable mandatory evidence, stale/abandoned WIP ownership, unmet install boundary, conflicting touch points, and external decision/authority. Blockers identify owner class, evidence, remediation, and recheck trigger; `unknown` is not treated as satisfied.

## 9. Engineering lanes and repository touch points

Assign one primary lane and zero or more secondary lanes from: **Runtime, Office UI, Documentation, Validation, Registry, AI Runtime, Infrastructure, Testing, Governance**. Rules use declared deliverables and expected paths, not title keywords alone. Cross-lane packages expose ownership boundaries; ambiguous assignment blocks readiness. Lane definitions and path patterns are versioned, and exceptions require rationale.

Repository touch points list normalized path/glob, operation (`add`, `modify`, `delete`, `migrate`, `unknown`), ownership (`exclusive`, `shared`, `review_only`), confidence, and source. Classify surfaces as `isolated_workstream`, `shared_non_runtime`, `production_runtime`, `schema_or_registry`, `generated_artifact`, or `unknown`. Unknown or overly broad globs raise merge risk and cannot be called parallel-safe.

## 10. Merge risk, complexity, duration, and readiness

Merge risk is deterministic: `low`, `medium`, `high`, or `critical`, with reason codes. Inputs include exact/glob path overlap with active assignments, shared/generated files, schema/migration/API changes, production runtime reach, breadth, uncertain touch points, dependency coupling, and merge sequence. A score may aid repeatability but the category and contributing facts must be exposed; critical includes incompatible migrations/contracts or concurrent exclusive ownership.

Estimated complexity is `trivial`, `small`, `medium`, `large`, `extra_large`, or `unknown`; estimated duration is a lower/expected/upper range or `unknown`. WP-4218 consumes an authorized WP-4214-compatible estimate when available and otherwise uses an explicitly versioned conservative planning rubric. It must not fabricate precision or infer duration from prose length.

Readiness is one of `ready`, `ready_with_coordination`, `blocked`, `needs_definition`, `needs_evidence`, `needs_review`, `in_progress`, `validation`, `complete`, or `superseded`. Only `ready` and authorized `ready_with_coordination` rows enter executable planning order.

## 11. Priority calculation and authoritative queue output

Priority is a transparent integer planning score from versioned inputs: declared institutional priority, dependency-unblocking value, defect/security/validation urgency, age after promotion (capped), evidence freshness, readiness, and coordination/merge-risk penalty. Missing data contributes zero plus an uncertainty flag, never a favorable assumption. No worker identity or performance ranking enters priority. Ties sort by dependency topological level, lower merge risk, promotion time, then WP identifier and stable candidate ID.

The queue artifact contains a run header and rows with at least:

- priority score, band, factors, and tie-break data;
- WP identifier and candidate identifier;
- source kinds and exact provenance references;
- primary/secondary implementation lanes;
- dependency status, blockers, and graph references;
- repository touch points and ownership;
- parallel safety/group and conflict reasons;
- merge-risk class and reasons;
- estimated complexity and duration range;
- readiness and reconciliation classification;
- evidence/freshness summary and last material change.

Also emit completed/superseded/non-actionable reconciliation views so exclusion is auditable. Machine-readable JSON is canonical for a run; Markdown is a deterministic rendering. “Authoritative” means the sole WP-4218 engineering planning projection for its cutoff, never a replacement for dispatch or source authorities.

## 12. Parallel execution and queue advancement

A parallel-safe group requires satisfied dependencies; disjoint exclusive touch points; compatible shared-file plans; bounded lanes; no common migration/schema/generated target; non-critical merge risk; and a declared merge sequence. Shared files require one named owning assignment; other assignments use review-only changes or an explicit handoff window. Overlapping exclusive paths, unknown touch points, incompatible contracts, or one package modifying another's inputs are conflicting.

Dependency predecessors merge and validate before dependents advance. Queue advancement occurs only after a successful fresh reconciliation run. Claim/assignment evidence moves a row to WIP but is not performed by this process. Reassignment requires closing the old attempt, releasing ownership, preserving evidence, and recording reason/new attempt. Abandoned work retains commits/PRs, residual criteria, blockers, and ownership-release evidence. Merge sequencing orders contract/schema migrations first only when compatibility gates say so, then providers before consumers, isolated changes, generated artifacts, and final integration/validation; package-specific evidence may override with rationale.

## 13. Freshness, audit history, and provenance

Default policy: repository sources are fresh only at the recorded commit; PR facts require a snapshot no older than 24 hours for claim/merge decisions; WIP requires a material-evidence heartbeat within 3 business days unless lane policy overrides; queue publication expires after 24 hours or immediately on a known material source change. These defaults are configuration, not silently embedded constants. Stale data remains visible with age and cannot substantiate readiness or completion.

Each run stores immutable manifest, input locators/digests, cutoff, adapter/schema/policy versions, normalized records, correlations, decisions/reason codes, dependency graph, queue, diagnostics, validation result, and predecessor run. Corrections append superseding records. Provenance must allow any output field to trace to source record(s) and policy rule. Secrets, PR tokens, and copied sensitive payloads are prohibited.

## 14. Required staged artifacts

Future implementation must create beneath `collaboration/workstreams/WP-4218/` only:

- README and authority/boundary statement;
- offline read-only adapters and normalization/correlation library;
- versioned schemas for sources, findings, graph, queue, audit manifest, and policy;
- deterministic policy/configuration for lanes, priority, freshness, risk, and lifecycle;
- synthetic fixtures covering every source/status/evidence conflict;
- CLI that reads explicit fixture/repository snapshots and writes only under staged/output or test temp roots;
- JSON queue, Markdown renderer, reconciliation ledger, dependency graph, and diagnostics examples;
- tests, validation report, implementation receipt, and install-handoff requirements (not installation).

## 15. Required tests and validation

Tests MUST cover:

1. exact, alias, probable, and false-positive duplicate detection;
2. full/partial supersession and residual criteria;
3. partial, implemented-unvalidated, completed, defective/stale, and contradictory evidence;
4. stale Parking Lot and WIP entries without automatic closure/abandonment;
5. dependency cycles, unknown dependencies, and stable topological ordering;
6. queue inclusion/exclusion, all required output fields, tie-breaks, and advancement;
7. lane assignment, ambiguous/cross-lane cases, and versioned exceptions;
8. merge-risk calculation and reason codes;
9. touch-point overlap, shared ownership, conflicting assignments, and parallel groups;
10. blocked/reassigned/abandoned work and merge sequencing;
11. missing/offline PR data represented as unknown;
12. identical logical output and byte-stable ordering across two runs;
13. schema validation, provenance traversal, stale snapshot expiry, and audit linkage;
14. no network dependency, no source mutation, and no write outside staged/temp roots.

Validation must run tests twice and compare outputs, validate all schemas/examples, inventory changed/written paths, test malformed/adversarial records, scan staged artifacts for secrets, and confirm no production orchestrator/shared runtime files changed. The report records exact commands, versions, fixture counts, failures/limitations, output digests, and install prohibition.

## 16. Acceptance and completion gates

WP-4218 implementation is complete only when all staged artifacts exist; required tests pass twice; deterministic outputs match; validation and security/path-boundary checks pass; and an implementation receipt links commit/PR, validation, known limitations, and output digests. Package authoring does not satisfy implementation completion.

No source lifecycle state is mutated by reconciliation. No output may be used for production installation until a separate install package is authorized, merged, validated, and accepted. No runtime scheduler, worker execution, Git/merge automation, Open WebUI, Grace, Helen, Alfred, Local Compute, Evelyn, production orchestrator, or shared runtime behavior is implemented by this package.
