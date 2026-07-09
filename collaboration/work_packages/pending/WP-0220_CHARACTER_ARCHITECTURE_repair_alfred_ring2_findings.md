# WP-0220 - Repair Alfred Ring 2 Findings and Validation Recipe Coverage

Status: Proposed
Priority: High
Owner: Office of Character Architecture
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Steward, Alfred, Office of Character Architecture, Audit / Validation
Classification: Estate Internal
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is a small repository repair package. It should address local Ring 2 review findings for WP-0219 by improving evidence clarity, adding or wiring deterministic validation recipe coverage where the existing Estate validation system supports it, and making protected-source exclusion explicit. This should not consume Codex CLI capacity by default.
```

Local runtime required:

```text
false
```

Local runtime requirement details:

```text
Implementation does not require live local services, GPU, network, mailbox, calendar, command-center state, or provider calls. Local validation from the repository checkout is sufficient.
```

Capacity note:

```text
Use Codex Cloud/Web for implementation. Use local deterministic validation and Ring 2 local GPU review after completion. Reserve Codex CLI only if validation recipe integration exposes a larger architecture conflict.
```

## Codex Command

```text
Read this work package and do exactly what it says.

Do not exceed the stated scope.

Do not create new offices, registries, providers, event systems, command surfaces, or resident identity systems.

Do not perform live provider calls.

Do not require live cloud, GPU, network, mailbox, calendar, worker, or command-center access in tests.

Write deterministic tests and validation evidence so local validation can confirm the result.
```

## Mission

Repair the local Ring 2 findings from WP-0219 so Alfred Resident Package v0.1 can move cleanly to Chief Architect / Steward acceptance review.

The Ring 2 review concluded `repair_needed` because it wanted clearer evidence around deterministic validation, the `no_recipe` validation limitation, completion receipt detail, and protected-source exclusion. This package should either resolve those findings directly or document why a finding is not blocking.

## Background

WP-0219 created and hardened Alfred's v0.1 resident package. Codex Cloud/Web completed PR #183 and reported:

```text
Ring 0 passed.
Ring 1 pytest passed with 19 passed.
validate-work-package --id WP-0219 returned no_recipe.
Ring 2 local GPU review was pending.
Ring 4 acceptance was pending.
```

After local sync to GitHub main, deterministic validation was run locally and passed:

```text
pytest -q tests/character_architecture/test_alfred_resident_package.py
19 passed
```

A Ring 2 local Ollama review then returned `review_status: repair_needed`, citing these actionable concerns:

```text
- no_recipe validation issue should be addressed or clarified.
- completion receipt should provide more detailed test information.
- protected-source exclusion should be made more explicit.
```

## Required Reading

Before implementation, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
docs/governance/workers/templates/Codex_Work_Package_Template_v1.md
collaboration/work_packages/pending/WP-0219_CHARACTER_ARCHITECTURE_alfred_resident_package_validation_and_exports.md
collaboration/work_packages/completions/WP-0219_codex_cloud_web_done.json
collaboration/work_packages/completions/WP-0219_character_architecture_done.json
docs/residents/alfred/README.md
docs/residents/alfred/public-charter.md
docs/residents/alfred/character-card.yaml
docs/residents/alfred/relationship-map.md
docs/residents/alfred/digital-health-profile.md
docs/residents/alfred/command-center-metadata.yaml
docs/residents/alfred/platform-exports/sillytavern-alfred-v0_1.json
docs/residents/alfred/platform-exports/open-webui-alfred-v0_1.md
docs/residents/alfred/platform-exports/text-generation-webui-alfred-v0_1.yaml
docs/residents/alfred/platform-exports/testing-checklist.md
tests/character_architecture/test_alfred_resident_package.py
```

If any file is missing locally, record it in the implementation report and continue with available canonical files.

## Scope

This package must implement:

1. Resolve or document the `no_recipe` issue for WP-0219.

Preferred approach:

```text
Add a validation recipe or recipe mapping for WP-0219 if the existing Estate validation system has a clear pattern for package-specific recipes.
```

Acceptable fallback:

```text
If no recipe system exists or adding one would require larger architecture work, create a documented validation evidence note stating that WP-0219 package-specific pytest is the deterministic source of truth and that no_recipe is a non-blocking limitation requiring future validation-system work.
```

2. Improve completion receipt detail for WP-0219, especially:

```text
- exact deterministic test command;
- exact result, including 19 passed;
- Ring 0 outcome;
- Ring 1 outcome;
- no_recipe limitation and whether it is blocking;
- skipped live calls;
- protected-source exclusion;
- readiness for Chief Architect / Steward review after repairs.
```

3. Add explicit protected-source exclusion evidence for Alfred's resident package.

Acceptable locations include one or more of:

```text
docs/residents/alfred/README.md
docs/residents/alfred/public-charter.md
docs/residents/alfred/character-card.yaml
docs/residents/alfred/platform-exports/testing-checklist.md
```

The evidence must state that Alfred v0.1 contains no protected source, no split-source private material, no UC material, and no live-access grant.

4. Strengthen deterministic tests if needed so they verify:

```text
- completion receipt contains 19 passed or equivalent explicit pytest result;
- completion receipt records skipped live calls;
- completion receipt records protected-source exclusion;
- Alfred artifacts explicitly exclude protected source;
- platform exports retain live-access warnings.
```

5. Create a completion receipt:

```text
collaboration/work_packages/completions/WP-0220_codex_cloud_web_done.json
```

## Out Of Scope

This package must not:

- redesign the validation system;
- create a new validation framework;
- create a new resident registry;
- create a new command surface;
- create or modify live event routing;
- implement Alfred runtime behavior;
- modify Alfred's canonical identity except to clarify evidence and boundaries;
- add protected, private, or split-source material;
- perform live platform imports;
- perform live provider calls;
- use Codex CLI unless explicitly escalated later.

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
Alfred remains Chief of Staff. Alfred remains a single-source Estate resident. Platform exports remain adapters. This package may clarify validation evidence but must not claim Chief Architect / Steward acceptance.
```

## Expected Artifacts

Expected implementation artifacts:

```text
collaboration/work_packages/completions/WP-0219_codex_cloud_web_done.json
docs/residents/alfred/README.md
docs/residents/alfred/platform-exports/testing-checklist.md
tests/character_architecture/test_alfred_resident_package.py
collaboration/work_packages/completions/WP-0220_codex_cloud_web_done.json
```

Optional, only if a clear existing validation recipe location exists:

```text
src/estate/core/work_package_validation.py
src/estate/cli/main.py
<existing validation recipe path>
<existing tests for work package validation recipes>
```

Do not modify CLI or core validation modules unless the existing pattern is obvious and low risk.

## Runtime Artifacts

If runtime artifacts are produced during local validation, use:

```text
runtime/validation/work_packages/WP-0220_validation.json
operations/validation/reports/WP-0220_validation.md
runtime/validation/reviews/WP-0220_review.json
runtime/validation/reviews/WP-0220_review.md
```

Do not commit live runtime outputs unless existing Estate validation practice requires evidence artifacts in source control.

## Test Requirements

Tests must cover:

- Alfred resident package tests still pass;
- protected-source exclusion is explicit;
- completion receipt includes deterministic test result detail;
- completion receipt records skipped live calls;
- completion receipt records known limitations;
- platform exports still avoid live-access claims without tools/context;
- no unauthorized protected-source content is introduced.

## Validation Rings

### Ring 0 - Static / Structural Validation

Required checks:

```powershell
CLS
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"

$required = @(
  "collaboration/work_packages/pending/WP-0220_CHARACTER_ARCHITECTURE_repair_alfred_ring2_findings.md",
  "collaboration/work_packages/completions/WP-0219_codex_cloud_web_done.json",
  "docs/residents/alfred/README.md",
  "docs/residents/alfred/platform-exports/testing-checklist.md",
  "tests/character_architecture/test_alfred_resident_package.py"
)

foreach ($path in $required) {
  if (-not (Test-Path $path)) { throw "Missing required artifact: $path" }
}

python - <<'PY'
import json
from pathlib import Path
json.loads(Path('collaboration/work_packages/completions/WP-0219_codex_cloud_web_done.json').read_text(encoding='utf-8'))
print('WP-0219 receipt JSON parse passed')
PY
```

### Ring 1 - Deterministic Test Validation

Required commands:

```powershell
CLS
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"
pytest -q tests/character_architecture/test_alfred_resident_package.py
python -m estate.cli.main validate-work-package --id WP-0220 --json
```

If no CLI validation command or recipe exists for WP-0220, record that limitation in the completion receipt and run the package-specific pytest test as the deterministic source of truth.

Expected evidence:

```text
runtime/validation/work_packages/WP-0220_validation.json
operations/validation/reports/WP-0220_validation.md
collaboration/work_packages/completions/WP-0220_codex_cloud_web_done.json
```

### Ring 2 - Local GPU Reasoning Review

The local reasoning reviewer should inspect:

- this work package;
- changed files;
- deterministic test output;
- WP-0219 and WP-0220 completion receipts;
- Alfred resident package artifacts;
- platform exports;
- protected-source exclusion statements;
- boundary and scope notes.

Reviewer questions:

```text
Did WP-0220 resolve or clearly document the WP-0219 Ring 2 findings?
Did deterministic validation pass?
Is the no_recipe issue resolved or explicitly documented as non-blocking?
Does the completion receipt now provide adequate detail?
Is protected-source exclusion explicit and test-backed?
Did Alfred remain Chief of Staff?
Did the package stay in scope?
Is WP-0219 now ready for Chief Architect / Steward acceptance review?
```

Expected commands, when the reviewer exists:

```powershell
CLS
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"
python -m estate.cli.main local-gpu-validation-review --work-package WP-0220 --json
python -m estate.cli.main local-gpu-validation-review-report --work-package WP-0220
```

If the local reviewer command does not exist, use the existing evidence-packet method and record the limitation.

### Ring 3 - CLI Escalation Validation

Use Ring 3 only when:

- validation recipe integration reveals a larger architecture conflict;
- deterministic tests cannot resolve the issue;
- Ring 2 review still reports unclear evidence after repairs;
- repair guidance requires stronger local reasoning.

Ring 3 validator rules:

```text
Prefer read-only validation.
Write validation artifacts only.
Do not repair implementation code unless explicitly assigned.
Do not become the default implementation worker.
```

### Ring 4 - Institutional Acceptance

Acceptance reviewer must confirm:

- Ring 0 evidence exists;
- Ring 1 evidence exists;
- Ring 2 recommendation is coherent or explicitly unavailable;
- WP-0219 Ring 2 findings were resolved or downgraded to documented limitations;
- no protected-source or live-access boundary issue remains;
- Alfred Resident Package v0.1 is ready for Chief Architect / Steward acceptance or repair decision.

## Completion Receipt Requirements

If implemented by Codex or another provider, create:

```text
collaboration/work_packages/completions/WP-0220_codex_cloud_web_done.json
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
- follow-up recommendations;
- whether WP-0219 Ring 2 findings were resolved, documented, or remain open.

## Promotion Criteria

This package is ready for promotion when:

- Ring 0 passes;
- Ring 1 passes;
- protected-source exclusion is explicit;
- completion receipt detail is improved;
- no_recipe is resolved or clearly documented as non-blocking / future validation-system work;
- Ring 2 produces ready_for_chief_architect_review or equivalent;
- Ring 3 is either not required or completed;
- completion receipt is present and complete;
- Chief Architect / Steward acceptance is recorded.

## Completion Signal

If implemented by Codex, create the completion receipt and include validation ring evidence paths.
