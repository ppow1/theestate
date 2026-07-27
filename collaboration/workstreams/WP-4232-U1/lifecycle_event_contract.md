# Lifecycle and event contract update

The v1 control and client contracts now expose `governed_local_test`, the new
provider commands, provider admission/execution stages, and the emitted
`provider.admitted`, `provider.execution.completed`, and `rollback.recorded`
events. The required completion chain is:

`progression.changed` → `provider.admitted` → `dispatch.submitted` →
`provider.execution.completed` → `dispatch.completed` →
`reconciliation.completed` → `validation.succeeded` →
`grace.receipt.recorded` → `objective.completed`.

Every event is emitted by the service after its durable record is written and
contains the existing envelope’s correlation, causation, authority, audit,
event ID, and position fields. Replay reconstructs the same lifecycle.
