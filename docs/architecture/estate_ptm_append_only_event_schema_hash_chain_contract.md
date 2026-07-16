# Estate PTM Append-only Event Schema and Hash-chain Contract

Status: Draft implementation-preparation artifact for PTM-02 Gate B
Campaign: PTM-02 — Canonical ledger and projection contracts
Package: CORE-PTM-002A
Date: 2026-07-16

## Authority and boundaries

This artifact defines the CORE-PTM-002A append-only event envelope, immutability rules, hash-chain verification expectations, and fixture plan for future PTM implementation packages. It is source-backed by the accepted PTM baseline, the PTM parallel execution plan, the PTM dependency manifests, and the Gate A read-only adapter contract.

This artifact is not production PTM code. It does not mutate source records, dispatch work, schedule work, accept validation, grant budget authority, or create a second dispatch queue, second registry, second scheduler, validation authority, or governance authority. Existing work-package files, Parking Lot records, dispatch evidence, validation reports, resident/operations records, and acceptance records remain authoritative in place and are only referenced by future events through source provenance.

## Canonical event envelope

Every future PTM event MUST use this envelope before any domain payload is interpreted:

```yaml
ptm_event:
  event_id: string
  event_type: string
  event_version: integer
  aggregate_type: portfolio | project | task | intake | file_import | schedule | finance | utilization | kpi | dispatch | migration | rollout | validation
  aggregate_id: string
  stream_id: string
  sequence_number: integer
  occurred_at: string
  recorded_at: string
  actor_ref: string
  authority_refs: [string]
  source_refs:
    - source_path: string
      source_sha256: string
      adapter_name: string
      adapter_version: string
  causation_id: string | null
  correlation_id: string | null
  command_id: string | null
  idempotency_key: string
  payload_schema: string
  payload: object
  previous_event_hash: string | null
  event_hash: string
  hash_algorithm: sha256
```

### Required field semantics

| Field | Requirement | Rationale |
| --- | --- | --- |
| `event_id` | Globally unique immutable event identifier; downstream CORE-PTM-002B owns exact minting format. | Keeps ledger identity stable without letting this package create a separate ID authority. |
| `event_type` | Lower-case dotted domain name such as `task.created`, `schedule.readiness_changed`, or `dispatch.evidence_linked`. | Provides a stable namespace for downstream payload schemas. |
| `event_version` | Positive integer version for the event type payload contract. | Allows payload evolution without changing the envelope. |
| `aggregate_type` | One of the enumerated PTM aggregate families in the envelope. | Prevents free-form registry expansion during Gate B. |
| `aggregate_id` | Identifier of the aggregate affected by the event. | Binds replay to a projected PTM object. |
| `stream_id` | Stable stream key used for sequence and hash-chain validation. | Defines the ordering scope for `previous_event_hash`. |
| `sequence_number` | Positive integer, strictly increasing by one within `stream_id`. | Supports deterministic replay and missing-event detection. |
| `occurred_at` | ISO-8601 timestamp for when the source-domain fact occurred or was observed. | Preserves source chronology. |
| `recorded_at` | ISO-8601 timestamp for when the PTM ledger event is appended. | Preserves ledger chronology. |
| `actor_ref` | Source-backed human, resident, service, or workflow reference that requested or caused the event. | Preserves accountability without creating a new actor registry. |
| `authority_refs` | Source-backed authority, package, acceptance, or governance references required for the event. | Keeps Steward, Chief Architect, Helen, Grace, Traffic Controller, validation, and dispatch boundaries visible. |
| `source_refs` | One or more adapter-backed source references with path, SHA-256, adapter name, and adapter version. | Ensures every future projection can trace back to original records. |
| `causation_id` | Event or command that directly caused this event; `null` only for initial imports or system observations with no direct cause. | Supports correction chains and replay diagnostics. |
| `correlation_id` | Shared identifier across related events or commands; `null` when no broader correlation exists. | Enables multi-stream fixture and workflow reconstruction. |
| `command_id` | Command envelope identifier when an event was emitted by a command; `null` for read-only import observations until command ingestion exists. | Connects CORE-PTM-002A to CORE-PTM-002B without redefining commands here. |
| `idempotency_key` | Stable key that prevents duplicate append for the same command scope. | Prevents accidental replay duplication. |
| `payload_schema` | Stable schema name and version for the domain payload. | Lets downstream packages add payload schemas without altering the envelope. |
| `payload` | Domain payload object; MUST NOT contain fields that contradict envelope provenance or authority fields. | Keeps envelope-level audit fields canonical. |
| `previous_event_hash` | Hash of the immediately prior event in the same stream; `null` only for sequence `1`. | Links events into an append-only chain. |
| `event_hash` | SHA-256 digest of canonical serialization with `event_hash` omitted. | Provides tamper-evidence for the event body. |
| `hash_algorithm` | Literal `sha256` for this contract version. | Avoids algorithm ambiguity during Gate B. |

## Canonical serialization and hash rules

Future implementation MUST compute `event_hash` using deterministic canonical serialization with these requirements:

1. Remove `event_hash` from the event object before hashing.
2. Preserve `previous_event_hash` exactly as stored, including `null` for the first event in a stream.
3. Sort object keys lexicographically at every object level.
4. Preserve array order exactly as supplied for semantically ordered arrays such as `source_refs`, `authority_refs`, and payload lists.
5. Serialize strings as UTF-8 JSON strings with standard escaping.
6. Serialize timestamps as normalized ISO-8601 strings with explicit UTC offset or `Z`.
7. Serialize integers as JSON numbers; do not serialize sequence numbers or versions as strings.
8. Serialize `null` as JSON `null`.
9. Compute SHA-256 over the resulting UTF-8 byte sequence and store the lowercase hexadecimal digest in `event_hash`.

The hash scope is one event. Chain validation is performed by comparing each event's `previous_event_hash` with the `event_hash` of the immediately preceding event in the same stream after events are ordered by `sequence_number`.

## Append-only immutability rules

1. Events MUST NOT be updated, deleted, rewritten, resequenced, or repaired in place.
2. Corrections MUST be represented by later compensating events that identify the corrected event through `causation_id` or explicit payload correction metadata.
3. Source records remain authoritative in their existing locations; event payloads reference source facts and do not replace work-package, Parking Lot, dispatch, validation, resident, operations, or acceptance records.
4. Adapter uncertainty MUST remain visible as event payload metadata or later projection warnings; uncertain values must not be silently guessed into authoritative event fields.
5. If a source record changes after an event is appended, future import logic MUST append a new observation or correction event rather than changing the prior event.
6. A stream's first event MUST use `sequence_number: 1` and `previous_event_hash: null`.
7. Every subsequent event in a stream MUST increment `sequence_number` by exactly one and point to the previous event hash.
8. Events that fail validation MUST NOT be appended; failed commands are handled by CORE-PTM-002B rejection reporting rather than ledger mutation.

## Replay validator expectations

A future replay validator for this contract MUST reject a ledger or fixture when any of these conditions are present:

- missing required envelope field;
- unknown `aggregate_type` or `hash_algorithm` other than `sha256`;
- non-positive or non-integer `event_version` or `sequence_number`;
- duplicate `event_id` anywhere in the replay set;
- duplicate `idempotency_key` within the same command scope;
- duplicate `sequence_number` within one `stream_id`;
- gap in `sequence_number` within one `stream_id`;
- first event in a stream has non-null `previous_event_hash`;
- non-first event has null or mismatched `previous_event_hash`;
- recomputed `event_hash` does not match the stored value;
- canonical serialization is non-deterministic for the same event object;
- any projected output field lacks at least one supporting `source_ref` and event ID.

A future replay validator SHOULD emit warnings, rather than hard failures, when source adapters report low parse confidence, path-derived status disagrees with body-declared status, or an optional correlation field is absent.

## Fixture plan

Future validation fixtures for CORE-PTM-002A and downstream TEST-PTM packages should use small repository-local JSON or YAML files that exercise both acceptance and rejection paths.

| Fixture | Minimum contents | Expected result |
| --- | --- | --- |
| `valid_task_lifecycle_single_stream` | Three task events in one stream: creation, status change, completion; sequence numbers `1..3`; valid previous hashes. | Replay passes and produces deterministic event order. |
| `valid_multi_stream_correlation` | Intake, task, schedule, and dispatch events in separate streams with shared `correlation_id` and source refs from Gate A adapter names. | Replay passes and correlation can be reconstructed without merging streams. |
| `valid_compensating_correction` | Original event plus later correction event that points to the original via `causation_id`. | Replay passes; projections can prefer corrected value while retaining audit trail. |
| `invalid_broken_previous_hash` | Second event in a stream points to a hash that does not equal the first event's recomputed hash. | Replay rejects hash-chain mismatch. |
| `invalid_sequence_gap` | Stream contains sequence `1` and `3` with no `2`. | Replay rejects missing sequence number. |
| `invalid_duplicate_idempotency` | Two accepted events from the same command scope share an `idempotency_key`. | Replay rejects duplicate append risk. |
| `warning_adapter_uncertainty` | Valid event whose source adapter reports low confidence or path/body status conflict in payload metadata. | Replay passes with warning preserved for projections. |

## Downstream handoff requirements

- CORE-PTM-002B may define exact event ID, command ID, idempotency, command envelope, and command rejection semantics, but it must not redefine the CORE-PTM-002A event envelope or hash-chain rules.
- CORE-PTM-003A and CORE-PTM-003B may define projection fields and replay outputs, but each projected field must trace back to event IDs and source refs defined here.
- INTAKE, FILE, CONV, SCHED, FIN, UTIL, KPI, DISPATCH, MIG, ROLL, UI, and TEST packages may add domain payload schemas and fixture instances, but they must not introduce a parallel ledger, queue, registry, scheduler, or authority boundary.
- Any package that needs to alter the event envelope, hash algorithm, stream sequencing rules, or immutability rules must stop and open a replan note for the PTM-02 Gate B checkpoint.

## Evidence note

This artifact is deliberately documentation-only and implementation-ready. It freezes the append-only event and hash-chain expectations for future packages while preserving accepted authority boundaries and leaving production schema/library files for later authorized implementation.
