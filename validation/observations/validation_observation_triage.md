# Validation Observation Triage Guide

Use this guide with `validation/observations/VALIDATION_REVIEW_CADENCE.md` when reviewing records from `validation/observations/validation_observations.jsonl` or `validation/observations/validation_observations.md`.

## Status Values

| Status | Meaning | Blocking? |
| --- | --- | --- |
| `open` | Recorded and awaiting review. | No. |
| `investigating` | More evidence is being gathered. | No, unless separately escalated by existing authority. |
| `accepted` | Review agrees the observation is valid enough to track. | No, unless confirmed and separately prioritized. |
| `deferred` | Valid or useful, but intentionally postponed with rationale. | No. |
| `converted-to-work-package` | Follow-up work exists and links back to the observation. | Governed by the follow-up work package. |
| `closed` | No further action is planned. | No. |

## Severity Values

| Severity | Meaning |
| --- | --- |
| `info` | Contextual note or low-risk finding. |
| `follow-up` | Needs later review but is not evidence of a defect. |
| `defect-candidate` | May be a defect; evidence is incomplete or not yet reviewed. |
| `confirmed-defect` | Evidence confirms reproducible behavior that fails expected behavior. |

## Decision Checklist

For each unresolved observation, answer these questions in order:

1. **Is the observation still relevant?** If no, set status to `closed` and record why.
2. **Is there evidence of a reproducible mismatch?** If yes, set severity to `confirmed-defect` and cite the evidence.
3. **Is evidence incomplete but concerning?** If yes, set severity to `defect-candidate`, use status `investigating`, and name the missing evidence.
4. **Does the response require scheduled work?** If yes, create or reference a work package, set status to `converted-to-work-package`, and link the observation ID from the work package.
5. **Can the issue safely wait?** If yes, set status to `deferred` and record rationale plus the next review trigger.
6. **Is no action warranted?** If yes, set status to `closed` and record the closure rationale.
7. **Otherwise, keep it visible.** Leave status as `open` or `accepted` with a concrete next action.

## Evidence Rules

- Confirmed defects must reference evidence, such as a failing command, file path, validation artifact, screenshot, or reproducible manual step.
- Defect-candidates must state what evidence is missing.
- Converted work packages must include the observation ID in their text and must be referenced from the observation record.
- Deferred observations must explain why deferral is safe and what will trigger reconsideration.
- Closed observations must explain why no action is needed.

## Roadmap Momentum Rule

Do not interrupt the active roadmap for every observation. Batch low-risk observations, convert only actionable work into work packages, and escalate only evidence-backed confirmed defects or items prioritized through existing Steward or Chief Architect authority.
