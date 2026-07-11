# WP-4023 Staged Resident Work Delegation and Handoff Runtime

This workstream stages deterministic delegation and handoff contracts under an isolated path for later installation by WP-4031.

## Contents

- `src/wp4023_delegation_runtime/runtime.py` — local delegation state machine, authority metadata contract, evidence model, ownership transfer guard, idempotent retry behavior, and handoff receipt creation.
- `tests/test_delegation_runtime.py` — staged pytest coverage for requests, acceptance/decline, authorized transfer, stalled/rejected visibility, idempotent retry, and completion receipts.
- `install_manifest.json` — integration handoff and validation plan.

## Isolation Boundary

No active assignment, CLI, Dispatch, Office, mailbox, audit, or shared runtime file is modified by this staged package. Delegation messages do not grant authority; future integration must supply authority and approval metadata from existing active mechanisms.
