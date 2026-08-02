# Engineering Notebook Operator Runbook

## Review

Inspect the machine-readable state and generated Markdown. Confirm status is
current, source digests match, objective and permitted write paths are expected,
blocker and validation results are truthful, and institutional acceptance is
`not_granted`.

## Handoff and resume

Use a governed request such as: “Engineering, hand this stage to a fresh coding
worker using the verified notebook.” The harness creates a packet from current
state, omits the old transcript, records a handoff, and requires acknowledgment.
Resume only when acknowledgment exactly matches the verified packet.

## Conflict and rejection

If the notebook is stale, ask for freshness verification. If conflicted, stop
and reconcile against the authoritative source. Reject updates that widen scope,
erase blockers, claim failed validation passed, grant authority, or contain
secrets. Preserve the rejection receipt and escalate the unresolved conflict.

## Steward-facing examples

- “Grace, show the current Engineering Notebook for this objective.”
- “Grace, why is this notebook stale?”
- “Grace, hand this stage to a fresh coding worker using the verified notebook.”
- “Engineering, resume from the verified notebook and perform only the current stage.”

These are procedural examples; they are not claimed as live conversational
routes until separately integrated and accepted.
