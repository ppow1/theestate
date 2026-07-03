# SERIES TASK WP-0060 — Estate Interaction Services and Adapter Registry

## Codex Command
Read `collaboration/work_packages/pending/WP-0060_SERIES_interaction_services_adapter_registry.md` and do exactly what it says.

## Mission
Create the first Estate Interaction Services and Adapter Registry so UI, voice, notification, resident conversation, and future interaction surfaces use registered adapters instead of hard-coded integrations.

## Scope
Create a bounded registry and service layer for interaction adapters.

Initial adapter categories should include:

- UI panels / workspaces
- notification transports
- voice STT adapters
- voice TTS adapters
- SillyTavern or conversation-surface adapters
- command palette commands
- activity console event providers

Possible outputs:

- `data/registry/interaction_adapters.json`
- `docs/operations/Interaction_Adapter_Registry_v1.md`
- optional helper module such as `src/estate/core/interaction_adapters.py`

## Registry Fields
Each adapter entry should include:

- adapter_id
- display_name
- adapter_type
- status
- local_first
- provider
- configuration_required
- secrets_required
- authority_boundary
- source_of_truth_boundary
- related_workspace
- notes

## Behavior Requirements
- Adapters are optional unless explicitly required by an existing subsystem.
- Missing adapters should degrade gracefully.
- No adapter may become the source of truth for institutional records.
- UI and voice adapters must route significant actions back to auditable Estate artifacts.

## Constraints
Do not implement external providers in this package. Do not store secrets. Do not create cloud dependencies. Do not bypass Alfred, mailboxes, or governance authority. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
If code is added, verify adapter registry loading, missing adapter handling, duplicate adapter ID detection, and category filtering. If documentation/data only, validate JSON parses and adapter IDs are unique.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0060_codex_done.json` using the standard completion schema.

## Merge Class
Class A unless implementation changes authority boundaries or source-of-truth semantics.
