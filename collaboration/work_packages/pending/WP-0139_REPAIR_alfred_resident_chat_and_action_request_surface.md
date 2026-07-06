# REPAIR TASK WP-0139 - Repair Alfred Resident Chat and Action Request Surface

## Codex Command

Read collaboration/work_packages/pending/WP-0139_REPAIR_alfred_resident_chat_and_action_request_surface.md and do exactly what it says.

## Mode

REPAIR

## Problem

Alfred's resident card and chat surface are operationally misleading and functionally degraded.

Observed behavior:

- The Steward asked Alfred for a simple conversational response such as a joke.
- Alfred returned a generic Estate status summary and repeated operational boundary language instead of responding to the user request.
- The Alfred card says local LLM is used when available and deterministic fallback is used otherwise, but the fallback behavior is too generic and ignores ordinary conversational intent.
- The Steward also asked Alfred to start TextGen/SillyTavern. The surface says Alfred will not execute privileged actions, but it does not clearly transform privileged action requests into governed AI Services requests, pending approvals, or copyable Steward commands.

This makes Alfred appear broken from the Steward surface.

## Architectural Boundary

Do not grant Alfred autonomous privileged execution.

Do not allow Alfred to claim Steward authorization from chat.

Do not bypass AI Services approval gates.

Do not convert the resident chat into an ungoverned shell.

The repair is to make Alfred's resident surface truthful, useful, and task-aware within existing governance.

## Required Outcomes

### 1. Conversational Intent Must Work

When the Steward asks Alfred for ordinary low-risk conversational output, Alfred must answer the request rather than always returning the same Estate status block.

Examples:

- "tell me a new joke" should produce a joke.
- "summarize this" should summarize the provided text or local artifact context when available.
- "what should I look at next" may produce Estate operational guidance.

Fallback mode is allowed, but fallback mode must still respect the user's immediate prompt.

### 2. Status Summary Must Be Intent-Gated

Alfred should not always prepend or replace responses with the same Estate status summary.

Estate status summaries should appear when:

- the user asks for status;
- the prompt implies Estate operational triage;
- an action request needs governance context;
- there is a high-priority local warning that truly requires Steward attention.

### 3. Privileged Action Requests Must Become Governed Requests

When the Steward asks Alfred to start/load/stop a governed AI service, Alfred must not silently fail and must not claim to have executed it.

Instead Alfred should produce one of the following, depending on existing architecture:

- create or surface a governed AI Services approval/request record;
- provide the exact approved local command for the Steward to run;
- route the request to the Office of the Steward AI Services / Models surface;
- state that execution is unavailable and explain the next governed step.

Required example:

If the Steward asks Alfred to start TextGen with `Qwen3-8B-Q6_K.gguf`, Alfred should respond with something equivalent to:

```text
I cannot execute privileged service operations from resident chat. I can prepare the governed request. Current approved command for Steward execution:
.\estate ai-services load-model --service textgen --model Qwen3-8B-Q6_K.gguf --actor alfred --approved-by steward --health-timeout-seconds 60 --health-interval-seconds 2 --json
```

If there is already an approval, Alfred should say that approval exists and provide the next execution/check command rather than implying the service is running.

### 4. Local LLM Adapter Visibility

The Alfred card claims local-first operation through the WP-0126 adapter path.

Add visible diagnostic state showing:

- local LLM adapter available/unavailable;
- selected provider/service;
- selected model if known;
- fallback mode active/inactive;
- reason for fallback;
- last adapter error if safe to display.

Do not expose secrets.

### 5. Resident Response Contract

Define or repair a response contract so Alfred responses distinguish:

- direct conversational response;
- local artifact summary;
- recommendation;
- proposed governed action;
- blocked privileged execution;
- fallback response.

The UI should render that distinction clearly enough for the Steward to understand what Alfred did and did not do.

### 6. Tests

Add or update tests proving:

1. A simple joke prompt receives a joke-like direct response and does not get replaced by a generic Estate status block.
2. A status prompt may return Estate status guidance.
3. A privileged TextGen start/load request is not executed from resident chat.
4. A privileged TextGen start/load request returns a governed next step or command.
5. Alfred does not claim execution unless the governed AI Services execution path returns a successful execution result.
6. Existing resident interaction persistence remains intact.
7. Attachments/redaction behavior remains intact.
8. Local LLM fallback state is surfaced safely.
9. No secrets are leaked from adapter diagnostics.

## Files To Inspect

Inspect and modify only the existing resident/Alfred architecture unless a narrow supporting change is required:

- `src/estate/residents/`
- `src/estate/core/steward_command_center.py`
- `runtime/alfred/duty_state.json`
- `runtime/resident_interactions/`
- `data/objects/RES-000001.json`
- tests covering WP-0126 resident interactions and Alfred surface behavior

Also inspect AI Services interfaces only as needed for governed request/command generation:

- `src/estate/ai_services/`
- `runtime/ai_services/approvals.json`
- `runtime/ai_services/model_assignments.json`
- `runtime/ai_services/model_preferences.json`

## Required Report Artifacts

Create:

```text
operations/residents/WP-0139_alfred_resident_chat_and_action_request_repair_report.md
runtime/resident_interactions/WP-0139_alfred_resident_chat_and_action_request_repair_report.json
collaboration/work_packages/completions/WP-0139_codex_done.json
```

The report must include:

- root cause;
- changed files;
- before/after behavior;
- how simple conversation is handled;
- how governed action requests are handled;
- whether local LLM adapter is available;
- fallback behavior;
- tests run;
- remaining limitations.

## Acceptance Criteria

WP-0139 is complete when Alfred's resident chat can answer simple conversational prompts, does not mask every prompt with generic Estate status text, accurately handles privileged AI Services requests as governed requests or copyable Steward commands, and clearly shows local LLM/fallback state without granting Alfred autonomous privileged execution.

## Merge Class

Class A. Escalate if implementation attempts to grant Alfred autonomous privileged execution, changes Steward authority, bypasses AI Services approvals, exposes public network access, or changes resident identity/governance semantics.
