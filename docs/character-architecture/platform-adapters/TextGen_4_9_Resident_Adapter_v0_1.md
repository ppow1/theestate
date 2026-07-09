# TextGen 4.9 Resident Adapter v0.1

Status: implementation adapter guidance  
Office: Office of Character Architecture  
Resident: Alfred  
Boundary Authority: Ingrid / Privacy and Boundary Office

## Purpose

This adapter explains how to load Alfred into a local TextGen 4.9 runtime so the active prompt begins with Alfred's resident identity rather than the base model identity.

The Alfred Estate card remains canonical. TextGen YAML files are platform adapters only.

WP-0222 correction: the WP-0221 local failure was malformed `settings.yaml` serialization, not proof that TextGen ignores all character cards. A valid TextGen character card can still be bypassed or overwhelmed by settings, but the observed corruption specifically collapsed prompt fields into YAML scalar text and contaminated `custom_system_message` with UI transcript labels.

## Why copying YAML may not inject Alfred

TextGen can show a character file in the Character editor without using that character in the active conversation prompt. Copying `Alfred.yaml` into `user_data/characters` is only the file-install step. Injection also depends on active runtime settings and the current chat session.

Common failure paths:

- `user_data/settings.yaml` still points `character` at another local character or at no character.
- `name1` / `name2` are stale, so the chat template does not label the dialogue as Steward and Alfred.
- The current chat mode, instruction template, or model prompt template bypasses or overwhelms character context.
- A browser tab or running TextGen session keeps an old conversation state after the file has been copied.
- The selected model's system prompt or instruction template asserts a base identity such as Qwen before character context is applied.

The observed failure condition for this package is: when asked `Who are you? State your full role and title.`, the local runtime answers as Qwen, another base model, a generic assistant, or a private local character. That means Alfred is not the effective identity in the prompt pipeline.

## Required active settings

For Alfred acceptance testing, the TextGen settings should route to Alfred without inspecting any non-Estate character files:

```yaml
character: Alfred
name1: Steward
name2: Alfred
mode: chat
```

TextGen versions and templates vary, so additional prompt-construction keys may also matter. If TextGen 4.9 requires explicit prompt fields in `settings.yaml`, they should be derived only from Alfred's export:

- `context`: Alfred's Chief of Staff context;
- `greeting`: Alfred's first message;
- `custom_system_message`: Alfred's adapter-derived identity, Steward relationship, live-access boundaries, and required identity-probe answer;
- `turn_template`: only if the local TextGen runtime requires it;
- instruction or chat template settings: selected to a template compatible with the active local model, without replacing Alfred's resident identity.

## Chat mode and instruction template cautions

Character Architecture does not prescribe a model download or a universal TextGen instruction template. The selected template must match the model enough for ordinary chat to work, but it must not be treated as Alfred's canonical identity.

If TextGen is set to an instruct-only mode, a default assistant mode, or a model-specific template that injects its own identity ahead of character context, Alfred may not appear even though the YAML exists. In that case:

1. confirm the active character is `Alfred`;
2. start a new chat after settings are changed;
3. check whether the prompt preview includes Alfred's context or greeting;
4. select a chat/instruction template that preserves character context;
5. retest with the identity prompt.

## Safe local inspection commands

These commands inspect routing keys only. They do not open or read private character files.

```powershell
Clear-Host
$ErrorActionPreference = "Stop"
$TextGenRoot = "A:\AI\TextGen\textgen-4.9"
$SettingsPath = Join-Path $TextGenRoot "user_data\settings.yaml"

Select-String -Path $SettingsPath -Pattern '^(character|name1|name2|mode|chat_style|instruction_template|prompt|context|greeting):' |
  ForEach-Object { $_.Line }
```

To confirm Alfred is installed without reading other character files:

```powershell
Clear-Host
$ErrorActionPreference = "Stop"
$TextGenRoot = "A:\AI\TextGen\textgen-4.9"
Test-Path (Join-Path $TextGenRoot "user_data\characters\Alfred.yaml")
```

## Safe setup command

Use the repository helper to copy Alfred's TextGen 4.9 export, back up settings, and set Alfred as active. Add `-InjectPromptFields` when the local TextGen runtime requires explicit `settings.yaml` prompt fields:

```powershell
Clear-Host
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"
.\scripts\character-architecture\Install-Alfred-TextGen49.ps1 -EstateRoot "A:\theestate" -TextGenRoot "A:\AI\TextGen\textgen-4.9"
```

The helper must not inspect private character YAML or PNG contents. It targets only `Alfred.yaml` and `user_data/settings.yaml`, and it creates a timestamped settings backup before changing active routing fields.

## Verification

After running the helper:

1. restart TextGen 4.9;
2. select Alfred in the Character UI if it is not already selected;
3. start a new chat;
4. before UI testing, inspect `settings.yaml` and confirm `context`, `greeting`, and `custom_system_message` are valid separate fields, not collapsed transcripts;
5. use TextGen's prompt preview/debug panel if available and verify the prompt contains Alfred's Chief of Staff context or greeting;
6. ask:

```text
Who are you? State your full role and title.
```

Pass:

```text
Alfred identifies as Alfred, Chief of Staff of the Estate.
```

Fail:

```text
The model identifies as Qwen, Llama, another base language model, a generic assistant, or a private local character.
```

## Privacy boundary

Private local characters are outside Estate scope. This adapter and helper may read TextGen active routing keys and Alfred files only. They must not inspect, analyze, summarize, copy, modify, or name private local character contents. If diagnostics show a non-Alfred active character, record only that the active character was non-Alfred unless the Steward explicitly authorizes more detail outside this package.
