# WP-0219 - Alfred Resident Package Validation and Platform Export Hardening

Status: Proposed
Priority: High
Owner: Office of Character Architecture
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Steward, Alfred, Office of Character Architecture, Office of the Steward, Helen / AI HR, Audit / Validation
Classification: Estate Internal
Created: 2026-07-08

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This package is primarily repository artifact hardening, structural validation, documentation refinement, and deterministic test creation. It should not consume scarce Codex CLI capacity by default. Codex Cloud/Web is suitable for implementing repository changes and tests. Local deterministic tooling should validate the result. Local RTX 4090 / Ollama should perform Ring 2 reasoning review after deterministic validation.
```

Local runtime required:

```text
false
```

Local runtime requirement details:

```text
No live local Estate services, GPU, network, or command-center runtime are required for implementation. Local validation should run from the repository checkout. The package may use Python and pytest if already available in the normal Estate development environment.
```

Capacity note:

```text
Do not use Codex CLI unless Ring 0, Ring 1, or Ring 2 reveals a complex cross-package conflict, local runtime failure, or architectural boundary ambiguity. Prefer Codex Cloud/Web for implementation and local deterministic tooling plus local GPU reasoning review for validation.
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

Harden Alfred's v0.1 resident package so it can serve as the first reference implementation for Estate resident identity artifacts and local character-platform exports.

The desired outcome is a structurally validated, reviewable Alfred resident package containing a public charter, canonical character card, relationship map, digital health profile, command-center metadata, and platform exports for SillyTavern, Open WebUI, and text-generation-webui.

## Background

The Office of Character Architecture has created initial Alfred resident artifacts under:

```text
docs/residents/alfred/
```

Alfred is the Estate's Chief of Staff. He is a single-source Estate resident, male presentation, responsible for protecting the Steward's attention, preparing briefings, tracking priorities, coordinating resident handoffs, and routing work through proper offices without absorbing specialist responsibilities.

This package should convert the initial draft artifacts into a stronger, testable resident package without changing Alfred's approved identity direction.

## Required Reading

Before implementation, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
docs/governance/workers/templates/Codex_Work_Package_Template_v1.md
docs/governance/offices/Office_of_Character_Architecture.md
docs/character-architecture/Resident_Identity_Standard_v0_1.md
docs/character-architecture/Resident_Source_Classification_v0_1.md
docs/character-architecture/Character_Card_Template_v0_1.md
docs/character-architecture/Resident_Charter_Template_v0_1.md
docs/character-architecture/Resident_Relationship_Standard_v0_1.md
docs/character-architecture/Personnel_Digital_Health_Standard_v0_1.md
docs/residents/alfred/public-charter.md
docs/residents/alfred/character-card.yaml
docs/residents/alfred/relationship-map.md
docs/residents/alfred/digital-health-profile.md
docs/residents/alfred/command-center-metadata.yaml
docs/residents/alfred/platform-exports/sillytavern-alfred-v0_1.json
docs/residents/alfred/platform-exports/open-webui-alfred-v0_1.md
docs/residents/alfred/platform-exports/text-generation-webui-alfred-v0_1.yaml
```

If any file is missing locally, record it in the implementation report and continue with available canonical files.

## Scope

This package must implement:

1. A resident package index / README for Alfred at:

```text
docs/residents/alfred/README.md
```

2. Structural consistency hardening across Alfred artifacts, including:

```text
resident name
office
source classification
public/protected source notice
canonical source references
platform export status
review and approval status
authority / non-authority boundary consistency
```

3. A deterministic validation script or test suite that verifies Alfred package presence and basic structural validity.

Acceptable implementation locations include one of these patterns, whichever best fits the current repo:

```text
tests/character_architecture/test_alfred_resident_package.py
scripts/validation/validate_alfred_resident_package.py
src/estate/character_architecture/...
```

4. Validation coverage for:

```text
JSON validity for SillyTavern export
YAML validity for canonical card and text-generation-webui export
required Markdown files present
required metadata fields present
canonical identity fields consistent across artifacts
platform exports contain live-access warning
platform exports do not claim live access by default
Alfred remains Chief of Staff and not a generic assistant
Alfred remains single-source Estate resident
```

5. A completion receipt template or actual completion receipt if implemented by Codex:

```text
collaboration/work_packages/completions/WP-0219_codex_cloud_web_done.json
```

6. Optional but preferred: a short human testing checklist for loading Alfred in local character interfaces:

```text
docs/residents/alfred/platform-exports/testing-checklist.md
```

## Out Of Scope

This package must not:

- create a new resident identity framework;
- create a new resident registry unless one already exists and cleanly accepts Alfred;
- implement a live command center;
- implement event routing infrastructure;
- implement worker assignment or provider routing;
- claim Alfred has live repo, mailbox, calendar, worker, or command-center access;
- modify split-source resident boundaries;
- add private or protected source content;
- change Alfred's role away from Chief of Staff;
- create visual image assets;
- perform live SillyTavern, Open WebUI, or text-generation-webui calls.

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
Alfred coordinates but does not absorb other offices. Alfred must not become Helen, Ingrid, Eleanor, Traffic Controller, Audit, Engineering, or Character Architecture. Platform exports are adapters only. The Estate public charter and canonical character card remain authoritative.
```

## Expected Artifacts

Create or update only paths justified by the existing codebase.

Expected implementation artifacts:

```text
docs/residents/alfred/README.md
docs/residents/alfred/platform-exports/testing-checklist.md
tests/character_architecture/test_alfred_resident_package.py
collaboration/work_packages/completions/WP-0219_codex_cloud_web_done.json
```

Alternative test/script paths are acceptable if they better match the repository's existing structure, but the completion receipt must state the chosen paths.

Optional integration touchpoints, if clean and low-risk:

```text
src/estate/cli/main.py
src/estate/core/work_package_validation.py
```

Do not modify CLI or core modules unless there is already an obvious validation extension point.

## Runtime Artifacts

If runtime artifacts are produced during local validation, use:

```text
runtime/validation/work_packages/WP-0219_validation.json
operations/validation/reports/WP-0219_validation.md
runtime/validation/reviews/WP-0219_review.json
runtime/validation/reviews/WP-0219_review.md
```

Do not commit live runtime outputs unless existing Estate validation practice requires evidence artifacts in source control.

## Test Requirements

Tests must cover:

- Alfred resident package required files exist;
- canonical card YAML parses;
- command-center metadata YAML parses;
- text-generation-webui YAML parses;
- SillyTavern JSON parses and uses `chara_card_v2`;
- required fields exist in canonical card;
- required role/source fields are consistent across files;
- platform exports contain an explicit warning not to claim live Estate access without tools/context;
- Alfred is described as Chief of Staff;
- Alfred is classified as a single-source Estate resident;
- no unauthorized private/protected source content is included;
- no unauthorized live provider/network/GPU calls are required.

## Validation Rings

Every implementation package must specify which validation rings apply.

### Ring 0 - Static / Structural Validation

Purpose: prove required files, schemas, imports, and declared artifacts exist.

Required checks:

```powershell
CLS
$ErrorActionPreference = "Stop"
$root = "A:\theestate"
Set-Location $root

$required = @(
  "docs/residents/alfred/README.md",
  "docs/residents/alfred/public-charter.md",
  "docs/residents/alfred/character-card.yaml",
  "docs/residents/alfred/relationship-map.md",
  "docs/residents/alfred/digital-health-profile.md",
  "docs/residents/alfred/command-center-metadata.yaml",
  "docs/residents/alfred/platform-exports/sillytavern-alfred-v0_1.json",
  "docs/residents/alfred/platform-exports/open-webui-alfred-v0_1.md",
  "docs/residents/alfred/platform-exports/text-generation-webui-alfred-v0_1.yaml"
)

foreach ($path in $required) {
  if (-not (Test-Path $path)) { throw "Missing required Alfred artifact: $path" }
}

python - <<'PY'
import json
from pathlib import Path
json.loads(Path('docs/residents/alfred/platform-exports/sillytavern-alfred-v0_1.json').read_text(encoding='utf-8'))
print('Ring 0 JSON parse passed')
PY
```

If the repository has a standard YAML parser dependency, include YAML parse checks for:

```text
docs/residents/alfred/character-card.yaml
docs/residents/alfred/command-center-metadata.yaml
docs/residents/alfred/platform-exports/text-generation-webui-alfred-v0_1.yaml
```

### Ring 1 - Deterministic Test Validation

Purpose: prove implementation behavior with deterministic commands.

Required commands:

```powershell
CLS
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"
pytest -q tests/character_architecture/test_alfred_resident_package.py
python -m estate.cli.main validate-work-package --id WP-0219 --json
```

If no CLI validation command exists yet, record that limitation in the completion receipt and run the package-specific pytest test as the deterministic source of truth.

Expected evidence:

```text
runtime/validation/work_packages/WP-0219_validation.json
operations/validation/reports/WP-0219_validation.md
collaboration/work_packages/completions/WP-0219_codex_cloud_web_done.json
```

### Ring 2 - Local GPU Reasoning Review

Purpose: use the local RTX 4090 / Ollama validation reviewer to reason over deterministic evidence.

The local reasoning reviewer should inspect:

- this work package;
- changed files;
- deterministic test output;
- validation artifact JSON/Markdown;
- completion receipt;
- Alfred resident package artifacts;
- platform exports;
- boundary and scope notes.

Reviewer questions:

```text
Did the implementation satisfy the package mission?
Did deterministic validation pass?
Did the completion receipt cover files changed, tests run, limitations, and skipped live calls?
Did Alfred remain Chief of Staff rather than generic assistant?
Did the work preserve Office / Occupant / Implementation / State separation?
Did the work preserve resident vs worker vs provider vs persona distinctions?
Did the work preserve Alfred's single-source Estate resident classification?
Did the platform exports avoid claiming live Estate access without tools/context?
Did the exports avoid unauthorized private/protected source content?
Did the package avoid creating duplicate registries, event systems, command surfaces, or offices?
Did the package stay in scope?
Is it ready for Chief Architect review, blocked, failed, or escalation-worthy?
```

Expected commands, when the reviewer exists:

```powershell
CLS
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"
python -m estate.cli.main local-gpu-validation-review --work-package WP-0219 --json
python -m estate.cli.main local-gpu-validation-review-report --work-package WP-0219
```

Expected evidence:

```text
runtime/validation/reviews/WP-0219_review.json
runtime/validation/reviews/WP-0219_review.md
```

### Ring 3 - CLI Escalation Validation

Purpose: use Codex CLI, ChatGPT CLI, or another local command-line reasoning provider only when local deterministic and GPU review are insufficient.

Use Ring 3 only when:

- local GPU review cannot resolve the issue;
- the failure spans many packages or subsystems;
- there is a complex architectural or boundary conflict;
- a platform export conflict cannot be resolved from canonical artifacts;
- repair guidance is needed but not yet authorized.

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

- Ring 0 evidence exists;
- Ring 1 evidence exists;
- Ring 2 recommendation is coherent or explicitly unavailable;
- unresolved concerns are documented;
- Alfred is acceptable as Resident Package v0.1 reference implementation candidate;
- platform exports are acceptable for local test conversations;
- promotion or repair decision is explicit.

## Completion Receipt Requirements

If implemented by Codex or another provider, create:

```text
collaboration/work_packages/completions/WP-0219_codex_cloud_web_done.json
```

The receipt must include:

- work_package_id;
- provider;
- files changed;
- tests run;
- validation commands run;
- runtime artifacts generated;
- docs updated;
- Office integration status;
- skipped live-provider calls;
- known limitations;
- follow-up recommendations.

## Promotion Criteria

This package is ready for promotion when:

- Ring 0 passes;
- Ring 1 passes;
- Ring 2 produces ready_for_chief_architect_review or equivalent, or records why the local reviewer is not yet available;
- Ring 3 is either not required or completed;
- completion receipt is present and complete;
- no blocking boundary or classification issue remains;
- Chief Architect / Steward acceptance is recorded.

## Completion Signal

If implemented by Codex, create the completion receipt and include validation ring evidence paths.
