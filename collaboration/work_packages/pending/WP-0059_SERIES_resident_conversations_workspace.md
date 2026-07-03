# SERIES TASK WP-0059 — Resident Conversations Workspace

## Codex Command
Read `collaboration/work_packages/pending/WP-0059_SERIES_resident_conversations_workspace.md` and do exactly what it says.

## Mission
Add the Resident Conversations workspace to the Estate Operations Center so Alfred, Helen, and future residents have a visible conversational surface without making conversation the source of truth.

## Scope
Create an Operations Center view or panel that supports resident-oriented conversation surfaces for:

- Alfred
- Helen
- future registered residents

The workspace should display:

- resident selection
- resident role and mailbox summary
- recent institutional messages related to that resident
- conversation placeholder or local interaction panel
- links to source artifacts where available
- transcript/audit placeholder where voice or chat sessions later become institutional records

## Behavior Requirements
- Conversation is an interface surface, not an authoritative record by itself.
- Important actions must link back to institutional artifacts, messages, work packages, or audit records.
- Use existing mailbox and resident identity data where available.
- Missing resident data should display gracefully.
- Respect UI principles from WP-0046.

## Constraints
Do not implement autonomous AI agents in this package. Do not bypass mailboxes, Communication Bus, or Steward authority. Do not add cloud services. Do not store secrets. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify rendering for Alfred, Helen, unknown resident, missing mailbox data, no conversation data, and linked source artifact display.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0059_codex_done.json` using the standard completion schema.

## Merge Class
Class A unless implementation changes resident authority or institutional record semantics.
