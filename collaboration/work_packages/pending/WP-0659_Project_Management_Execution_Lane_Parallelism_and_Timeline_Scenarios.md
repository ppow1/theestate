# WP-0659 — Project Management Execution Lane, Parallelism, and Timeline Scenarios

Status: Pending
Owner: Chief Architect
Execution lane: Codex
Change class: Analysis, decomposition, and planning only

## Objective

Produce an execution-ready decomposition of the Estate Project and Task Management program that identifies what must be done, where each work package should execute, what may run in parallel, what must remain sequential, and the estimated completion timelines for three delivery scenarios:

1. All Codex.
2. Hybrid: local RTX 4090 workers plus Codex.
3. All local, except work that cannot safely or practically execute locally.

Do not implement production code in this work package.

## Required inputs

Review and use the complete PTM specification suite created by WP-0658, including:

- `docs/architecture/estate_project_task_management_architecture.md`
- `docs/architecture/estate_project_task_management_protocol.md`
- `docs/architecture/estate_project_task_management_data_model.md`
- `docs/architecture/estate_project_task_management_user_experience.md`
- `docs/architecture/estate_project_task_management_kpi_financial_utilization_catalog.md`
- `docs/architecture/estate_project_task_management_implementation_roadmap.md`
- `collaboration/work_packages/planning/estate_project_task_management_work_package_backlog.md`

Also inspect the existing Engineering Worker Runtime, Dispatch Queue, local worker adapter, validation paths, and current repository structure before assigning execution lanes.

## Mandatory analysis

### 1. Refine the implementation backlog into concrete work packages

For every PTM backlog item, produce one or more bounded work-package definitions with:

- work-package ID and title;
- objective and deliverables;
- repository scope;
- dependencies and readiness gates;
- acceptance criteria;
- expected tests and validation;
- preferred execution lane;
- permitted alternate lanes;
- prohibited lanes;
- required context breadth;
- estimated effort range;
- estimated elapsed time range;
- uncertainty and confidence;
- review lane;
- whether a local 4090 worker can execute it safely.

The output may leave implementation details for later packages, but it must divide the program into sufficiently clear, bounded packages for scheduling and routing.

### 2. Execution capability and routing matrix

Define the decision model for assigning work among:

- Chief Architect / ChatGPT planning;
- Codex;
- local RTX 4090 coding workers;
- deterministic local scripts and ordinary Python tooling;
- validation-only workers or independent reviewers;
- Grace operational scheduling;
- Helen staffing and capability assessment;
- Steward-only decisions.

For each work type, record suitability, limitations, context requirements, expected quality, privacy constraints, cost considerations, and escalation triggers.

Provider or worker recommendations are advisory only. Existing Traffic Controller, Dispatch, budget, privacy, validation, and acceptance boundaries remain authoritative.

### 3. Dependency graph and parallelism map

Build a dependency graph for all proposed PTM work packages. Classify each relationship as:

- hard sequential dependency;
- soft dependency;
- parallel-safe;
- parallel with integration checkpoint;
- mutually exclusive or competing implementation branch.

Identify:

- critical path;
- earliest practical start for each package;
- maximum useful concurrency;
- shared-file or shared-contract collision risks;
- integration and validation checkpoints;
- packages that should be split to improve parallel execution;
- packages that must remain serial to avoid schema or authority drift.

Include Mermaid diagrams and a machine-readable dependency table.

### 4. Timeline scenarios

Produce schedule projections for at least these scenarios:

#### Scenario A — All Codex

Assume all eligible design and implementation packages are executed through Codex, with realistic review, merge, validation, and rework intervals.

#### Scenario B — Hybrid local 4090 plus Codex

Assign bounded, well-specified, locally suitable packages to the RTX 4090 worker lane and reserve broad-context, cross-cutting, architectural, or high-risk packages for Codex. Exploit safe parallelism.

#### Scenario C — Maximum local execution

Assign every practical package to local workers, identifying work that still requires Codex, Chief Architect, or Steward involvement. Include expected slowdown, extra decomposition, additional validation, and higher rework risk where applicable.

For every scenario provide:

- assumptions;
- lane assignment by work package;
- number of sequential waves;
- number of parallel waves;
- critical path;
- estimated best case, expected case, and conservative case;
- expected review and rework allowance;
- major schedule risks;
- capacity bottlenecks;
- projected Codex usage;
- projected local 4090 utilization;
- qualitative cost comparison;
- confidence rating.

Do not present false precision. Clearly distinguish measured facts, historical evidence, estimates, and unknowns.

### 5. Scheduling and resource projection protocol

Define the fields and calculation rules the future PTM system must use for:

- duration estimates;
- confidence ranges;
- dependencies;
- calendars and availability;
- worker capacity;
- provider quotas;
- concurrency limits;
- GPU/VRAM reservations;
- queue wait;
- review and validation time;
- rework allowance;
- financial estimates;
- forecast changes;
- actual-versus-plan reconciliation.

### 6. Recommended kickoff sequence

Recommend the exact next work packages after this analysis, including whether `SPEC-PTM-001`, an execution capability baseline, and `CORE-PTM-001` should be separate packages or combined. Explain the decision.

The recommendation must identify the first package that can be sent to a local worker and the first package that should remain with Codex.

## Required outputs

Create:

1. `docs/architecture/estate_ptm_execution_routing_matrix.md`
2. `docs/architecture/estate_ptm_dependency_and_parallelism_plan.md`
3. `docs/architecture/estate_ptm_timeline_scenarios.md`
4. `docs/architecture/estate_ptm_scheduling_projection_protocol.md`
5. `collaboration/work_packages/planning/estate_ptm_detailed_execution_backlog.md`
6. `collaboration/work_packages/completions/WP-0659_completion_receipt.md`

The detailed execution backlog must be suitable for later conversion into individual pending work-package files.

## Constraints

- Do not implement production PTM code.
- Do not create a second Dispatch Queue, execution system, scheduler, or governance layer.
- Do not assume every task is suitable for the local 4090.
- Do not assume Codex work is automatically serial; identify safe concurrency.
- Do not claim exact timelines without documenting assumptions and uncertainty.
- Preserve Helen, Grace, Traffic Controller, Chief Architect, and Steward authority boundaries.
- Reuse existing Estate work-package, Dispatch, worker runtime, evidence, validation, and acceptance patterns.

## Acceptance criteria

- Every proposed PTM implementation package has an execution-lane recommendation and dependency classification.
- The critical path and parallel-safe groups are explicit.
- All-Codex, hybrid, and maximum-local timeline scenarios are complete and comparable.
- Estimates include best, expected, and conservative ranges with confidence and assumptions.
- Local 4090 suitability and Codex necessity are justified package by package.
- The output defines the next executable work packages and their order.
- No production implementation or second execution path is introduced.

## Delivery

Open a pull request for Chief Architect review. Do not merge it.