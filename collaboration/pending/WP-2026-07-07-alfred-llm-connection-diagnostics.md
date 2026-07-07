# WP-2026-07-07 - Alfred LLM Connection Diagnostics

Status: pending
Classification: Estate Internal
Requested by: Pat / Steward
Area: Office of the Steward, Alfred, AI Services / Models, startup diagnostics

## Mission

Investigate why Alfred opened inside the Office of the Steward without an active LLM connection and defaulted to the no-LLM/settings state after the workstation restarted from a Windows update.

The goal is not to redesign Alfred. The goal is to determine why the Office can start while Alfred has no usable LLM backend, document the cause, and add diagnostics so the failure mode is visible and recoverable.

## Context

After a Windows update, Pat started the Office of the Steward from the desktop launcher. The local Office server started, but when Pat opened Alfred, Alfred indicated that no LLM connection or provider settings were available.

This is operationally significant because the Office of the Steward may appear to be running while an essential service dependency is missing. The user should not have to infer that Alfred has lost connection only after trying to ask a question.

A separate launcher batch file fix has already been produced for opening the browser. This work package is specifically for the Alfred / LLM diagnostics issue.

## Problem Statement

The Office of the Steward can start in a state where Alfred does not have access to an LLM provider, but the startup flow does not clearly explain:

- which provider Alfred expected,
- where Alfred's provider settings are loaded from,
- whether the configured provider was missing, reset, unreachable, or not started,
- whether this is caused by environment variables, runtime files, service discovery, local model service state, or configuration persistence,
- how the user should recover.

## Scope

Investigate and document:

1. Where Alfred's LLM/provider configuration is stored.
2. Whether the configuration is tracked, generated, ignored, local-only, or runtime-only.
3. Whether Windows restart/update could have removed or changed any required environment variables, services, working directories, or runtime state.
4. Whether Alfred depends on an external local service being started before the Office loads.
5. Whether the Office startup sequence performs provider discovery.
6. Whether failed provider discovery is logged, surfaced in the UI, or silently converted into the no-LLM state.
7. Whether AI Services / Models status already has an authoritative artifact that should be used.

## Required Outcome

Produce a clear diagnostic path for Alfred's LLM state.

At minimum, the system should be able to answer:

- Alfred expected provider: `<name or none>`
- Configuration source: `<file/env/runtime/discovery source>`
- Provider reachable: yes/no/unknown
- Failure reason: `<missing config, service unavailable, bad endpoint, missing key, model unavailable, etc.>`
- Recovery hint: `<what Pat should check or start>`

## Implementation Guidance

Prefer using existing Estate mechanisms before adding new ones.

Possible implementation targets:

- Office startup console output.
- Office UI status panel.
- Alfred panel status message.
- AI Services / Models status artifact.
- Runtime validation artifact.
- Existing operations/status report.

The exact mechanism should follow the current Estate architecture once inspected.

## Boundaries

- Do not redesign Alfred.
- Do not introduce a new provider registry if an existing AI service/model discovery mechanism already exists.
- Do not hardcode secrets, API keys, or provider-specific credentials.
- Do not require internet access.
- Do not break local/offline operation.
- Do not treat a missing LLM backend as acceptable silence.
- Do not modify the launcher batch file except if required to expose the diagnostic result.

## Acceptance Criteria

This work package is complete when:

1. The source of Alfred's LLM configuration is identified.
2. The cause of the no-LLM startup state is documented.
3. The Office or Alfred exposes a clear diagnostic when no LLM provider is available.
4. The diagnostic distinguishes missing configuration from unreachable provider/service where practical.
5. A recovery hint is shown or written to a visible status artifact.
6. The behavior remains local-first and compatible with the Estate's current AI Services / Models direction.
7. The implementation note explains what changed and how Pat can verify it.

## Suggested Verification

1. Start the Office with the expected LLM provider available.
2. Confirm Alfred reports a healthy provider state.
3. Stop or disable the expected provider.
4. Restart the Office.
5. Confirm Alfred or the Office visibly reports the missing/unreachable provider with a useful cause and recovery hint.
6. Restore the provider and confirm Alfred recovers without requiring undocumented manual steps.

## Notes

This issue was discovered because the Office server started successfully but Alfred was not operationally ready. The Estate should distinguish UI/server availability from AI-service readiness.
