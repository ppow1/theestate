# SERIES TASK WP-0109 — Resident Conversation Session and Audit Trail

## Codex Command
Read `collaboration/work_packages/pending/WP-0109_SERIES_resident_conversation_session_and_audit_trail.md` and do exactly what it says.

## Mode
SERIES

## Mission
Create the first local resident conversation session and audit trail framework so Alfred, Helen, and future Estate residents can participate in bounded conversation sessions while preserving institutional source-of-truth, provenance, and reviewability.

## Background
The Estate already has resident-facing surfaces through the Steward Command Center, Resident Card framework, Resident Conversations workspace, Resident Runtime Presence Model, Alfred Online Duty Runner, and Helen Online Duty Runner. The Resident Conversations workspace intentionally began as a visible interface placeholder rather than an authoritative chat engine.

The next step is to create the local session and audit model that allows resident conversations to become operationally useful without allowing transient chat to become the source of truth. Important outcomes must still be routed to work packages, messages, decisions, validation artifacts, or other canonical Estate records.

## Scope
Implement a local-first resident conversation session framework and audit trail.

The framework should support, at minimum:

- creating a resident conversation session
- assigning the session to a resident such as Alfred or Helen
- recording session metadata
- recording participant roles
- recording timestamps
- recording prompts, responses, operator notes, or session events where appropriate
- recording source artifact references used during the session
- marking session outcomes such as informational, needs Steward, work package candidate, decision candidate, validation follow-up, or no action
- linking important outcomes to canonical artifacts where available
- exposing session summaries to the Resident Conversations workspace
- preserving an audit trail suitable for later validation and review

## Out of Scope
Do not implement unrestricted autonomous conversation.

Do not allow chat transcripts to become governance authority by themselves.

Do not allow residents to approve, merge, validate, institutionalize, hire, terminate, or execute work packages through conversation alone.

Do not implement Resident Action Authority Boundary enforcement in this package except for simple explicit labeling of non-authoritative session outcomes.

Do not require cloud services, external chat APIs, external identity providers, or internet access.

Do not store secrets.

Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Required Behavior
- Resident conversation sessions must be local-first and file-backed or otherwise locally auditable.
- Conversations must distinguish session transcript from institutional decision record.
- Every session should identify resident, participant role, time, status, and source artifacts when available.
- Important outcomes should point toward canonical follow-up artifacts rather than silently becoming authority.
- Missing optional data should degrade gracefully.
- The Resident Conversations workspace should display session summaries or clear placeholders where available.
- The framework should support Alfred and Helen first while remaining extensible to future residents.

## Safety and Authority Constraints
- Conversation is an interface surface, not an authoritative record by itself.
- Do not infer Steward approval from resident conversation.
- Do not infer validation success from resident conversation.
- Do not execute work packages automatically from conversation.
- Do not grant resident authority through transcript existence.
- Preserve local-first operation.
- Do not broad-stage generated artifacts.

## Required CLI / Command Surface
Add or reuse local command surfaces consistent with existing Estate CLI conventions. Acceptable commands may include:

```bash
PYTHONPATH=src python -m estate.cli.main resident-conversation start --resident Alfred --json
PYTHONPATH=src python -m estate.cli.main resident-conversation list --json
PYTHONPATH=src python -m estate.cli.main resident-conversation show --session SESSION_ID --json
```

Use existing command names if the repository already defines a better convention. Document the final command surface in the completion receipt.

## Required Artifacts
Expected artifacts may include:

- resident conversation session core module
- local session/audit storage path
- schema or documented JSON shape for session records
- integration with Resident Conversations workspace where appropriate
- tests for session creation, listing, summary display, source artifact references, and authority boundary labels
- validation recipe for WP-0109
- `collaboration/work_packages/completions/WP-0109_codex_done.json`

## Tests
Verify:

- sessions can be created for Alfred and Helen locally
- session records contain resident, timestamps, participants, status, and source references where provided
- session summaries can be listed and rendered
- missing session data degrades gracefully
- transcript/session records do not imply governance, validation, merge, or Steward authority
- CLI JSON output is valid
- Resident Conversations workspace consumes session summaries if available

## Validation Recipe Requirement
Add or update the validation recipe for WP-0109. The recipe must be registered in the existing validation framework and must not return `no_recipe`. Classify checks as required or observational, use local-first non-destructive commands, and ensure this package can be evaluated by:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0109 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

## Codex Completion Receipt Requirement
Create `collaboration/work_packages/completions/WP-0109_codex_done.json` with at least:

- `work_package_id`
- `codex_status`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- `summary`
- `files_changed`
- `tests_run`
- `known_limitations`
- `ready_for_ca_review`
- `merge_authority`
- `validation_recipe_status`
- `production_readiness_command_status` if run
- final resident conversation command surface
- session/audit storage path
- explicit authority limitations

## Production Readiness Requirement
Run or document the equivalent of:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0109 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If production readiness remains blocked by the later Resident Action Authority Boundary package, record that as an expected limitation.

## Demonstration Requirements
Document exact commands run and observed status. Include sample session JSON for Alfred or Helen where practical, including non-authoritative status and source artifact references.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0109_codex_done.json` using the standard completion schema.

Set `ready_for_ca_review=true` only if tests, receipt metadata, validation recipe status, and production-readiness obligations are satisfied or explicitly documented with limitations.

## Merge Class
Class A unless conversation records are made authoritative, resident authority is changed, governance authority is changed, validation authority is changed, or automatic action semantics are introduced; escalate to Class B if those semantics are altered.
