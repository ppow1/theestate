# WP-4039 — Multi-Resident Conversation Room Core

Status: Pending
Execution Mode: PARALLEL-STAGED
Owner: Office of Character Architecture / Resident Runtime Implementation Stream
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate resident collaboration capability

## Concurrency

This package is safe to execute concurrently with WP-4038, WP-4040, and WP-4041.

All implementation work must remain isolated under:

`collaboration/workstreams/WP-4039/`

Do not modify active gateway, CLI, Office, mailbox, Dispatch, resident registry, model-control, or shared runtime files in this package.

Staged work is not installed work.

## Depends On

- Installed resident runtime foundations from WP-4031.
- Active residents and gateway patterns established by WP-4034 and WP-4035.
- Existing session, context assembly, capability, delegation, and model-assignment contracts.

WP-4036 through WP-4038 may be in progress or merged. This package must not require Evelyn to be live in order to complete its staged contract.

## Objective

Create a deterministic, staged core for governed multi-resident conversation rooms so the Steward can converse with multiple Estate residents in one shared thread without flattening them into one generic voice, losing private-chat separation, or creating a second chat platform.

The staged core must support:

- explicit room creation;
- participant invitations and removals;
- resident-specific turn generation;
- deterministic speaking order;
- targeted questions to one or more residents;
- optional resident-to-resident responses;
- room-level context with resident-specific filtered context;
- transcript references without duplicating existing canonical transcript storage;
- identity-preserving attribution;
- private-room classification and access boundaries;
- truthful blocked, unavailable, declined, and deferred states;
- resumable room sessions;
- Open WebUI-compatible future integration contract;
- audit-safe metadata;
- no automatic authority expansion.

## Governing Principle

A conversation room is a coordination surface, not a constitutional office, command authority, scheduler, queue, or replacement for individual resident chats.

Separate resident chats remain first-class.

Multi-resident rooms add shared discussion; they do not erase private continuity, office boundaries, or resident identity.

## Required Staged Artifacts

Create the following under `collaboration/workstreams/WP-4039/`:

- `src/multi_resident_room.py`
- `tests/test_multi_resident_room.py`
- `schemas/conversation_room_v1.json`
- `schemas/conversation_turn_v1.json`
- `fixtures/sample_room.json`
- `fixtures/sample_turns.json`
- `room_contract.md`
- `integration_notes.md`
- `rollback_notes.md`
- `install_manifest.json`

Also create:

- `collaboration/work_packages/completions/WP-4039_codex_done.json`

The completion receipt must clearly state that the work is staged and uninstalled.

## Core Data Model

Define a room record with at least:

- `schema_version`
- `room_id`
- `display_name`
- `classification`
- `created_by`
- `created_at`
- `status`
- `participants`
- `resident_participants`
- `human_participants`
- `room_purpose`
- `room_mode`
- `speaking_policy`
- `context_policy`
- `transcript_reference`
- `session_reference`
- `active_topic`
- `pending_questions`
- `audit_metadata`

Participant records must distinguish:

- invited;
- accepted;
- declined;
- unavailable;
- removed;
- suspended.

No resident may be treated as present merely because their identifier appears in a request.

## Room Modes

Support at least:

1. `roundtable` — each accepted resident may respond in deterministic order.
2. `targeted` — only explicitly addressed residents respond.
3. `moderated` — a named moderator proposes speaking order without granting authority.
4. `consultation` — one primary resident responds and may request bounded input from others.
5. `quiet_observer` — selected participants receive room context but do not respond unless invited.

Mode changes must be explicit, recorded, and reversible.

## Speaking Policy

Implement deterministic speaking-order logic.

The policy must support:

- explicit ordered list;
- alphabetical resident order;
- role-priority order supplied by the caller;
- targeted override;
- moderator-selected order with recorded rationale;
- decline, unavailable, and deferred outcomes.

Do not use hidden model discretion to decide who speaks.

Do not allow residents to monopolize the room through recursive self-invocation.

Enforce a bounded maximum number of resident responses per user turn.

## Identity Preservation

Every generated turn must carry:

- resident ID;
- display name;
- office/role metadata when available;
- source room ID;
- source user-turn ID;
- turn order;
- response status;
- model/provider metadata when supplied by an adapter;
- fallback status;
- context omissions;
- authority disclaimer metadata.

The runtime must never merge several resident responses into one unattributed voice.

## Context Boundaries

Build a staged interface that accepts caller-supplied resident context packets.

The room core must:

- maintain shared room context separately from resident-private context;
- allow each resident to receive a filtered view;
- record omitted or prohibited context;
- never copy private Evelyn relationship-layer content into a shared room by default;
- never copy private HR, security, or workforce records into the room without explicit authorized promotion;
- preserve source references;
- avoid storing duplicate transcript bodies when a canonical transcript reference exists.

## Targeted Addressing

Support user forms equivalent to:

- “Alfred, answer this.”
- “Helen and Grace, weigh in.”
- “Everyone, give me your view.”
- “Ingrid, review the privacy implications after Grace proposes a plan.”

The staged core may receive normalized target IDs from a future adapter. It does not need to implement natural-language parsing unless that can be done deterministically and without modifying active code.

## Resident-to-Resident Interaction

Support bounded resident-to-resident turns only when explicitly enabled for the room or requested by the human participant.

Requirements:

- no autonomous infinite dialogue;
- no hidden side conversations;
- no authority transfer through conversation;
- every resident-to-resident turn remains visible in the room transcript;
- maximum depth and maximum turn count are explicit;
- a resident may decline or defer;
- the human may interrupt or stop the exchange.

## Session and Resume

Provide deterministic room lifecycle functions such as:

- `create_room`
- `invite_participant`
- `accept_participant`
- `decline_participant`
- `remove_participant`
- `set_room_mode`
- `submit_user_turn`
- `plan_resident_turns`
- `record_resident_turn`
- `pause_room`
- `resume_room`
- `archive_room`
- `room_snapshot`

Use stable IDs and idempotency/resume tokens where appropriate.

Do not create a second transcript database.

## Safety and Authority Boundaries

The staged core must not:

- execute privileged actions;
- appoint, hire, approve, merge, dispatch, spend, or change policy;
- grant a resident additional information access because they share a room;
- infer participant consent from registry presence;
- auto-invite every active resident;
- expose private resident memory by default;
- create an autonomous background discussion loop;
- contact model providers directly;
- modify active gateway routing;
- represent staged work as live.

## Future Open WebUI Integration Contract

Document how a future adapter can expose a room as an OpenAI-compatible model or conversation surface while keeping room membership and routing inside the Estate.

The contract should anticipate a model identifier such as:

`estate/room/<room-id>`

or a controlled generic endpoint such as:

`estate/conference-room`

Do not hard-code the final identifier as constitutional truth.

The future adapter must be able to return clearly attributed resident responses in a format Open WebUI can display without losing speaker identity.

## Office and UI Projection

Provide a staged, read-only projection payload including:

- room name;
- status;
- classification;
- participants and participation state;
- current mode;
- active topic;
- pending invited speakers;
- last activity;
- blocked reasons;
- transcript/session references;
- safe actions available to the current caller.

Do not create a new Office tab or modify active Office surfaces.

## Deterministic Tests

Tests must cover at least:

- room creation with stable identity;
- explicit invitation and acceptance;
- no implicit participation;
- deterministic roundtable order;
- targeted participant selection;
- participant decline and unavailable states;
- bounded response count;
- visible resident attribution;
- separate shared and resident-specific context;
- prohibited private-context omission;
- pause/resume behavior;
- idempotent retry;
- resident-to-resident depth limits;
- archive behavior;
- no privileged action execution;
- Office/Open WebUI-safe projection;
- staged/uninstalled status.

Tests must not call live models, network services, Open WebUI, Ollama, or external providers.

## Install Manifest

`install_manifest.json` must include:

- work package ID;
- execution mode;
- staged status;
- all staged artifacts;
- proposed future active install paths;
- shared-file conflict risks;
- required source packages;
- validation command;
- rollback instructions;
- explicit `staged_work_is_installed: false`.

Proposed future install targets may include a new canonical module such as:

`src/estate/core/multi_resident_conversation.py`

but WP-4039 must not write that active file.

## Acceptance Criteria

WP-4039 is complete when:

1. The staged room core is deterministic and fully tested.
2. Multiple residents retain distinct identity and attribution.
3. Room membership is explicit and consent/state aware.
4. Private and shared context remain separated.
5. Resident-to-resident interaction is bounded and visible.
6. No active shared runtime or gateway files were modified.
7. The install manifest and integration contract are complete.
8. The completion receipt truthfully marks the work staged and uninstalled.

## Completion Report

The Codex completion response must summarize:

- files created;
- tests run and exact results;
- staged status;
- future integration targets;
- known conflicts or dependencies;
- confirmation that no active gateway or runtime integration was performed.
