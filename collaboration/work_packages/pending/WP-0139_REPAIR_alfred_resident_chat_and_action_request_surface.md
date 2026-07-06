# REPAIR TASK WP-0139 - Repair Alfred Resident Chat Availability and Action Request Surface

## Codex Command

Read collaboration/work_packages/pending/WP-0139_REPAIR_alfred_resident_chat_and_action_request_surface.md and do exactly what it says.

## Mode

REPAIR

## Correction To Prior Interpretation

Do not assume the Steward asked Alfred to start TextGen or SillyTavern.

The Steward asked whether TextGen and SillyTavern could be started manually. That is different from asking Alfred to execute a privileged start operation.

The immediate failure is more basic: Alfred appears offline or out of commission from the resident chat surface. The Steward asked Alfred to tell a new joke and Alfred did not respond at all.

## Problem

Alfred's resident card and chat surface are unavailable or functionally degraded.

Observed behavior:

- Alfred Resident Card renders and accepts input.
- The card shows `Operational Status: Active` and `Presence State: waiting_for_steward`.
- The Steward entered a simple prompt: `tell me a new joke`.
- Alfred did not produce a new response.
- Earlier behavior also showed Alfred returning a generic Estate status block instead of answering ordinary conversational intent.
- The surface claims local-first operation through the WP-0126 adapter path, with deterministic fallback when no local model is available, but the UI does not clearly show whether the request is queued, failed, processing, timed out, using fallback, or blocked by adapter failure.

This makes Alfred appear active while the interaction path is not actually functioning.

## Architectural Boundary

Do not grant Alfred autonomous privileged execution.

Do not allow Alfred to claim Steward authorization from chat.

Do not bypass AI Services approval gates.

Do not convert the resident chat into an ungoverned shell.

The repair is to make Alfred's resident surface truthful, available, and task-aware within existing governance.

## Investigation Requirements

Before changing behavior, diagnose the request path end-to-end:

1. Browser/UI submit handler for the Alfred card.
2. Resident surface endpoint wiring: `/api/residents/alfred/surface`.
3. WP-0126 resident interaction API route handling.
4. Session persistence under `runtime/resident_interactions/sessions`.
5. Attachment handling under `runtime/resident_interactions/attachments`.
6. Alfred implementation routing.
7. Local LLM adapter availability.
8. Deterministic fallback path.
9. Error/timeout reporting back to the UI.
10. Generated Command Center JavaScript or form wiring if the static page is responsible for sending the request.

The primary root-cause question is:

```text
Why does a submitted Alfred message not produce a visible Alfred response?
```

## Required Outcomes

### 1. Alfred Must Respond Or Surface A Clear Failure

When the Steward submits a prompt from Alfred's resident card, the UI must do one of the following:

- display Alfred's response;
- display that the request is still processing with a durable pending state;
- display a safe, specific failure state with enough diagnostic information to repair the path.

The UI must not remain indefinitely stuck at:

```text
Alfred is reviewing local Estate context...
```

without either a response, timeout, retry option, or diagnostic state.

### 2. Conversational Intent Must Work

When the Steward asks Alfred for ordinary low-risk conversational output, Alfred must answer the request rather than always returning the same Estate status block.

Examples:

- `tell me a new joke` should produce a joke or a fallback joke.
- `summarize this` should summarize the provided text or local artifact context when available.
- `what should I look at next` may produce Estate operational guidance.

Fallback mode is allowed, but fallback mode must still respect the user's immediate prompt.

### 3. Status Summary Must Be Intent-Gated

Alfred should not always prepend or replace responses with the same Estate status summary.

Estate status summaries should appear when:

- the user asks for status;
- the prompt implies Estate operational triage;
- an action request needs governance context;
- there is a high-priority local warning that truly requires Steward attention.

### 4. Privileged Action Requests Must Be Truthful If They Occur

If a future prompt asks Alfred to start/load/stop a governed AI service, Alfred must not silently fail and must not claim to have executed it.

Instead Alfred should produce one of the following, depending on existing architecture:

- create or surface a governed AI Services approval/request record;
- provide the exact approved local command for the Steward to run;
- route the request to the Office of the Steward AI Services / Models surface;
- state that execution is unavailable and explain the next governed step.

This is a secondary requirement. Do not treat it as evidence that the Steward already asked Alfred to start anything.

### 5. Local LLM Adapter Visibility

The Alfred card claims local-first operation through the WP-0126 adapter path.

Add visible diagnostic state showing:

- local LLM adapter available/unavailable;
- selected provider/service;
- selected model if known;
- fallback mode active/inactive;
- reason for fallback;
- last adapter error if safe to display;
- last request timestamp;
- last response timestamp;
- last timeout or transport error if any.

Do not expose secrets.

### 6. Resident Response Contract

Define or repair a response contract so Alfred responses distinguish:

- direct conversational response;
- local artifact summary;
- recommendation;
- proposed governed action;
- blocked privileged execution;
- fallback response;
- request queued;
- request failed;
- request timed out.

The UI should render that distinction clearly enough for the Steward to understand what Alfred did and did not do.

### 7. Tests

Add or update tests proving:

1. Submitting an Alfred prompt produces a visible response or visible safe failure state.
2. The UI does not remain indefinitely stuck in `reviewing local Estate context`.
3. A simple joke prompt receives a joke-like direct response and does not get replaced by a generic Estate status block.
4. A status prompt may return Estate status guidance.
5. A local LLM adapter failure falls back or reports a safe diagnostic state.
6. No secrets are leaked from adapter diagnostics.
7. Existing resident interaction persistence remains intact.
8. Attachments/redaction behavior remains intact.
9. A privileged TextGen start/load request is not executed from resident chat.
10. A privileged TextGen start/load request returns a governed next step or command if such a prompt is actually submitted.
11. Alfred does not claim execution unless the governed AI Services execution path returns a successful execution result.

## Files To Inspect

Inspect and modify only the existing resident/Alfred architecture unless a narrow supporting change is required:

- `src/estate/residents/`
- `src/estate/core/steward_command_center.py`
- `runtime/alfred/duty_state.json`
- `runtime/resident_interactions/`
- `data/objects/RES-000001.json`
- tests covering WP-0126 resident interactions and Alfred surface behavior

Also inspect AI Services interfaces only as needed for future governed request/command generation:

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
- why Alfred did not respond to the joke prompt;
- how simple conversation is handled;
- how failed/offline/timeout states are surfaced;
- how governed action requests would be handled if asked;
- whether local LLM adapter is available;
- fallback behavior;
- tests run;
- remaining limitations.

## Acceptance Criteria

WP-0139 is complete when Alfred's resident chat can respond to submitted prompts or surface a clear safe failure, does not remain stuck in a processing state, can answer simple conversational prompts, does not mask every prompt with generic Estate status text, accurately handles future privileged AI Services requests as governed requests or copyable Steward commands, and clearly shows local LLM/fallback state without granting Alfred autonomous privileged execution.

## Merge Class

Class A. Escalate if implementation attempts to grant Alfred autonomous privileged execution, changes Steward authority, bypasses AI Services approvals, exposes public network access, or changes resident identity/governance semantics.
