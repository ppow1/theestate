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

### Manual and Parking Lot acceptance matrix

Future implementation of this slice must validate the following cases before promotion from dry-run/staging behavior to event emission:

| Case | Required validation | Authorized result | Forbidden result |
| --- | --- | --- | --- |
| New manual candidate | Required fields, requester, authority references, dedupe key, and proposed target type are present. | Stage a candidate and present explicit confirmation. | Create a task, project, portfolio, registry entry, or dispatch item before confirmation. |
| Parking Lot candidate | Source path, source hash, body-declared status, path-derived status, title/body excerpt, and Parking Lot provenance are preserved. | Stage a candidate with `intake_source_type: parking_lot` and immutable source references. | Rewrite, move, close, or otherwise mutate the Parking Lot source artifact. |
| Potential duplicate | Dedupe key and evidence references identify an active candidate, confirmed intake record, or projected task/project. | Present duplicate evidence and require a duplicate, reject, or confirm decision. | Silently merge records or overwrite candidate/source fields. |
| Validation failure | Missing required field, unsupported source type, source hash mismatch, or malformed proposed target. | Return structured warnings/rejection details and emit zero canonical events. | Emit partial intake, creation, dispatch, or projection events. |
| Confirmed candidate | Confirmation command passes frozen command-envelope, authority, and hash-chain requirements. | Emit `intake.candidate_confirmed.v1` followed by the applicable downstream creation/link event. | Bypass the append-only ledger/projection spine or create a second queue/registry. |

### Evidence notes for future package promotion

- The manual/Parking Lot intake handler surface is bounded to candidate staging, dedupe presentation, explicit confirmation, duplicate marking, rejection, or supersession.
- All state-changing outcomes must be represented as canonical append-only PTM events using the already frozen event envelope; dry-run and validation-failure paths emit no persistent events.
- Parking Lot and manually referenced source artifacts remain authoritative in place and are referenced by path plus SHA-256 provenance.
- This contract depends on `CORE-PTM-003A` projection fields and intentionally does not redefine project, task, portfolio, scheduler, or dispatch projections.

## INTAKE-PTM-001B conversation intake and dedupe confirmation contract

Conversation intake covers future command/intake handlers that propose PTM candidates from governed Resident, Office, or command conversations. Future handlers must not treat conversational text as authority by itself. They must bind every candidate to a conversation message reference, actor/requester reference, timestamp, command envelope, and any cited source artifacts.

Conversation intake must return a confirmation response containing:

- the candidate title, description, proposed target type, and source references;
- possible duplicate matches and the evidence used to score them;
- the proposed event payloads that would be emitted on confirmation;
- a no-mutation dry-run indication when the user is only previewing; and
- a durable audit reference after confirmation, duplicate marking, or rejection.

Duplicate handling from conversation must follow the shared governed intake model. If the requester confirms that a candidate is a duplicate, the handler records the duplicate decision and links to the retained record; it must not create another registry, side list, or task record outside the PTM ledger/projection spine.

Conversation intake handlers must use these payload schemas under the frozen event envelope:

- `intake.conversation_candidate_staged.v1`
- `intake.conversation_candidate_confirmed.v1`
- `intake.conversation_candidate_rejected.v1`
- `intake.conversation_candidate_marked_duplicate.v1`
- `intake.conversation_candidate_superseded.v1`

### Conversation candidate command contract

Future conversation commands that propose PTM work must be staged as dry-run or candidate commands before mutation. The command payload must include the command text or normalized intent, the message or thread reference, the requesting actor, cited source references, proposed target type, dedupe key, and the confirmation token returned to the user. Confirmation tokens are scoped to the command, actor, candidate, dedupe result, and proposed payload preview; changing any of those values invalidates the confirmation and returns `needs_confirmation` again.

A conversational statement such as "make this a task" is therefore only an intake request. It is not task creation until the user confirms the candidate preview through the same frozen PTM command envelope used by CLI, library, UI, and Resident command surfaces. Dry-run previews and validation failures must emit zero persistent events.

### Conversation intake acceptance matrix

Future implementation of this slice must validate the following cases before conversation-originated candidates can emit canonical PTM events:

| Case | Required validation | Authorized result | Forbidden result |
| --- | --- | --- | --- |
| Preview from conversation | Command envelope, actor reference, conversation/message reference, source references, proposed title/description, target type, dedupe key, and dry-run flag are present. | Return a preview with proposed payloads, duplicate evidence, warnings, and no-mutation status. | Mint a task, project, portfolio, registry row, dispatch item, or confirmation event from preview alone. |
| Explicit confirmation | Confirmation token still matches the candidate, actor, dedupe result, source references, and proposed payload preview. | Emit `intake.conversation_candidate_confirmed.v1` and then the applicable downstream creation or link event. | Reuse a stale confirmation token after edited content, changed duplicate result, or different actor. |
| Potential duplicate | Dedupe evidence identifies an active candidate, accepted intake record, projected task/project, or source artifact match. | Present retained-record evidence and require confirm-new, mark-duplicate, reject, or supersede decision. | Silently merge, overwrite retained records, or create another task without a duplicate decision. |
| Duplicate decision | Requester selects the retained record and supplies the duplicate decision through the command envelope. | Emit `intake.conversation_candidate_marked_duplicate.v1` with retained record, candidate, evidence, actor, and source refs. | Create a second registry, side list, dispatch queue row, or hidden conversation-only task. |
| Validation or authority failure | Missing authority, invalid source reference, stale expected stream version, malformed target, or unsupported command is detected. | Return structured rejection/warning details and emit zero canonical events. | Emit partial intake, creation, schedule, dispatch, projection, Helen, Grace, or budget events. |
| Rejection or supersession | Requester rejects the candidate or replaces it with a better-scoped candidate. | Emit the rejection or supersession event with reason and replacement/retained references where applicable. | Delete the original conversation evidence or mutate source artifacts. |

### Conversation audit and downstream handoff notes

- Every accepted, rejected, duplicate, or superseded conversation candidate must preserve `command_id`, `correlation_id`, `causation_id`, conversation/message references, actor references, authority references, source hashes where available, and the emitted event IDs.
- Conversation-originated candidates may hand off to `CONV-PTM-001` resident command surfaces only through the governed intake command contract; resident commands must not define a separate creation path.
- Conversation audit output is a projection/read model over canonical events and source references, not a second conversation task registry.
- Helen, Grace, Traffic Controller, budget, scheduling, dispatch, validation, and acceptance authority boundaries remain unchanged; conversation intake may request or reference those lanes but may not approve or complete their decisions.

## FILE-PTM-001A approved file-import format inventory

File import planning is limited to inventory and future fixture needs. Approved initial import formats are:

| Format | Allowed use | Required parser behavior | Fixture need |
| --- | --- | --- | --- |
| Markdown work-package file | Import structured package/task candidates from repository Markdown. | Preserve headings, status text, source path, SHA-256, and unresolved fields as warnings. | Valid pending package, completed package, status mismatch, missing required heading. |
| JSON manifest | Import package, campaign, dependency, or registry metadata from existing JSON manifests. | Validate JSON syntax, stable identifiers, and source SHA-256 without mutating the source. | Valid manifest, duplicate ID, missing dependency target, malformed JSON. |
| CSV table | Import tabular backlog rows when explicitly approved by future package scope. | Require header mapping, row number provenance, UTF-8 input, and per-row rejection reasons. | Valid rows, duplicate rows, missing required column, invalid encoding. |
| Plain text note | Stage a manual-review candidate only. | Preserve text and source hash; require human confirmation for all structured fields. | Single note, ambiguous note, duplicate note. |

No importer may execute source mutation, auto-accept a candidate, or bypass the governed intake confirmation contract.

### Parser inventory constraints

Future parser work must treat this inventory as the bounded allow-list until a later accepted package changes it. Each parser must return normalized candidate records plus structured warnings, never direct PTM task, project, portfolio, schedule, dispatch, budget, or validation events. Parser outputs feed the shared intake candidate envelope and must preserve the original file bytes through source path, parser format, section or row locator, and SHA-256 provenance.

| Parser surface | Required extracted fields | Required rejection or warning cases | Downstream handoff |
| --- | --- | --- | --- |
| Markdown work-package file | Title or first heading, body status, path-derived status when available, owner/lane text, dependency references, validation commands, and source section locators. | Missing title, contradictory statuses, unsupported heading structure, dependency reference not present in the current manifest, and source hash mismatch. | Stage one or more `file_import` candidates for governed confirmation; do not rewrite the Markdown source. |
| JSON manifest | Manifest type, stable package/campaign/dependency IDs, referenced paths, dependency edges, readiness status, and source object pointers. | Malformed JSON, duplicate ID in the same manifest, dependency target absent from the manifest baseline, unexpected top-level shape, and non-UTF-8 input. | Stage metadata-backed candidates or report-only findings for Chief Architect review; do not update manifests. |
| CSV table | Header mapping, row number, normalized title/description columns, optional owner/lane/status columns, and raw row hash. | Missing required column, duplicate normalized row, invalid encoding, unparseable quoted field, and row-level required-field failure. | Stage per-row candidates with row provenance and per-row rejection reasons. |
| Plain text note | Entire note text, inferred title suggestion, source hash, and ambiguity warnings. | Empty note, ambiguous target type, duplicate text hash, and insufficient authority/source references. | Stage manual-review candidates only; require human confirmation for all structured fields. |

### Fixture inventory for future parser implementation

Future implementation packages should create deterministic fixtures before enabling any importer behavior. Minimum fixture coverage is:

- Markdown: valid pending package, valid completion receipt or completed package, body/path status mismatch, missing required heading, malformed dependency reference, and duplicate title with different source path.
- JSON: valid package manifest excerpt, valid campaign/dependency manifest excerpt, duplicate package ID, missing dependency target, malformed JSON, and unexpected top-level shape.
- CSV: valid UTF-8 backlog table, duplicate row, missing required column, invalid encoding sample, embedded delimiter/quote case, and row with blank title.
- Plain text: single actionable note, ambiguous note requiring human target selection, duplicate note by content hash, and note lacking authority references.

Fixture assertions must check accepted, rejected, duplicate, and warning paths; source SHA-256 preservation; deterministic ordering; and dry-run behavior with zero emitted persistent events.

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
