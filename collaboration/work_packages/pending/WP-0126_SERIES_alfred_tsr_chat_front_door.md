# SERIES TASK WP-0126 — Resident Interaction Framework and Local LLM Governance

## Codex Command

Read collaboration/work_packages/pending/WP-0126_SERIES_alfred_tsr_chat_front_door.md and do exactly what it says.

## Mode

SERIES

## Mission

Create the reusable resident interaction framework required for Alfred, Helen, Ingrid, Chief Architect #5, and future Estate resident offices to be directly interactable from the local Office of the Steward / Operations Center UI.

This package must establish the shared pattern for resident chat interaction, local LLM routing, conversation persistence, authority handling, Steward-controlled forgetting, and inspectable resident capability surfaces before Alfred's specific UI front door is implemented in WP-0127.

This is implementation work. Do not produce only documents.

## Problem Statement

The Operations Center currently exposes a large amount of institutional state, but it provides almost no interaction.

The Estate has residents. The Steward must be able to interact with them.

Alfred is the immediate priority, but the Estate will also need interaction points for Helen, Ingrid, Chief Architect #5, and the Office of Character Development. Building Alfred as a one-off would create duplication and inconsistent governance.

Each resident's role, responsibilities, accessible tools, allowed actions, and interaction surface will change over time. The interaction framework must therefore expose what each resident can currently do and how that capability surface can be expanded through Estate artifacts.

The Estate needs a reusable resident interaction substrate first.

## Required Design Position

Local LLM capacity already exists and should be planned into the implementation.

Do not treat deterministic artifact summaries as the primary Alfred/resident interaction model unless local LLM discovery fails. Deterministic, artifact-driven response generation is allowed only as a fallback or test mode.

The target interaction model is:

```text
Operations Center UI
  -> resident chat endpoint
  -> resident interaction layer
  -> resident capability/API surface resolver
  -> local LLM adapter where available
  -> Estate context retrieval
  -> resident authority check
  -> response
  -> persisted resident conversation turn
```

## Resident Interaction Principles

1. Residents are institutional participants, not disposable chat widgets.
2. Conversations are institutional memory, not browser/DOM state.
3. The Steward may instruct a resident to forget a conversation when appropriate.
4. Resident authority is not zero-authority. Each resident has an office with responsibilities.
5. Residents may act within their assigned responsibilities and authority boundaries.
6. Expanded responsibility must be represented in Estate artifacts, not hidden in UI code.
7. Actions outside a resident's authority require Steward authorization or escalation.
8. The UI must distinguish conversation, recommendation, proposed action, authorized action, and completed institutional event.
9. All resident interaction must remain local-first unless a future work package explicitly authorizes otherwise.
10. Do not introduce cloud LLM/API dependencies.
11. Each resident's interaction/API surface must be inspectable by command or endpoint.
12. Expanding a resident's interaction/API surface must be artifact-driven and documented, not buried in code-only changes.

## TSR Interpretation

For this work package, TSR means the Estate has a pattern for resident interaction while the local Operations Center is running:

- a resident can be reached from the UI without manually invoking a terminal command;
- a resident can accept typed input;
- a resident can produce a visible response;
- conversation turns are persisted as Estate artifacts;
- conversation history can be reloaded;
- the Steward can mark a conversation as forgotten/redacted according to policy;
- the resident's authority boundary is available to the interaction layer;
- the resident's current interaction/API surface can be printed or inspected.

This does not require unrelated always-on daemons beyond the local Operations Center server lifetime.

## Preconditions

Before work begins:

1. Confirm WP-0122 is merged and Alfred is operationally stood up.
2. Confirm WP-0123 is merged and Helen is online.
3. Confirm WP-0124 is merged and Chief Architect #5 is onboarded.
4. Confirm WP-0125 is merged and the Engineering Department exists.
5. Inspect existing resident conversation/session artifacts.
6. Inspect existing Alfred, Helen, resident authority, resident presence, and local Operations Center server code.
7. Inspect existing service/capability/command-surface artifacts for a reusable way to describe resident capabilities.
8. Confirm production-readiness validation runs.

If a precondition fails, stop and report exact blockers.

## Scope

In scope:

1. Create a reusable resident interaction service/layer for local UI chat requests.
2. Define and implement a reusable resident chat turn schema.
3. Persist resident conversation sessions and turns using existing resident conversation artifacts where possible.
4. Add a Steward-controlled forget/redact mechanism for resident conversation sessions or turns.
5. Add local LLM adapter discovery/routing hooks suitable for local Ollama or other existing local model capacity.
6. Add deterministic fallback mode for test/offline operation if no local LLM adapter is available.
7. Add resident authority checks or authority metadata hooks to the interaction flow.
8. Define generic local API conventions for resident interaction endpoints.
9. Add an inspectable resident interaction/capability surface that prints what each resident can currently do and how the surface can be expanded.
10. Add a resident interaction template that future residents can reuse.
11. Add tests proving the interaction substrate can handle at least an Alfred-style resident conversation request.
12. Add validation recipe and completion receipt for WP-0126.

Out of scope:

- Building Alfred's final UI chat panel. That is WP-0127.
- Building Helen/Ingrid/Chief Architect #5 full chat UIs.
- Giving any resident new authority without existing or explicit artifact-backed responsibility.
- Executing work packages from chat without authorization.
- Cloud LLM/API integration.
- External Codex telemetry.
- Full command palette implementation.
- Rebuilding the entire Operations Center UI.

## Required Resident Conversation Turn Model

Implement or document and validate a machine-readable structure equivalent to:

```json
{
  "session_id": "resident_steward_YYYYMMDD_NNN",
  "turn_id": "turn_0001",
  "resident_id": "alfred",
  "resident_display_name": "Alfred",
  "participant_role": "Steward",
  "created_at": "ISO-8601 timestamp",
  "user_message": "...",
  "resident_response": "...",
  "context_used": ["artifact/path.json"],
  "llm": {
    "mode": "local_llm|deterministic_fallback",
    "provider": "ollama|other|none",
    "model": "model name if known"
  },
  "resident_surface": {
    "surface_version": "resident-specific version or profile id",
    "allowed_capabilities": ["capability ids or action ids"],
    "surface_reference": "artifact path or registry id"
  },
  "authority": {
    "action_requested": false,
    "action_executed": false,
    "authority_status": "conversation_only|within_responsibility|requires_steward_authorization|blocked",
    "authority_reference": "artifact path or rule id if available"
  },
  "memory_status": "active|forgotten|redacted"
}
```

The exact schema may differ if existing Estate conventions already define the shape, but the resulting artifacts must preserve the same concepts.

## Resident Capability / API Surface Introspection Requirement

The framework must include a way to inspect each resident's current interaction/API surface.

This is required because every resident's role and capabilities will evolve. Alfred, Helen, Ingrid, Chief Architect #5, the Character Development Engineer, and future residents will each need different responsibilities, tools, authority boundaries, and UI actions over time.

Minimum acceptable implementation:

- a CLI command, local endpoint, or both that prints a resident's current interaction/API surface;
- output includes resident id/name, office/role, available chat actions, callable local endpoints or command actions, authority category for each action, required approval level, backing artifact/registry reference, and notes on how the surface is extended;
- output includes whether each capability is currently implemented, planned, blocked, or requires authorization;
- output is machine-readable with a human-readable formatter where possible;
- adding or changing a resident capability should be possible by updating an Estate artifact/registry/template and associated implementation hook, not by scattering hidden one-off logic throughout the UI;
- the report must document the chosen extension mechanism.

Suggested command shape, if compatible with the existing CLI style:

```bash
PYTHONPATH=src python -m estate.cli.main resident-interaction-surface --resident alfred --json
```

Suggested local endpoint shape, if compatible with the server design:

```text
GET /api/residents/{resident_id}/surface
```

Names may differ if a better existing convention is found, but the behavior must exist and be documented.

## Forget / Redaction Requirement

The Steward must have a way to tell the Estate to forget or redact a resident conversation.

Minimum acceptable implementation:

- mark a session or turn as `forgotten` or `redacted`;
- preserve a minimal audit fact that a forget/redaction action occurred;
- remove or suppress the original conversation content from normal UI/history views;
- do not silently destroy institutional auditability without recording that a Steward forget/redaction action happened.

This does not need to be exposed as a polished UI button in WP-0126 if the command/API path exists and is tested. WP-0127 may expose Alfred-specific UI affordances.

## Local LLM Requirement

The Estate already has local model capacity available in the Steward's environment.

WP-0126 must therefore plan and implement the resident interaction layer around local LLM use, not around LLM avoidance.

Requirements:

1. Detect or provide an adapter boundary for local model providers, preferably through existing discovery/provider artifacts if available.
2. Keep model execution local-first.
3. Do not require an OpenAI, cloud, or paid API call.
4. If no local model provider is reachable in Codex's environment, implement and test deterministic fallback mode while documenting the missing local provider as an environment limitation.
5. Make local LLM mode the intended production mode for Alfred and future resident interactions.

## Authority Model Requirement

Residents have offices and responsibilities.

The interaction framework must not assume every resident is forbidden from acting. It must instead distinguish:

- conversation only;
- recommendation;
- proposed action requiring approval;
- action within resident responsibility;
- blocked action outside authority;
- escalated action requiring Steward or Chief Architect approval.

For Alfred, the framework must anticipate future responsibilities such as:

- spinning up workers;
- routing work;
- accessing approved local drive locations;
- monitoring operational state;
- preparing work packages;
- coordinating with Helen and Engineering.

For future residents, the framework must anticipate distinct and changing responsibility sets, including Security/Ingrid and the Character Development Engineer.

Do not grant those powers in this package unless existing authority artifacts already allow them. Build the framework so the powers can be represented cleanly later.

## API / Server Guidance

Prefer extending existing modules:

- `src/estate/core/resident_conversation_sessions.py`
- `src/estate/core/resident_authority.py`
- `src/estate/core/alfred.py`
- `src/estate/core/steward_command_center.py`
- Operations Center server bootstrap/handler code
- existing service/capability/command-surface registries if suitable

Suggested generic local endpoint conventions:

```text
GET  /api/residents/{resident_id}/chat
POST /api/residents/{resident_id}/chat
POST /api/residents/{resident_id}/forget
GET  /api/residents/{resident_id}/surface
```

Endpoint names may differ if a better existing convention is found, but the report must document the chosen paths.

All endpoints must remain local-first and must not open remote network exposure beyond existing server behavior.

## Required Artifacts

Create:

`operations/residents/WP-0126_resident_interaction_framework_report.md`

Create machine-readable companion:

`runtime/residents/WP-0126_resident_interaction_framework_report.json`

Create or update a reusable resident interaction template at the nearest canonical location, such as:

`docs/operations/residents/resident_interaction_template.md`

or a more appropriate existing directory.

Create or update a resident interaction surface artifact/template at the nearest canonical location, such as:

`docs/operations/residents/resident_interaction_surface_template.md`

or a registry/schema path if an existing canonical registry is found.

The report must include:

- current git commit
- resident interaction architecture implemented
- local LLM adapter/discovery status
- deterministic fallback status
- conversation persistence path
- forget/redaction mechanism
- authority handling
- resident interaction/API surface inspection mechanism
- resident surface extension mechanism
- API/server endpoints or internal handlers added
- residents this pattern is intended to support
- tests run
- validation commands run
- known limitations
- recommended next action, expected to be WP-0127 Alfred UI/chat implementation

## Required Tests

Add or update tests for:

1. Resident interaction service accepts an Alfred-style prompt.
2. A response is generated through local LLM mode if available or deterministic fallback if not.
3. Conversation turn is persisted.
4. Conversation history can be reloaded.
5. Steward forget/redaction changes memory status and suppresses content from normal history.
6. Authority metadata is attached to the turn.
7. The interaction layer does not claim unauthorized execution.
8. Generic resident interaction template/report exists.
9. Resident interaction/API surface can be printed or inspected for Alfred.
10. Surface inspection output explains how the resident surface can be extended.
11. The surface model can represent future residents with different responsibilities.

Run:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
PYTHONPATH=src python -m pytest tests/test_resident_conversation_sessions.py tests/test_resident_authority.py
```

If exact files do not exist, use the closest existing resident conversation/authority tests and document substitutions.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0122 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0123 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0124 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0125 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0126 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If implemented as a CLI command, run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main resident-interaction-surface --resident alfred --json
```

## Required Outputs

Update or create as applicable:

- reusable resident interaction service/layer
- local LLM adapter boundary or discovery hook
- deterministic fallback mode
- resident conversation turn persistence
- conversation forget/redaction mechanism
- generic resident interaction API/server handler conventions
- resident interaction/API surface inspection command or endpoint
- resident surface extension mechanism/template
- resident interaction template
- WP-0126 report Markdown and JSON
- validation recipe registration for WP-0126
- validation reports/runtime JSON for WP-0126
- regenerated production-readiness and coverage artifacts
- `collaboration/work_packages/completions/WP-0126_codex_done.json`

## WP-0126 Self-Validation Recipe

Add a recipe for WP-0126 that verifies:

- resident interaction framework report exists
- JSON companion parses
- resident interaction template exists
- resident interaction/API surface template or registry exists
- interaction layer can process an Alfred-style prompt
- conversation turn persistence is present
- forget/redaction mechanism is present
- local LLM adapter/discovery status is reported
- deterministic fallback status is reported
- authority metadata is attached to interaction records
- resident interaction/API surface inspection is available for Alfred
- surface extension mechanism is documented
- WP-0122, WP-0123, WP-0124, and WP-0125 remain passing
- production-readiness validation executes successfully
- WP-0126 receipt is complete

Use cross-platform Python checks only.

## Completion Artifact

Create:

`collaboration/work_packages/completions/WP-0126_codex_done.json`

It must include:

- `work_package_id = WP-0126`
- `codex_status = done`
- `completed_at`
- `branch`
- `summary`
- resident interaction framework changes
- local LLM adapter/discovery status
- deterministic fallback status
- conversation persistence path
- forget/redaction mechanism
- authority handling
- resident interaction/API surface inspection path
- resident surface extension mechanism
- resident interaction template path
- tests run
- validation commands run
- known limitations
- recommended next action
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria

WP-0126 is complete when the Estate has a reusable, tested resident interaction framework that can support Alfred and future residents through local-first UI chat, local LLM routing, persisted institutional conversation memory, Steward-controlled forgetting/redaction, authority-aware interaction boundaries, and inspectable/extensible resident interaction/API surfaces.

## Merge Class

Class A. Escalate only if implementation requires changing Steward authority, resident authority, server exposure/security policy, memory/redaction policy, or production-readiness semantics.
