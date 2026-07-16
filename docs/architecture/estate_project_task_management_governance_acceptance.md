# Estate Project Task Management Governance Acceptance Boundary

Status: Accepted Gate 0 validation artifact
Package: `SPEC-PTM-001`
Campaign: `PTM-00`
Date: 2026-07-16

## Purpose

This artifact records the Gate 0 governance boundary accepted for the Estate Project Task Management (PTM) implementation-preparation program. It is a validation and specification artifact only; it does not authorize production PTM implementation.

## Accepted authority baseline

The governing PTM baseline is the Steward / Chief Architect acceptance recorded in `docs/architecture/estate_ptm_specification_acceptance.md`. That acceptance covers the specification suite produced by WP-0658, the bounded package library and manifests produced by WP-0660, and the parallel campaign execution model produced by WP-0661.

The accepted baseline includes:

- the PTM architecture, protocol, data model, user-experience, KPI, financial, utilization, scheduling, roadmap, and backlog documents;
- the 28 PTM planning-draft packages under `collaboration/work_packages/planning/ptm_drafts/`;
- the PTM package, campaign, and dependency manifests under `collaboration/work_packages/planning/`;
- the parallel fan-out, contract-freeze, midpoint-integration, and final-integration model in `docs/architecture/estate_ptm_parallel_campaign_execution_plan.md`;
- eight campaign containers, `PTM-00` through `PTM-07`; and
- Codex-only execution as the immediate implementation strategy for this program.

## Frozen Gate 0 boundaries

Downstream PTM packages must treat the following Gate 0 boundaries as frozen unless a later Chief Architect / Steward replan explicitly changes them:

1. **Authority boundary:** PTM work remains governed by the existing Steward, Chief Architect, Helen, Grace, and Traffic Controller authority model. No package may create a new governance authority or bypass required review.
2. **Execution-lane boundary:** This implementation cycle is Codex-only. The local RTX 4090 worker is inactive for PTM campaign work in this cycle.
3. **Implementation boundary:** Gate 0 authorizes implementation-preparation work only. It does not authorize production PTM code, production merge, budget authority, or operational rollout.
4. **Planning-unit boundary:** Package estimates and dependency planning use minute-scale active execution, validation, and rework estimates from the accepted WP-0660/WP-0661 manifests.
5. **Campaign boundary:** Campaign containers are authorization handoff units, not a second dispatch queue, second package registry, second scheduler, or replacement governance process.
6. **Contract-freeze boundary:** The WP-0661 fan-out model controls when event, ID, projection, intake, route, schedule, dispatch, and validation contracts freeze. Downstream packages must not redefine those frozen contracts independently.

## Required downstream behavior

Downstream PTM packages must:

- use the pending-package paths promoted in `collaboration/work_packages/planning/estate_ptm_package_manifest.json` and `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json`;
- follow package dependencies and launch groups from `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json`;
- follow campaign handoff paths and concurrency limits from `collaboration/work_packages/planning/estate_ptm_campaign_manifest.json` and `docs/architecture/estate_ptm_parallel_campaign_execution_plan.md`;
- stop and replan if a package requires a new governance authority, a second dispatch queue, a second registry, a second scheduler, or a change to a frozen upstream contract; and
- preserve Chief Architect review and non-merge expectations unless a separate accepted workflow authorizes merge.

## Gate 0 acceptance finding

`SPEC-PTM-001` accepts the canonical PTM specification boundaries for downstream implementation-preparation packages. The package is source-backed by the accepted PTM specification acceptance, parallel execution plan, dependency plan, pending package, planning draft, and PTM manifests. No second queue, registry, scheduler, or governance authority is introduced by this Gate 0 artifact.
