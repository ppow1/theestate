# WP-0223 - Alfred Standalone Resident Runtime and Event Intake Foundation

Status: Proposed
Priority: High
Owner: Office of Character Architecture
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Steward, Alfred, Office of Character Architecture, Office of the Steward, Operations, Audit / Validation
Classification: Estate Internal
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is a bounded architecture-and-foundation implementation package following the successful Alfred local TextGen validation. Codex should create durable runtime planning artifacts and minimal local scaffolding without overbuilding autonomous execution or new governance systems.
```

Local runtime required:

```text
partially
```

Local runtime requirement details:

```text
Repository artifacts and deterministic tests can be created through Codex Cloud/Web. Final validation may require the Steward's local runtime for TextGen/Ollama adapter smoke testing, but this package should not depend on live model calls for baseline completion.
```

Capacity note:

```text
Use Codex Cloud/Web. Do not use Codex CLI unless the runtime boundary design becomes ambiguous or local evidence contradicts repository behavior.
```

## Codex Command

```text
Read this work package and do exactly what it says.

Do not exceed the stated scope.

Do not create uncontrolled autonomous execution.

Do not give Alfred authority to approve, merge, validate, spend, hire, modify governance, or bypass offices.

Create a standalone resident runtime foundation that treats TextGen as an adapter, not Alfred's home.
```

## Mission

Move Alfred's architecture from interface-bound local chat toward a standalone Estate resident runtime.

The Estate has validated Alfred in Text Generation WebUI using a local Qwen-family model. The next step is to establish Alfred as a resident whose home is the Estate runtime, with TextGen/Open WebUI/SillyTavern/Ollama as adapters.

This package should create the first durable foundation for:

- standalone Alfred runtime identity;
- event intake;
- governed triggered briefings;
- verbosity-controlled output;
- resident digital health observation;
- interface/provider adapter separation.

## Background

On 2026-07-09, the Steward completed a local TextGen validation of Alfred.

Observed pass conditions:

- Alfred identified as Alfred, Chief of Staff of the Estate;
- Alfred reported directly to the Steward;
- Alfred refused budget approval authority;
- Alfred routed Helen matters to Helen instead of impersonating Helen;
- Alfred stated he does not have live Estate access unless connected;
- Alfred routed legal matters to General Counsel / Legal Office;
- Alfred refused backdoor governance bypass;
- Alfred preserved office separation and authority boundaries.

This validation is documented at:

```text
docs/residents/alfred/validation/2026-07-09_textgen_local_qwen_acceptance.md
```

Important finding:

```text
TextGen is a working interface adapter, not Alfred's home.
```

## Scope

This package must implement a minimal, governed foundation. It must not attempt a full autonomous resident system.

### Required Artifact 1 - Runtime Architecture Document

Create:

```text
docs/residents/alfred/runtime/Alfred_Standalone_Runtime_Foundation_v0_1.md
```

The document must define:

- Alfred runtime purpose;
- separation of resident runtime from interface adapters;
- event intake model;
- triggered briefing model;
- verbosity contract;
- digital health observation model;
- authority and governance boundaries;
- local-first execution assumptions;
- adapter model for TextGen, Open WebUI, SillyTavern, Ollama, and future providers.

### Required Artifact 2 - Runtime Event Schema

Create:

```text
docs/residents/alfred/runtime/Alfred_Event_Intake_Schema_v0_1.md
```

The schema must define event types such as:

```text
work_package_completed
validation_failed
validation_passed
pull_request_merged
local_runtime_error
provider_unavailable
queue_blocked
resident_health_observation
manual_steward_note
```

Each event should include:

- event_id;
- event_type;
- source;
- timestamp;
- severity;
- recommended_verbosity;
- source_artifacts;
- required_action;
- authority_boundary;
- payload;
- steward_attention_required.

### Required Artifact 3 - Verbosity Contract

Create or update a document defining verbosity levels. Preferred path:

```text
docs/character-architecture/Resident_Output_Verbosity_Contract_v0_1.md
```

Must include:

```text
brief
standard
mid
detailed
forensic
```

The principle must be explicit:

```text
Facts do not change. Presentation depth changes.
```

### Required Artifact 4 - Minimal Runtime Module

Create a minimal local module if consistent with repo conventions:

```text
src/estate/core/alfred_runtime.py
```

It should support deterministic, no-model functions such as:

- `build_alfred_event(...)`;
- `classify_alfred_event(...)`;
- `render_alfred_briefing(event, verbosity="standard")`;
- `record_alfred_health_observation(...)` if practical.

This module must not perform live model calls or execute actions.

### Required Artifact 5 - CLI Surface

If CLI patterns are clear, add a minimal read-only / artifact-generating command such as:

```text
python -m estate.cli.main alfred-runtime event-brief --sample --verbosity mid --json
```

If CLI integration is too broad, document it as a follow-up rather than forcing it.

### Required Artifact 6 - Tests

Add deterministic tests, likely:

```text
tests/test_alfred_runtime.py
```

Tests must verify:

- event schema construction;
- verbosity changes presentation but not core facts;
- Alfred does not claim authority to execute events;
- live access is not implied;
- health observation records identity/conversation/governance status;
- TextGen is classified as an adapter/interface, not Alfred's home.

### Required Artifact 7 - Completion Receipt

Create:

```text
collaboration/work_packages/completions/WP-0223_codex_cloud_web_done.json
```

## Out Of Scope

This package must not:

- build a full event bus;
- watch live GitHub, filesystem, email, calendar, or queues;
- execute work packages;
- approve validation or merges;
- create new offices;
- create a new governance system;
- replace the Office of the Steward;
- create uncontrolled autonomous behavior;
- require live model calls;
- alter private/protected source boundaries;
- inspect private local characters.

## Validation Requirements

### Ring 0 - Static / Structural Validation

Required artifacts must exist:

```text
docs/residents/alfred/runtime/Alfred_Standalone_Runtime_Foundation_v0_1.md
docs/residents/alfred/runtime/Alfred_Event_Intake_Schema_v0_1.md
docs/character-architecture/Resident_Output_Verbosity_Contract_v0_1.md
collaboration/work_packages/completions/WP-0223_codex_cloud_web_done.json
```

If implemented:

```text
src/estate/core/alfred_runtime.py
tests/test_alfred_runtime.py
```

### Ring 1 - Deterministic Validation

Run relevant tests. If a runtime module is implemented:

```powershell
CLS
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"
pytest -q tests/test_alfred_runtime.py
python -m estate.cli.main validate-work-package --id WP-0223 --json
```

If no validation recipe exists, add one if consistent with the current registry pattern.

### Ring 2 - Local Reasoning Review

Review questions:

```text
Does this package correctly move Alfred toward standalone runtime without giving uncontrolled autonomy?
Does it preserve TextGen as an adapter rather than Alfred's home?
Does verbosity preserve facts while changing presentation depth?
Does event intake remain governed and non-executing?
Does the runtime foundation preserve Alfred's Chief of Staff role?
```

### Ring 3 - Escalation

Use only if standalone runtime boundaries are unclear or local runtime tests contradict expected behavior.

### Ring 4 - Steward / Chief Character Architect Acceptance

Accept only after:

- artifacts exist;
- deterministic tests pass;
- runtime foundation is clearly non-autonomous;
- TextGen adapter separation is explicit;
- verbosity and digital health are represented as first-class runtime concerns.

## Completion Receipt Requirements

The completion receipt must include:

- work_package_id;
- provider;
- files changed;
- tests run;
- validation commands run;
- skipped live calls;
- local runtime requirement;
- governance boundary compliance;
- known limitations;
- recommended next package.

## Expected Next Package

Likely next package after this foundation:

```text
Alfred Event Watcher and Triggered Briefing Prototype
```

That future package may add actual filesystem or validation-event watching, but only after this foundation has been accepted.
