# Operational Campaign Engine

The Operational Campaign Engine gives the Operations Manager a governed way to advance an approved multi-step initiative without requiring the Steward to trigger every routine step manually.

## Scope

Campaigns are not an alternate authority system. A campaign must carry pre-approved delegated authority before the runtime will start, pause, resume, advance, block, cancel, or complete it. Campaign completion remains separate from institutional acceptance.

## Campaign model

`estate.core.operational_campaigns` represents an approved campaign as:

- campaign goals and tempo;
- ordered phases with dependencies;
- entry criteria, exit criteria, evidence requirements, delegated authority, blockers, holds, and escalation conditions;
- approved authority including allowed directors, allowed actions, allowed phase ids, and routine advancement limits;
- persisted campaign state and typed event history.

## Runtime behavior

`OperationalCampaignRuntime` persists state under `runtime/operational_campaigns/`:

- `campaigns.json` stores campaign state;
- `events.jsonl` stores event history;
- `status.json` surfaces next eligible actions, blockers, tempo, and exceptions.

The runtime supports:

- `start`
- `pause`
- `resume`
- `advance`
- `block`
- `cancel`
- `complete`

## Integration seams

Routine campaign advancement uses existing seams instead of bypassing Estate controls:

1. **Traffic Controller constraints**: every Operations Manager action is checked against pre-approved `CampaignAuthority`. Non-routine phases or phases with escalation conditions produce a `RecommendedAction` escalation instead of improvising.
2. **Provider recommendation**: routine provider work is evaluated through `evaluate_provider_routing_recommendation` before dispatch metadata is created.
3. **Dispatch**: routine work is enqueued with `enqueue_dispatch_request`; the runtime does not call live providers directly.
4. **Scheduler**: the runtime is deterministic and can be called by the existing Operations Scheduler as a bounded cycle target.
5. **Validation**: phase validation commands and evidence requirements are carried into dispatch metadata and completion checks.

## Acceptance notes

- Eligible routine phases can advance automatically through dispatch.
- Movement remains governed by Traffic Controller-style authority checks.
- Provider work uses dispatch and provider recommendation seams.
- Governance or authority exceptions escalate as recommended actions.
- Completion sets `institutional_acceptance` to `false`; Steward acceptance is separate.
