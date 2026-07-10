# WP-4007 — Ingrid Privacy, Classification, and Boundary Inventory

Status: Pending
Owner: Character Architecture / Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4004, WP-4005
Classification: Estate Internal

## Objective

Create the authoritative inventory of privacy, classification, connector, protected-source, journal, continuity, and personnel boundaries Ingrid must govern before Ingrid's full resident implementation begins.

## Required Scope

Inventory and classify:

- resident identity records;
- public and private interaction layers;
- working journals;
- reflection records;
- continuity artifacts;
- workforce assessments;
- cognitive-health records;
- personnel and onboarding records;
- mailbox and communication content;
- connector-derived data;
- protected private local character material;
- provider prompts and outputs;
- Office and task-board summaries.

For each class define:

- owner;
- minimum classification;
- allowed readers;
- allowed writers;
- permitted summaries;
- export restrictions;
- retention expectations;
- audit requirements;
- connector requirements;
- escalation path.

## Required Outputs

- `docs/residents/ingrid/Ingrid_Boundary_Inventory_v0_1.md`
- versioned machine-readable boundary matrix;
- validation rules consumable by Helen, Grace, and Character Continuity;
- focused tests proving private-to-public leakage is rejected;
- `operations/validation/reports/WP-4007_ingrid_boundary_inventory.md`;
- `collaboration/work_packages/completions/WP-4007_codex_done.json`.

## Boundaries

Do not design Ingrid's entire personality. Do not create new classifications if existing Estate classifications can absorb the requirement. Do not inspect protected private local character content. Do not centralize unrestricted secrets into one file.

## Acceptance Criteria

- every relevant resident and workforce artifact class has an explicit boundary;
- minimum-necessary access is enforceable;
- public summaries cannot include restricted source content;
- Helen and Grace integrations can consume the boundary matrix without becoming privacy authorities;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4007_Ingrid_Privacy_Classification_and_Boundary_Inventory.md and do exactly what it says.
```
