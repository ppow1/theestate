# Estate Comms8 Durable Consultation Foundation

Status: Implemented and locally validated  
Date: 2026-08-07

## Decision

`DURABLE_CONSULTATION_FOUNDATION_READY`

The Estate now has a local SQLite consultation-memory boundary. It owns
logical consultation lineage and durable reasoning context; Comms8 remains
the authoritative live request/lifecycle mechanism.

## Discovery and ownership

PTM is the Estate project/task planning and traceability backbone. Its accepted
implementation baseline is an append-only project/task event log with
rebuildable projections. The repository currently exposes PTM through bounded
read-only adapters and pilot projections; no suitable PTM runtime database was
found for consultation history. Consultation records therefore do not extend
or duplicate PTM objects.

Selected store:

`A:\theestate-data\consultations\consultations.db`

Owner: `estate.core.consultation_store.ConsultationStore`.

The store is created lazily, uses SQLite transactions with `BEGIN IMMEDIATE`,
and supports reopen/recovery without a database service. PTM linkage is by
reference only (`ptm_project_id`, `ptm_work_item_id`) and remains optional.

## Identity contract

Each root receives an Estate-allocated logical ID such as `1.00`. A
continuation receives `1.01` through `1.99`. The persistent fields distinguish
root number, turn number, logical ID, root logical ID, parent turn, and an
explicit predecessor for rollover roots.

The `ec8-*` request ID is stored separately and is never replaced by the
logical consultation ID. `workflow_id`, actor, worker, status, and timestamps
are also retained.

Allocation is atomic and uniqueness-protected. A request for a continuation
after `.99` fails with `rollover_required_after_.99`; a new root may be
allocated only with an existing `.99` `continues_from` predecessor.

## Durable record and search

The record stores bounded current evidence, prior-context summary, question,
objective, recommendation, response and response ID, expected/observed result,
validation evidence, new constraint, continuation reason, status, PTM links,
Comms8 linkage, and GitHub projection metadata. Tags are normalized into an
indexed child table.

Search is bounded and indexed by logical ID, PTM project, tag, workflow,
status, and Comms8 request ID. Semantic/vector search is intentionally out of
scope.

## Comms8 context envelope

Future create/continuation requests should carry the logical ID, root ID,
parent turn, current objective/question, compact prior summary, immediate
recommendation where relevant, Grace's attempted action, observed evidence,
new constraint, and a durable-history reference. Full history is not copied
into every request.

If supplied context is insufficient, the future worker contract is a truthful
`CONTEXT_REQUIRED` result identifying the root and missing range; no model may
improvise missing history.

## GitHub projection

GitHub remains a human-readable asynchronous projection/archive, not runtime
authority and not a transaction dependency. Projection state is `pending`,
`published`, or `failed`, with an optional reference. Projection updates are
local and idempotent; a GitHub outage does not block consultation allocation,
Comms8, response persistence, or validation.

## Future boundaries

The next ChatGPT worker package will use a generic Comms8 mailbox contract:
list/claim the next eligible request as `worker_id=chatgpt`, process only that
request, read its consultation envelope, acknowledge, reason, respond, and
resolve. It receives no Steward-supplied request ID or browser-specific prompt.

Future Grace automation will decide whether work warrants a root or
continuation, allocate through this store, attach the resulting Comms8 request,
observe completion, retrieve the authoritative response, validate the
recommendation, and close, continue, or escalate. It will not allocate IDs
independently or treat response receipt as closure.

If reasoning becomes governed local execution, the existing Local Execution
Adapter Protocol remains the boundary. Consultation ID, PTM references, and
evidence lineage travel as references in the adapter request; the adapter is
not modified by this foundation.

## Implemented files

- `src/estate/core/consultation_store.py`
- `tests/test_consultation_store.py`

## Validation

Focused foundation tests: `7 passed`.

They cover root/continuation persistence, atomic duplicate prevention, `.99`
rollover gating, standalone and PTM-linked records, tags/search, Comms8
attachment, response/validation persistence, GitHub projection states, and
database reopen persistence.

## Activation

No running service consumes this store yet.

- Ctrl+F5: NOT REQUIRED
- New Open WebUI conversation: NOT REQUIRED
- Open WebUI restart: NOT REQUIRED
- Grace Resident Gateway restart: NOT REQUIRED
- Estate Runtime Host/core restart: NOT REQUIRED
- Comms8 service restart: NOT REQUIRED
- MCP adapter restart: NOT REQUIRED
- ChatGPT plugin reconnect: NOT REQUIRED
- Dedicated browser restart: NOT REQUIRED
- Workstation reboot: NOT REQUIRED

`NO_RUNTIME_RESTART_REQUIRED` for this foundation increment. Future code that
imports the store will require only the smallest owner-specific process
restart, if that owner is already running; no activation is required now.
