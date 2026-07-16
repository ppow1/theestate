# WP-0662 — Promote PTM Drafts and Create Executable Campaign Handoffs

Status: Pending
Owner: Chief Architect
Execution lane: Codex
Change class: Execution preparation and work-package promotion only

## Objective

Convert the accepted Estate Project and Task Management planning baseline into an executable Codex campaign package set.

This work package must:

1. record and honor the Steward / Chief Architect acceptance already committed at `docs/architecture/estate_ptm_specification_acceptance.md`;
2. revalidate all 28 PTM planning drafts against the current repository, manifests, and WP-0661 parallel execution plan;
3. promote every valid planning draft into a complete executable Pending work-package file;
4. create executable campaign instruction documents that group the promoted packages into launchable Codex campaigns;
5. produce an ordered handoff index containing the exact Codex command for each campaign and clearly state which campaign commands may be submitted simultaneously.

Do not execute the PTM implementation in this work package. This package prepares and authorizes the executable work-package and campaign files only.

## Accepted authority baseline

The following acceptance is authoritative:

- `docs/architecture/estate_ptm_specification_acceptance.md`

The accepted baseline includes:

- the WP-0658 PTM specification suite;
- the 28 planning drafts under `collaboration/work_packages/planning/ptm_drafts/`;
- the package, campaign, and dependency manifests under `collaboration/work_packages/planning/`;
- the WP-0661 contract-first parallel fan-out and midpoint integration plan;
- Codex-only execution for this implementation cycle.

Do not route any PTM implementation package to the local RTX 4090 worker in this cycle.

## Required inputs

Review at minimum:

- `docs/architecture/estate_ptm_specification_acceptance.md`
- `docs/architecture/estate_ptm_parallel_campaign_execution_plan.md`
- `docs/architecture/estate_ptm_dependency_and_parallelism_plan.md`
- `collaboration/work_packages/planning/estate_ptm_package_manifest.json`
- `collaboration/work_packages/planning/estate_ptm_campaign_manifest.json`
- `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json`
- every Markdown file under `collaboration/work_packages/planning/ptm_drafts/`
- current work-package naming, status, completion, and campaign conventions in the repository

## Required promotion work

### 1. Revalidate every planning draft

For every draft package:

- confirm its ID, title, parent category, scope, dependencies, readiness gates, deliverables, validation approach, and acceptance lane;
- confirm its package-level dependency position against the WP-0661 execution DAG;
- confirm shared-file and shared-schema collision controls;
- replace obsolete source references or assumptions;
- resolve filename defects, punctuation hazards, or inconsistent paths;
- preserve the atomic package ID unless a documented collision requires a controlled replacement.

### 2. Create complete executable Pending packages

Create one executable Pending Markdown file for every valid PTM planning draft under:

`collaboration/work_packages/pending/`

Each promoted file must be complete and immediately usable by Codex. It must include at least:

- package ID and title;
- status `Pending`;
- owner and execution lane `Codex`;
- campaign ID and launch group;
- objective;
- exact repository scope;
- required inputs;
- bounded implementation deliverables;
- explicit non-goals and authority boundaries;
- dependencies and readiness gates;
- parallel-safety classification;
- shared-file/shared-schema collision controls;
- branch and integration expectations;
- required validation commands and evidence;
- acceptance criteria;
- required completion receipt path;
- delivery requirement to open a pull request and not merge it unless the package specifically states a different accepted workflow.

A planning-draft summary is not sufficient. Every promoted Pending file must contain enough context for a fresh Codex task to execute without referring back to this promotion package for missing instructions.

### 3. Preserve the WP-0661 parallel model

Use the WP-0661 model as controlling execution topology:

- root acceptance and inventory remain foundation gates;
- canonical event, ID, and projection contracts freeze before broad fan-out;
- parallel campaigns may begin as soon as their package-level dependencies are satisfied;
- shared contracts may not be independently changed by downstream branches;
- midpoint integration gates limit divergence;
- rollout remains after formal validation.

Do not convert the program back into eight fully serial campaigns.

### 4. Create executable campaign instruction documents

Create one campaign instruction document for each executable campaign under:

`collaboration/work_packages/campaigns/ptm/`

Use stable filenames such as:

- `PTM-00_Governance_Acceptance.md`
- `PTM-01_Read_Only_Source_Inventory.md`
- `PTM-02_Canonical_Contracts.md`
- `PTM-03_Governed_Intake_and_Import.md`
- `PTM-04_Visibility_and_Command_Surfaces.md`
- `PTM-05_Scheduling_Utilization_Financials_and_KPIs.md`
- `PTM-06_Dispatch_Evidence_and_Pilot_Migration.md`
- `PTM-07_Validation_and_Rollout.md`

Adjust campaign names only where the accepted manifests require it.

Each campaign instruction must include:

- campaign ID and title;
- campaign status and authority basis;
- included Pending work-package paths;
- exact package launch order;
- package groups that may run simultaneously;
- packages that must remain serial;
- prerequisite campaigns and package gates;
- contract-freeze requirements;
- branch naming guidance;
- integration branch or checkpoint requirements;
- merge order;
- validation required before the next fan-out or final integration;
- stop/replan conditions;
- the exact Codex handoff command for that campaign.

Campaign documents must let the Steward submit one campaign command rather than manually submit every package.

### 5. Create the ordered Codex handoff index

Create:

`collaboration/work_packages/campaigns/ptm/PTM_EXECUTABLE_CAMPAIGN_HANDOFF_INDEX.md`

The index must contain:

- all campaign documents in dependency order;
- the exact Codex handoff command for each campaign;
- a clearly labeled `Submit now`, `Submit together`, `Submit after midpoint integration`, and `Submit after final validation` sequence;
- which commands may be launched simultaneously in separate Codex tasks;
- which command must complete before the next group starts;
- the midpoint integration commands or campaign documents;
- the final integration and rollout commands;
- a concise operator checklist for verifying each campaign PR before launching the next group.

The index must not require the Steward to derive commands from manifests manually.

## Required manifest updates

Update:

- `collaboration/work_packages/planning/estate_ptm_package_manifest.json`
- `collaboration/work_packages/planning/estate_ptm_campaign_manifest.json`
- `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json`

For every promoted package, record:

- the executable Pending path;
- readiness status;
- campaign instruction path;
- Codex execution lane;
- launch group;
- package dependencies;
- integration checkpoint;
- promotion source draft path.

Campaign manifest entries must have populated execution-lane allocations and package paths. Do not leave required campaign routing fields empty.

## Required validation

Before claiming completion, verify programmatically that:

- all 28 accepted planning drafts have either a corresponding Pending package or a documented evidence-based exception;
- every promoted Pending package exists;
- every promoted package has all mandatory sections;
- every package ID is unique;
- every dependency points to an existing promoted package or accepted authority gate;
- every package belongs to exactly one primary campaign;
- every campaign instruction references existing Pending package files;
- every campaign contains an exact Codex handoff command;
- the handoff index references every campaign instruction;
- commands identified as simultaneous are dependency-safe under WP-0661;
- campaign-level execution-lane and path fields are populated in the manifests;
- no local-worker routing remains active for this implementation cycle;
- no production PTM implementation was performed;
- no second dispatch queue, second registry, second scheduler, or new governance authority was introduced.

Include validation commands and results in the completion receipt.

## Required outputs

Create or update:

1. one executable Pending work-package file for every accepted PTM planning draft;
2. all campaign instruction documents under `collaboration/work_packages/campaigns/ptm/`;
3. `collaboration/work_packages/campaigns/ptm/PTM_EXECUTABLE_CAMPAIGN_HANDOFF_INDEX.md`;
4. the three updated PTM manifests;
5. `collaboration/work_packages/completions/WP-0662_completion_receipt.md`.

## Acceptance criteria

- Steward / Chief Architect acceptance is recorded and referenced.
- All valid PTM planning drafts are promoted into executable Pending packages.
- Every executable package is complete enough for a fresh Codex task.
- Campaign documents support campaign-level Codex execution.
- The handoff index gives exact commands in the correct dependency order.
- Parallel launch groups and midpoint integration gates match WP-0661.
- Codex-only routing is enforced for this implementation cycle.
- No production PTM implementation occurs in this package.

## Delivery

Open a pull request for Chief Architect review. Do not merge it.
