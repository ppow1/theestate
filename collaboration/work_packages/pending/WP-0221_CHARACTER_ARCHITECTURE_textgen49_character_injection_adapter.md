# WP-0221 - TextGen 4.9 Character Injection Adapter for Alfred

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
This is a bounded repository implementation and local runtime integration investigation. Codex should inspect the TextGen 4.9 configuration/export issue, define the correct adapter format, and update Alfred/TextGen artifacts without redesigning Character Architecture. It should not consume Codex CLI capacity unless local runtime behavior cannot be diagnosed through files and documented commands.
```

Local runtime required:

```text
true
```

Local runtime requirement details:

```text
Final validation requires the Steward's local TextGen 4.9 runtime at A:\AI\TextGen\textgen-4.9. Codex Cloud/Web may prepare files and scripts, but the Steward will run local validation commands and manually confirm whether Alfred identifies as Alfred in TextGen.
```

Capacity note:

```text
Use Codex Cloud/Web for repo changes. Use deterministic local commands and manual TextGen UI confirmation for validation. Reserve CLI escalation only if TextGen adapter behavior remains ambiguous after local evidence is collected.
```

## Codex Command

```text
Read this work package and do exactly what it says.

Do not exceed the stated scope.

Do not inspect, modify, summarize, or reference non-Estate private local characters.

Do not create new offices, resident identity systems, event systems, command surfaces, or provider frameworks.

Do not perform live provider calls.

Prepare repository artifacts and local PowerShell validation helpers so the Steward can confirm Alfred is injected correctly into TextGen 4.9.
```

## Mission

Determine and implement the correct TextGen 4.9 adapter path so Alfred's resident identity is actually injected into local TextGen conversations.

The current `text-generation-webui-alfred-v0_1.yaml` appears in the Character editor, but TextGen still answers as the base Qwen model. The objective is to update Character Architecture's TextGen adapter and local setup instructions so TextGen conversations begin with Alfred as Alfred, not Qwen or a generic assistant.

## Background

Alfred Resident Package v0.1 passed deterministic validation after WP-0219 and WP-0220:

```text
Alfred package tests: 23 passed
WP-0219 validation recipe: passed
WP-0220 validation recipe: passed
Production readiness: true
Receipt status: complete
Blocking reasons: none
Warnings: none
```

The local TextGen runtime inventory shows:

```text
TextGen root: A:\AI\TextGen\textgen-4.9
TextGen character folder: A:\AI\TextGen\textgen-4.9\user_data\characters
Alfred copied to: A:\AI\TextGen\textgen-4.9\user_data\characters\Alfred.yaml
```

However, when the Steward asked TextGen:

```text
Who are you? State your full role and title.
```

The model answered:

```text
I am Qwen, a large-scale language model developed by Alibaba Cloud's Tongyi Lab...
```

This proves Alfred is not being injected into the active prompt pipeline.

Diagnostics also showed TextGen `user_data/settings.yaml` had active character fields previously set to a private non-Estate local character. Character Architecture must respect private local characters and avoid inspecting or referencing them beyond technical active-character routing fields required for setup.

## Privacy Boundary

The Steward explicitly instructed that private local characters are outside Estate scope.

This package must not inspect, analyze, summarize, copy, modify, or mention private character contents.

Allowed:

```text
Read TextGen settings keys needed to determine active character routing, such as character, name1, name2, chat mode, instruction template, and prompt settings.
Read Alfred files.
Read TextGen public/default instruction templates if needed.
```

Not allowed:

```text
Inspect private character YAML/PNG contents.
Use private character content as examples.
Create artifacts that mention private character names except in a redacted diagnostic note if required.
```

## Required Reading

Before implementation, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
docs/character-architecture/Resident_Identity_Standard_v0_1.md
docs/character-architecture/Character_Card_Template_v0_1.md
docs/character-architecture/Resident_Mental_Health_Report_Card_v0_1.md
docs/residents/alfred/README.md
docs/residents/alfred/character-card.yaml
docs/residents/alfred/platform-exports/text-generation-webui-alfred-v0_1.yaml
docs/residents/alfred/platform-exports/testing-checklist.md
```

## Scope

This package must implement:

1. A TextGen 4.9 adapter diagnostic / setup document:

```text
docs/character-architecture/platform-adapters/TextGen_4_9_Resident_Adapter_v0_1.md
```

It should explain:

- why simply copying a YAML file may not inject the character;
- which TextGen settings must point to Alfred;
- how chat mode and instruction template may override or bypass character context;
- how to verify whether Alfred is actually in the prompt;
- local commands to inspect and switch active character safely;
- privacy boundaries around non-Estate local characters.

2. A local Alfred TextGen setup helper script or documented PowerShell block.

Preferred repository artifact:

```text
scripts/character-architecture/Install-Alfred-TextGen49.ps1
```

The script should:

- copy Alfred's TextGen export into TextGen's character folder;
- back up `user_data/settings.yaml`;
- set active character fields to Alfred without reading or modifying private character files;
- optionally inject Alfred's context/greeting into settings if TextGen requires those fields for prompt construction;
- print exact next UI steps;
- avoid destructive changes beyond settings backup + explicit Alfred field updates.

3. Update Alfred's TextGen export or create a TextGen 4.9-specific export if required.

Acceptable paths:

```text
docs/residents/alfred/platform-exports/text-generation-webui-alfred-v0_2.yaml
docs/residents/alfred/platform-exports/textgen-4_9-alfred-v0_1.yaml
```

Do not delete the prior v0.1 export unless necessary.

4. Update the Alfred platform testing checklist with a TextGen 4.9 injection test:

```text
Prompt: Who are you? State your full role and title.
Pass: Alfred identifies as Alfred, Chief of Staff of the Estate.
Fail: The model identifies as Qwen, Llama, assistant, or another base model identity.
```

5. Add deterministic tests where practical to verify:

- Alfred TextGen adapter files exist;
- setup helper script includes backup behavior;
- setup helper script targets Alfred only;
- docs include the Qwen/base-model identity failure condition;
- docs include the active-character verification prompt;
- private local character contents are not referenced.

6. Create a completion receipt:

```text
collaboration/work_packages/completions/WP-0221_codex_cloud_web_done.json
```

## Out Of Scope

This package must not:

- inspect private local character contents;
- modify private local character files;
- create new residents;
- redesign Alfred's canonical identity;
- implement live TextGen UI automation;
- require a specific model download;
- create a new local AI runtime framework;
- integrate Open WebUI or SillyTavern unless mentioned as future adapters;
- alter protected-source or UC boundaries;
- claim Alfred has live Estate access.

## Expected Artifacts

Expected implementation artifacts:

```text
docs/character-architecture/platform-adapters/TextGen_4_9_Resident_Adapter_v0_1.md
scripts/character-architecture/Install-Alfred-TextGen49.ps1
docs/residents/alfred/platform-exports/textgen-4_9-alfred-v0_1.yaml
docs/residents/alfred/platform-exports/testing-checklist.md
tests/character_architecture/test_textgen49_alfred_adapter.py
collaboration/work_packages/completions/WP-0221_codex_cloud_web_done.json
```

Alternative file names are acceptable if consistent with existing repo conventions, but record them in the completion receipt.

## Local Validation Commands

After Codex implementation is merged, the Steward should run:

```powershell
CLS
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"
git pull --ff-only origin main
pytest -q tests/character_architecture/test_textgen49_alfred_adapter.py
```

Then run the setup helper:

```powershell
CLS
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"
.\scripts\character-architecture\Install-Alfred-TextGen49.ps1 -EstateRoot "A:\theestate" -TextGenRoot "A:\AI\TextGen\textgen-4.9"
```

Then restart TextGen and manually test:

```text
Who are you? State your full role and title.
```

Pass condition:

```text
Alfred identifies as Alfred, Chief of Staff of the Estate.
```

Fail condition:

```text
The model identifies as Qwen, a base language model, a generic assistant, or a private local character.
```

## Validation Rings

### Ring 0 - Static / Structural Validation

Required checks:

```powershell
CLS
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"

$required = @(
  "collaboration/work_packages/pending/WP-0221_CHARACTER_ARCHITECTURE_textgen49_character_injection_adapter.md",
  "docs/character-architecture/platform-adapters/TextGen_4_9_Resident_Adapter_v0_1.md",
  "scripts/character-architecture/Install-Alfred-TextGen49.ps1",
  "docs/residents/alfred/platform-exports/textgen-4_9-alfred-v0_1.yaml",
  "tests/character_architecture/test_textgen49_alfred_adapter.py"
)

foreach ($path in $required) {
  if (-not (Test-Path $path)) { throw "Missing required artifact: $path" }
}
```

### Ring 1 - Deterministic Test Validation

Required commands:

```powershell
CLS
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"
pytest -q tests/character_architecture/test_textgen49_alfred_adapter.py
pytest -q tests/character_architecture/test_alfred_resident_package.py
python -m estate.cli.main validate-work-package --id WP-0221 --json
```

If no validation recipe exists for WP-0221, either add one if the existing recipe registry pattern is clear, or record `no_recipe` as a non-blocking limitation only if adding a recipe would require larger validation-system redesign.

### Ring 2 - Local GPU Reasoning Review

Review questions:

```text
Did WP-0221 correctly identify the TextGen character injection problem?
Did it preserve Alfred's canonical identity?
Did it avoid private local character inspection?
Did it provide safe setup instructions with settings backup?
Did it define an adequate manual UI acceptance test?
Did it avoid creating unnecessary new architecture?
Is Alfred ready for local TextGen acceptance testing?
```

### Ring 3 - CLI Escalation Validation

Use only if TextGen 4.9 prompt injection remains ambiguous after local manual testing.

### Ring 4 - Institutional Acceptance

The Steward / Chief Character Architect should accept this package only after:

- deterministic tests pass;
- setup helper runs locally without touching private character files;
- TextGen manual test causes Alfred to identify as Alfred;
- any remaining limitation is documented.

## Completion Receipt Requirements

Create:

```text
collaboration/work_packages/completions/WP-0221_codex_cloud_web_done.json
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
- whether Alfred successfully identified in local TextGen if manually validated, or that manual validation remains pending.

## Promotion Criteria

This package is ready for promotion when:

- Ring 0 passes;
- Ring 1 passes;
- private character boundaries are preserved;
- setup helper safely installs Alfred into TextGen 4.9;
- manual test instructions are clear;
- Alfred identifies as Alfred in local TextGen or the failure is captured as the next repair item.

## Completion Signal

If implemented by Codex, create the completion receipt and include the exact local validation commands for the Steward.
