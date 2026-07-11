# WP-0530 Operational Workflow Contract

WP-0530 stages guided operational workflows on top of the WP-0523 guided-action contract. This is installed work for active Office runtime files.

## Runtime Guarantees
- Each workflow exposes step-by-step inputs, preconditions, confirmations, guidance, evidence, generated artifacts, and rollback guidance where available.
- Sessions can be saved with `to_snapshot` and resumed with `from_snapshot` without skipping missing confirmations or preconditions.
- State-changing steps require `advance` and invoke named canonical handlers supplied by the installed Office layer.
- The staged runtime reports `awaiting_input`, `awaiting_confirmation`, `blocked`, `failed`, and `completed` truthfully.

## Authority Boundary
The workflow layer does not approve, accept, merge, retry, or select providers automatically. Confirmations are records that an authorized caller supplies; they are not a substitute for the existing Office authority gate.

## Browser/Workspace Contract
The browser contract reports staged/not-installed status, current step guidance, readiness, allowed actions, evidence, artifacts, and explicit authority prohibitions.
