# WP-0660 — Correct PTM Execution Decomposition and Hour-Scale Timeline Model

Status: Pending
Owner: Chief Architect
Execution lane: Codex
Change class: Corrective analysis, decomposition, and planning only

## Objective

Correct the material misunderstanding in the WP-0659 execution-planning report.

The Estate does not accept the prior 10–36 implementation-day projections as a valid model for this program. The planning unit is expected to be minutes or hours of active execution, not focused implementation days.

This work package must complete the deliverables omitted by PR #360 and rebuild the execution projections from complete bounded work-package drafts using the Steward's operating assumptions below.

Do not implement production PTM code in this work package.

## Correction baseline

PR #360 produced a useful broad campaign outline, but it did not satisfy WP-0659 because it:

- retained the original 17 broad backlog rows instead of producing the fully decomposed package library;
- did not create one complete draft Markdown file for every resulting work package;
- did not create the required package and campaign manifests;
- did not provide package-by-package RTX 4090 suitability and Codex necessity;
- replaced the requested execution scenarios with serial, balanced-Codex, and aggressive-Codex timing models;
- estimated the work in implementation days without evidence that Estate work packages require day-scale active execution.

Treat the WP-0659 report as preliminary source material only. Do not preserve its day-scale estimates as authoritative.

## Steward planning assumptions

Use the following as explicit planning assumptions unless repository evidence demonstrates that a particular package is materially different:

1. No properly bounded PTM work package should require more than 60 minutes of active execution.
2. Most properly bounded PTM work packages should require less than 15 minutes of active execution.
3. The initial 17 backlog categories are not necessarily the final package count. Split broad categories until they meet bounded execution expectations.
4. Approximately eight hours of active execution capacity should be treated as ample for a program of roughly 17 ordinary bounded packages, before external wait states.
5. Review latency, queue wait, merge delay, Steward availability, failed validation, rework, and blocked dependencies must be reported separately from active execution time.
6. Do not convert short machine execution into multi-day estimates by assuming human software-development pacing.
7. Codex may challenge an assumption for a specific package only by citing concrete scope, repository, validation, migration, or integration evidence.

The purpose is not to force an artificially low number. The purpose is to model how this Estate actually executes bounded AI work packages.

## Required time model

For every package and campaign distinguish at least:

- active execution time;
- validation time;
- expected rework allowance;
- integration time;
- queue wait;
- human/Steward review wait;
- blocked dependency wait;
- total machine-active time;
- total expected wall-clock elapsed time under stated availability assumptions.

All package estimates must be expressed primarily in minutes or hours. Days may be shown only as a secondary wall-clock conversion where unavoidable external waits justify them.

Use estimate ranges rather than unsupported exact values:

- best case;
- expected case;
- conservative case;
- confidence rating;
- estimate basis.

## Required execution scenarios

Recalculate these exact scenarios:

### Scenario A — All Codex

All eligible analysis, drafting, implementation, and validation work executes through Codex, while Chief Architect and Steward decisions remain human authority gates.

Report:

- package sequence;
- parallel-safe Codex groups;
- number of Codex task submissions or campaigns;
- total active Codex execution minutes/hours;
- expected validation and rework time;
- expected wall-clock time under one available Codex lane;
- expected wall-clock time where multiple Codex tasks may safely run concurrently.

### Scenario B — Hybrid RTX 4090 plus Codex

Route bounded local-suitable packages to the existing local RTX 4090 worker lane and reserve broad-context, cross-cutting, architecture-sensitive, or high-risk work for Codex.

Report:

- package-by-package lane assignment;
- packages that run concurrently locally and through Codex;
- total Codex active time;
- total local active time;
- projected 4090 utilization;
- critical path;
- expected wall-clock time;
- review and integration checkpoints.

### Scenario C — Maximum local execution

Route every safe and practical package to local RTX 4090 workers, while identifying packages or decisions that still require Codex, Chief Architect, Steward, Grace, Helen, Traffic Controller, or independent validation.

Report:

- local decomposition overhead;
- extra validation and rework risk;
- packages prohibited from local execution;
- total local active time;
- remaining Codex active time;
- critical path and expected wall-clock time.

## Required complete package library

Create one complete planning-draft Markdown file for every resulting package under:

`collaboration/work_packages/planning/ptm_drafts/`

The final package count must be determined by sound decomposition and may be greater or less than 17.

Every draft must include:

- package ID and title;
- status `Planning Draft — Not Authorized for Execution`;
- parent PTM backlog category;
- objective;
- bounded deliverables;
- exact repository scope;
- source inputs;
- dependencies;
- readiness gates;
- preferred execution lane;
- permitted alternate lanes;
- prohibited lanes;
- local RTX 4090 suitability and justification;
- context breadth;
- active execution estimate in minutes;
- validation estimate in minutes;
- rework allowance;
- expected wall-clock range;
- parallelism classification;
- shared-file collision risks;
- acceptance criteria;
- validation commands or validation approach;
- review and acceptance lane;
- prerequisite revalidation requirement before promotion to Pending.

A summary row is not a substitute for an individual draft file.

## Campaign and wave structure

Group the complete package library into executable campaigns or waves so the Steward does not need to submit dozens of packages individually.

Each campaign must include:

- campaign ID and title;
- objective;
- included package IDs and draft paths;
- prerequisite campaigns and readiness gates;
- packages that run serially;
- parallel-safe groups;
- maximum useful concurrency;
- execution-lane allocation;
- integration checkpoints;
- campaign acceptance gate;
- active execution estimate by lane;
- best, expected, and conservative wall-clock estimates;
- conditions requiring the campaign to stop or replan.

Campaigns are authorization and submission containers. Work packages remain the atomic execution and evidence units.

## Required machine-readable manifests

Create:

1. `collaboration/work_packages/planning/estate_ptm_package_manifest.json`
2. `collaboration/work_packages/planning/estate_ptm_campaign_manifest.json`
3. `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json`

The package manifest must map every package to:

- file path;
- parent category;
- campaign;
- preferred lane;
- alternate/prohibited lanes;
- active execution estimate;
- validation estimate;
- dependencies;
- parallel group;
- confidence;
- readiness status.

The campaign manifest must support future instructions such as:

- execute Campaign PTM-01 using All Codex;
- execute Campaign PTM-03 using Hybrid routing;
- execute the next ready campaign using Local Preferred routing.

The dependency manifest must identify hard dependencies, soft dependencies, parallel-safe relationships, integration checkpoints, shared-file collisions, and mutually exclusive branches.

## Required reports

Create or replace the planning outputs with:

1. `docs/architecture/estate_ptm_execution_routing_matrix.md`
2. `docs/architecture/estate_ptm_dependency_and_parallelism_plan.md`
3. `docs/architecture/estate_ptm_timeline_scenarios.md`
4. `docs/architecture/estate_ptm_scheduling_projection_protocol.md`
5. `collaboration/work_packages/planning/estate_ptm_detailed_execution_backlog.md`
6. the complete draft package library under `collaboration/work_packages/planning/ptm_drafts/`
7. the three machine-readable manifests listed above;
8. `collaboration/work_packages/completions/WP-0660_completion_receipt.md`

The timeline report must explicitly explain why its estimates differ from PR #360 and must not silently retain the prior day-scale model.

## Required kickoff recommendation

Identify:

- the first campaign ready for Chief Architect acceptance;
- the first campaign executable entirely by Codex;
- the first campaign suitable for hybrid execution;
- the first individual package suitable for the RTX 4090 worker;
- the packages that must remain with Codex;
- the expected total active execution time and expected elapsed time for the recommended strategy.

Do not authorize or execute any implementation package as part of this corrective planning assignment.

## Validation requirements

Before claiming completion, verify programmatically that:

- every manifest package points to an existing draft file;
- every draft contains all required sections;
- every dependency points to a known package;
- every package belongs to exactly one primary campaign;
- every campaign references existing packages;
- all three required execution scenarios are present;
- all scenario totals are derived from the package estimates;
- no package active execution estimate exceeds 60 minutes without a documented evidence-based exception;
- packages over 15 expected active minutes are flagged for review or further decomposition;
- no production runtime, second queue, second registry, or governance authority was introduced.

Include the validation commands and results in the completion receipt.

## Acceptance criteria

- The missing WP-0659 package-library and manifest deliverables are complete.
- The timing model uses minutes and hours for active execution.
- Active execution and wall-clock waiting are clearly separated.
- All-Codex, Hybrid, and Maximum-Local scenarios are directly comparable.
- Package-level estimates roll up mathematically into campaigns and scenarios.
- Parallelism and critical paths are derived from the full package set.
- Every package has a justified execution-lane assignment.
- The prior 10–36 implementation-day model is explicitly corrected rather than repeated.
- No production implementation is performed.

## Delivery

Open a pull request for Chief Architect review. Do not merge it.