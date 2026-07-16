# Estate Project and Task Management KPI, Financial, and Utilization Catalog

## KPI registry contract

Each KPI defines ID, name, owner, formula, numerator, denominator, source events, period, baseline, target, trend, thresholds, exclusions, freshness, confidence, and unknown-value behavior.

## Project KPIs

Completion rate, blocked percentage, overdue work, schedule variance, reopenings, failed/abandoned branches, validation pass rate, acceptance pass rate, forecast accuracy, estimated versus actual effort, velocity, and throughput.

## Task KPIs

Creation-to-triage, triage-to-ready, ready-to-start, execution duration, validation duration, acceptance delay, total cycle time, retries, dispatch attempts, reopenings, blocker duration, branch changes, and final outcome.

## Worker and provider KPIs

Completion rate, first-pass validation rate, failure/retry rate, median execution time, evidence completeness, scope violations, rework rate, blocker time, task-type suitability, utilization, cost per accepted work, and accepted work per dollar.

## Operational KPIs

Work in progress, throughput, queue age, dispatch backlog, validation backlog, acceptance backlog, on-time completion, escalation frequency, utilization/overcommitment, and productive versus blocked utilization.

## Governance and quality KPIs

Provenance completeness, staffing evidence completeness, authorization-reference completeness, read/write-boundary completeness, validation coverage, failed-closed events, unauthorized execution attempts, acceptance without required evidence, audit-chain integrity, and stale/missing ownership.

## Financial and efficiency KPIs

Budget variance, forecast variance, cost per completed/accepted task, rework cost rate, failed-branch cost, local versus external cost, spend by project/provider, cost avoided by local execution, throughput per compute hour, accepted work per dollar, first-pass accepted work per dollar, and cost per validation pass.

## Utilization measures

Available, committed, productive, blocked, idle, overcommitted, queued, validation/rework, maintenance unavailable, project/type allocation, GPU active/reserved, VRAM allocation/peak, CPU/RAM/storage/cache/power/thermal observations, model load/unload time, provider share, quotas, rate limits, availability, and local/external routing mix.

## Data quality

Mandatory fields block KPI publication when absent. Optional and estimated fields publish with confidence labels. Telemetry-derived fields record source and sampling interval. Stale or manipulated data causes warning or suppression rather than false precision.

## Required analysis answers

- **Canonical source of truth:** the append-only Project Task Management event log plus immutable referenced evidence. Current tables, cards, and workspace views are projections.
- **Projection rebuild:** projections are deleted and replayed from ordered events, validating schema version, hash chain, and causation references.
- **ID preservation:** IDs are minted once by namespace (`PORT-`, `PROJ-`, `TASK-`, `BRANCH-`, `WP-`, `DISP-`, `INTAKE-`, `KPI-`, `COST-`) and never reused; import mappings, split/merge/branch events preserve source and descendant IDs.
- **References vs canonical objects:** Parking Lot rows, work-package files, dispatch queue rows, runtime evidence, validation reports, and acceptance records remain authoritative in their domains and are referenced by canonical project/task objects rather than copied into a second execution system.
- **Duplicates:** duplicate detection uses normalized title, source hash, source object ID, semantic hints, and human confirmation; duplicates create `duplicate_detected` and optional `merged_into` events, never silent overwrites.
- **Retention:** archive hides from default planning; trash marks reversible removal; restore reverses trash/archive; legal/audit hold prevents purge; immutable events and evidence references remain retained.
- **Helen and Grace visibility:** task detail summarizes staffing readiness and operational supervision with links to evidence, hiding raw implementation noise by default.
- **Provider recommendations:** recommendations are advisory evidence; Traffic Controller/Operations decisions and budget gates authorize provider selection.
- **Dispatch readiness gates:** scheduling, capacity, budget, privacy/classification, validation-plan, read/write-boundary, and acceptance-owner checks must pass before Dispatch becomes Ready.
- **Cost reconciliation:** local and external estimates are evented, actuals are imported or telemetry-derived, and variances reconcile against accepted cost records.
- **KPI protection:** formulas declare required events, freshness, confidence, exclusions, owner, and manipulation controls; unknown values remain unknown.
- **Scale:** workspace relies on indexed projections, virtualized lists, progressive detail disclosure, saved filters, and graph condensation.
- **Branches:** branches are graph overlays on tasks, not deeply nested folders; winning, abandoned, superseded, and merged paths remain visible in a branch graph.
- **Smallest safe pilot:** ingest selected Parking Lot items into a read-only project/task ledger, link one existing work package and dispatch evidence, compute basic cycle-time and audit completeness KPIs, and expose a compact Office card without execution changes.
