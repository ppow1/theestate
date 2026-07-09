# WP-0224 - Resident Standup Sprint and Qmaster Return Gate

Status: Proposed
Priority: Critical
Owner: Office of Character Architecture
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Steward, Alfred, Helen, Office of the Steward, Qmaster workstream
Classification: Estate Internal
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This package is an operational sprint package. It must move the Estate from resident foundation work toward usable resident capability quickly, without turning resident architecture into an all-consuming branch that blocks return to Qmaster.
```

Local runtime required:

```text
partially
```

Local runtime requirement details:

```text
Repository implementation and deterministic tests should complete through Codex Cloud/Web. Steward local runtime may be needed later for TextGen/Ollama smoke testing, but this package must not depend on live model calls for completion.
```

Capacity note:

```text
Bias toward an 80/20 working implementation. Do not spend the package polishing abstractions that do not materially help stand up Alfred, stand up Helen, or return focus to Qmaster.
```

## Codex Command

```text
Read this work package and do exactly what it says.
```

## Mission

Stand up the minimum useful resident layer needed to return the Steward to Qmaster work.

The Estate has validated Alfred locally and implemented the first standalone runtime foundation in WP-0223. That work must now become useful enough to stop consuming the entire development agenda.

This package has three practical outcomes:

1. Alfred has a runnable standalone MVP loop, not just foundation artifacts.
2. Helen has a minimum viable resident package and export path comparable to Alfred's first operational layer.
3. The Estate records a Qmaster return gate so resident work does not sprawl indefinitely.

## Operating Principle

Use the 80/20 rule.

```text
Get the resident layer useful enough to support Qmaster.
Do not chase perfection before returning to Qmaster.
Correct the remaining 20% while operating.
```

This package must think operationally, not academically.

## Background

The Steward's current strategic priority is not endless resident architecture expansion.

The Steward needs:

- Alfred stood up;
- Helen stood up;
- enough resident runtime capability to support real work;
- a return to Qmaster development.

Character Architecture work is justified because it should help Qmaster and the broader Estate move faster. It must not become a permanent detour.

## Scope

### Required Outcome 1 - Alfred Standalone Runtime MVP

Build on WP-0223 and implement a runnable local MVP loop for Alfred.

Preferred module/entry paths, if consistent with repository conventions:

```text
src/estate/core/alfred_runtime.py
src/estate/cli/main.py
```

The MVP loop must support:

- reading local event files from a governed intake folder;
- classifying events through the WP-0223 schema;
- rendering Alfred briefings at supported verbosity levels;
- writing briefing artifacts to a governed output folder;
- recording a simple runtime/audit log;
- explicitly recording actions Alfred did not take;
- running without live model calls;
- refusing to imply live Estate access unless an event explicitly supplies context.

Suggested local folders:

```text
runtime/alfred/events/inbox
runtime/alfred/events/processed
runtime/alfred/briefings
runtime/alfred/logs
runtime/alfred/state
```

If another runtime folder convention already exists, use it rather than inventing a conflicting structure.

Minimum CLI surface:

```text
python -m estate.cli.main alfred-runtime run-once --sample --verbosity mid --json
python -m estate.cli.main alfred-runtime run-once --inbox runtime/alfred/events/inbox --verbosity mid --json
```

If the existing CLI pattern differs, use the existing pattern while preserving equivalent capability.

### Required Outcome 2 - Helen Minimum Viable Resident Package

Create a minimum viable Helen resident package sufficient for later local export and testing.

Do not overbuild Helen.

Helen must have enough durable identity to be stood up after Alfred, including:

- resident profile;
- role summary;
- reporting/authority boundaries;
- office routing rules;
- protected-source boundaries;
- no impersonation rules;
- connector honesty rules;
- initial validation prompts;
- platform export placeholder or first export if the export pattern is already clear.

Preferred paths, if consistent with Alfred's structure:

```text
docs/residents/helen/Helen_Resident_Profile_v0_1.md
docs/residents/helen/Helen_Resident_Validation_v0_1.md
docs/residents/helen/platform-exports/textgen-4_9-helen-v0_1.yaml
```

If the repository has a canonical resident package pattern from Alfred, follow that pattern rather than inventing a new one.

Helen must not be derived from or inspect private local characters.

### Required Outcome 3 - Qmaster Return Gate

Create a short planning artifact that defines when resident work pauses and Qmaster resumes.

Preferred path:

```text
docs/character-architecture/Qmaster_Return_Gate_After_Resident_Standup.md
```

This document must define:

- why resident work was undertaken;
- what is required before returning to Qmaster;
- what is explicitly not required before returning to Qmaster;
- the minimum acceptance line for Alfred;
- the minimum acceptance line for Helen;
- the next Qmaster handoff condition.

Required principle:

```text
Resident work exists to support Estate execution and Qmaster progress. It must not become an indefinite blocker to Qmaster.
```

### Required Outcome 4 - Tests

Add deterministic tests for the new functionality.

Likely test files:

```text
tests/test_alfred_runtime_mvp.py
tests/character_architecture/test_helen_resident_package.py
```

Tests must verify:

- Alfred run-once processes a sample event;
- Alfred writes a briefing artifact;
- Alfred writes or updates a runtime log;
- Alfred does not execute the underlying action;
- verbosity affects presentation depth;
- Helen resident artifacts exist;
- Helen boundaries are present;
- Helen export does not reference protected/private local characters;
- Qmaster return gate exists and contains the required principle.

### Required Outcome 5 - Validation Recipe

Add a WP-0224 validation recipe if consistent with current validation registry conventions.

Expected command:

```powershell
CLS
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"
python -m estate.cli.main validate-work-package --id WP-0224 --json
```

### Required Outcome 6 - Completion Receipt

Create:

```text
collaboration/work_packages/completions/WP-0224_codex_cloud_web_done.json
```

The receipt must include:

- work_package_id;
- provider;
- files changed;
- tests run;
- validation commands run;
- whether live model calls were avoided;
- Alfred MVP behavior summary;
- Helen package summary;
- Qmaster return gate summary;
- known limitations;
- recommended next action.

## Out Of Scope

This package must not:

- build a full production daemon/service manager;
- implement uncontrolled autonomous actions;
- approve, merge, validate, spend, delete, or modify governance on Alfred's behalf;
- build a full Helen runtime;
- create additional residents beyond Helen;
- inspect private local characters;
- require live TextGen, Ollama, Open WebUI, or SillyTavern calls;
- redesign Estate governance;
- block Qmaster return on perfect resident completeness.

## Acceptance Criteria

Accept this package only if:

- Alfred can run a deterministic local run-once MVP loop;
- Alfred can produce briefing artifacts from event input;
- Alfred records what happened without executing unauthorized actions;
- Helen has a minimum viable resident package following Alfred's pattern;
- Qmaster return gate exists;
- tests pass;
- WP-0224 validation passes;
- scope remains operational and 80/20.

## Steward Intent

The Steward needs Alfred and Helen stood up so work can return to Qmaster.

This package must preserve momentum.

Do not turn resident architecture into an all-consuming project.

## Expected Next Step After Completion

After WP-0224, the next action should normally be one of:

```text
Return to Qmaster work with Alfred/Helen available as support residents.
```

or, only if absolutely required:

```text
Create one narrowly scoped fix package for a blocking defect found in Alfred or Helen standup.
```

Do not continue resident expansion by default.
