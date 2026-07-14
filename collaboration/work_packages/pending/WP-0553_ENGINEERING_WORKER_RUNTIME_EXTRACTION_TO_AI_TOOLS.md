# WP-0553 — Engineering Worker Runtime Extraction to AI Tools

Status: Ready for implementation
Office owner: Chief Architect #5
Work-package range: WP-0500 through WP-0599
Repository: ppow1/theestate
Depends on: Campaign 0550 / PR #344 merged

## Objective

Extract the executable local engineering worker runtime from the Estate repository into the Steward-controlled AI tools area while preserving the Estate as the governance and control plane.

Production target:

`A:\AI\Tools\EngineeringWorkerRuntime`

Related external roots:

- Worktrees: `A:\AI\EngineeringWorktrees`
- Run evidence: `A:\AI\EngineeringRuns`

The Estate must retain only contracts, adapters, staffing and operations records, dispatch decisions, qualification summaries, evidence hashes, canonical evidence paths, and institutional acceptance records.

## Current state to refine

Campaign 0550 added:

- `src/estate/core/local_engineering_department.py`
