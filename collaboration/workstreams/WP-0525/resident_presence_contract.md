# WP-0525 Resident Presence Contract

## Scope
This staged contract defines a resident-presence and operational-activity surface for Office installation by WP-0531. The staged module is not installed work and does not modify shared active Office files.

## Required Truthful Fields
Each resident card must expose:

- resident identity and office;
- current duty state and source status;
- active assignment, if supplied by source records;
- last completed duty, if supplied by source records;
- blocker and attention requirement;
- source update timestamp, viewer `as_of` timestamp, computed age, and stale indicator;
- drill-down links for assignments, conversations, mailboxes, work packages, and supporting evidence where supplied;
- explicit missing-evidence indicator when no supporting evidence is supplied.

## Guardrails
- Do not fabricate resident activity, assignments, completions, blockers, or evidence.
- Do not infer hidden monitoring or surveillance from presence data.
- Do not expand resident or operational authority; the surface is informational only.
- Local staged state must be marked `staged_not_installed`.
- Stale and attention indicators must be visible rather than silently normalized.

## Filters
The staged implementation supports filtering by resident name/id, office, status, and attention state.

## Conflict Surface
Expected installation overlaps are declared with existing `steward_presence`, resident cards/duty summaries, and operational activity modules. WP-0531 must reconcile those surfaces before installing this staged work.
