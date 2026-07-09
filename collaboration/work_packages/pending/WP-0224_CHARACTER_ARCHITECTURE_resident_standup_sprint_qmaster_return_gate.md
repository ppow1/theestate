# WP-0224 - Resident Standup Sprint Aligned to Background Operations Runtime

Status: Proposed
Priority: Critical
Owner: Office of Character Architecture
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Steward, Alfred, Helen, Office of the Steward, CueMastery workstream, Background Operations Runtime
Classification: Estate Internal
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This package is an operational resident standup sprint. It must make Alfred and Helen useful without creating a competing event runtime. WP-0617 is the Estate-wide Background Operations Event Runtime. WP-0224 must align residents to that architecture and avoid turning Character Architecture into an all-consuming branch that blocks CueMastery.
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
Bias toward an 80/20 working implementation. Do not polish abstractions that do not materially help stand up Alfred, stand up Helen, integrate resident readiness with WP-0617, or return focus to CueMastery.
```

## Codex Command

```text
Read this work package and do exactly what it says.
```

## Mission

Stand up the minimum useful resident layer needed to return the Steward to CueMastery work, while aligning resident operation with the Estate-wide Background Operations Event Runtime defined by WP-0617.

WP-0224 must not implement a parallel event system.

WP-0617 owns the Estate-wide background operations substrate:

```text
an event occurs
  -> a standing watch or rule notices it
  -> the background operations runtime produces the next governed artifact
  -> participants receive work/update/review requests through proper channels
  -> the Office shows what is happening and what requires the Steward
```

WP-0224 owns resident standup and resident-facing integration points:

```text
Alfred and Helen resident artifacts
  -> resident readiness and validation prompts
  -> resident-specific request/briefing patterns
  -> resident-sensitive boundary rules
  -> CueMastery return gate
  -> hooks/fixtures/examples compatible with WP-0617 background operations requests
```

This package has four practical outcomes:

1. Alfred is stood up as the first operational resident with resident-facing background-operations integration points.
2. Helen receives a minimum viable resident package and export path comparable to Alfred's first operational layer.
3. Resident task visibility is expressed through WP-0617-compatible events/requests/status concepts, not a competing runtime.
4. The Estate records a CueMastery return gate so resident work does not sprawl indefinitely.

## Steward Intent

The Steward needs Alfred and Helen stood up so work can return to CueMastery.

Resident architecture is important, but it must not become the entire project.

Alfred is needed because the Steward cannot stay inside resident-development conversations indefinitely. Alfred must become able to keep an eye on resident tasks and Estate task flow through the background operations layer while the Steward returns to CueMastery or other primary work.

This package must therefore prepare Alfred and Helen for event-driven operations without duplicating WP-0617.

## Operating Principle

Use the 80/20 rule.

```text
Get the resident layer useful enough to support CueMastery.
Do not chase perfection before returning to CueMastery.
Correct the remaining 20% while operating.
```

This package must think operationally, not academically.

## Relationship to WP-0617

WP-0617 is the controlling architecture for background event-driven operations.

WP-0224 must:

- reference WP-0617 as the background operations substrate;
- avoid creating a separate resident event feed, resident watch daemon, or resident dispatch queue;
- express resident task visibility using WP-0617-compatible event/request/status patterns;
- define how Alfred and Helen should receive or generate governed background operation requests;
- preserve Character Architecture boundaries for resident identity, protected sources, continuity, and no-impersonation rules;
- make clear that TextGen/Open WebUI/SillyTavern/Ollama are resident interface/model adapters, not the event runtime.

WP-0224 may include deterministic fixtures or helper functions that prepare WP-0617-compatible resident-related events or requests, but it must not own the Estate-wide evaluator loop.

## Background

The Steward's current strategic priority is not endless resident architecture expansion.

The Steward needs:

- Alfred stood up;
- Helen stood up;
- resident readiness visible to background operations;
- enough resident capability to support real work;
- a return to CueMastery development.

Character Architecture work is justified because it should help CueMastery and the broader Estate move faster. It must not become a permanent detour.

## Scope

### Required Outcome 1 - Alfred Operational Resident Standup

Build on WP-0219 through WP-0223 and make Alfred's resident standup usable in the larger Estate architecture.

Required work:

- document Alfred's operational standup status;
- define Alfred's role in relation to WP-0617 background operation requests;
- define what kinds of background operation requests Alfred may receive, summarize, route, or brief;
- define what Alfred must never execute directly;
- define how Alfred reports lack of live access unless supplied by event/request artifacts;
- define how Alfred uses verbosity when producing briefings from background operation requests;
- update or add deterministic resident validation prompts for event-driven/background-operation scenarios.

Preferred artifact path:

```text
docs/residents/alfred/runtime/Alfred_Background_Operations_Integration_v0_1.md
```

This document must state:

```text
WP-0617 owns the background operations runtime. Alfred consumes, prepares, or summarizes governed operation requests through that substrate. Alfred does not own a competing event loop.
```

### Required Outcome 2 - Alfred Background Operation Fixtures or Helpers

Add minimal deterministic fixtures or helper functions, if consistent with repository conventions, that create resident-related operation request examples compatible with the WP-0617 model.

Examples:

```text
resident_standup_status_request
resident_validation_review_request
resident_identity_boundary_review_request
cuemastery_return_gate_status_request
```

These may live in documentation, tests, or lightweight code depending on existing repository structure.

If code is added, it should be small and deterministic. It must not call live models or providers.

Acceptable implementation examples:

- a helper that builds a WP-0617-compatible request payload for Alfred review;
- a fixture file under tests/fixtures;
- documentation examples consumed by tests;
- a small CLI/sample command only if it fits existing CLI conventions.

Do not create:

- a separate resident event runtime;
- a resident-specific watch daemon;
- a separate resident dispatch queue;
- a second background operations status system.

### Required Outcome 3 - Helen Minimum Viable Resident Package

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
- background-operations request boundary rules;
- initial validation prompts;
- platform export placeholder or first export if the export pattern is already clear.

Preferred paths, if consistent with Alfred's structure:

```text
docs/residents/helen/Helen_Resident_Profile_v0_1.md
docs/residents/helen/Helen_Resident_Validation_v0_1.md
docs/residents/helen/platform-exports/textgen-4_9-helen-v0_1.yaml
docs/residents/helen/runtime/Helen_Background_Operations_Integration_v0_1.md
```

If the repository has a canonical resident package pattern from Alfred, follow that pattern rather than inventing a new one.

Helen must not be derived from or inspect private local characters.

### Required Outcome 4 - Resident / Background Operations Boundary Document

Create or update a Character Architecture document that defines how residents relate to WP-0617.

Preferred path:

```text
docs/character-architecture/Resident_Background_Operations_Boundary_v0_1.md
```

This document must define:

- WP-0617 owns event watches, background operation events, background operation requests, runtime status, and Office-visible background operations reports;
- Character Architecture owns resident identity, resident validation, resident exports, resident-sensitive boundaries, and resident-specific prompt/briefing behavior;
- residents may consume or prepare governed operation requests;
- residents do not directly execute providers, approve institutional truth, bypass Traffic Controller, or replace validation;
- resident/persona/worker/provider/office roles must remain distinct;
- character-sensitive or protected-source events require Ingrid/Steward or appropriate Chief Architect review.

### Required Outcome 5 - CueMastery Return Gate

Create a short planning artifact that defines when resident work pauses and CueMastery resumes.

Preferred path:

```text
docs/character-architecture/CueMastery_Return_Gate_After_Resident_Standup.md
```

This document must define:

- why resident work was undertaken;
- what is required before returning to CueMastery;
- what is explicitly not required before returning to CueMastery;
- the minimum acceptance line for Alfred;
- the minimum acceptance line for Helen;
- the next CueMastery handoff condition;
- how Alfred is expected to keep an eye on resident/CueMastery transition tasks through WP-0617 background operations rather than through a separate resident runtime.

Required principle:

```text
Resident work exists to support Estate execution and CueMastery progress. It must not become an indefinite blocker to CueMastery.
```

### Required Outcome 6 - Tests

Add deterministic tests for the new functionality.

Likely test files:

```text
tests/character_architecture/test_resident_background_operations_boundary.py
tests/character_architecture/test_helen_resident_package.py
```

Tests must verify:

- Alfred background-operations integration artifact exists;
- Alfred integration explicitly names WP-0617 as the background runtime owner;
- Alfred integration does not define a competing resident event loop;
- resident/WP-0617 boundary artifact exists;
- boundary artifact preserves role separation among residents, workers, providers, personas, offices, and background operations;
- resident operation examples are compatible with WP-0617 request concepts where practical;
- Helen resident artifacts exist;
- Helen boundaries are present;
- Helen background-operations boundary is present;
- Helen export does not reference protected/private local characters;
- CueMastery return gate exists and contains the required principle.

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
- Alfred standup summary;
- Alfred/WP-0617 integration summary;
- Helen package summary;
- Helen/WP-0617 integration summary;
- CueMastery return gate summary;
- known limitations;
- recommended next action.

## Out Of Scope

This package must not:

- build a full production daemon/service manager;
- implement the WP-0617 background operations runtime;
- create a separate resident event feed, watch daemon, dispatch queue, or status system;
- implement uncontrolled autonomous actions;
- approve, merge, validate, spend, delete, or modify governance on Alfred's or Helen's behalf;
- build a full Helen runtime;
- create additional residents beyond Helen;
- inspect private local characters;
- require live TextGen, Ollama, Open WebUI, or SillyTavern calls;
- redesign Estate governance;
- block CueMastery return on perfect resident completeness.

## Acceptance Criteria

Accept this package only if:

- Alfred is documented as stood up enough to participate in WP-0617-style background operations;
- Alfred's role does not duplicate WP-0617 runtime responsibilities;
- resident/background-operations boundary is explicit;
- Helen has a minimum viable resident package following Alfred's pattern;
- Helen includes background-operations boundary language;
- CueMastery return gate exists;
- tests pass;
- WP-0224 validation passes;
- scope remains operational and 80/20.

## Expected Next Step After Completion

After WP-0224, the next action should normally be one of:

```text
Run or implement WP-0617 so background operations can carry Alfred/Helen resident task awareness while the Steward returns to CueMastery.
```

or:

```text
Return to CueMastery work with Alfred/Helen available as support residents and WP-0617 identified as the event-driven substrate.
```

Only create a narrowly scoped fix package if a blocking defect prevents Alfred/Helen standup or WP-0617 alignment.

Do not continue resident expansion by default.
