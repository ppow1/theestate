# Traffic Controller / Operations Manager Integration

Status: Implemented  
Classification: Estate Internal

## Purpose

The Traffic Controller / Operations Manager layer records operational posture for Estate work movement. It reviews current runtime artifacts, recommends queue actions, records hold/release/cancel/defer/escalate/assignment decisions, and writes Office-readable summaries.

It does **not** execute providers, provision workers, run a daemon, or replace Alfred, Helen, Ingrid, or the Orchestrator.

## Responsibility Boundary

- **Traffic Controller / Operations Manager:** decides operational posture and records durable operational decisions.
- **Orchestrator:** mechanically evaluates eligible work and creates dispatch state.
- **Helen:** provisions workers.
- **Ingrid:** owns classification and boundary review.
- **Steward:** final authority.
- **Providers:** execute, plan, validate, research, or document only through their own contracts.

## Review Model

Operations reviews are represented by `OperationsReview` in `src/estate/core/traffic_controller.py`. Reviews include counts for intake, schedule, dispatch, assignment, and provider health artifacts; Steward/boundary attention flags; warnings for missing upstream artifacts; and recommended actions.

Recommended actions are represented by `RecommendedAction` and support: `assign`, `reprioritize`, `hold`, `release`, `defer`, `cancel`, `escalate`, `request_boundary_review`, `request_revision`, `request_validation`, and `no_action`.

## Decision Model

Operations decisions are represented by `OperationsDecision` in `src/estate/core/operations_manager.py`. Decisions preserve priority, target, assignment label, provider/worker/seat references, boundary attention flags, summary safety, and metadata.

Decision types are: `assign`, `reprioritize`, `hold`, `release`, `defer`, `cancel`, `escalate`, `request_boundary_review`, `request_revision`, and `request_validation`.

## Runtime Artifact Paths

The runtime writes:

- `runtime/operations/control/reviews/`
- `runtime/operations/control/decisions/`
- `runtime/operations/control/status/latest.json`
- `runtime/operations/control/status/summary.json`
- `runtime/operations/control/status/summary.md`

Runtime directories are created only when commands write artifacts.

## CLI Examples

```powershell
Clear-Host
cd A:\theestate
.\estate.bat operations-review
.\estate.bat operations-decide --decision-type assign --target-type work_package --target-id WP-0609 --assignment-label A2C2 --decided-by Steward --reason "Assign orchestration runtime to C2"
.\estate.bat operations-decisions-list
```

Use `--json` on `operations-review` or `operations-decisions-list` for machine-readable output.

## Integration Inputs

Review generation reads available artifacts and warns when they are absent:

- `runtime/orchestrator/intake/status/queue.json`
- `runtime/orchestrator/schedule/status/queue.json`
- `runtime/orchestrator/dispatch/status/queue.json`
- `runtime/workers/assignments/status/board.json`
- `runtime/providers/health/status/summary.json`

Provider health and assignment board summaries are consumed without duplicating their models.

## Operational Events

Decision recording emits compatible operational events through the existing operational event feed when available. Boundary review and escalation decisions use visible attention states so they remain actionable rather than hidden errors.

## Boundary Behavior

Traffic Controller decisions do not weaken classification. `Restricted`, `Steward Only`, and `Local Only` reasons are redacted in summaries unless the decision explicitly marks `summary_safe: true`. Decision artifacts must not contain credentials, tokens, raw prompts, or private source material.

## Office Consumption Notes

The Office should read `runtime/operations/control/status/summary.json` or `summary.md` for current posture, blocked items, provider capacity warnings, assignment gaps, recommended next actions, and recent decisions. The review artifact remains the detailed source of count evidence and upstream warnings.
