# Conference Room Moderator and Lifecycle Operator Guide

## Canonical artifacts

The governed configuration is `config/conference_room_config.json`; its initial moderator is Alfred (`RES-000001`). Session records use `conference_room_session.v1` and are stored locally under `runtime/conference_room/sessions/<sha256-session-id>.json`. The filename deliberately does not disclose the Open WebUI session identifier. Configuration changes are audited in `runtime/conference_room/config_audit.jsonl`, and timestamped configuration backups are retained beside the configuration.

## Change and verify the default

Run these as separate PowerShell invocations (each supplied example starts by clearing the host):

```powershell
CLS
./operations/scripts/Set-EstateConferenceModerator.ps1 -Resident Marie
```

```powershell
CLS
./operations/scripts/Set-EstateConferenceModerator.ps1 -Verify
```

Names and canonical resident IDs are accepted through the canonical registry. Unknown and inactive residents fail closed. The write is atomic. **No Resident Gateway restart is required** because configuration is loaded when each new conference is created. Existing conferences retain their creation-time moderator and current state.

## Roll back

The change command reports its timestamped `.bak` path. Restore without hand-editing JSON by invoking the same supported command with the former resident shown in its output:

```powershell
CLS
./operations/scripts/Set-EstateConferenceModerator.ps1 -Resident Alfred
```

## Inspect and accept

Open WebUI responses include an `estate.conference_state` diagnostic envelope containing the room ID, roster, moderator, backup, lifecycle history, and audit events. Ordinary `Who is currently present?` and `Who is the moderator?` requests provide conversation-safe answers without repository paths.

Manual acceptance:

1. Open a new `estate/conference-room` chat and verify only Steward and the configured moderator appear.
2. Say `Invite Grace, Helen, and Judy.` and verify three separately attributed acknowledgements and no other resident turn.
3. Say `Make Helen moderator and keep Alfred as a regular participant.`, then inspect moderator and roster.
4. Say `Make Grace the backup moderator.`, then `Helen, leave the conference.`; verify Grace's audited succession.
5. Address Grace and verify departed Helen receives no context. Attach an image and verify only the planned active resident receives the bounded visual summary through the existing gateway adapter.
6. Change the default to Marie, create a new chat, verify Marie opens it, and restore Alfred with the rollback command above.

Common errors are an unknown/inactive registry entry or an attempt to assign moderation/backup to someone who has not joined. These are rejected without partial state changes. If a moderator leaves without a backup, moderator-dependent operations pause for Steward direction. Non-Open-WebUI compatibility calls without a session ID are ephemeral and cannot be relied upon for chat continuation.

## Known limitations

Intent recognition intentionally covers governed command phrases and canonical resident names rather than unconstrained semantic interpretation. Invitations acknowledge through an independently attributed resident dispatch in the same HTTP response. There is no cross-session migration command; existing rooms are deliberately immutable with respect to later default changes.
