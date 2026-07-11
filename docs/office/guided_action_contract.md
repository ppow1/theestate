# WP-0523 Guided Action Contract

## Scope
WP-0523 stages a reusable guided-action framework for multi-step Office actions such as `validate -> review -> promote`. It is installed work for the active Office runtime.

## Declarative Workflow Model
A guided workflow declares:

- workflow id and title;
- the existing authority gate that remains in force;
- ordered steps;
- required inputs;
- required confirmations;
- preconditions;
- whether step evidence is required;
- whether a step is irreversible.

## State Contract
Sessions report truthful states:

- `not_started` for a step that has not yet begun;
- `awaiting_input` when required inputs or preconditions are absent;
- `awaiting_confirmation` when explicit approval/confirmation is absent;
- `ready` when the current step may be run by a caller with authority;
- `running` while a handler is active;
- `blocked` when a handler or cancellation rule reports a governed blocker;
- `failed` when a handler errors or required evidence is missing;
- `cancelled` when safely cancelled before irreversible work;
- `completed` when all declared steps have completed.

## Authority Boundary
The framework does not create authority. Confirmations are explicit records, not implied approvals. The staged runtime never auto-confirms, never auto-approves promotion, and never edits shared active Office files.

## Evidence and Audit Contract
Every step start, blocked/failed result, completion, input, confirmation, precondition, cancellation, and ignored terminal advance is appended to session audit evidence. Completed steps that require evidence must return an evidence link or the session fails truthfully.

## Resume Contract
A session snapshot contains the declarative workflow, current step index, status, inputs, confirmations, preconditions, evidence, audit log, and terminal reasons. Restoring a snapshot must not skip missing confirmations or preconditions.

## Cancellation Contract
Cancellation is safe before irreversible steps. If the current irreversible step is already ready, cancellation is blocked and must be resolved by an explicit Office disposition rather than silently cancelled.

## Browser Contract
The reusable browser contract exposes the current step, readiness, permitted UI actions, session snapshot, staged/not-installed status, and explicit authority boundary. A browser may render guidance from this contract but must call the same governed actions and preserve existing authority gates.

## Install Boundary
WP-0531 performs installation. Expected integration targets include a dedicated installed guided-action runtime, Office action registration, browser/UI rendering hooks, tests, and docs.
