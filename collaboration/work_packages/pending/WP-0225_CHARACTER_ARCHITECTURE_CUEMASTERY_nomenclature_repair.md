# WP-0225 - CueMastery and IONOGE Nomenclature Repair

Status: Proposed
Priority: Critical
Owner: Office of Character Architecture
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Steward, Alfred, Helen, Character Architecture, CueMastery workstream, IONOGE workstreams
Classification: Estate Internal
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is a narrow corrective repair package. Recent resident standup artifacts incorrectly used Qmaster/qmaster for CueMastery. The Steward also identified IONOGE as a dictation-sensitive canonical term. This package must repair the current CueMastery mistake and add explicit nomenclature guardrails without expanding resident architecture scope.
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
This is a correction and guardrail package, not a new design effort. Repair nomenclature, add dictation-sensitive validation references, update tests/validation references, and stop.
```

## Codex Command

```text
Read this work package and do exactly what it says.
```

## Mission

Correct the resident standup and Character Architecture artifacts so the project/workstream is named **CueMastery**, not Qmaster/qmaster or dictation-derived variants.

Also add an explicit canonical nomenclature guard for **IONOGE**, which is pronounced:

```text
eye-oh-no-gee
```

The prior CueMastery mistake escaped review in WP-0224. This package repairs that mistake and adds validation so known dictation failures do not continue to spread.

## Correct Names

### CueMastery

The correct name is:

```text
CueMastery
```

Use CueMastery in prose, headings, titles, workstream names, and user-facing documents.

Use lowercase `cuemastery` only where a lowercase machine identifier is appropriate, such as a JSON fixture field, snake_case identifier, or filename convention.

### IONOGE

The correct name is:

```text
IONOGE
```

Pronunciation aid:

```text
eye-oh-no-gee
```

Use IONOGE in prose, headings, titles, workstream names, and user-facing documents.

Use lowercase `ionoge` only where a lowercase machine identifier is appropriate, such as repository names, hostnames, JSON fields, snake_case identifiers, filenames, or URLs.

## Dictation / Mishearing Risk

The Steward often uses dictation. CueMastery and IONOGE are both prone to speech-recognition errors.

CueMastery is frequently misconstrued as variants involving the letter Q, queue/line terminology, or separated words.

IONOGE is pronounced eye-oh-no-gee and dictation frequently fails to capture it correctly.

Do not use these CueMastery variants:

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

Do not use these IONOGE variants in active artifacts unless they are part of this repair package's forbidden-term list or a documented URL/hostname/repository identifier that is already canonical lowercase:

```text
Ionoge
ion oge
ion-oge
Iono Gee
IonoGee
Ionogy
Eyeonoge
Eye Oh No Gee
Eye-Oh-No-Gee
```

Historical compatibility notes should be avoided unless necessary to explain the repair.

## Scope

### Required Outcome 1 - Rename / Replace Incorrect CueMastery Nomenclature

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

### Required Outcome 2 - Rename Affected CueMastery Artifact Paths Where Practical

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

### Required Outcome 3 - Add Canonical Nomenclature Guard Artifact

Create or update a small canonical terminology guard artifact for dictation-sensitive names.

Preferred path:

```text
docs/character-architecture/Canonical_Nomenclature_Guard_v0_1.md
```

It must include at least:

```text
CueMastery
IONOGE
```

For each term, include:

- canonical spelling;
- pronunciation aid if useful;
- allowed lowercase machine identifier;
- forbidden dictation/misheard variants;
- note that canonical terminology must be used in resident and Character Architecture artifacts.

Do not turn this into a broad registry project. Keep it small and useful.

### Required Outcome 4 - Validation Guard

Add deterministic validation that fails if the incorrect CueMastery names remain in active Character Architecture / resident standup artifacts.

At minimum, tests must scan the relevant WP-0224/WP-0225 files and assert that these strings do not appear outside the WP-0225 repair package's own forbidden-term list or the canonical nomenclature guard's forbidden-term examples:

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

Also add validation that the canonical terminology guard contains IONOGE with pronunciation `eye-oh-no-gee` and allowed lowercase machine identifier `ionoge`.

### Required Outcome 5 - Completion Receipt

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
- canonical terms added;
- tests run;
- validation commands run;
- known limitations;
- confirmation that live calls were avoided.

### Required Outcome 6 - Validation Recipe

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
- canonical nomenclature guard exists;
- CueMastery and IONOGE canonical entries are present;
- deterministic tests pass;
- completion receipt exists;
- forbidden CueMastery nomenclature does not remain in active affected files.

## Out Of Scope

This package must not:

- change the purpose of CueMastery;
- change the purpose of IONOGE;
- redesign the resident standup architecture;
- redesign WP-0617;
- create a broad terminology registry beyond this minimal guard;
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
- a canonical nomenclature guard records CueMastery and IONOGE;
- IONOGE pronunciation is recorded as eye-oh-no-gee;
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
