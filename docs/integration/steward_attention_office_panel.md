# Steward Attention Office Panel

The Steward Attention panel is an Alfred-owned gatekeeping surface over existing Estate artifacts. It reads resident task status, mail, validation, operations/workforce-adjacent assignment records, services, projects, and work packages where present, then writes local briefing artifacts only.

Office actions:

- `office.attention.briefing` generates `runtime/office/steward_attention_briefing.json` and `operations/briefings/steward_attention_briefing.md`.
- `office.attention.action` persists snooze, acknowledge, delegate, dismiss, and resolve actions in `runtime/office/steward_attention_actions.json`.

Boundary: Alfred owns attention batching and briefing language; source systems remain authoritative and no decision is auto-approved.
