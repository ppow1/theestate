# CME Execution-Branch Controlled Fixture Acceptance — 2026-08-07

Status: accepted; complete CME-owned execution branch proven.

This acceptance uses the existing detached CME observer boundary and a new
safe fixture under `Temp/cme-execution-fixtures/full-loop-20260807/`. The
fixture starts with `actual=incorrect`, `expected=correct`, and
`status=invalid`; `INVARIANT.md` defines the required correction. Production,
live runtime, and source paths are prohibited from the provider write scope.

The fixture manifest provides restart identity. A restarted acceptance reuses
the same consultation and existing evidence/execution requests by durable
purpose and consultation correlation. Completed evidence is historical and
does not suppress a materially distinct execution request. No consultation
8.00 state is reopened or changed.

The live path will record Grace intent, CME-owned reasoning, optional bounded
read-only fixture evidence, validated `EXECUTION_RECOMMENDED`, the neutral
execution request, provider/attempt evidence, fixture before/after state,
validation, CME-owned reevaluation, Grace outcome, final CME state, and an
inert duplicate tick. A truthful bounded non-execution result remains a
blocker rather than being converted into execution.

Activation requirements for the normal path: no manual mailbox-worker launch,
no manual execution-provider launch, no Estate service restart, no browser
restart, and no workstation reboot. Only the detached acceptance harness is
required.

## Live result

Detached run `cme-owner-20260807T181913080846Z-e4d1fd30cd` reused consultation
9.00. CME-owned reasoning first returned `MORE_REASONING_REQUIRED`; read-only
provider evidence proved the fixture invalid without modification. The
continuation then authoritatively returned `EXECUTION_RECOMMENDED`, but its
structured execution object omitted `required_capability`,
`validation_criteria`, `evidence_requirements`, and consultation correlation.
The acceptance failed closed and did not execute or alter the fixture.

Detached terminal reconciliation completed successfully: CME is `IDLE`, the
lock is absent, and the duplicate tick is `EMPTY_QUEUE`.

Precise blocker: `EXECUTION_RECOMMENDATION_INVALID:SPEC_MISSING_REQUIRED_FIELDS`.

## Superseding accepted continuation

The producer prompt now enumerates the canonical execution fields and neutral
capability vocabulary. The strict validator also accepts the canonical
`consultation_id` correlation object, requires path-only scopes, and requires
explicit `write_scope` for repair/write objectives. A malformed recommendation
creates one idempotent format-repair continuation without evidence reacquisition
or execution.

Detached run `cme-owner-20260807T185213865238Z-8395944474` completed the same
controlled root. The valid recommendation selected
`software_engineering_test`, wrote only the fixture file, and completed physical
attempt `attempt-e22d32c59b16` through execution request `exec-58b8a31e261c`.
The fixture changed from invalid to valid. Continuation 9.04 returned
authoritative `INFORMATION_ONLY`; CME ended `IDLE`, the lock was absent, and
the duplicate tick returned `EMPTY_QUEUE`.

Accepted receipt: `CHATGPT_EXECUTION_RECOMMENDATION_SCHEMA_READY`.
