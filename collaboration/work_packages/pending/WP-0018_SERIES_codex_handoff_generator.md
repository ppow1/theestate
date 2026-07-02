# SERIES TASK WP-0018 — Codex Handoff Generator

## Codex Command
Read `collaboration/work_packages/pending/WP-0018_SERIES_codex_handoff_generator.md` and do exactly what it says.

## Mode
SERIES. Depends on WP-0016 and WP-0017 being accepted or at least reviewed for the minimum work package fields/state expectations.

## Mission
Create a small generator that emits the simple Codex launch command for a pending work package.

## Why This Is Next
The Steward should not manually compose long prompts. The work package file is the contract; the launch command is just a pointer.

## Requirements
- Add a command or script that lists pending work packages and prints copy-ready Codex commands.
- The generated command format should be:
  `<MODE> TASK\n\nRead:\n<path>\n\nand do exactly what it says.`
- Detect mode from filename prefixes: SERIES, PARALLEL, ARCHITECTURE_FIRST.
- Include path, title, mode, and dependency notes in a human-readable list.
- Do not submit to Codex automatically.

## Expected Outputs
- CLI or script for listing pending Codex commands.
- Tests covering command generation for series, parallel, and architecture-first packages.
- Documentation for Steward usage.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0018_codex_done.json` with status, PR URL, files changed, tests run, and ready_for_ca_review=true.

## Merge Class
Class A — bounded implementation after CA verification.
