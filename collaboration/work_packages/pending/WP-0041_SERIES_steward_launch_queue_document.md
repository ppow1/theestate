# SERIES TASK WP-0041 — Steward Launch Queue Document

## Codex Command
Read `collaboration/work_packages/pending/WP-0041_SERIES_steward_launch_queue_document.md` and do exactly what it says.

## Mode
SERIES.

## Mission
Create the repository-resident Steward Launch Queue document so the Steward can copy Codex commands without asking a Chief Architect for the next item.

## Scope
Generate and maintain:

- `collaboration/work_packages/codex_series_queue.md`

The document should list ready work packages in order. Each item must have the task heading outside the copy block and only the Codex prompt inside the copy block.

## Required Format
For each queued package:

# SERIES TASK

```text
Read:

collaboration/work_packages/pending/WP-XXXX_NAME.md

and do exactly what it says.
```

## Behavior Requirements
- Include all pending SERIES work packages not yet completed.
- Do not include completed packages if completion records exist.
- Preserve simple copy/paste usability.
- Add a brief queue status section at the top.

## Constraints
Do not automate Codex submission. Do not change work package content. Do not edit ledger or devlog.

## Tests
If code is added, test queue generation. If documentation-only, validate links/paths exist.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0041_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
