# CAMPAIGN-0681 Grace Operational Coordination Contract

Status: WP-0694 implementation contract
Authority: Derived from the accepted Office of Operations and CAMPAIGN-0681 authority boundaries

## Purpose

`estate.core.grace_operations_runtime.build_operational_coordination_view` extends
the existing Grace runtime with a read-only projection of the WP-0692 momentum
observer and WP-0693 blocker classifier. It does not create an Operations Center
state store, queue, scheduler, mailbox, or decision authority.

## Inputs and precedence

The view consumes:

1. the observation-only campaign momentum object;
2. optional blocker classifications keyed by canonical campaign or package ID;
3. evidence references, warnings, dependency state, and follow-up destinations
   already supplied by those canonical producers.

The adapter copies its inputs and performs no source mutation. A momentum input
that is not explicitly observation-only, lacks canonical identity, lacks evidence,
or carries stale or contradictory warnings fails closed. A protected blocker or
protected/acceptance state always remains a protected stop.

## Grace view

Each package row exposes:

- observed state and dependency satisfaction;
- canonical evidence and freshness warnings;
- blocker class and severity;
- recommended next action and proper office or authority lane;
- an explicit action class;
- whether bounded coordination is permitted;
- whether the item is a protected stop; and
- `authorizes_action: false`.

The ordering highlights failed, blocked, protected, indeterminate, and degraded
items before eligible work. This is presentation order only. Grace does not set
Engineering priority through the view.

## Coordination request

`create_coordination_request` produces the existing repository-message envelope
only for an evidence-backed item whose action class is `coordinate`. The caller
must supply the canonical destination name, employee ID, and mailbox ID; the
adapter never guesses them from a title. The envelope requires acknowledgement,
links the work package and evidence, and states that it grants no execution or
decision authority.

`record_coordination_request` writes that envelope only to the canonical
`collaboration/messages/` directory. It refuses duplicate IDs, non-coordination
message types, non-Grace sources, and any request that claims to authorize action.
It does not route the message, rebuild mailbox indexes, acknowledge it, dispatch
work, or mutate campaign state. Those remain later integration and office actions.

Representative recorded request:

```json
{
  "id": "msg_grace_20260718_wp0694_coordination",
  "source": "Grace",
  "source_employee_id": 12,
  "destination": "Office of the Chief Architect",
  "destination_employee_id": 9,
  "destination_mailbox_id": 9,
  "message_type": "coordination_request",
  "related_work_package": "WP-0694",
  "requires_ack": true,
  "operational_context": {
    "action_class": "coordinate",
    "authorizes_action": false
  }
}
```

## Authority boundary

Grace may observe, recommend, coordinate delegated operations, request action
through existing mechanisms, and escalate. Grace may not assign personnel,
approve architecture, accept Engineering work, merge, deploy, spend, make a
protected decision, or convert acknowledgement into work completion. The view and
message envelope are evidence and transport inputs, not authority records.

## Reuse and duplicate avoidance

- Momentum truth: `campaign_momentum_observer.py`.
- Blocker truth: `operational_blocker_classifier.py`.
- Action classes: `operational_action_taxonomy.py`.
- Grace runtime: `grace_operations_runtime.py`.
- Communication transport: existing `collaboration/messages/` envelope and mailbox
  discovery mechanisms.
- Dispatch: existing Dispatch only; WP-0694 adds no dispatch mutation.

No replacement registry, dashboard authority, message bus, state store, scheduler,
validator, acceptance path, office, or protected-decision mechanism is introduced.
