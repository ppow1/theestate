# WP-4219 — Engineering Campaign Dashboard

- **Status:** Pending
- **Source:** Estate Authored Backlog Implementation campaign assignment; no matching Parking Lot item
- **Mode:** architecture-only authoring; future isolated staged implementation
- **Future implementation root:** `collaboration/workstreams/WP-4219/`
- **Install authority:** none; runtime installation requires a separate implementation/install package

## 1. Mission and authority

Define and, in a future package, stage a canonical operator-facing **Engineering Campaign Dashboard** that presents engineering execution state without becoming a source of that state. The dashboard is a deterministic, read-only presentation projection for execution queue, work-package readiness, engineering lanes, merge readiness and risk, dependencies, blockers, parallel opportunities, campaign health, repository reconciliation, Parking Lot, WIP, completion, validation, activity, metrics, audit, and provenance.

The dashboard is not a database, queue, scheduler, assignment authority, Git client, merge controller, acceptance authority, Office replacement, or operational command surface. It MUST reference authoritative records in place, expose contradictions and unknowns, and never mutate a source. A displayed action is guidance only unless a separately governed system authorizes it.

This package authors architecture only. It MUST NOT implement a runtime dashboard, Open WebUI page, browser UI, React, HTML, CSS, JavaScript, runtime scheduler, worker execution, Git automation, repository automation, shared runtime, or production dashboard behavior.

## 2. Required reuse and non-duplication boundary

WP-4219 consumes, and MUST NOT redefine:

| Provider | Consumed contract | Dashboard treatment |
|---|---|---|
| WP-4214 — Duration Estimation | versioned estimate range, confidence, components, freshness, provenance, actual/calibration summaries | render estimates and duration metrics; preserve `unknown`/`not_estimable`; never calculate or calibrate estimates |
| WP-4215 — Parallel Worker Orchestration | advisory assignments, lanes, worker capacity/health, parallel groups, ownership, conflicts, merge order, audit | visualize plans and utilization; never assign, reserve, rebalance, dispatch, or control workers |
| WP-4217 — Local Git Synchronization Assistant | repository observations, divergence/conflict exposure, freshness, recommendations, diagnostic provenance | summarize repository and merge exposure; never fetch, pull, push, stash, reset, rebase, merge, or remediate |
| WP-4218 — Backlog Reconciliation and Execution Queue | canonical run manifest, queue, reconciliation ledger, graph, readiness, blockers, lanes/touch points, parallel safety, merge risk, freshness, evidence links | primary dashboard projection; never create a second queue, reconcile independently, or write lifecycle state |

Also reuse the Engineering Campaign Operational Status Model, evidence/acceptance contracts, Parking Lot and WIP authorities, PTM source references, validation reports, completion receipts, and hosting-provider snapshots. Existing Office/Steward/operator surfaces remain authoritative for their own purposes. WP-4219 may deep-link to them but MUST NOT copy their action controls, inboxes, lifecycle mutation, or broad Estate operations concepts.

Provider absence, incompatible versions, or stale data is a visible degraded state. It never licenses a local substitute calculation. Until WP-4214–4218 implementations publish compatible artifacts, affected panels show `unavailable` with the missing contract and no favorable inference.

## 3. Dashboard architecture

The future implementation is a renderer over an immutable **dashboard snapshot**:

```text
versioned read-only provider adapters (WP-4214/15/17/18 + governed evidence)
                              |
                compatibility + freshness gate
                              |
     normalized references (no second domain record or queue)
                              |
 deterministic summary/panel view-model + invariant validation
                              |
 machine-readable snapshot + deterministic non-browser reference rendering
                              |
                 operator-selected read-only views
```

A snapshot binds `dashboard_snapshot_id`, campaign scope, repository cutoff, provider run IDs/digests, source high-watermarks, schema/policy/renderer versions, `observed_at`, freshness policy, previous snapshot, validation verdict, and output digests. Logical panel content and order must be byte-stable for identical provider artifacts and policy; observation metadata is isolated in the envelope.

Publication is fail-closed and transactional. An invalid candidate never replaces the last valid snapshot. The header shows whether the view is `fresh`, `degraded`, `stale`, `invalid`, or `unavailable`, identifies the last valid snapshot, and lists provider-specific reasons. The renderer may filter and sort an immutable snapshot but may not silently recompute domain state.

## 4. Common view and interaction contract

Every panel uses the same campaign/package identity, lifecycle vocabulary, cutoff, status tokens, freshness presentation, severity colors plus text/icon equivalents, and source-link behavior. Each summary value exposes:

- literal value and unit, status (`known`, `unknown`, `conflict`, `not_applicable`, `unavailable`), and definition/version;
- source provider, record/run identifier, exact locator/digest, observed/effective times, and age;
- applied filter/scope and denominator for aggregates;
- reason codes, contradictions, and drill-down to contributing records;
- last material transition and previous comparable value when meaningful.

Default scope is one explicitly selected campaign. Cross-campaign totals are labeled portfolio summaries and never blended into campaign health. Filters include campaign, lane, readiness, classification, blocker, risk, validation, freshness, and time window. Filters change presentation only. Stable ordering is defined per panel, keyboard/accessibility requirements are reserved for the future UI package, and information cannot depend on color alone.

## 5. Required dashboard panels

### 5.1 Executive Summary

Show campaign identity, snapshot health/freshness, package counts by lifecycle/readiness, ready/blocked/WIP/validation/complete counts, top blockers, critical merge exposure, estimated completion range with confidence, queue age, stale count, and outstanding authority decisions. Health is a reason-coded assessment, not a manufactured completion percentage or acceptance decision.

### 5.2 Execution Queue

Render the WP-4218 queue without copying it: stable rank, priority factors, WP, readiness, lane, dependencies, blockers, parallel group, merge risk, duration range/confidence, source cutoff, and last material change. Expose excluded/completed/superseded rows through linked reconciliation views. Never label the projection as dispatched or executable authority.

### 5.3 Ready Work

Show only WP-4218 `ready` and authorized `ready_with_coordination` rows, readiness evidence, coordination conditions, duration estimate, lane/capability needs, touch points, validation plan, parallel compatibility, and next authorized actor/action. Unknown or stale mandatory evidence excludes a row.

### 5.4 Blocked Work

Group blockers by dependency, evidence, definition, validation, merge/repository, ownership, duplicate/supersession review, external decision, and installation boundary. Show first unresolved time, age, owner class, affected dependents, remediation/recheck trigger, and source. The view does not clear blockers.

### 5.5 Parallel Opportunities

Consume WP-4215 plans and WP-4218 parallel groups. Show compatible packages, lane capacity, estimated overlap/savings when supplied, exclusive/shared paths, owning assignment, merge sequence, coordination gates, conflicts, and confidence/freshness. Absence of a WP-4215 plan means `unavailable`, not parallel-safe.

### 5.6 Merge Risk

Show package/PR, risk class and reasons, base/head/validated commits, overlap/exclusive ownership, contract/schema/migration/generated-file exposure, branch divergence and predicted conflicts from WP-4217, required sequence, reviews/checks, and stale hosting facts. It recommends review priority but never merges or declares acceptance.

### 5.7 Repository Health

Summarize WP-4217 local/remote observation availability, branch divergence, dirty/untracked/stash state when policy permits, unresolved/conflict exposure, orphan branches/PRs, validation-to-head mismatch, last synchronization observation, and recommendations. Secrets and raw sensitive diffs are prohibited. No Git operation is offered.

### 5.8 Parking Lot

Reference canonical Parking Lot rows and WP-4218 reconciliation: Captured, Promoted, implementing/validation projection, Complete, Closed, stale, missing WP, conflicting, duplicate, and superseded counts. Show promotion milestone, condition, linked WP/evidence, age, next review, and discrepancies. Never mutate status or invent an item.

### 5.9 Work In Progress

Show attempt, package, owner/worker class, lane, branch/PR references, state, material heartbeat, age, current evidence, blockers, path ownership, estimate versus elapsed (when comparable), next checkpoint, and stale/abandoned/reassignment facts. Do not infer activity from file modification time or provide worker controls.

### 5.10 Completed Work

Show reconciliation-classified completion by package with merge/commit, receipt, validation, acceptance/closure state, actual duration, completed scope, and residual/defect evidence. Separate `implemented_and_complete` from merged-only, receipt-only, accepted, and closed. Authoring receipts are never implementation completion.

### 5.11 Dependency Graph

Render WP-4218 typed nodes/edges, topological levels, critical/unblocking paths, cycles, unmet/unknown dependencies, supersession and validation/install relationships, selected-node evidence, and downstream impact. Only explicit/provider-authorized readiness edges block execution; inferred relationships are labeled review candidates. Provide an equivalent tabular representation.

### 5.12 Engineering Metrics

Present governed definitions and denominators for authored, merged, validation progress, average implementation duration, estimated completion, queue age, stale work, blocked work, lane utilization, and merge-conflict exposure. Section 6 defines the metric contract.

### 5.13 Validation Status

Show required recipes, latest verdict, tested commit/digest/environment, age/expiry, missing/failing/stale/conflicting results, post-merge status, and acceptance distinction. A passing test does not imply acceptance and a newer commit invalidates a commit-bound verdict for readiness purposes.

### 5.14 Recent Activity

Chronologically show material provider events—authoring, promotion, assignment evidence, commit/PR transitions, validation, receipt, blocker, merge, acceptance, closure, and reconciliation publication—with actor/authority, source time, ingestion time, IDs, and links. File mtimes and chat assertions are not activity facts.

### 5.15 Audit History

Show immutable snapshot lineage, provider cutoffs/digests, policy/schema/renderer changes, publication verdicts, changed summary fields with reason codes, corrections/supersession, and reviewer-visible export references. Audit records cannot be edited through the dashboard.

## 6. Engineering metrics and health indicators

Each metric carries `metric_id`, definition version, campaign/time scope, numerator, denominator, unit, value/range, confidence/status, provider cutoff, sources, and exclusions. Never replace missing facts with zero.

| Metric | Required presentation |
|---|---|
| Work packages authored | count of package authoring events/records in window; distinguish currently pending and authoring receipts |
| Work packages merged | count with hosting/local merge evidence; separate merged from validated, accepted, complete, and closed |
| Validation progress | passed required recipes / all applicable required recipes; show failed, missing, stale, waived, and N/A separately |
| Average implementation duration | mean plus median, sample count/range, start/end semantics, outlier policy; consume governed actuals/WP-4214 semantics |
| Estimated completion | lower/expected/upper campaign range, confidence, assumptions and critical dependencies from compatible providers |
| Queue age | current time minus queue promotion/readiness start as defined; show median, maximum, bands, and unknown count |
| Stale work | count/rate by versioned freshness rule and source; distinguish queue, WIP, validation, Git/PR, and provider staleness |
| Blocked work | count/rate plus duration, severity, reason/owner and downstream impact; never count unknown as unblocked |
| Lane utilization | planned/active load divided by declared compatible capacity from WP-4215; show units, unknown capacity, overcommit |
| Merge conflict exposure | packages/PR pairs with risk reasons, weighted and unweighted counts, affected paths, uncertainty; consume WP-4217/18 |

Health indicators are `healthy`, `attention`, `critical`, or `unknown`, always with facts and policy thresholds: queue freshness, evidence completeness, dependency integrity, blockage pressure/age, lane capacity/imbalance, validation coverage, merge exposure, repository synchronization, completion coherence, and audit continuity. Campaign health aggregates by an explicit versioned rule and may be `unknown`; it does not grant a gate or acceptance decision.

## 7. Operator summaries

The snapshot emits deterministic summaries for:

1. **Now:** fresh ready work, active WIP, new blockers, validation/merge decisions due.
2. **Next:** dependency-unlocking and parallel opportunities with conditions and estimate ranges.
3. **Risk:** stale evidence, critical merge exposure, cycles, over-capacity lanes, conflicting lifecycle claims.
4. **Progress:** authored/merged/validated/completed deltas and estimate-to-actual trend.
5. **Authority:** decisions awaiting named authority and the exact evidence prerequisite.

Summaries use templates and stable reason ordering. They contain no generative unsupported prose; every sentence/field traces to provider facts and a renderer rule. Empty states distinguish `none`, `unknown`, `unavailable`, and `filtered_out`.

## 8. Operator workflows

### Daily review

Verify header/cutoffs → inspect degraded/stale providers → read Executive Summary and new risks → review WIP/blockers/validation/merge risk → inspect Ready/Parallel opportunities → follow evidence links → record decisions only in their governing systems → request a refresh. The dashboard itself performs no decision or mutation.

### Campaign startup

Select canonical campaign → verify package identity/dependencies and compatible provider versions → require a fresh WP-4218 reconciliation → inspect readiness, graph, lanes, merge ownership, estimates, validation plans, and repository baseline → confirm authority decisions outside the dashboard → publish the initial validated snapshot.

### Campaign shutdown

Freeze a final source cutoff → reconcile every package and open attempt/PR → separate merged, validated, accepted, complete, closed, residual and superseded work → review Parking Lot/WIP disposition, receipts, validation and repository health → publish final snapshot/audit export → record campaign acceptance/closure only through protected authority.

### Queue refresh

Request provider refresh through its existing authorized process → wait for immutable WP-4218 run → bind compatible WP-4214/15/17 artifacts by cutoff → validate completeness/compatibility/determinism → publish candidate or retain last valid snapshot with failure diagnostics. Never refresh by scraping/mutating sources from the dashboard.

### Assignment generation

Filter Ready Work → inspect dependencies/touch points/duration/capacity → consume a WP-4215 advisory plan → review conflicts and merge sequence → export/link the advisory selection → submit it to the separately governed assignment authority. No dashboard assignment action exists.

### Merge review

Select package/PR → verify base/head, validated digest, reviews/checks, dependency order, ownership overlap, WP-4217 exposure, WP-4218 risk, receipt/acceptance distinction → record merge decision in the hosting/governance authority → refresh providers and confirm post-merge reconciliation.

### Dependency review

Inspect graph and table → focus cycles/unknown/unmet/critical-path edges → follow evidence → correct or approve inferred relations only in the governing package/graph authority → refresh reconciliation → verify downstream readiness change and audit diff.

### Parking Lot reconciliation

Compare board-native state with WP-4218 projection → inspect missing WP/evidence, stale promotion, duplicate/supersession, WIP and completion conflicts → update only the canonical Parking Lot through its governed workflow → refresh and verify the projected change. WP-4219 never promotes or closes an item.

## 9. Freshness, audit, and provenance

The dashboard inherits provider freshness and adds snapshot freshness. It displays provider observed/effective/cutoff times, age, threshold/policy version, expiration reason, and whether a material source changed. The strictest mandatory-provider expiry governs an action-oriented panel; informational panels may remain visible but visibly stale. Clock/skew and unavailable time evidence yield `unknown`.

Every panel, aggregate, graph element, summary sentence, and health indicator traverses to the provider record(s), source locators/digests, and renderer rule. Snapshot lineage is append-only. Corrections create a superseding snapshot. Tokens, credentials, private raw payloads, copied sensitive diffs, and unbounded personal/worker telemetry are prohibited.

## 10. Future implementation deliverables and installation boundary

A future implementation package may create only beneath `collaboration/workstreams/WP-4219/`:

- authority/boundary README and provider compatibility matrix;
- versioned dashboard snapshot/view-model schemas and renderer policy;
- read-only adapters for published WP-4214/4215/4217/4218 artifacts and governed evidence references;
- deterministic summary, panel, metric, health, graph/table, and non-browser reference renderers;
- synthetic fixtures, examples, tests, validation report, implementation receipt, and `INSTALL_HANDOFF.md`.

WP-4219 authoring does not authorize that implementation. No browser/UI framework or production integration is included. A separate future implementation package must define the staged code; a later install package must name the destination surface, reuse an existing Office/operator architecture, prevent duplicate queues/actions, define ownership/security/accessibility/performance, migrations, compatibility, rollback, validation, and acceptance.

## 11. Required validation

Future validation MUST prove:

1. **dashboard completeness:** all 15 panels and required fields/empty/degraded states exist;
2. **view consistency:** common IDs, vocabulary, scope, cutoff, freshness, statuses and links agree across panels;
3. **dependency visualization:** typed edges, cycles, unknowns, critical/unblocking paths and accessible table are correct;
4. **queue visualization:** WP-4218 rank/content/exclusions are preserved without a second queue;
5. **metrics generation:** definitions, denominators, ranges, unknowns and source traces are correct;
6. **engineering lane presentation:** capacity, utilization, assignments, cross-lane work and unavailable WP-4215 data are honest;
7. **merge-risk presentation:** WP-4217/4218 reasons, commit binding, ownership and stale PR facts are preserved;
8. **operator workflows:** daily/startup/shutdown/refresh/assignment/merge/dependency/Parking Lot walkthroughs reach sources and never mutate them;
9. **deterministic summaries:** identical logical inputs produce byte-identical logical snapshots/renderings twice;
10. provider compatibility/freshness failure, conflicting evidence, missing host/network data, malformed/adversarial input, schema validation, provenance traversal, audit lineage, secret scanning, and write-boundary enforcement.

Validation records exact commands, versions, fixture/panel/metric counts, two-run output digests, failures and limitations. Tests must assert no network requirement, source mutation, Git operation, scheduling/dispatch/assignment/merge/acceptance effect, or write outside the staged/test-temp root.

## 12. Acceptance criteria

1. Architecture defines every requested panel, metric, workflow, freshness, audit, provenance, and health behavior.
2. WP-4214, WP-4215, WP-4217, and WP-4218 are consumed through compatible published artifacts and are not redefined.
3. Existing Office/operator UI concepts and canonical source authorities are referenced, not duplicated.
4. Queue, dependency, lane, merge-risk, completion, reconciliation, validation and Parking Lot presentations retain source status, evidence and uncertainty.
5. Summaries and metrics are deterministic, definition-versioned, scoped, explainable, and provenance-complete.
6. No dashboard output grants execution, assignment, Git, merge, lifecycle, installation, validation, or acceptance authority.
7. Future implementation and production installation each require separately authorized packages; no runtime/UI code is part of this authoring package.
8. Required validation covers completeness, consistency, visualizations, metrics, workflows, determinism, security and no-mutation boundaries.

Package authoring is complete when this contract, its supporting design, documentation checks, and authoring completion receipt are reviewed. Engineering Campaign Dashboard implementation remains pending.
