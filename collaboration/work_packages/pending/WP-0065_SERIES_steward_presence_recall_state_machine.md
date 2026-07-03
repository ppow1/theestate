# SERIES TASK WP-0065 — Steward Presence and Recall State Machine

## Codex Command
Read `collaboration/work_packages/pending/WP-0065_SERIES_steward_presence_recall_state_machine.md` and do exactly what it says.

## Mission
Implement the Steward Presence and Recall State Machine so Alfred and the Operations Center can distinguish between normal operation, Steward-away operation, recall-needed state, recalled state, acknowledged state, and resumed operation.

## Scope
Create a bounded local state model for Steward presence and recall state using existing Estate artifacts where available:

- Steward Recall Decision Model
- Recall Audit Log
- Notification Router outputs
- Gotify delivery reports
- Notification Center workspace outputs
- Morning Briefing outputs
- Operations Center status bar/Mission Control integration points

Possible outputs:

- `runtime/steward/steward_presence_state.json`
- `operations/steward/steward_presence_state.md`
- helper module such as `src/estate/core/steward_presence.py` if consistent with existing patterns

## State Model
Support at least:

- present
- away
- autonomous_operation
- recall_requested
- recall_sent
- recall_acknowledged
- resumed
- unknown

## Behavior Requirements
- State transitions must be explicit and auditable.
- Missing evidence should produce `unknown` or warning states, not fabricated certainty.
- Alfred may use this state to decide whether to continue operating or request recall.
- The Operations Center should be able to display current state and transition history where feasible.
- Do not notify the Steward directly from this package unless an existing safe router call already exists and is explicitly invoked by the Steward.

## Constraints
Do not create biometric or passive surveillance. Do not track the Steward outside Estate-approved signals. Do not bypass Alfred or recall authority. Do not implement mobile app behavior. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify valid transitions, invalid transition handling, missing evidence, unknown state, recall requested, recall acknowledged, resumed operation, and JSON/Markdown output generation where implemented.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0065_codex_done.json` using the standard completion schema.

## Merge Class
Class A unless implementation changes recall authority or personal tracking policy; escalate to Class B if those boundaries change.
