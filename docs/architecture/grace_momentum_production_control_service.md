# Grace Momentum production control service

`estate.core.grace_momentum_service` is the canonical authenticated command,
query and event boundary for Open WebUI, Estate UI, CLI and workers. Its stable
wire contract is `estate.grace-momentum-control.v1`; consumers should use the
`reference_command`, `TEST_IDENTITIES`, and `FakeGraceMomentumService` fixtures
before connecting to a deployed transport.

Production records live only below `runtime/production/grace_momentum`. The
service never reads or writes fixture roots. Every command has an authenticated
Office identity, an authority source, correlation/causation IDs, idempotency key
and audit reference. Grace controls directives, CME evaluates continuation,
Engineering authorizes technical progression, and Dispatch owns logistics.

The service supports `fixture`, `shadow`, `bounded_live`, and `disabled` modes.
All modes suppress provider effects. `bounded_live` records a governed request
only; a separately admitted provider adapter is required before any execution.
`disabled` rejects all commands. Checkpoints retain event position and completed
idempotency effects; `subscribe(cursor)` returns ordered replayable events.

Health reports storage availability. Readiness is false when disabled and always
reports that provider effects are disabled. Rollback is setting mode to
`disabled`; persisted records and audit events remain available for inspection.
