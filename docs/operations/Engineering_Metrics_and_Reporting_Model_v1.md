# Engineering Metrics and Reporting Model v1

Status: Gate C operational contract  
Owner: Chief Architect

## Measurement rules

Metrics are timestamped, reproducible, read-only projections from canonical events. Every value publishes window, population, formula version, source high-watermark, exclusions, unresolved conflicts, and observation time. Durations use canonical event timestamps and a declared UTC/business-calendar policy. Missing endpoints yield censored/unknown observations, not zero. Retries remain distinct attempts. Metrics inform decisions; they never set priority, staffing, readiness, routing, validation, acceptance, or authority.

## Metric catalog

| Metric | Formula | Canonical source records | Interpretation boundary |
|---|---|---|---|
| campaign throughput | campaigns explicitly accepted in window / window duration | Chief Architect campaign acceptance decisions | do not count merge or receipt |
| package cycle time | `package_acceptance_at - intake_ready_for_planning_at`, median/P50/P90 | PTM lifecycle + acceptance decision | report cancelled/censored separately |
| queue latency | `assignment_or_dispatch_eligible_at - intake_at` | PTM lifecycle/eligibility | includes governance wait; not worker speed |
| readiness latency | `first_ready_at - readiness_evaluation_requested_at` | PTM readiness events | split blocker classes |
| implementation time | sum of active execution-attempt intervals | Dispatch/provider result events | excludes queue/validation; overlapping attempts unioned per package |
| validation latency | `terminal_validation_at - validation_requested_at` by phase | recipe/report/reconciliation events | passing and failing cohorts separate |
| integration latency | `merge_or_close_at - PR_opened_at` | hosting Git/PR events | open PRs censored; merge is not acceptance |
| rework rate | packages with a new implementation attempt after failed validation/rejected review / packages reaching validation | attempt, validation, PR review | planned iteration is excluded and declared |
| blocker age | `as_of - first_unresolved_at`; recovery = `resolved_at - first_unresolved_at` | PTM/Grace blocker events | group by class/owner; age is not severity |
| provider success/failure | terminal successful/failed attempts / terminal provider attempts | Dispatch/provider reconciliation | timeout/cancelled shown separately; stratify provider/version/work class |
| Codex/local utilization | active attempt time for lane / active attempt time across measured lanes | provider/Dispatch attempt events | not staffing utilization or quality |
| stale package count | active packages exceeding declared no-material-transition threshold | PTM events + status policy | threshold shown; blocked packages not hidden |
| orphan branch/PR count | branches/PRs lacking active owner/package or terminal disposition | Git/PR + branch ownership | automated/dependency branches excluded explicitly |
| continuity handoff frequency | verified handoffs / active-package-months | continuity artifacts + assignments | simple handoffs and full renewals split |
| reflection-trigger frequency | governed trigger events / officeholder-months | Helen/reflection process records | trigger is not failure or renewal approval |
| Steward interruption rate | routine scheduling requests to Steward / package transitions | canonical messages/decisions + PTM events | protected/priority/exception decisions reported separately |
| autonomous transition percentage | eligible package transitions completed without Steward scheduling request / eligible transitions × 100 | PTM events and linked communication decisions | excludes constitutionally retained Steward decisions from denominator and publishes exclusions |

A provider “success” means its bounded execution result met the provider-event success contract, not validation or acceptance. “Without Steward scheduling” means the transition was advanced by its already-authorized owner/mechanism; it never masks a required Steward authority event.

## Reporting surfaces

All surfaces query the same status projection and link through to canonical sources:

- **Grace operational campaign view:** ready/active/blocked packages, checkpoint age, next authorized operational action, blocker owner, handoff risk. No architecture approval control.
- **Chief Architect portfolio:** campaign/gate state, architectural decisions, evidence completeness, commit-bound validation, PR/integration and acceptance decisions.
- **Helen demand view:** role/capability requirements, assigned capacity, shortages, handoff/health triggers. No priority control.
- **Alfred routing view:** unresolved/overdue acknowledgements, destination resolution and canonical message links. No work state mutation.
- **Steward executive summary:** outcomes, protected exceptions, strategic blockers, interruption rate and decisions actually requiring Steward authority.
- **Campaign detail/package drill-down:** complete mapped status record, attempts, evidence, Notebook index, timeline and next actor.
- **Blocker/risk aging:** class, impact, owner, first-seen, last transition, recovery target and escalation route.
- **Provider evidence:** stratified capability/health, success/failure, latency, utilization, expiry and sample size; never an automatic selector.

Reuse existing boards, PTM/orchestrator and operations command/dashboard surfaces. A generated page declares `read_only`, observation time, source links and conflicts; export or cache cannot accept commands or overwrite sources.
