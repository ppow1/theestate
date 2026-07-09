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
This package is an operational sprint package. It must move the Estate from resident foundation work toward useful resident capability quickly, without turning resident architecture into an all-consuming branch that blocks return to Qmaster.
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
Bias toward an 80/20 working implementation. Do not spend the package polishing abstractions that do not materially help stand up Alfred, stand up Helen, keep resident tasks running, or return focus to Qmaster.
```

## Codex Command

```text
Read this work package and do exactly what it says.
```

## Mission

Stand up the minimum useful resident layer needed to return the Steward to Qmaster work.

The Estate has validated Alfred locally and implemented the first standalone runtime foundation in WP-0223. That work must now become useful enough to stop consuming the entire development agenda.

This package has four practical outcomes:

1. Alfred has a runnable standalone MVP loop, not just foundation artifacts.
2. Alfred begins moving from turn-driven chat toward event-driven operation.
3. Helen has a minimum viable resident package and export path comparable to Alfred's first operational layer.
4. The Estate records a Qmaster return gate so resident work does not sprawl indefinitely.

## Steward Intent

The Steward needs Alfred and Helen stood up so work can return to Qmaster.

Resident architecture is important, but it must not become the entire project.

Alfred is needed specifically because the Steward cannot stay inside resident-development conversations indefinitely. Alfred must become capable of keeping an eye on resident tasks and Estate task flow while the Steward moves back to Qmaster or other primary work.

This package must therefore prioritize useful event-driven operation over another purely turn-driven or document-only resident increment.

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
- Alfred capable of non-turn-driven event awareness at MVP level;
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
runtime/alfred/tasks
```

If another runtime folder convention already exists, use it rather than inventing a conflicting structure.

Minimum CLI surface:

```text
python -m estate.cli.main alfred-runtime run-once --sample --verbosity mid --json
python -m estate.cli.main alfred-runtime run-once --inbox runtime/alfred/events/inbox --verbosity mid --json
```

If the existing CLI pattern differs, use the existing pattern while preserving equivalent capability.

### Required Outcome 2 - Non-Turn Event-Driven Operation MVP

Alfred must not remain only a turn-driven chat resident.

Implement a minimal event-driven operating mode that can be run locally without live model calls.

Minimum acceptable capability:

```text
Alfred can be invoked repeatedly or in a lightweight watch loop.
Alfred can notice new local event files without the Steward writing a chat prompt for each event.
Alfred can produce briefing artifacts and logs from those events.
Alfred can record task/watch status so the Steward can later ask what happened.
```

Preferred CLI surface, if consistent with the repository:

```text
python -m estate.cli.main alfred-runtime watch --inbox runtime/alfred/events/inbox --interval 10 --max-cycles 3 --verbosity mid --json
python -m estate.cli.main alfred-runtime status --json
```

If a persistent watch command is too much for this package, implement a deterministic bounded loop command instead. It must still demonstrate non-turn-driven behavior by processing pending event files without chat interaction.

The watch/status implementation must be conservative:

- no uncontrolled autonomous actions;
- no background daemon/service manager requirement;
- no deleting user files;
- no approving, merging, validating, spending, or modifying governance;
- no live model requirement;
- no claim that Alfred has live access beyond the folders/events supplied to the runtime.

### Required Outcome 3 - Resident Task Tracking for Steward Return to Qmaster

Implement or document a minimal resident task tracking surface so Alfred can keep resident work visible while the Steward returns to Qmaster.

Minimum capability:

- record known resident-runtime tasks or watched task entries;
- mark tasks as observed, briefed, blocked, or needs_steward_attention;
- surface a status summary through CLI or artifact output;
- include Qmaster-related task routing as a first-class use case.

Suggested event/task examples:

```text
wp_0224_codex_submitted
wp_0224_pr_opened
wp_0224_validation_failed
wp_0224_validation_passed
helen_package_missing_export
qmaster_return_gate_ready
qmaster_work_resumed
```

This does not need to be a full project management system. It only needs to give Alfred a place to keep an eye on active resident/Qmaster transition items.

### Required Outcome 4 - Helen Minimum Viable Resident Package

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

### Required Outcome 5 - Qmaster Return Gate

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
- the next Qmaster handoff condition;
- how Alfred is expected to keep an eye on resident/Qmaster transition tasks while the Steward returns to Qmaster.

Required principle:

```text
Resident work exists to support Estate execution and Qmaster progress. It must not become an indefinite blocker to Qmaster.
```

### Required Outcome 6 - Tests

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
- Alfred can process pending event files without a chat turn;
- Alfred watch/bounded-loop mode does not execute unauthorized actions;
- Alfred status or task tracking can report active/observed items;
- verbosity affects presentation depth;
- Helen resident artifacts exist;
- Helen boundaries are present;
- Helen export does not reference protected/private local characters;
- Qmaster return gate exists and contains the required principle.

### Required Outcome 7 - Validation Recipe

Add a WP-0224 validation recipe if consistent with current validation registry conventions.

Expected command:

```powershell
CLS
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"
python -m estate.cli.main validate-work-package --id WP-0224 --json
```

### Required Outcome 8 - Completion Receipt

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
- Alfred non-turn/event-driven behavior summary;
- resident task tracking summary;
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
- Alfred can process event files without the Steward issuing a chat prompt for each event;
- Alfred can produce briefing artifacts from event input;
- Alfred records what happened without executing unauthorized actions;
- Alfred has a minimal status/task tracking surface for resident/Qmaster transition work;
- Helen has a minimum viable resident package following Alfred's pattern;
- Qmaster return gate exists;
- tests pass;
- WP-0224 validation passes;
- scope remains operational and 80/20.

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
