# WP-4000 — Helen Workforce Runtime Integration

Status: Pending
Owner: Resident Runtime Implementation Stream
Originating Office: Character Architecture
Execution Target: Codex
Classification: Estate Internal

## Purpose

Complete the first production-facing integration of Helen's workforce-development implementation.

The design is already established. This package is an implementation and integration task, not an invitation to redesign Helen, redefine her office, or alter Estate constitutional boundaries.

## Read First

Before editing code, read these artifacts completely:

- `docs/residents/helen/Helen_Resident_Profile_v0_2.md`
- `docs/residents/helen/Helen_Resident_Validation_v0_2.md`
- `docs/residents/helen/Helen_Hiring_Onboarding_Workflow_v0_1.md`
- `docs/residents/helen/Helen_Local_Standup_Runbook_v0_1.md`
- `docs/residents/helen/Helen_Standup_Readiness_Matrix_v0_1.md`
- `docs/residents/helen/runtime/Helen_Workforce_Development_Runtime_Integration_v0_2.md`
- `docs/residents/helen/platform-exports/textgen-4_9-helen-v0_2.yaml`
- `src/estate/core/helen_workforce.py`
- `src/estate/cli/helen_workforce.py`
- `tests/test_helen_workforce.py`
- `tests/test_helen_workforce_cli.py`
- `tests/character_architecture/test_helen_resident_package.py`
- `src/estate/core/background_operations.py`
- `src/estate/core/background_operations_runtime.py`
- `src/estate/cli/main.py`

## Architectural Invariants

These are mandatory and must remain true:

1. Helen is the Estate resident for Human Resources and Workforce Development.
2. Helen may conduct approved hiring and onboarding workflows for already authorized roles.
3. Helen may not create offices, grant constitutional authority, approve budgets, merge code, or bypass Steward-reserved appointments.
4. Helen evaluates both worker-level and institutional causes of failure.
5. Helen owns workforce development, staffing readiness, onboarding quality, cognitive-health review, lessons learned, reflection-cycle support, and Character Continuity support.
6. Grace / Office of Operations owns operational conduct and queue movement.
7. Engineering executes engineering work, including CueMastery work.
8. Ingrid owns privacy, classification, connector, and protected-source boundaries.
9. Alfred protects the Steward's attention and receives concise workforce exceptions.
10. The resident operates through the runtime. The resident does not become the runtime.
11. Helen must not execute providers, control operational sequencing, create a parallel dispatch queue, or fabricate live connector state.
12. Private journals and sensitive cognitive-health details must not become unrestricted operational telemetry.
13. Grace must remain a candidate or approved future staffing target until all constitutional, validation, runtime-registration, and Steward-reserved appointment prerequisites are satisfied.
14. Existing v0.1 artifacts must remain compatible unless a failing test proves a necessary repair.
15. Do not inspect, reference, summarize, or incorporate protected private local character material.

## Existing Implementation

The repository already contains:

- `WorkforceRequest`
- `WorkforceAssessment`
- `HelenWorkforceStore`
- local JSON artifact persistence under `runtime/workforce_development/`
- a standalone CLI in `estate.cli.helen_workforce`
- focused unit tests

Treat this as the baseline implementation. Improve or extend it only where required by this package.

## Required Scope

### 1. Integrate Helen into the Main Estate CLI

Add a governed top-level command surface to `src/estate/cli/main.py`.

Preferred command shape:

```text
estate helen-workforce request-create --file <path>
estate helen-workforce assessment-create --file <path>
estate helen-workforce request-show --request-id <id>
estate helen-workforce requests-list
estate helen-workforce assessments-list
estate helen-workforce status
```

Requirements:

- Reuse the existing implementation in `src/estate/cli/helen_workforce.py` or refactor shared command behavior into a small reusable layer.
- Do not duplicate business rules in two independent implementations.
- Preserve `--json` support.
- Preserve local-first execution.
- Keep error messages deterministic and useful.
- Do not create new generic CLI frameworks or registries merely for this task.

### 2. Define Stable JSON Schemas

Create versioned JSON schemas for:

- workforce request;
- workforce assessment;
- workforce status summary.

Place them in an existing appropriate schema location if one exists. Otherwise use:

```text
docs/schemas/workforce_development/
```

Schema requirements:

- explicit version field;
- required and optional fields;
- allowed enum values;
- classification rules;
- privacy-sensitive field rules;
- example payloads;
- no unrestricted journal body field;
- explicit non-authority flags where appropriate.

Do not introduce a new schema registry if an existing convention can absorb these files.

### 3. Add Runtime Event Interoperability

Implement a narrow bridge between Helen workforce artifacts and the existing background/operational event substrate.

Required behavior:

- A newly created workforce request may emit a governed event artifact describing that the request exists.
- A workforce assessment that requires Steward attention, boundary review, temporary stand-down, succession review, or governance review may emit a governed attention event.
- Events must not execute providers, move operational queues, appoint personnel, or create institutional truth.
- Sensitive subjects must preserve boundary-review requirements.
- Event creation must be deterministic and testable.
- Avoid modifying the background runtime's core behavior unless necessary.
- Prefer a small adapter or helper over broad coupling.

### 4. Surface Workforce Status to Existing Office/Operations Views

Identify the smallest existing status surface that can absorb Helen workforce status without creating a new dashboard institution.

At minimum, expose:

- open requests;
- in-review requests;
- ready-for-action requests;
- boundary-review count;
- Steward-attention count;
- assessment count;
- latest request identifier;
- latest assessment identifier;
- explicit flags that no provider execution, operational queue control, or constitutional authority grant occurred.

Use an existing Office of the Steward, command-center, status-board, or resident-presence surface where practical.

Do not build the full participant task board in this package.

### 5. Strengthen Store Semantics

Review and improve `HelenWorkforceStore` where needed.

Required checks:

- reject duplicate request or assessment identifiers unless an explicit idempotent replay is byte-for-byte equivalent;
- reject assessment creation for a missing request;
- preserve request/assessment subject consistency;
- write artifacts atomically where the repository has an existing pattern for atomic writes;
- ensure status generation remains valid with malformed or unrelated files present;
- include latest request and latest assessment identifiers in status;
- do not silently swallow validation errors;
- preserve deterministic filesystem layout.

Do not add a database.

### 6. Tests

Add or update tests covering:

- main Estate CLI command registration and execution;
- standalone CLI compatibility;
- JSON schema validity and example payloads;
- duplicate/idempotency behavior;
- missing-request assessment rejection;
- malformed artifact handling;
- event bridge behavior;
- sensitive subject boundary review;
- Steward attention escalation;
- status-surface integration;
- Grace remains unappointed and in review when prerequisites are missing;
- zero provider execution;
- zero operational queue control;
- zero constitutional authority grant;
- full existing Helen test compatibility.

Tests must not depend on live providers, network access, private local characters, or an actual TextGen process.

## Out of Scope

Do not:

- redesign Helen's personality or office;
- create Grace's final resident package;
- appoint or activate Grace;
- implement the full Character Continuity system;
- implement unrestricted worker journals;
- build a new Operations dashboard institution;
- create a new mailbox subsystem;
- execute live AI providers;
- alter CueMastery execution ownership;
- change constitutional governance;
- remove or weaken existing privacy restrictions;
- rewrite unrelated CLI code;
- perform broad repository cleanup.

## Expected Files

The exact file set may vary, but likely changes include:

- `src/estate/cli/main.py`
- `src/estate/cli/helen_workforce.py`
- `src/estate/core/helen_workforce.py`
- one small runtime/event adapter module if needed
- one existing status-surface module if needed
- versioned workforce schema files
- focused tests
- validation report
- completion receipt

## Validation Commands

Run at minimum:

```powershell
CLS
Set-Location A:\theestate
python -m pytest tests\test_helen_workforce.py tests\test_helen_workforce_cli.py tests\character_architecture\test_helen_resident_package.py -q
```

Also run all new focused tests introduced by this package.

Then run the relevant broader CLI/runtime tests for any modules modified.

If the full suite is practical, run:

```powershell
CLS
Set-Location A:\theestate
python -m pytest -q
```

If the full suite is not run or contains unrelated pre-existing failures, record that fact precisely in the validation report.

## Manual CLI Demonstration

Using a temporary repository root or test fixture, demonstrate:

1. request creation;
2. request listing;
3. assessment creation;
4. request status transition;
5. workforce status output;
6. event artifact creation when escalation criteria are met;
7. explicit non-execution and non-authority flags.

Do not populate production runtime data with fictional test records unless the package explicitly cleans them up before completion.

## Acceptance Criteria

WP-4000 is complete only when:

1. Helen workforce commands are available through the main Estate CLI.
2. The standalone CLI remains functional or is cleanly preserved as a compatibility wrapper.
3. Versioned JSON schemas and examples exist and validate.
4. Workforce requests and assessments can emit governed operational events without performing execution or movement.
5. Helen workforce status is visible through an existing Estate status surface.
6. Store idempotency, missing-request, subject-integrity, and malformed-artifact behavior are tested.
7. Grace cannot be marked hired, appointed, or active through this implementation without her missing prerequisites.
8. Existing Helen architectural tests pass.
9. All focused implementation tests pass.
10. Validation evidence is written to:

```text
operations/validation/reports/WP-4000_helen_workforce_runtime_integration.md
```

11. A completion receipt is written to:

```text
collaboration/work_packages/completions/WP-4000_codex_done.json
```

12. The receipt truthfully records commands run, tests passed/failed, files changed, known limitations, and whether any live provider or operational execution occurred.

## Completion Receipt Required Fields

The completion receipt must contain at least:

- `work_package_id`
- `status`
- `summary`
- `files_changed`
- `validation_commands`
- `validation_results`
- `known_limitations`
- `live_provider_called`
- `provider_execution_performed`
- `operational_queue_control_performed`
- `constitutional_authority_granted`
- `grace_appointed_or_activated`
- `completed_at`

Expected values for the authority flags are all `false`.

## Implementation Principle

Build the smallest complete implementation that makes Helen's workforce artifacts first-class Estate runtime records.

Strengthen existing systems. Do not create new institutions when an existing runtime, CLI, schema, event, or status surface can absorb the responsibility.
