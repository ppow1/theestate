# Validation Review Cadence

This cadence keeps validation observations visible without allowing every observation to interrupt the active roadmap. Observations are review inputs until the review decision explicitly escalates, defers, converts, or closes them.

## Scope and Inputs

- Primary observation log: `validation/observations/validation_observations.jsonl`
- Human-readable observation log: `validation/observations/validation_observations.md`
- Triage decision guide: `validation/observations/validation_observation_triage.md`
- Follow-up work package locations: `collaboration/work_packages/pending/` or another existing work-package state directory chosen by the authorized reviewer.

This cadence does not create a new department or governance body. The reviewer acts under existing Steward, Chief Architect, or delegated validation responsibilities and does not override Chief Architect or Steward authority.

## Review Frequency and Triggers

Validation observations should be reviewed on the first applicable trigger:

1. **Weekly maintenance pass:** review all open, investigating, accepted, and deferred observations once per week when validation work is active.
2. **Pre-roadmap planning:** review unresolved observations before selecting or sequencing a new group of work packages.
3. **Release or handoff checkpoint:** review observations related to areas being released, handed off, or declared complete.
4. **Evidence update:** review an observation when new validation evidence materially changes its severity, reproducibility, or recommended next action.
5. **Staleness trigger:** review any deferred observation whose rationale references a date, milestone, or dependency that has passed.

The weekly pass is intentionally lightweight: unresolved observations are triaged, not automatically corrected.

## Responsible Review Role

The review is performed by the existing validation reviewer, implementation steward, Chief Architect delegate, or Steward delegate responsible for the affected work stream. The reviewer may recommend escalation, but Chief Architect and Steward authority remains unchanged.

## Non-Blocking Rule

Validation observations remain non-blocking by default. They block roadmap or merge activity only when an authorized reviewer explicitly escalates them into one of these outcomes:

- a confirmed defect with evidence and a blocking decision;
- a follow-up work package that is prioritized by the existing roadmap process;
- a Steward or Chief Architect directive using existing authority.

## Review Steps

1. Read the current observation records in `validation/observations/validation_observations.jsonl` or the rendered table in `validation/observations/validation_observations.md`.
2. Identify observations with statuses that require attention: `open`, `investigating`, `accepted`, or `deferred`.
3. Compare each observation with current validation evidence, related work-package context, and any linked follow-up work package.
4. Assign one triage category from `validation/observations/validation_observation_triage.md`.
5. Record the decision in the observation record by updating status, severity when appropriate, recommended next action, linked follow-up work package when created, and rationale in the source or action text.
6. If a work package is created, include the observation ID in the work-package text and set `linked_follow_up_work_package` on the observation.
7. Preserve forward roadmap momentum by batching low-risk follow-ups and deferring non-urgent items with rationale instead of interrupting active work.

## Triage Categories

Use these categories during review:

| Category | Use When | Required Record Update |
| --- | --- | --- |
| Observation | The finding remains a non-blocking note or needs more context. | Keep or set status to `open` or `investigating`; keep severity as `info`, `follow-up`, or `defect-candidate`. |
| Defect-candidate | The finding may indicate incorrect behavior but lacks enough evidence for confirmation. | Set severity to `defect-candidate`; status should be `investigating` or `accepted`; recommended next action must name the missing evidence. |
| Confirmed defect | Evidence demonstrates a reproducible mismatch between expected and observed behavior. | Set severity to `confirmed-defect`; status should remain `accepted` until corrective work is created or completed; reference evidence. |
| Convert to work package | The issue or improvement needs explicit scheduled work. | Set status to `converted-to-work-package`; populate `linked_follow_up_work_package`; new work package must link back to the observation ID. |
| Deferred | The finding is valid enough to retain but should not interrupt current roadmap work. | Set status to `deferred`; recommended next action must include rationale and the future trigger for reconsideration. |
| Closed with no action | The finding is invalid, obsolete, expected behavior, duplicate, or not worth action. | Set status to `closed`; recommended next action must state the closure rationale. |

## When an Observation Becomes a Confirmed Defect

An observation becomes a confirmed defect only when the record references evidence sufficient for a reviewer to understand the problem without relying on memory. Evidence may include:

- a failing command and output location;
- a reproducible manual validation step;
- a current file path and behavior mismatch;
- a related work-package acceptance criterion that is not satisfied;
- a screenshot or captured artifact path when UI behavior is involved.

Confirmed defects must not rely on vague statements such as "seems broken" or "reported elsewhere." If evidence is incomplete, keep the item as a defect-candidate and record the missing evidence.

## When an Observation Becomes a Work Package

Convert an observation into a work package when one or more of these conditions apply:

- the remediation requires implementation, documentation, validation tooling, or operator workflow changes;
- the finding is important but too large to handle inside the current validation pass;
- the corrective action needs prioritization, ownership, or acceptance criteria;
- a confirmed defect should be fixed through normal work-package tracking.

Converted work packages must include the originating observation ID, for example `Originating observation: VO-0001`. The observation record must set `linked_follow_up_work_package` to the new work-package ID and status to `converted-to-work-package`.

## When an Observation Is Deferred

Defer an observation when the finding is plausible or useful but should not disrupt active work. Deferred observations must retain rationale in `recommended_next_action`, including:

- why it is safe to defer;
- what event, date, dependency, or roadmap checkpoint should trigger reconsideration;
- any evidence that should be gathered before the next review.

A deferred observation is still unresolved and should be revisited at the next matching trigger.

## When an Observation Is Closed With No Action

Close an observation with no action when review determines that:

- the observation is no longer reproducible;
- the behavior is expected and documented;
- the observation duplicates another tracked item;
- the affected capability has been superseded or removed;
- the cost of action outweighs the retained value.

The closure rationale must be recorded so future reviewers do not reopen the same item without new evidence.

## Decision Recording

Decision updates should preserve the original observation ID and any relationship to source work packages. At minimum, record:

- `status` reflecting the decision;
- `severity` reflecting the evidence level;
- `recommended_next_action` with rationale, next trigger, or closure reason;
- `linked_follow_up_work_package` when converted;
- source/evidence references when confirming a defect.

Do not modify prior validation result artifacts simply to make a decision look cleaner. If a past validation result matters, cite it from the observation decision rather than rewriting it.
