# Engineering Communication and Escalation Standard v1

Status: Gate C operational contract  
Canonical quick reference: `AI_COMMUNICATION_HINTS.md`

Repository-backed messages are the durable inter-office communication mechanism defined by `AI_COMMUNICATION_HINTS.md`.

## Routing matrix

| Need | Mechanism | Rule |
|---|---|---|
| durable inter-office notice/decision request | `collaboration/messages/*.json` | resolve identities through personnel/mailbox registries; message is authoritative communication, not package state |
| find office messages | `collaboration/mailboxes/index.json` | discovery only; rebuild with canonical mailbox-index command |
| campaign scope/gates | `collaboration/campaigns/*.md` plus decision records | amendments preserve prior version and authority |
| executable scope/status evidence | work package, canonical PTM record, comments/receipt | receipt reports delivery; it cannot self-accept |
| daily attention | Daily Board/Active Work existing surfaces | link canonical item; board does not become queue/state |
| valuable deferred idea | Parking Lot board and detailed PL item | capture is explicit non-action until promoted |
| architecture/package/gate acceptance | Chief Architect decision communication | cite exact evidence/commit/PR; absence means awaiting acceptance |
| constitutional, priority, safety, or exception decision | Steward escalation | never use Steward for routine scheduling |

Use Alfred for routing, discovery, summaries, reminders and acknowledgement visibility. Grace coordinates momentum and blocker escalation. Helen receives staffing/capability and reflection-readiness needs. Neither a routed message nor acknowledgement changes canonical lifecycle state.

## Required message content

Follow `AI_COMMUNICATION_HINTS.md` envelope fields and add: literal campaign/package/attempt IDs; subject type (`information`, `action_request`, `decision_request`, `blocker`, `handoff`, `acceptance_request`); canonical source/evidence links and digests; requested actor/action; authority basis; due/review trigger; blocker class/age if applicable; acknowledgement requirement; and safe fallback. Never paste secrets or use chat as the sole record.

## Copy-ready patterns

**Operational handoff**

> `[HANDOFF] CAMPAIGN_ID / WP_ID / ATTEMPT_ID — branch OWNER at COMMIT; canonical state STATE (SOURCE); validated evidence LINKS; unresolved BLOCKERS; next authorized action ACTION by ACTOR after PREREQUISITES. Acknowledge ownership; this message does not change PTM, branch, validation, or acceptance state.`

**Chief Architect decision/acceptance request**

> `[DECISION REQUEST] CAMPAIGN_ID / WP_ID — decide DECISION under AUTHORITY. Review PR/COMMIT, evidence manifest, verdicts, hazards, and alternatives at LINKS. Current state remains AWAITING_ACCEPTANCE; requested outcome is accept/reject/return with decision record.`

**Blocker escalation**

> `[BLOCKER: CLASS, AGE] CAMPAIGN_ID / WP_ID — observed FACT at TIME from SOURCE. Impact: IMPACT. Owner: OWNER. Attempts/evidence: LINKS. Decision or action requested from ACTOR by TRIGGER. Work fails closed at STATE; no constraint has been waived.`

**Provider failure / transfer**

> `[EXECUTION INTERRUPTION] CAMPAIGN_ID / WP_ID / OLD_ATTEMPT — provider/run RESULT and evidence LINKS. Branch OWNER/COMMIT remains unchanged. Safe stop: STATUS. Proposed new attempt/provider requires fresh eligibility, selection, Dispatch, and explicit branch reassignment where applicable.`

**Steward exception escalation**

> `[STEWARD DECISION] CAMPAIGN_ID / WP_ID — protected/priority/constitutional exception QUESTION; authority basis BASIS; options and consequences OPTIONS; Chief Architect/Grace status LINKS. Routine scheduling is not requested.`

After creating a message, rebuild mailbox discovery with `PYTHONPATH=src python -m estate.cli.main mailbox-index --json` when operating locally. Record resulting lifecycle decisions in their canonical system; do not leave the decision only in mail.
