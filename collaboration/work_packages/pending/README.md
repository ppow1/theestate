# Pending Codex Work Packages

Status: Pending
Classification: Estate Internal
Owner: Chief Architect #3 / Steward

## Purpose

This folder holds Codex-ready or architecture-first work package drafts so the Steward can hand Codex a simple instruction:

```text
Open the specified work package file in ppow1/theestate and execute the directions inside.
```

## Execution Modes

- `SERIES`: do only after its listed dependency packages are merged.
- `PARALLEL`: may be handed to Codex alongside other parallel packages if they do not touch the same hot files.
- `ARCHITECTURE-FIRST`: do not hand directly to Codex for implementation until Chief Architect review produces an implementation package.

## Current Recommended Order

1. WP-0013 is already handed to Codex.
2. Next Codex-ready sequence:
   - WP-0014 mailbox destination coverage
   - WP-0015 message acknowledgement and reply flow
   - WP-0025 local operational validation runner
3. Architecture-first packages should be reviewed by Chief Architects before Codex implementation.

## Hot File Warning

Many implementation packages may touch `src/estate/cli/main.py`. Avoid handing multiple CLI-heavy packages to Codex simultaneously unless they are clearly independent or Codex is asked to branch from the latest merged main.
