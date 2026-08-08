# Estate Grace Reasoning Loop Implementation and Operations

## Operational-memory grounding

The canonical Grace Resident Gateway recognizes a bounded class of
current-state and consultation-history questions and invokes the read-only
operational snapshot. The snapshot is backed by:

- `A:\theestate-data\consultations\consultations.db` for consultation
  lineage, terminal responses, execution requests, and physical attempts;
- `A:\theestate-data\chatgpt-mailbox-worker\cme-owner-state.json` for the
  current CME state.

The query is deterministic and carries `consultation_store` and `cme_runtime`
provenance. Missing or unreadable authoritative state produces
`STATE_UNAVAILABLE`; model prose cannot fill the gap. Operational reads do
not call the local language model and do not write resident history.

For root semantics, continuation `N.04` belongs to root `N.00`. Completion is
selected from the latest durably ordered turn with a response and terminal
turn state, then roots are compared by authoritative update timestamp and
sequence. Execution occurrence is calculated from durable execution records.

Normal activation boundary: no service restart, worker relaunch, Comms8
restart, MCP restart, browser restart, ChatGPT reconnect, or workstation
reboot is required for this read path. A Grace Resident Gateway restart is
required only if its process has not loaded the deployed code; Open WebUI
restart is conditional on its model catalog or gateway connection being
cached and stale.

## Action claim provenance

`process_chat` records `claim_provenance` as `model_inference` for ordinary
resident prose. A side-effect claim is admitted only with a successful
runtime result carrying `authoritative_action`; a verification claim may use
`authoritative_read`. Without that evidence, the runtime returns an explicit
statement that the action has not been performed or verified. This is a
narrow action-boundary guard, not universal natural-language policing.

The primary catalog model `estate/grace` and the Resident Gateway display
label “Grace (Estate Resident Gateway)” intentionally share the same resident
package and grounding filter. The latter is a presentation alias, not a
second operational-memory source or database.

## Composite request orchestration

The grounding branch has two modes. Direct authoritative reads terminate at
the snapshot only when that snapshot fully answers the request. Composite
operational prompts preserve the original message, acquire the same bounded
snapshot, and pass it as `per_request_authoritative_evidence` into
`process_chat`. The result is checked against bounded obligations such as
provenance, executed/recommended/requested/pending distinctions, and a
requested terminal classification. One repair pass is permitted.

The exact provenance regression now returns `INSUFFICIENT_EVIDENCE` after
stating that no recording occurred, identifying the authoritative read as the
only executed operation, and leaving any write/documentation action pending.
The read-only before/after counts remain unchanged.

## External reasoning dispatch and provenance

The Grace Gateway recognizes ordinary second-opinion language and routes it
through the existing consultation/Comms8/reasoning path. The response
envelope contains request-correlated external-reasoning provenance: root and
turn, Comms8 request, provider, response, status, and a bounded contribution.
These fields are unavailable on failure rather than invented. A previous
unrelated consultation cannot satisfy the current request's correlation.

The gateway was reloaded with the workspace source explicitly preferred over
an older installed Estate package. Focused delegation and grounding tests
pass. The first exact live run reached the repaired dispatch boundary but the
ChatGPT worker failed before authoritative completion; the durable evidence
is preserved under runtime/evidence/cme-owner-isolation/ and remains a
blocker for the live second-opinion receipt.

Terminal selection is evidence-derived after response composition. A model
cannot select `AUTHORITATIVELY_COMPLETED` merely because it completed the
provenance question. Only a successful correlated `authoritative_action` may
select that token; a genuinely requested but queued action selects
`PENDING_EXECUTION`; an unproven underlying action selects
`INSUFFICIENT_EVIDENCE`.

## Reason -> execute -> observe -> reason handoff

The live structured-decision handler remains provider-neutral through
request creation and capability routing. On a terminal execution result it
records validation evidence, then uses the existing execution-continuation
contract to attach a new turn beneath the same root with the execution
request/result reference. The next CME tick is the only worker activation
boundary for reevaluation; completed requests are not rerun.

The 2026-08-08 live acceptance attempt reached Grace intake and created root
`12.00`, but the browser returned an unmarked eight-character assistant
surface with no tool cards before Comms8 responded. The worker therefore
failed closed with `authoritative_comms8_completion_not_proven`; no execution
request was created. Evidence is preserved under the corresponding detached
run directory and is not treated as completion.

## Multi-lane operations and recovery

`estate.core.grace_parallel_portfolio` extends the consultation store with
durable CME activation reservations. The portfolio planner is bounded and
deterministic, exposing READY, ACTIVE, HELD_CAPACITY, WAITING_STEWARD,
VERIFYING, COMPLETE, FAILED, and UNKNOWN with a reason for each candidate.
Two selectors can race safely because the reservation transaction is SQLite
authoritative; continuation-scoped idempotency prevents duplicate CME ticks.

The lifecycle is `RESERVED -> LAUNCHING -> ACTIVE`; the implementation never
uses the CME controller PID as a fake worker PID. Capacity exhaustion is
`HELD_FOR_CAPACITY`/`HELD_CAPACITY`, not failure or global CME busy. Counts are
portfolio-wide durable counts. One root's stale owner, provider failure,
evidence budget, or Steward wait must not clear or freeze unrelated roots.

Process-sensitive ownership tests are run only via
`tools/cme_owner_isolation.py`. Detached run
`cme-owner-20260808T103745815136Z-491998b28f` completed with exit code 0 and
26 passing tests; its manifest, stdout, stderr, and completion marker are
under `runtime/evidence/cme-owner-isolation/`. Live provider/browser
acceptance remains a separate evidence gate.

This reconciles PL-0016/WP-4215 principles selectively: durable ownership,
capacity, dependency/hold reasoning, deterministic priority, and
reconciliation are reused conceptually, while consultation SQLite, CME,
Comms8, execution routing, and existing work-package authorities remain the
production sources of truth.

## Live acceptance blocker

Live ordinary-language intake created roots `19.00` and `20.00` concurrently.
The durable reservation proof showed `20.00` ACTIVE with a real worker PID and
`19.00` HELD_FOR_CAPACITY at observed reasoning capacity one. Root `14.00`
already proved the full bounded execution/reevaluation path with a real
ChatGPT/Comms8 response and completed local Codex Bridge execution.

The browser acceptance then failed closed at the product boundary: the
authenticated `?surface=work` CDP target has no attached Estate Comms8 Live
app, while the former titled `/c/` target is stale and produces stable prose
without authoritative Comms8 resolution. Target selection was repaired to
prefer Work, and the existing UI recovery seam was attempted; it now truthfully
returns `LIVE_APP_NOT_FOUND`. PL-0016/WP-4215 therefore remains open for the
Steward's app-attachment action and subsequent rerun of Comms8 correlation,
worktree/conflict, failure-isolation, and Grace conversational portfolio
acceptance. No premature lifecycle closure is recorded.
