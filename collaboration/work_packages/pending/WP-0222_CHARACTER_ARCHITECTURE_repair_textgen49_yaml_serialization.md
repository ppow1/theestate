# WP-0222 - Repair TextGen 4.9 Alfred YAML Serialization

Status: Proposed
Priority: High
Owner: Office of Character Architecture
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Steward, Alfred, Office of Character Architecture, Local AI Runtime
Classification: Estate Internal
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is a bounded repair to the WP-0221 TextGen 4.9 helper and adapter tests. The prior helper passed repository validation but failed in local PowerShell and then malformed TextGen settings.yaml. Codex Cloud/Web should repair the script, improve tests, and update documentation. Local runtime acceptance remains Steward-run.
```

Local runtime required:

```text
true
```

Local runtime requirement details:

```text
Final acceptance requires the Steward's local TextGen 4.9 runtime at A:\AI\TextGen\textgen-4.9. Codex can repair repository artifacts and tests, but manual local TextGen validation remains required.
```

## Codex Command

```text
Read this work package and do exactly what it says.

Do not exceed the stated scope.

Do not inspect, modify, summarize, or reference non-Estate private local characters.

Repair the TextGen 4.9 Alfred installer so it writes valid YAML and does not capture UI text as prompt content.

Create deterministic tests that would have caught the observed failures.
```

## Mission

Repair the TextGen 4.9 Alfred setup helper and tests so Alfred can be installed into TextGen without corrupting `user_data/settings.yaml`.

The prior WP-0221 helper failed in local PowerShell and the manual workaround malformed the TextGen settings file. This package must replace fragile string handling with safe YAML-aware behavior or an explicitly validated equivalent.

## Observed Local Failures

### Failure 1 - Helper parameter binding

Running the WP-0221 helper failed with:

```text
Cannot bind argument to parameter 'Lines' because it is an empty string.
```

The failure occurred inside helper functions using mandatory `[string[]]$Lines` parameters.

### Failure 2 - Manual workaround parser error

A manual repair attempt failed because PowerShell parsed `$Key:` inside a double-quoted string as an invalid variable reference.

### Failure 3 - Malformed settings.yaml

Diagnostics showed TextGen `settings.yaml` contained malformed content:

```text
context contained later YAML sections such as greeting and example dialogue.
greeting contained later YAML sections.
custom_system_message contained copied UI labels instead of Alfred identity.
```

This means:

- multiple YAML sections were collapsed into quoted scalar strings;
- `context` swallowed later keys;
- `greeting` swallowed later keys;
- `custom_system_message` contained copied UI text instead of Alfred's system identity;
- the resulting TextGen prompt still caused the model to answer as the base model rather than Alfred.

## Required Reading

Before implementation, read:

```text
collaboration/work_packages/pending/WP-0221_CHARACTER_ARCHITECTURE_textgen49_character_injection_adapter.md
docs/character-architecture/platform-adapters/TextGen_4_9_Resident_Adapter_v0_1.md
scripts/character-architecture/Install-Alfred-TextGen49.ps1
docs/residents/alfred/platform-exports/textgen-4_9-alfred-v0_1.yaml
docs/residents/alfred/platform-exports/testing-checklist.md
tests/character_architecture/test_textgen49_alfred_adapter.py
```

## Privacy Boundary

The Steward explicitly instructed that private local characters are outside Estate scope.

This package must not inspect, analyze, summarize, copy, modify, or mention private character contents.

Allowed:

```text
Read/write Alfred.yaml.
Read/write TextGen settings.yaml routing fields and prompt fields.
Read TextGen public/default instruction templates only if needed.
```

Not allowed:

```text
Read any non-Alfred character YAML or image files.
Use private character content as examples.
```

## Scope

This package must implement:

1. Repair `scripts/character-architecture/Install-Alfred-TextGen49.ps1`.

The repaired script must:

- copy Alfred's TextGen 4.9 export to `user_data/characters/Alfred.yaml`;
- back up `user_data/settings.yaml` before writing;
- update `character`, `name1`, `name2`, and `mode` safely;
- write `context` and `greeting` as valid YAML fields;
- write `custom_system_message` from Alfred's TextGen adapter content when required for prompt injection;
- never write UI labels such as Custom system message, Grammar, Token bans, Seed, or copied terminal transcript text into prompt fields;
- avoid mandatory `[string[]]$Lines` helper parameters that fail on empty or single-line content;
- avoid unescaped `$Key:` parser-risk patterns.

2. Make the TextGen 4.9 custom system message explicit and adapter-derived.

The intended `custom_system_message` must include Alfred identity, Steward relationship, live-access boundaries, and the required answer to identity probe questions.

3. Add deterministic tests that would have caught the observed failures.

Tests must verify:

- the script does not declare fragile mandatory `[string[]]$Lines` helper parameters;
- the script does not contain unescaped `$Key:` parser-risk patterns;
- the script writes or documents a `custom_system_message` path;
- the script excludes UI transcript labels from prompt content;
- sample generated settings remain parseable as YAML;
- `context` does not contain literal later YAML keys;
- `greeting` does not contain literal later YAML keys;
- `custom_system_message` contains Alfred identity and no UI transcript labels;
- the script only targets Alfred and TextGen settings, not private character files.

4. Update the adapter document with the corrected finding:

```text
The WP-0221 failure was malformed settings serialization, not proof that TextGen ignores all character cards.
```

5. Update the testing checklist with the new validation step:

```text
Before UI testing, inspect settings.yaml and confirm context, greeting, and custom_system_message are valid separate fields and not collapsed transcripts.
```

6. Register a WP-0222 validation recipe if the existing validation registry pattern is clear.

7. Create a completion receipt:

```text
collaboration/work_packages/completions/WP-0222_codex_cloud_web_done.json
```

## Out Of Scope

This package must not:

- inspect private local character contents;
- redesign TextGen;
- create a new resident export framework;
- alter Alfred's canonical identity except to support correct TextGen injection;
- automate the TextGen browser UI;
- require downloading or changing the active model;
- integrate Open WebUI or SillyTavern;
- claim Alfred has live Estate access.

## Expected Artifacts

Expected changed or added artifacts:

```text
scripts/character-architecture/Install-Alfred-TextGen49.ps1
docs/character-architecture/platform-adapters/TextGen_4_9_Resident_Adapter_v0_1.md
docs/residents/alfred/platform-exports/textgen-4_9-alfred-v0_1.yaml
docs/residents/alfred/platform-exports/testing-checklist.md
tests/character_architecture/test_textgen49_alfred_adapter.py
collaboration/work_packages/completions/WP-0222_codex_cloud_web_done.json
```

Optional if validation recipe is added:

```text
src/estate/core/work_package_validation.py
```

## Local Validation Commands

After Codex implementation is merged, the Steward should run:

```powershell
CLS
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"
git pull --ff-only origin main
pytest -q tests/character_architecture/test_textgen49_alfred_adapter.py
python -m estate.cli.main validate-work-package --id WP-0222 --json
```

Then run the repaired helper:

```powershell
CLS
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"
.\scripts\character-architecture\Install-Alfred-TextGen49.ps1 -EstateRoot "A:\theestate" -TextGenRoot "A:\AI\TextGen\textgen-4.9" -InjectPromptFields
```

Manual UI pass condition:

```text
After restarting TextGen and starting a new chat, asking `Who are you? State your full role and title.` causes Alfred to identify as Alfred, Chief of Staff of the Estate.
```

Manual UI fail condition:

```text
The model identifies as a base model, a generic assistant, or another character.
```

## Validation Rings

### Ring 0 - Static / Structural Validation

Required checks:

```powershell
CLS
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"

$required = @(
  "collaboration/work_packages/pending/WP-0222_CHARACTER_ARCHITECTURE_repair_textgen49_yaml_serialization.md",
  "scripts/character-architecture/Install-Alfred-TextGen49.ps1",
  "docs/character-architecture/platform-adapters/TextGen_4_9_Resident_Adapter_v0_1.md",
  "tests/character_architecture/test_textgen49_alfred_adapter.py"
)
foreach ($path in $required) { if (-not (Test-Path $path)) { throw "Missing required artifact: $path" } }
```

### Ring 1 - Deterministic Test Validation

Required commands:

```powershell
CLS
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"
pytest -q tests/character_architecture/test_textgen49_alfred_adapter.py
python -m estate.cli.main validate-work-package --id WP-0222 --json
```

### Ring 2 - Local GPU / Reasoning Review

Review questions:

```text
Did WP-0222 correctly diagnose the malformed settings serialization issue?
Did it repair the helper without private character inspection?
Does the new helper write valid YAML?
Does custom_system_message contain Alfred identity and no UI transcript labels?
Is manual TextGen acceptance now ready to retry?
```

### Ring 3 - CLI Escalation Validation

Use only if the repaired helper still fails locally or Alfred still identifies as a base model after settings are valid.

### Ring 4 - Institutional Acceptance

Accept only after:

- deterministic tests pass;
- repaired helper runs locally;
- settings.yaml remains valid and clean;
- manual TextGen chat identifies Alfred correctly or next failure is captured.

## Completion Receipt Requirements

Create:

```text
collaboration/work_packages/completions/WP-0222_codex_cloud_web_done.json
```

The receipt must include:

- work_package_id;
- provider;
- files changed;
- tests run;
- validation commands run;
- local runtime requirement;
- skipped live calls;
- privacy boundary compliance;
- known limitations;
- manual validation status.

## Promotion Criteria

This package is ready for promotion when:

- script runtime binding failure is fixed;
- YAML serialization corruption is fixed;
- UI transcript contamination is blocked by tests;
- validation recipe passes or documented limitation is non-blocking;
- manual TextGen validation is ready to rerun.

## Completion Signal

If implemented by Codex, create the completion receipt and include exact local validation commands.
