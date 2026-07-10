# WP-0530 - Guided Operational Workflows

## Codex Command
Read collaboration/work_packages/pending/WP-0530_PARALLEL_STAGED_Guided_Operational_Workflows.md and do exactly what it says.

## Mode
PARALLEL-STAGED

## Mission
Build staged guided workflows for common Estate operations using existing canonical handlers and authority gates.

## Initial Workflow Families
- work-package review and promotion;
- validation request, evidence review, and next action;
- resident onboarding preparation;
- project intake and assignment;
- local service readiness and approved launch;
- incident or failure triage;
- operational handoff and follow-up.

## Required Capabilities
- step-by-step guided inputs;
- precondition and authority checks;
- save/resume;
- explicit confirmation before state-changing steps;
- evidence links and generated artifacts;
- truthful blocked/failed/completed states;
- rollback or recovery guidance where supported;
- no automatic approval, acceptance, merge, retry, or provider selection.

## Staging Requirements
Create under `collaboration/workstreams/WP-0530/`:

```text
install_manifest.json
staged/office_operational_workflows.py
staged/test_office_operational_workflows.py
operational_workflow_catalog.json
operational_workflow_contract.md
validation_notes.md
rollback_notes.md
```

Do not modify shared active Office files. WP-0531 performs installation.

## Conflict Surface
Expected final targets include a dedicated workflow module and catalog, Office workspace/action hooks, tests, and docs. Reuse WP-0523's guided-action contract rather than creating a competing framework.

## Validation
Prove representative workflows, save/resume, blocked preconditions, explicit confirmations, canonical handler invocation, and no authority bypass.

## Completion Receipt
Create `collaboration/work_packages/completions/WP-0530_codex_done.json` and state that staged work is not installed work.
