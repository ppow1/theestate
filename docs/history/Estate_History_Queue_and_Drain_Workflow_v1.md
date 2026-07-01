# Estate History Queue and Drain Workflow v1

Status: Version 1 Standard
Owner: Eleanor / Archives and Registrar
Operational Coordinator: Alfred / Chief of Staff
Architecture Owner: Chief Architect
Validation Owner: Audit
Classification: Estate Internal

## Purpose

The Estate protects two hot canonical history files:

- estate_ledger/ledger.md
- development/devlog.md

These files are the official chronological record of Estate Changes and development activity.

Routine workers must not edit these files directly.

Instead, routine workers submit pending history notes into a queue. Only explicit history-drain or global-sync tasks reconcile queued notes into the canonical ledger and devlog.

This pattern is modeled after CueMastery's devlog queue pattern and adapted to the Estate's two-file history structure.

## Why This Exists

The Collaboration Layer allows multiple workers and GitHub-mediated edits.

That creates a risk: parallel workers can all try to edit ledger.md and devlog.md at the same time, causing merge conflicts, drift, duplicated EC entries, skipped numbers, and audit failures.

The queue protects the hot files while preserving institutional memory.

## Protected Canonical Files

The following files are protected hot canonical files:

- estate_ledger/ledger.md
- development/devlog.md

Only explicit history-drain or global-sync work may edit them.

Routine work packages must submit queued notes instead.

## History Queue Locations

Pending notes:

- estate_history/queue/pending

Drained notes:

- estate_history/queue/drained

Rejected notes:

- estate_history/queue/rejected

Templates:

- estate_history/templates

## Routine Worker Rule

Routine workers may create or update files under the history queue.

Routine workers must not directly edit:

- estate_ledger/ledger.md
- development/devlog.md

If a worker performs work that needs history, the worker writes a pending history note.

## History Note Requirements

A pending history note should include:

- proposed EC number if known
- title
- timestamp
- author or worker
- classification
- files changed
- summary
- audit status if known
- whether canonical ledger/devlog reconciliation is required
- related commit or branch if known

## Drain Workflow

A drain task performs the following controlled process:

1. Inspect pending history notes.
2. Confirm the next unused EC number.
3. Resolve duplicates or numbering drift.
4. Add canonical entries to estate_ledger/ledger.md.
5. Add canonical entries to development/devlog.md.
6. Move processed notes to estate_history/queue/drained.
7. Run audit locally.
8. Commit only after audit is clean.

## EC-000086 Repair

EC-000086 was created through GitHub to add the reusable worker seed chat template, but the canonical ledger/devlog were not updated in the same change.

The correct repair is not to teach every worker to edit ledger/devlog.

The correct repair is to add a pending history note and drain it through this workflow.

## Audit Expectations

Audit should remain the final validator.

A clean state requires:

- ledger structure passes
- devlog structure passes
- latest ledger EC appears in devlog
- latest git EC matches latest ledger EC
- git working tree clean

## Future Automation

Future automation may:

- collect pending history notes
- propose EC numbers
- detect drift
- generate ledger/devlog entries
- prepare drain commits
- validate audit before merge

Automation must not remove Eleanor's institutional record authority or Audit's validation role.
