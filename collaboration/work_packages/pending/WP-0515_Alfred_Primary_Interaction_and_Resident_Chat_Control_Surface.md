# WP-0515 - Alfred Primary Interaction and Resident Chat Control Surface

Status: Proposed
Priority: High
Owner: Chief Architect #5
Classification: Estate Internal

## Mission

Make Alfred's Office page interaction-first and ensure resident chat is a real, reliable control surface.

## Required Controls and Behavior

- Place the Alfred composer at the top of the page.
- Focus the composer on page entry where appropriate.
- Enter sends; Shift+Enter inserts a new line.
- The Send button invokes the same canonical handler as Enter.
- Support stop/cancel only where the current resident runtime supports it truthfully.
- Support clear/forget conversation through existing governed behavior.
- Open and inspect conversation history.
- Retry failed local responses without duplicating successful turns.
- Request Alfred duties and briefings through canonical handlers.
- Show model, runtime, and provider status truthfully.
- Provide a launch or integration path to Open WebUI when available while retaining working Office text access.

## Boundaries

Do not create a second resident runtime, conversation registry, provider router, or chat service. Do not fabricate streaming, cancellation, or model state.

## Testing

Prove browser-to-handler-to-conversation-state-to-render behavior for send, Enter-to-send, Shift+Enter, retry, forget, history, and briefing requests. No live external provider calls in deterministic tests.

## Acceptance Criteria

1. Alfred chat is the primary interaction on the page.
2. Enter-to-send works reliably.
3. Conversation actions persist and render after refresh.
4. Failures are visible and recoverable.
5. No decorative or fake controls remain.
6. Focused tests and WP-0515 validation pass.

## Completion Receipt

```text
collaboration/work_packages/completions/WP-0515_codex_done.json
```

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0515_Alfred_Primary_Interaction_and_Resident_Chat_Control_Surface.md and do exactly what it says.
```
