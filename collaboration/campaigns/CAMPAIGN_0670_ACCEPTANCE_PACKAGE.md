# CAMPAIGN-0670 Protected Acceptance Package

Status: **prepared for Chief Architect and Steward review; not accepted**
Authority basis: existing Engineering Department Charter, Steward direction, and CAMPAIGN-0670.
Objective: operationalize Engineering from approved campaign intake through acceptance preparation without a second scheduler, queue, validator, registry, or acceptance path.

## Included packages and inventory

| WP | Submission/integration observation | Principal deliverables |
|---|---|---|
| 0670 | receipt exists; deliverables integrated; acceptance/Gate A record absent | current-state, gap/overlap and reuse maps |
| 0671 | receipt exists; deliverables integrated; acceptance/Gate B record absent | intake, decomposition, readiness contracts and templates |
| 0672 | receipt exists; deliverable integrated; acceptance/Gate B record absent | execution-lane/provider-routing contract |
| 0673 | receipt exists; deliverables integrated; independent acceptance/Gate C record absent | evidence, validation/integration and acceptance/closure contracts; templates/recipe |
| 0674 | receipt exists; deliverables integrated; acceptance/Gate C record absent | status, Notebook, metrics, communication, reflection and dashboard contracts |
| 0675 | implementation/evidence prepared on one branch; PR/merge/protected decisions pending | assessment, pilot, authority proof, failure report, runtime observation, this package, receipt |

Receipts are completion submissions, not protected acceptance. Their historical `not merged` statements conflict with current Git integration for WP-0670–WP-0674; reviewers must reconcile this explicitly rather than treating either prose or file presence as a gate decision.

## Integrated evidence and pilot result

The reconciliation matrix is in `docs/operations/Engineering_Department_Operational_Readiness_Assessment_v1.md`. `PILOT-0670-01` traversed every required lifecycle stage, using live repository definitions/receipts/Git/tests and named fixtures for PTM writes, staffing reservation, Dispatch/provider execution, integration decision, merge/post-merge controls, and protected acceptance. The pilot proves a recoverable fail-closed operating contract; it does not assert live production control-plane health.

Authority boundaries are proven in `CAMPAIGN_0670_authority_boundary_proof.md`. Twelve required fault cases and their state, owner, evidence, recovery, and escalation are in `CAMPAIGN_0670_failure_mode_validation_report.md`. The machine-readable observation is `runtime/departments/engineering/CAMPAIGN_0670_closure_readiness.json` and is explicitly non-authoritative.

## Unresolved conditions and risks

1. **Chief Architect:** reconcile package receipts/Git and record explicit package dispositions and Gate A, B, and C decisions.
2. **Independent validator:** validate the WP-0675 delivered commit and report against the exact SHA/environment.
3. **Integration owner:** review and, only if authorized, merge the PR; then record merged commit and checkpoint.
4. **Operations/validation owner:** execute canonical post-merge validation/reconciliation/readiness against that commit.
5. **Chief Architect:** decide Gate D and Engineering campaign acceptance using exact evidence.
6. **Steward:** make only the applicable final institutional/protected decision; no routine scheduling request.
7. Live PTM eligibility, staffing capacity, provider health/reservation, Dispatch, provider interruption, and pause/resume should be exercised before broad rollout.

Until these close, risks are stale or contradictory state, unqualified live-provider assumptions, validation bound to the wrong SHA, and premature acceptance. Every risk fails closed; no protected gate is averaged away.

## Recommended decision

**Do not accept CAMPAIGN-0670 yet.** Record it as **Conditionally Ready for protected acceptance review**. After conditions 1–4 close, the Chief Architect may accept, accept with bounded conditions, reject to a named stage, or block. Applicable Steward final acceptance follows, never precedes, engineering acceptance/readiness evidence.

## Rollout prerequisites and next campaign

No broad rollout is authorized. The exact recommended next campaign is **“CAMPAIGN-0670 Engineering Operational Control-Plane Live Qualification”**: one low-risk package must exercise canonical PTM eligibility, Helen staffing evidence, provider health/reservation, Execution Dispatch, one controlled provider interruption/recovery, independent validation, merge, post-merge readiness, pause/resume, and metrics/continuity projection. It must reuse the contracts here and must not begin until CAMPAIGN-0670 receives protected acceptance or an explicit authority authorizes the bounded follow-on.

## Archive and continuity instructions

Do not archive now. After protected acceptance, index the campaign definition, six immutable definitions/receipts, PR and merged SHA, validation/readiness reports, gate and acceptance decisions, this package, runtime observation and unresolved condition dispositions. Preserve contradictions and superseding records; do not rewrite receipts. Add a closure observation through the existing Notebook/document surface, complete any triggered reflection/handoff, name continuity owner and recovery entry point, then archive only through existing conventions.

## Requested review sequence

Chief Architect reconciliation and PR review → independent WP-0675 validation → authorized merge → post-merge checkpoint/readiness → Chief Architect Gate D/engineering decision → applicable Steward institutional decision → continuity/archive. No step is implied by the previous one.
