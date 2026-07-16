# Estate PTM ID Minting and Command Contract

Status: Draft implementation-preparation artifact for PTM-02 Gate B
Campaign: PTM-02 — Canonical ledger and projection contracts
Package: CORE-PTM-002B
Date: 2026-07-16

## Authority and boundaries

This artifact defines the CORE-PTM-002B PTM ID minting service contract, command envelope, command validation sequence, rejection contract, and downstream handoff rules for future implementation packages. It extends, but does not redefine, the CORE-PTM-002A append-only event envelope and hash-chain contract in `docs/architecture/estate_ptm_append_only_event_schema_hash_chain_contract.md`.

This artifact is documentation-only. It does not add production PTM code, mutate authoritative source records, dispatch work, schedule work, accept validation, grant budget authority, create a second dispatch queue, create a second registry, create a second scheduler, or introduce a new governance authority. Existing work-package files, Parking Lot records, dispatch evidence, validation reports, resident and operations records, and acceptance records remain authoritative in place.

## Canonical PTM ID service

Future PTM implementation must expose one canonical ID minting service interface to CLI, library, UI, import, Resident-command, scheduling, finance, dispatch, migration, and validation surfaces. Downstream packages must request IDs from this interface rather than generating private identifiers.

### ID service operations

```yaml
ptm_id_service:
  mint_id:
    input:
      entity_type: string
      slug_hint: string | null
      requested_at: string
      requested_by: string
      authority_refs: [string]
      source_refs: [object]
      correlation_id: string | null
    output:
      id: string
      entity_type: string
      prefix: string
      slug: string | null
      ulid: string
      minted_at: string
      minted_by: string
      authority_refs: [string]
      source_refs: [object]
  validate_id:
    input:
      id: string
      expected_entity_type: string | null
    output:
      valid: boolean
      entity_type: string | null
      errors: [string]
```

### ID formats

All persistent PTM IDs use a lower-case prefix plus a ULID. Aggregate IDs that benefit from a human clue include a normalized slug between the prefix and ULID. Slugs are hints only; the ULID supplies uniqueness.

| Entity type | Prefix | Format | Minted for |
| --- | --- | --- | --- |
| `event` | `evt` | `evt_<ulid>` | Immutable ledger events. |
| `command` | `cmd` | `cmd_<ulid>` | One command request envelope. |
| `correlation` | `cor` | `cor_<ulid>` | Multi-command or multi-event workflow correlation. |
| `portfolio` | `pf` | `pf_<slug>_<ulid>` | Portfolio aggregates. |
| `project` | `prj` | `prj_<slug>_<ulid>` | Project aggregates. |
| `task` | `tsk` | `tsk_<slug>_<ulid>` | Task aggregates. |
| `intake` | `int` | `int_<slug>_<ulid>` | Intake candidates and accepted intake records. |
| `file_import` | `fil` | `fil_<slug>_<ulid>` | Import sessions and source-file mappings. |
| `schedule` | `sch` | `sch_<slug>_<ulid>` | Schedule projection or readiness aggregates. |
| `financial` | `fin` | `fin_<slug>_<ulid>` | Budget, cost, approval, and reconciliation aggregates. |
| `utilization` | `utl` | `utl_<slug>_<ulid>` | Resource or lane utilization aggregates. |
| `kpi` | `kpi` | `kpi_<slug>_<ulid>` | KPI definitions, measurements, and dashboard aggregates. |
| `dispatch_evidence` | `dsp` | `dsp_<slug>_<ulid>` | References to existing dispatch evidence; not dispatch queue rows. |
| `migration` | `mig` | `mig_<slug>_<ulid>` | Migration batches and pilot slices. |
| `validation` | `val` | `val_<slug>_<ulid>` | Validation runs, reports, and evidence links. |
| `rollout` | `rol` | `rol_<slug>_<ulid>` | Rollout runbooks, gates, and adoption records. |

### ID normalization rules

1. IDs must be lower-case ASCII strings matching their entity-type format.
2. `<ulid>` must be a 26-character Crockford Base32 ULID string normalized to lower case for stored PTM IDs.
3. `<slug>` must be derived from a human hint by lower-casing, replacing non-alphanumeric runs with one hyphen, trimming leading/trailing hyphens, and limiting the stored slug to 48 characters.
4. Empty, unavailable, or sensitive hints must use no slug when the format permits no slug, or the neutral slug `item` when a slugged aggregate format is required.
5. IDs are immutable and must never be reused after rejection, archive, merge, correction, deletion request, or migration rollback.
6. A command may pre-mint target aggregate IDs during validation, but those IDs become persistent only if the command is accepted or if the rejection report must preserve an attempted ID for audit.
7. Source-system identifiers remain source metadata; they must not be treated as canonical PTM IDs.

## Command envelope

Every future PTM mutation request from CLI, library, UI, Resident command, import, schedule, finance, dispatch, migration, or validation surfaces must use the same command envelope before any domain payload is interpreted.

```yaml
ptm_command:
  command_id: string
  command_type: string
  command_version: integer
  requested_at: string
  requested_by: string
  authority_refs: [string]
  source_refs:
    - source_path: string
      source_sha256: string
      adapter_name: string
      adapter_version: string
  target_aggregate_type: portfolio | project | task | intake | file_import | schedule | finance | utilization | kpi | dispatch | migration | rollout | validation | null
  target_aggregate_id: string | null
  correlation_id: string | null
  causation_id: string | null
  idempotency_key: string
  expected_stream_id: string | null
  expected_stream_version: integer | null
  payload_schema: string
  payload: object
  dry_run: boolean
  requested_output: event_append | validation_report | projection_preview
```

### Required field semantics

| Field | Requirement |
| --- | --- |
| `command_id` | Canonical `cmd_<ulid>` identifier minted by the PTM ID service. |
| `command_type` | Lower-case dotted verb phrase such as `task.create`, `task.update_status`, `intake.accept`, or `dispatch.link_evidence`. |
| `command_version` | Positive integer version for the command payload contract. |
| `requested_at` | ISO-8601 timestamp with explicit UTC offset or `Z`. |
| `requested_by` | Source-backed human, resident, service, or workflow reference; not a new actor registry. |
| `authority_refs` | Existing work package, acceptance, approval, governance, validation, dispatch, Helen, Grace, Traffic Controller, Chief Architect, or Steward references required to evaluate authority. |
| `source_refs` | Adapter-backed provenance for the request or candidate facts. Empty only for purely synthetic administrative commands that still have authority references. |
| `target_aggregate_type` | Aggregate family being mutated, or `null` only for commands whose first accepted event creates the aggregate. |
| `target_aggregate_id` | Existing or pre-minted target ID, or `null` for creation commands that mint during validation. |
| `correlation_id` | Shared `cor_<ulid>` workflow ID when the command participates in a larger operation; otherwise `null`. |
| `causation_id` | Prior command or event that directly caused this command; otherwise `null`. |
| `idempotency_key` | Stable key scoped to command type, requester, target, and source facts to prevent duplicate event append. |
| `expected_stream_id` | Stream to check for optimistic concurrency; `null` only when no prior stream exists. |
| `expected_stream_version` | Last known sequence number for the stream; `null` for creation or read-only validation commands. |
| `payload_schema` | Stable schema name and version for the domain payload. |
| `payload` | Domain request body. It must not contradict envelope authority, source, target, or idempotency fields. |
| `dry_run` | When true, command validation returns a report and emits no persistent events. |
| `requested_output` | Declares whether the caller expects appendable events, a validation-only report, or a projection preview. |

## Command validation and handling sequence

Future handlers must process commands in this order:

1. Validate envelope shape, required fields, command version, timestamps, and ID formats.
2. Validate `command_id`, `target_aggregate_id`, and `correlation_id` with the canonical PTM ID service.
3. Validate source references against the Gate A adapter contract fields: adapter name, adapter version, source path, source SHA-256, evidence references, and warnings.
4. Validate authority references without creating new approval authority or bypassing existing Steward, Chief Architect, Helen, Grace, Traffic Controller, dispatch, validation, or acceptance boundaries.
5. Validate idempotency key scope and return the prior accepted result if the same accepted command is replayed exactly.
6. Validate optimistic concurrency by comparing `expected_stream_version` with the current stream sequence number when a stream exists.
7. Validate domain payload schema and domain-specific invariants.
8. If `dry_run` is true, return a validation report and append no events.
9. Mint any required target aggregate, event, or correlation IDs through the canonical ID service.
10. Build appendable CORE-PTM-002A events with `command_id`, `correlation_id`, `causation_id`, `idempotency_key`, source refs, authority refs, and target aggregate IDs preserved.
11. Append events atomically in stream order only after every event passes the CORE-PTM-002A hash-chain and envelope validation rules.
12. Return a structured command result that includes accepted event IDs or rejection reasons.

## Command result and rejection contract

Command handlers must return one of these result states without introducing additional lifecycle states:

| Result state | Ledger effect | Required response fields |
| --- | --- | --- |
| `accepted` | One or more events appended. | `command_id`, `event_ids`, `aggregate_ids`, `stream_ids`, `idempotency_key`, `warnings`. |
| `accepted_noop` | No new events because an identical accepted command was replayed. | `command_id`, `prior_command_id`, `prior_event_ids`, `idempotency_key`, `warnings`. |
| `rejected` | No events appended. | `command_id`, `rejection_reasons`, `rejected_at`, `authority_refs`, `source_refs`, `warnings`. |
| `dry_run_passed` | No events appended. | `command_id`, `validation_findings`, `would_mint_ids`, `would_emit_event_types`, `warnings`. |
| `dry_run_failed` | No events appended. | `command_id`, `rejection_reasons`, `validation_findings`, `warnings`. |

Rejection reasons must be structured, source-backed, and safe to display in CLI, library, UI, Resident, and validation contexts. Minimum reason codes are `invalid_envelope`, `invalid_id`, `missing_authority`, `source_unavailable`, `source_hash_mismatch`, `duplicate_idempotency_key`, `stream_version_conflict`, `payload_schema_invalid`, `domain_rule_failed`, `dry_run_only`, and `unsupported_command_type`.

## CLI and library contract

Future CLI and library implementations must be thin transport surfaces over the command envelope.

```text
ptm command validate --command <path> [--json]
ptm command submit --command <path> [--dry-run] [--json]
ptm id mint --entity-type <type> [--slug-hint <hint>] --authority-ref <ref> [--json]
ptm id validate --id <id> [--expected-entity-type <type>] [--json]
```

- CLI commands must read and write the same envelope/result shapes used by the library.
- UI and Resident command paths must call the library contract rather than bypassing it.
- `--dry-run` must force `dry_run: true` and must never append events.
- Human-readable output may summarize the result, but JSON output must preserve all structured fields.

## Downstream handoff requirements

- CORE-PTM-003A and CORE-PTM-003B may project command IDs, correlation IDs, aggregate IDs, and rejection warnings, but they must not redefine the ID formats or command envelope.
- INTAKE and FILE packages must use this command contract for governed creation/import paths and must preserve duplicate-detection and source-hash evidence.
- UI and CONV packages must expose command affordances through this contract and must not create private task lists, resident-only commands, or hidden mutation routes.
- SCHED, FIN, UTIL, KPI, DISPATCH, MIG, ROLL, and TEST packages may define domain payload schemas and command fixtures, but they must not create a parallel queue, registry, scheduler, ID authority, command bus, or governance authority.
- Any package that needs to change ID formats, command result states, authority validation, idempotency behavior, or rejection semantics must stop and open a replan note for the PTM-02 Gate B checkpoint.

## Fixture plan

Future validation fixtures should include:

| Fixture | Minimum contents | Expected result |
| --- | --- | --- |
| `valid_task_create_command` | `task.create` command with source refs, authority refs, dry_run false, and no existing stream. | Accepted result with minted task ID and one or more appendable events. |
| `valid_dry_run_intake_accept` | `intake.accept` command with `dry_run: true`. | `dry_run_passed`; no events appended; would-emit event types listed. |
| `valid_idempotent_replay` | Same command envelope submitted twice with identical idempotency key and payload. | First accepted; second `accepted_noop` referencing prior events. |
| `invalid_missing_authority` | Mutation command with insufficient authority refs. | Rejected with `missing_authority`; no events appended. |
| `invalid_stream_conflict` | Update command whose `expected_stream_version` is stale. | Rejected with `stream_version_conflict`; no events appended. |
| `invalid_source_hash` | Command source ref whose stored SHA-256 no longer matches source evidence. | Rejected with `source_hash_mismatch`; no events appended. |

## Evidence note

This artifact freezes the PTM ID and command contracts needed by downstream Gate B consumers while preserving the CORE-PTM-002A event envelope and accepted Estate authority boundaries. It is intentionally implementation-ready documentation only.
