# WP-4039 Staged Room Contract

This directory contains an uninstalled coordination core for governed multi-resident conversation rooms. A room is a shared discussion surface only; it is not an Office, scheduler, command authority, model provider, transcript database, or replacement for individual resident chats.

## Lifecycle

The staged Python module exposes deterministic functions: `create_room`, `invite_participant`, `accept_participant`, `decline_participant`, `remove_participant`, `mark_unavailable`, `set_room_mode`, `submit_user_turn`, `plan_resident_turns`, `record_resident_turn`, `pause_room`, `resume_room`, `archive_room`, `room_snapshot`, and read-only `office_projection`.

## Membership and identity

Participants are only eligible to speak after explicit invitation and acceptance. Supported participant states are invited, accepted, declined, unavailable, removed, and suspended. Registry presence is never consent. Resident turns carry resident ID, display name, role/office metadata, room ID, source user turn ID, turn order, response status, model metadata supplied by adapters, fallback status, context omissions, and authority-disclaimer metadata.

## Modes and speaking policy

Supported modes are roundtable, targeted, moderated, consultation, and quiet_observer. Speaking order is deterministic by explicit ordered list, alphabetical resident display name, role priority, normalized target override, or moderator-selected order with rationale. The module enforces a maximum response count per user turn and does not permit recursive autonomous discussion.

## Context boundaries

Shared room context and resident-specific packets remain separate. Prohibited private context classifications such as Evelyn private relationship content, HR-private records, security-private records, and workforce-private records are omitted unless a caller explicitly marks authorized promotion. Transcript references point to canonical stores; transcript bodies are not duplicated.

## Authority boundaries

The core does not execute privileged actions, contact model providers, change active routing, grant access, auto-invite residents, or represent staged work as live. `execute_privileged_action` returns a blocked result for privileged verbs.
