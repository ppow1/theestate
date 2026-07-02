# SERIES TASK WP-0030 — Mission Registry and Mission Numbering Standard

## Codex Command
Read `collaboration/work_packages/pending/WP-0030_SERIES_mission_registry_numbering_standard.md` and do exactly what it says.

## Mode
SERIES. Depends on WP-0016 Work Package Registry proposal, WP-0017 Work Package State Machine proposal, WP-0028 Document Registry, and WP-0029 Artifact Provenance Model.

## Mission
Create the first Mission Registry and Mission Numbering Standard so Estate missions can be tracked as durable institutional objects distinct from work packages, events, and audit records.

## Why This Is Next
The Estate now has work packages, operational reports, document registry concepts, and artifact provenance. The Steward also needs durable mission/task identifiers and human-readable mission titles so long-running initiatives can survive individual chats, workers, and implementation cycles.

## Scope
Create a bounded mission registry and standard.

Possible outputs:

- `docs/operations/Mission_Registry_Standard_v1.md`
- `data/registry/missions.json`

## Mission Registry Fields
Define and populate fields such as:

- mission_id
- mission_title
- mission_type
- status
- owner
- steward_authorization
- related_work_packages
- related_documents
- related_artifacts
- created_at
- updated_at
- notes

## Numbering Standard
Define a simple mission ID convention. Example:

- `MISSION-0001`
- `AO-0001` for Autonomous Operations epic if already established
- or another simple convention consistent with current Estate naming

Keep the convention small and do not over-engineer.

## Initial Mission Entries
Seed the registry with a small set of current missions if supported by existing artifacts, such as:

- Estate operational stabilization
- Work package pipeline
- Alfred operational activation
- Helen HR operational onboarding
- Autonomous Estate Operations / Steward Recall if already documented

If evidence is insufficient, mark entries as proposed or unresolved rather than inventing authority.

## Expected Outputs
- Mission registry standard document.
- Initial machine-readable mission registry.
- Optional CLI/helper if consistent with existing patterns, for example:

```bash
PYTHONPATH=src python -m estate.cli.main mission-registry --json
```

## Constraints
Do not replace work package IDs. Do not replace EC numbers. Do not replace audit evidence. Do not create new governance offices. Do not invent Steward approvals. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Add tests if code is added. If registry-only, validate:

- registry JSON parses
- mission IDs are unique
- related work package references are strings and preserve existing WP IDs
- no invented approvals are marked as final

## Completion Signal
Before finishing, create `collaboration/work_packages/completions/WP-0030_codex_done.json` with work_package_id, codex_status=done, completed_at, branch, pull_request_url, summary, files_changed, tests_run, known_limitations, ready_for_ca_review=true, merge_authority=ca_verified_auto_merge_allowed.

## Merge Class
Class A for bounded registry/documentation implementation after CA verification. Escalate to Class B only if implementation changes governance authority, replaces existing IDs, or asserts Steward approvals not present in evidence.
