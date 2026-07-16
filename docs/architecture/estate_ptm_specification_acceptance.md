# Estate PTM Specification Acceptance

Status: Accepted
Accepted by: Steward / Chief Architect
Acceptance date: 2026-07-16

## Decision

The Estate Project and Task Management specification suite produced by WP-0658, the bounded package library and manifests produced by WP-0660, and the parallel campaign execution model produced by WP-0661 are accepted as the governing planning baseline for implementation preparation.

This acceptance authorizes Codex to prepare the existing 28 PTM planning drafts for execution by promoting them into properly written Pending work-package files and by producing executable campaign handoff instructions in dependency order.

This acceptance does not itself execute production implementation, merge implementation branches, grant budget authority, create a second dispatch queue, or alter established Helen, Grace, Traffic Controller, Chief Architect, or Steward authority boundaries.

## Accepted baseline

The accepted baseline includes:

- the PTM architecture, protocol, data model, user-experience, KPI, financial, utilization, scheduling, roadmap, and backlog documents;
- the 28 planning-draft package files under `collaboration/work_packages/planning/ptm_drafts/`;
- the package, campaign, and dependency manifests under `collaboration/work_packages/planning/`;
- the parallel fan-out, contract-freeze, midpoint-integration, and final-integration model in `docs/architecture/estate_ptm_parallel_campaign_execution_plan.md`;
- eight campaign containers, PTM-00 through PTM-07;
- Codex-only execution as the immediate implementation strategy for this program.

## Execution-preparation direction

Codex is authorized to:

1. Revalidate every planning draft against the current repository and accepted manifests.
2. Convert every valid PTM planning draft into a complete executable Pending work-package file.
3. Preserve atomic package IDs, dependencies, scopes, validation requirements, and acceptance lanes.
4. Update package, campaign, and dependency manifests so every executable package points to its Pending path and current readiness state.
5. Create executable campaign instruction documents that permit campaign-level Codex handoff rather than requiring the Steward to submit all 28 packages individually.
6. Incorporate the WP-0661 parallel launch groups, contract freezes, midpoint integration gates, branch controls, and merge checkpoints.
7. Return an ordered handoff index containing the exact Codex command for each campaign and identifying which commands may be submitted simultaneously.

## Immediate routing decision

For this implementation cycle, use Codex for all executable PTM campaign work. Do not route packages to the local RTX 4090 worker during this cycle, even where local execution was previously listed as preferred or permitted.

## Acceptance limitation

Planning drafts remain non-executable until Codex completes the authorized promotion task and the resulting Pending files and campaign handoff documents are merged and verified.
