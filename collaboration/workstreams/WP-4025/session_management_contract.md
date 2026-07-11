# WP-4025 Staged Resident Session Management Contract

This staged contract defines the install handoff for durable resident session management and conversation recovery.  It is intentionally uninstalled and must be reviewed by WP-4031 before integration with `src/estate/core/resident_interaction.py`, resident gateway APIs, Open WebUI adapters, continuity records, or Office surfaces.

## Required Behaviors Staged

- Create, name, rename, resume, archive, forget, and recover resident sessions.
- Validate canonical `RES-*` resident identity for every session operation and reject identity drift during recovery.
- Link sessions to an active operational cycle and persist that linkage in checkpoints.
- Persist conversation checkpoints and references to existing resident chat records without creating a second transcript store.
- Recover safely after service restart or interrupted registry writes by using atomic registry replacement and quarantining stray temporary files.
- Map Open WebUI conversation identifiers to private resident sessions.
- List session status deterministically while excluding archived and forgotten sessions from active memory by default.
- Preserve compatibility with existing resident chat records through `conversation_record_refs` pointers.

## Privacy and Office Surface Boundary

Staged sessions are private resident runtime state.  Public Office surfaces may display status metadata only after installation review, and must not expose private session content.  Forgotten sessions retain audit events but drop checkpoint, Open WebUI, and conversation-record references.

## Install Handoff

WP-4031 should install this by wiring the staged `ResidentSessionStore` semantics into the shared runtime store and gateway endpoints after conflict review.  The staged module should not be imported by production paths until that handoff is complete.
