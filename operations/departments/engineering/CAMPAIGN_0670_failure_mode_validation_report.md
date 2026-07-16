# CAMPAIGN-0670 Failure-Mode Validation Report

Date: 2026-07-16. Method: deterministic tabletop exercises against WP-0671–WP-0674 contracts; no production controls were mutated.

| Case | Explicit state | Owner | Evidence path | Recovery | Escalation outcome |
|---|---|---|---|---|---|
| missing intake authority | `held`, readiness `not_ready` | intake authority / Chief Architect | intake source and PTM disposition | record valid parent authority or reject | route decision; no decomposition/Dispatch |
| unmet dependency | `blocked`, ineligible | dependency owner / integration owner | PTM dependency record and predecessor acceptance | complete/accept predecessor or authorized waiver | Chief Architect only for Engineering waiver |
| unavailable worker/provider | `not_ready` or paused | Helen for capacity; routing owner for provider | staffing, health, capacity, reservation refs | reassign and reevaluate; fresh selection/reservation | Grace coordinates; no silent fallback |
| provider failure after partial work | attempt `failed`, package interrupted | branch owner / routing owner | run result, partial commit, logs, handoff | preserve attempt; new attempt, eligibility, Dispatch, explicit transfer | Chief Architect resolves scope/branch ambiguity |
| validation failure | `validation_failed` | validator then package owner | recipe, SHA, environment, report | repair on governed branch; rerun affected stages | no merge/acceptance while failed |
| missing validation recipe | readiness `not_ready` | package owner / Chief Architect | definition and recipe registry lookup | author and approve reproducible recipe | cannot Dispatch |
| stale branch/conflicting PR | `conflict`, integration blocked | integration owner | Git refs, base/head, open PR records | rebase/close/serialize and rerun bound validation | Chief Architect resolves architecture collision |
| contradictory completion evidence | projection `conflict` | evidence owner / validator | receipt, PTM state, report and SHA comparison | superseding correction; retain history; revalidate | no precedence guess, acceptance blocked |
| context rollover | `continuity_blocked` until acknowledged | current owner; Grace/Helen per trigger | handoff/addendum, manifest, hashes | safe-stop, reconcile, explicit transfer/onboarding | full reflection if health trigger applies |
| Steward authority blocker | `blocked_protected` | Steward | durable decision request and authority basis | Steward decision or bounded rejection/hold | only protected question escalates; no routine scheduling |
| post-merge regression | `regression_open`; affected evidence invalid | integration/operations owner | merged SHA, post-merge report, original decision | preserve history; rollback/repair; renewed validation/readiness | renewed acceptance if bound evidence changed |
| campaign pause/resume | `paused`; not cancelled/accepted | authorized campaign owner | pause decision, safe stop, branch/reservation disposition | verify resume conditions; reevaluate stale gates and attempts | material replan returns to Chief Architect |

## Exercise conclusion

All twelve cases stop before an unsafe next action, preserve stable IDs and prior evidence, name one recovery owner, and use existing escalation paths. None invents a waiver, provider fallback, acceptance inference, or second queue. Live system fault injection is outside this non-production-destructive pilot and remains a rollout prerequisite.
