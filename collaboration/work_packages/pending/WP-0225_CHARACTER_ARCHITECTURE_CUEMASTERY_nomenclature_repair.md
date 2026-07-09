# WP-0225 - CueMastery Nomenclature Repair

Status: Proposed
Priority: Critical
Owner: Office of Character Architecture
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Steward, Alfred, Helen, Character Architecture, CueMastery workstream
Classification: Estate Internal
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is a narrow corrective repair package. Recent resident standup artifacts incorrectly used Qmaster/qmaster. The correct project/workstream name is CueMastery. This must be corrected quickly without expanding resident architecture scope.
```

Local runtime required:

```text
false
```

Local runtime requirement details:

```text
This repair should be completed from repository context with deterministic tests and validation. No live model, provider, GPU, TextGen, Ollama, Open WebUI, SillyTavern, browser, network, email, or calendar access is required.
```

Capacity note:

```text
This is a correction, not a new design effort. Repair the nomenclature, update tests/validation references, and stop.
```

## Codex Command

```text
Read this work package and do exactly what it says.
```

## Mission

Correct the resident standup and Character Architecture artifacts so the project/workstream is named **CueMastery**, not Qmaster/qmaster or dictation-derived variants.

The prior name escaped review in WP-0224. This package repairs that mistake and adds validation so the wrong form does not continue to spread.

## Correct Name

The correct name is:

```text
CueMastery
```

Use CueMastery in prose, headings, titles, workstream names, and user-facing documents.

Use lowercase `cuemastery` only where a lowercase machine identifier is appropriate, such as a JSON fixture field, snake_case identifier, or filename convention.

## Dictation / Mishearing Risk

The Steward often uses dictation. CueMastery is frequently misconstrued as variants involving the letter Q, queue/line terminology, or separated words. This package must explicitly guard against those variants.

Do not use:

```text
Qmaster
qmaster
Q Master
Q mastery
Q Mastery
queue mastery
Queue Mastery
QueueMastery
Cue Mastery
CUEMASTERY
```

unless a short historical compatibility note is absolutely required to explain the repair. Prefer no historical note unless needed.

## Scope

### Required Outcome 1 - Rename / Replace Incorrect Nomenclature

Search the repository for incorrect occurrences of:

```text
Qmaster
qmaster
Q Master
Q mastery
Q Mastery
queue mastery
Queue Mastery
QueueMastery
Cue Mastery
CUEMASTERY
```

Replace them with the correct CueMastery form.

Known files likely affected by WP-0224 include:

```text
collaboration/work_packages/pending/WP-0224_CHARACTER_ARCHITECTURE_resident_standup_sprint_qmaster_return_gate.md
docs/character-architecture/Qmaster_Return_Gate_After_Resident_Standup.md
docs/residents/alfred/runtime/Alfred_Background_Operations_Integration_v0_1.md
docs/residents/helen/Helen_Resident_Profile_v0_1.md
docs/residents/helen/runtime/Helen_Background_Operations_Integration_v0_1.md
src/estate/core/work_package_validation.py
collaboration/work_packages/completions/WP-0224_codex_cloud_web_done.json
tests/character_architecture/test_resident_background_operations_boundary.py
tests/fixtures/background_operations/resident_operation_requests_wp0224.json
```

This list may not be complete. Search the repository rather than relying only on the list.

### Required Outcome 2 - Rename Affected Artifact Paths Where Practical

Rename the Qmaster return gate artifact to use CueMastery.

Expected replacement path:

```text
docs/character-architecture/CueMastery_Return_Gate_After_Resident_Standup.md
```

Remove or replace the old path:

```text
docs/character-architecture/Qmaster_Return_Gate_After_Resident_Standup.md
```

Update all references, validation recipes, tests, fixtures, and completion receipts to the new path.

If repository mechanics make deletion awkward, leave a tiny redirect/stub only if necessary, but preferred outcome is that the incorrect filename is gone.

### Required Outcome 3 - Validation Guard

Add deterministic validation that fails if the incorrect names remain in active Character Architecture / resident standup artifacts.

At minimum, tests must scan the relevant WP-0224/WP-0225 files and assert that these strings do not appear:

```text
Qmaster
qmaster
Q Master
Q mastery
Q Mastery
queue mastery
Queue Mastery
QueueMastery
Cue Mastery
CUEMASTERY
```

The test may allow the string list inside the WP-0225 repair package itself only if necessary to define forbidden terms. Prefer implementing the scan so it ignores this repair work package's forbidden-term list rather than allowing future spread.

### Required Outcome 4 - Completion Receipt

Create:

```text
collaboration/work_packages/completions/WP-0225_codex_cloud_web_done.json
```

The receipt must include:

- work_package_id;
- provider;
- files changed;
- terms replaced;
- paths renamed or deleted;
- tests run;
- validation commands run;
- known limitations;
- confirmation that live calls were avoided.

### Required Outcome 5 - Validation Recipe

Add a WP-0225 validation recipe if consistent with current validation registry conventions.

Expected local validation command:

```powershell
CLS
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"
python -m estate.cli.main validate-work-package --id WP-0225 --json
```

The recipe must include:

- required corrected artifacts exist;
- old Qmaster return gate path is absent or an intentional redirect stub;
- deterministic tests pass;
- completion receipt exists;
- forbidden nomenclature does not remain in active affected files.

## Out Of Scope

This package must not:

- change the purpose of CueMastery;
- redesign the resident standup architecture;
- redesign WP-0617;
- add new residents;
- add new event runtimes;
- run live providers;
- alter private/protected source boundaries;
- inspect private local characters;
- expand beyond nomenclature repair and validation guardrails.

## Acceptance Criteria

Accept this package only if:

- active resident/Character Architecture artifacts use CueMastery correctly;
- incorrect Qmaster/qmaster/QueueMastery/CUEMASTERY forms are removed from active affected files;
- the return gate artifact path is corrected or intentionally redirected;
- tests pass;
- WP-0225 validation passes;
- completion receipt exists;
- no unrelated architecture expansion occurs.

## Expected Next Step After Completion

After this repair, return to the prior execution path:

```text
Continue CueMastery work with Alfred/Helen resident support and WP-0617 background operations alignment.
```

Do not continue resident expansion by default.
