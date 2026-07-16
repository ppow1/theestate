# Estate PTM Governed Intake and Import Contracts

Status: Draft implementation-preparation artifact for PTM-03 Gate C
Campaign: PTM-03 — Governed intake and import contracts
Packages: INTAKE-PTM-001A, INTAKE-PTM-001B, FILE-PTM-001A, FILE-PTM-001B
Date: 2026-07-16

## Authority and boundaries

This artifact bounds the governed PTM manual intake, Parking Lot promotion, conversation intake, file-import inventory, and file-import reporting contracts for future implementation. It is source-backed by the accepted PTM baseline, the PTM parallel execution plan, the dependency manifests, the PTM planning drafts, and the Gate B canonical ledger and projection contract.

This artifact does not authorize production PTM code, does not mutate source work packages or Parking Lot records, and does not create a second dispatch queue, second registry, second scheduler, local-worker route, or new governance authority. Future handlers must use the frozen PTM event envelope, command envelope, ID formats, projection envelope, and authority boundaries from `docs/architecture/estate_ptm_canonical_ledger_and_projection_contracts.md`.

## Shared governed intake model

### Intake candidate envelope

Future intake handlers may stage a candidate only through a canonical intake candidate envelope before any task, project, or portfolio event is emitted:

```yaml
ptm_intake_candidate:
  intake_id: string
  intake_source_type: manual | parking_lot | conversation | file_import
  intake_source_ref: string
  title: string
  description: string
  requested_by: string
  captured_at: string
  authority_refs: [string]
  source_refs: [object]
  dedupe_key: string
  dedupe_candidates: [string]
  confirmation_state: candidate | needs_confirmation | confirmed | rejected | duplicate | superseded
  proposed_target_type: portfolio | project | task | unknown
  proposed_target_id: string | null
  warnings: [string]
```

`intake_id` must use the frozen `int_<slug>_<ulid>` format. Candidate staging is not task creation; a candidate becomes a PTM task, project, or portfolio only after the governed confirmation command succeeds and emits append-only PTM events.

### Dedupe key rules

The dedupe key is a deterministic hash over normalized title, source path or conversation reference, requester, proposed target type, and source-specific stable identifiers. Dedupe checks must compare against active candidates, confirmed intake records, and existing projected tasks or projects. A dedupe match must preserve all candidate source references and must not silently merge or overwrite source records.

### Confirmation outcomes

| Outcome | Required behavior |
| --- | --- |
| `confirmed` | Emit a canonical intake confirmation event and then the applicable downstream creation/link event using the frozen event envelope. |
| `duplicate` | Emit a duplicate decision event referencing the retained candidate and matched record; do not mint a second task. |
| `rejected` | Emit a rejection event with structured reason and source references; do not mutate the source artifact. |
| `needs_confirmation` | Return a review prompt/report only; emit no task/project events. |
| `superseded` | Reference the replacement candidate or accepted record through a compensating event. |

## INTAKE-PTM-001A manual and Parking Lot intake contract

Manual and Parking Lot intake may propose candidates from human-entered text, existing Parking Lot entries, pending work-package notes, or backlog rows. Future handlers must:

1. preserve the original source path, source hash, body-declared status, and path-derived status where present;
2. stage candidates with `intake_source_type` of `manual` or `parking_lot`;
3. calculate the dedupe key before presenting confirmation;
4. require explicit confirmation before emitting task/project/portfolio events;
5. emit zero canonical events when validation fails; and
6. leave Parking Lot and source artifacts authoritative in place.

Required manual/Parking Lot event payload schemas are limited to domain payloads under the frozen event envelope:

- `intake.candidate_staged.v1`
- `intake.candidate_confirmed.v1`
- `intake.candidate_rejected.v1`
- `intake.candidate_marked_duplicate.v1`
- `intake.candidate_superseded.v1`

## INTAKE-PTM-001B conversation intake and dedupe confirmation contract

Conversation intake covers future command/intake handlers that propose PTM candidates from governed Resident, Office, or command conversations. Future handlers must not treat conversational text as authority by itself. They must bind every candidate to a conversation message reference, actor/requester reference, timestamp, command envelope, and any cited source artifacts.

Conversation intake must return a confirmation response containing:

- the candidate title, description, proposed target type, and source references;
- possible duplicate matches and the evidence used to score them;
- the proposed event payloads that would be emitted on confirmation;
- a no-mutation dry-run indication when the user is only previewing; and
- a durable audit reference after confirmation, duplicate marking, or rejection.

Duplicate handling from conversation must follow the shared governed intake model. If the requester confirms that a candidate is a duplicate, the handler records the duplicate decision and links to the retained record; it must not create another registry, side list, or task record outside the PTM ledger/projection spine.

## FILE-PTM-001A approved file-import format inventory

File import planning is limited to inventory and future fixture needs. Approved initial import formats are:

| Format | Allowed use | Required parser behavior | Fixture need |
| --- | --- | --- | --- |
| Markdown work-package file | Import structured package/task candidates from repository Markdown. | Preserve headings, status text, source path, SHA-256, and unresolved fields as warnings. | Valid pending package, completed package, status mismatch, missing required heading. |
| JSON manifest | Import package, campaign, dependency, or registry metadata from existing JSON manifests. | Validate JSON syntax, stable identifiers, and source SHA-256 without mutating the source. | Valid manifest, duplicate ID, missing dependency target, malformed JSON. |
| CSV table | Import tabular backlog rows when explicitly approved by future package scope. | Require header mapping, row number provenance, UTF-8 input, and per-row rejection reasons. | Valid rows, duplicate rows, missing required column, invalid encoding. |
| Plain text note | Stage a manual-review candidate only. | Preserve text and source hash; require human confirmation for all structured fields. | Single note, ambiguous note, duplicate note. |

No importer may execute source mutation, auto-accept a candidate, or bypass the governed intake confirmation contract.

## FILE-PTM-001B file-import report and SHA-256 mapping contract

Every future file import session must produce a deterministic report envelope:

```yaml
ptm_file_import_report:
  import_id: string
  command_id: string
  requested_by: string
  requested_at: string
  dry_run: boolean
  source_files:
    - source_path: string
      source_sha256: string
      parser_format: markdown_work_package | json_manifest | csv_table | plain_text_note
      parser_version: string
  accepted_records: [object]
  rejected_records: [object]
  duplicate_records: [object]
  sha256_mappings: [object]
  emitted_event_ids: [string]
  warnings: [string]
```

`import_id` must use the frozen `fil_<slug>_<ulid>` format. `sha256_mappings` must map each source file and accepted/rejected/duplicate row or section to its SHA-256 provenance. Accepted records point to candidate or confirmed intake IDs; rejected records include reason codes; duplicate records include the retained record ID and evidence. Dry-run reports must emit no persistent events.

## Gate C reconciliation notes

- Intake and file import use the frozen PTM command, ID, event, hash-chain, and projection contracts rather than redefining them.
- File import feeds governed intake candidates; it does not bypass manual/conversation confirmation semantics.
- Duplicate decisions are auditable events or dry-run report entries, never silent merges.
- Source artifacts remain authoritative in place and are referenced through path and SHA-256 mappings.
- No second queue, second registry, second scheduler, local-worker route, or new governance authority is introduced.
