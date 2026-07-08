# Codex Work Package Template v1

Status: Template
Owner: Chief Architect / Steward
Classification: Estate Internal
Purpose: Standard template for implementation packages submitted to Codex Cloud/Web, Codex CLI, or equivalent implementation providers.

## Template Use

Copy this template when creating implementation work packages.

Every implementation package must define:

- implementation objective
- scope and non-scope boundaries
- expected artifacts
- deterministic validation commands
- local validation artifacts
- local GPU reasoning review expectations
- CLI escalation conditions
- completion receipt requirements
- promotion criteria

## Package Header

```text
# WP-XXXX - <Package Title>

Status: Proposed
Priority: <Low | Normal | High | Critical>
Owner: <Chief Architect / Steward / Office>
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: <Office / subsystem / resident / worker>
Classification: <Public | Estate Internal | Sensitive | Private>
Created: YYYY-MM-DD
```

## Provider Assignment Guidance

Recommended implementation provider:

```text
<codex_cloud_web | codex_cli | chatgpt_planning | local_ollama_gpu | deterministic_local_tooling | human_review>
```

Provider rationale:

```text
<Explain why this package should use the recommended provider.>
```

Local runtime required:

```text
<true | false>
```

Local runtime requirement details:

```text
<Fill this in when implementation needs the local Estate drive, local services, local GPU, Windows path behavior, or PowerShell.>
```

Capacity note:

```text
<Describe whether this package should avoid premium CLI capacity, prefer Cloud/Web, or use local GPU/decomposition first.>
```

## Codex Command

```text
Read this work package and do exactly what it says.

Do not exceed the stated scope.

Do not create new offices, registries, providers, event systems, or command surfaces unless explicitly required.

Do not perform live provider calls unless explicitly required.

Do not require live cloud, GPU, or network access in tests unless explicitly approved.

Write deterministic tests and validation evidence so local validation can confirm the result.
```

## Mission

```text
<One or two paragraphs describing the desired implementation outcome.>
```

## Background

```text
<Brief context. Include prior packages or existing subsystems this package must respect.>
```

## Required Reading

Before implementation, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
<package-specific files>
```

If any file is missing locally, record it in the implementation report and continue with available canonical files.

## Scope

This package must implement:

1. `<required capability>`
2. `<required capability>`
3. `<required capability>`

## Out Of Scope

This package must not:

- `<explicit non-scope item>`
- `<explicit non-scope item>`
- `<explicit non-scope item>`

## Architectural Boundaries

This package must preserve the following boundaries:

```text
Planning may propose.
Routing may recommend.
Traffic Controller / Operations Manager decides movement.
Future mechanical coordination layers apply approved movement rules.
Dispatch queues hold candidate work.
Execution provider adapters perform provider handoff.
Audit and Validation produce evidence.
Chief Architect / Steward accepts institutional truth.
```

Package-specific boundary notes:

```text
<Describe any authority, security, privacy, or subsystem boundaries.>
```

## Expected Artifacts

Create or update only paths justified by the existing codebase.

Expected implementation artifacts:

```text
src/...
tests/...
docs/integration/...
```

Optional integration touchpoints, if clean and low-risk:

```text
src/estate/cli/main.py
src/estate/core/steward_command_center.py
src/estate/core/operator_activity_stream.py
src/estate/core/work_package_validation.py
```

## Runtime Artifacts

If runtime artifacts are required, use local runtime paths such as:

```text
runtime/<subsystem>/current.json
runtime/<subsystem>/events.jsonl
runtime/<subsystem>/report.md
```

Do not commit live runtime outputs unless the package explicitly requires an evidence artifact.

## Test Requirements

Tests must cover:

- `<behavior>`
- `<behavior>`
- `<boundary condition>`
- `<failure or blocked condition>`
- no unauthorized live provider/network/GPU calls

## Validation Rings

Every implementation package must specify which validation rings apply.

### Ring 0 - Static / Structural Validation

Purpose: prove required files, schemas, imports, and declared artifacts exist.

Required checks:

```powershell
<PowerShell file existence checks>
<JSON/schema/import checks>
```

### Ring 1 - Deterministic Test Validation

Purpose: prove implementation behavior with deterministic commands.

Required commands:

```powershell
pytest -q <package-specific tests>
python -m estate.cli.main <package-specific command> --json
python -m estate.cli.main validate-work-package --id WP-XXXX --json
```

Expected evidence:

```text
runtime/validation/work_packages/WP-XXXX_validation.json
operations/validation/reports/WP-XXXX_validation.md
collaboration/work_packages/completions/WP-XXXX_codex_done.json
```

### Ring 2 - Local GPU Reasoning Review

Purpose: use the local RTX 4090 / Ollama validation reviewer to reason over deterministic evidence.

The local reasoning reviewer should inspect:

- this work package
- changed files
- deterministic test output
- validation artifact JSON/Markdown
- completion receipt
- expected runtime artifacts
- Office visibility artifacts, if applicable
- boundary and scope notes

Reviewer questions:

```text
Did the implementation satisfy the package mission?
Did deterministic validation pass?
Did the completion receipt cover files changed, tests run, limitations, and skipped live calls?
Did the work stay in scope?
Were any duplicate registries, event systems, command surfaces, or offices introduced?
Are boundary, privacy, and classification notes respected?
Is the package ready for Chief Architect review, blocked, failed, or escalation-worthy?
```

Expected commands, when the reviewer exists:

```powershell
python -m estate.cli.main local-gpu-validation-review --work-package WP-XXXX --json
python -m estate.cli.main local-gpu-validation-review-report --work-package WP-XXXX
```

Expected evidence:

```text
runtime/validation/reviews/WP-XXXX_review.json
runtime/validation/reviews/WP-XXXX_review.md
```

### Ring 3 - CLI Escalation Validation

Purpose: use Codex CLI, ChatGPT CLI, or another local command-line reasoning provider only when local deterministic and GPU review are insufficient.

Use Ring 3 only when:

- local GPU review cannot resolve the issue
- the failure spans many packages or subsystems
- local runtime context plus stronger reasoning is required
- there is a complex architectural or boundary conflict
- repair guidance is needed but not yet authorized

Ring 3 validator rules:

```text
Prefer read-only validation.
Write validation artifacts only.
Do not repair implementation code unless explicitly assigned.
Do not become the default implementation worker.
```

### Ring 4 - Institutional Acceptance

Purpose: Chief Architect / Steward acceptance of institutional truth.

Acceptance reviewer must confirm:

- validation evidence exists
- local review recommendation is coherent
- unresolved concerns are documented
- promotion or repair decision is explicit

## Completion Receipt Requirements

If implemented by Codex or another provider, create:

```text
collaboration/work_packages/completions/WP-XXXX_<provider>_done.json
```

The receipt must include:

- work_package_id
- provider
- files changed
- tests run
- validation commands run
- runtime artifacts generated
- docs updated
- Office integration status
- skipped live-provider calls
- known limitations
- follow-up recommendations

## Promotion Criteria

This package is ready for promotion when:

- Ring 0 passes
- Ring 1 passes
- Ring 2 produces ready_for_chief_architect_review or equivalent
- Ring 3 is either not required or completed
- completion receipt is present and complete
- no blocking boundary or classification issue remains
- Chief Architect / Steward acceptance is recorded

## Completion Signal

If implemented by Codex, create the completion receipt and include validation ring evidence paths.
