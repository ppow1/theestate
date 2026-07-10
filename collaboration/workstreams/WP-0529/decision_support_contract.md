# WP-0529 Decision Support Contract

This staged work defines advisory-only decision support for Office work items. It is not installed work and does not modify shared active Office files.

## Inputs

Each `WorkItem` supplies:

- identity, title, state, controlling artifact, and workspace links;
- dependency IDs and explicit blocker labels;
- named evidence paths;
- optional alternative governed paths;
- update timestamp and advisory authority label.

## Outputs

`build_decision_support` returns deterministic recommendations with:

- blocker and dependency explanations;
- missing-evidence lists;
- evidence-backed next actions;
- confidence, uncertainty, and freshness indicators;
- alternative governed paths;
- links to controlling artifacts and workspaces;
- an explicit governance boundary separating recommendation from authorization, execution, validation, and acceptance.

## Governance Boundary

The staged module is rule-based first. It does not call a model provider, mutate input work item state, authorize work, execute work, validate work, or accept work. Optional model assistance may only be added later behind existing provider boundaries by the WP-0531 installation owner.

## Conflict Surface

Expected installation targets overlap with Mission Control, Operations Manager, Traffic Controller, and executive workspace rendering. These overlaps are declared in `install_manifest.json` and must be reconciled before installation.
