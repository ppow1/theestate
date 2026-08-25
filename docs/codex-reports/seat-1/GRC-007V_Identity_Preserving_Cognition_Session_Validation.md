# GRC-007V — Identity-Preserving Grace Cognition Session Validation

Package: GRC-007V
Roadmap package: GRC-003-F3 — Identity-preserving Grace cognition session boundary
Role: C1 independent implementation validator
Verdict: PASS

## Scope and repository verification

The implementation commit was independently fetched and verified in
`ppow1/Riverview`:

- Branch: `codex/c484-operator-persistent-service`
- Commit: `726b88755f8881fb283b5ac9a472290c6d33f37b`
- Parent: `005f953f63975ae83a1d61291ee1dbe9d80bf74a`
- Subject: `Implement identity-preserving cognition sessions`

The commit changes only:

- `src/riverview/reasoning/session.py`
- `src/riverview/reasoning/__init__.py`
- `tests/test_cognition_session.py`

No runtime gateway, F1 contract, F2 provenance module, early F4 assembler,
migration, provider implementation, model, GPU, or Campaign Runner file was
changed.

## F3 roadmap compliance

PASS. The accepted GRC-003-F3 definition is an identity-preserving cognition
session boundary over existing `ImplementationBinding`, `RuntimeSession`,
resident runtime/context identity anchors, and River persistence. Its required
scope is session/turn identity, implementation replacement continuity,
wrong-binding/stale-context rejection, persisted readback, and no provider or
resource execution.

The implementation matches that boundary through `CognitionSession`,
`CognitionSessionTurn`, `CognitionSessionBoundary.open`,
`open_from_runtime`, `bind_request`, `replace_implementation`,
`reconstruct`, and `validate_turn`. It does not silently implement later
provider routing, model invocation, resource selection, escalation, or F4.

F3 remains correctly classified; this is not a relabeled F4 or provider task.

## Identity and session/request checks

PASS. `CognitionSession` carries independent UUIDs for session, resident,
occupant, office, and implementation, plus a separate authority reference,
bounded state references, status, and schema version. Construction rejects a
session ID equal to the resident ID. `CognitionSessionTurn` separately carries
session ID, request ID, correlation ID, and the identity correspondence.

The inspected implementation preserves:

`Office != Occupant != Resident != Implementation != State`

and keeps authority separately represented. `session_id != resident_id` and
`session_id != request_id` are enforced. Multiple requests can share a session
while retaining distinct request and correlation IDs.

`bind_request` compares resident, occupant, office, implementation, and
authority against the session before appending the durable attachment event.
`validate_turn` and reconstruction repeat the correspondence checks, so the
durable boundary is not protected only by constructor use.

## Adversarial identity probes

PASS.

- Transcript content claiming another resident is not a session field and is
  ignored by supported payload reconstruction; authoritative resident,
  occupant, office, implementation, and session IDs remain unchanged.
- Provider/model metadata is absent from the session and turn envelopes.
  Adding provider-like or transcript-like payload keys does not replace typed
  identity fields.
- A request with a wrong resident or office is rejected before attachment.
- A turn from session A is rejected when validated against session B.
- Wrong authority is rejected at request binding.
- Runtime/binding occupant mismatch, runtime/context office mismatch, inactive
  binding, and stale context are rejected by `open_from_runtime`.
- Implementation replacement retains session, resident, occupant, office,
  authority, and state references and records the predecessor implementation
  in an append-only River event.

The focused F3 tests genuinely exercise these cases rather than only checking
constructors. I also inspected the direct `from_payload`, `validate_turn`,
runtime adapter, and reconstruction paths.

## F2 provenance integration and lineage

PASS. F3 uses the existing River/EventStore protocol and records session-open
and request-attached events under the `cognition_session` aggregate. The
attached request ID and correlation remain distinct from the session ID.

F3 does not alter the accepted F2 provenance writer or its exact stored-request
correspondence gates. Session membership is an additional relation; it is not
used as a substitute for F2 request/result validation or authority. The
accepted F2 tests for resident/occupant/office/implementation/authority/source
mismatch, forged result rejection, correlation/causation, failure provenance,
and restart lineage passed in the independent run.

The source-to-request/result lineage remains owned by F2. The F3 session event
provides the bounded session relation without claiming that session membership
alone authorizes a result.

## Persistence and restart

PASS. No process-local object identity is required. `CognitionSessionBoundary`
appends immutable River events; `reconstruct` reads the durable
`cognition_session` aggregate, requires exactly one opening event, applies
request attachments and implementation replacements, and revalidates identity
correspondence during replay.

Independent real PostgreSQL probe against `EventStore`:

`POSTGRES_SESSION_RELOAD c11740cf-6dc1-4595-b1cb-54a3b64e4cd9 c11740cf-6dc1-4595-b1cb-54a3b64e4cd9 1 True True`

This created a session and matching F1 request, persisted the River events,
created a new EventStore and session boundary, reloaded the aggregate, and
verified the same session ID, resident identity, and request membership.

The durable path is therefore not dependent on transcript similarity, provider
conversation ID, model identity, office display text, or Python object survival.

## Bounds, serialization, and failures

PASS. State references are capped at 64 entries and 512 characters each. The
session and turn envelopes contain no transcript or arbitrary content map.
Schema version, UUID, authority, timestamp, status, and required identity
fields are validated on serialization round-trip. Missing/malformed fields,
unsupported schema, naive timestamps, invalid UUIDs, invalid authority,
session/resident identity collision, wrong-session turn, stale context, and
identity mismatch fail closed.

The session boundary has no execution dispatcher or authority-grant operation;
transcript, provider metadata, and cognition content cannot widen execution
authority. Provider/resource selection and model invocation remain outside F3.

Search of the changed implementation found no inappropriate hard binding to
OpenAI, ChatGPT, Ollama, fixed models/endpoints, RTX 3060/4090, P100/V100, GPU
IDs, or provider hosts.

## Independent test evidence

The exact implementation worktree was tested with the repository source path
explicitly selected:

- F3 session plus focused F1/F2/provider/context/runtime/authority selection:
  **91 passed**.
- Expanded F3/F1/F2 and resident persistence/continuity selection:
  **97 passed**.
- Real PostgreSQL session persistence/reconstruction probe: **PASS**.
- Compile/import behavior: test collection and execution completed without
  import or compile errors.

The F3 tests cover session identity, wrong session/identity, transcript and
provider non-identity, implementation replacement, home/high shared session,
serialization, bounded references, runtime correspondence, stale context,
and durable reconstruction. F2 regression tests cover exact request/result
correspondence and forged downstream provenance rejection.

## Early F4 and next package

Early F4 preserved: **PASS**. The GRC-005 bounded packet assembler remains in
the commit and was not changed or accepted by this validation.

The accepted dependency graph does not make F3 a prerequisite for F4; F4 is a
separate foundation package depending on F1 and existing bounded context. The
existing GRC-005 early F4 implementation is therefore eligible for its own
independent validation, but it is not accepted merely because F3 passed.

Recommended next action: **GRC-005V independent validation of the existing
early F4 bounded packet assembler**. Keep F4 acceptance separate, then use the
accepted graph to gate later E2/E3 work. P1/P2 remain required policy/resource
dependencies for E1 and are not silently accepted by this F3 result.

## Conclusion

No blocking defect was found. F3 preserves Estate identity separation,
session/request distinction, bounded state, durable reconstruction, F2
correspondence boundaries, provider neutrality, and the authority boundary.

Grace implementation readiness: **READY_FOR_NEXT_GRC_PACKAGE**
