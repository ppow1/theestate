# WP-0657 — Complete Open WebUI Engineering Dispatch Execution Metadata

Status: Pending
Owner: Chief Architect
Execution Target: Codex
Priority: Immediate

## Objective
Repair the Open WebUI Engineering assignment path so the dispatch item it creates is immediately eligible for the existing WP-0656 dispatch-to-engineering-worker bridge without manual queue editing.

## Verified Failure
The Open WebUI command successfully created Helen, Grace, Traffic Controller, and Dispatch artifacts, but the resulting queue item failed `prepare_handoff(...)` with:

- provider is required
- prompt_source or work-package source is required
- allowed_read_paths are required
- authorization or decision reference is required

The actual dispatch was `dispatch-6d215cd2e75a`, initially `Queued`, then manually moved to `Ready`. The bridge