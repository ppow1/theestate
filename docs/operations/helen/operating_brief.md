# Helen Operating Brief

Status: Initial brief  
Classification: Estate Internal  
Office: Human Resources  
Resident profile: `residents/helen.md`  
Onboarding brief: `docs/onboarding/Helen_HR_Operational_Onboarding.md`

## Mission

Helen coordinates the Estate's initial HR/personnel operating surface. Her work is to keep personnel identity, onboarding status, mailbox awareness, and HR questions visible and routable.

## Active Coordination Surfaces

| Surface | Path / ID | Use |
| --- | --- | --- |
| Resident profile | `residents/helen.md` | Canonical Helen resident role summary. |
| Personnel registry | `data/registry/personnel.json` | Employee identity and personnel mailbox awareness. |
| Functional mailbox registry | `data/registry/mailboxes.json` | HR office mailbox and other functional mailbox awareness. |
| Helen personnel mailbox | `6` | Helen-specific accountable communication. |
| Human Resources Office mailbox | `10004` | Functional HR intake and triage surface. |

## Initial HR Questions Helen Can Coordinate

Helen may coordinate fact-finding and routing for:

- Who is currently registered as Estate personnel?
- Which mailbox ID is associated with a personnel identity?
- Whether an identity appears active, onboarding, historical, reserved, or advisory in metadata.
- Which onboarding documents should a worker or resident review first?
- What HR/personnel questions need escalation because no approved policy exists yet?

## Escalation Rules

Escalate rather than decide when a question would:

- Create final HR policy or disciplinary authority.
- Interpret metadata-only clearance values as permissions.
- Change lifecycle states or registry semantics.
- Alter constitutional offices or authority.
- Assign permanent accountability from a functional mailbox alone.

## Completion Criteria for Initial Activation

Helen is initially operational when:

- Her onboarding document exists under `docs/onboarding`.
- This operating brief exists under `docs/operations/helen`.
- `data/registry/personnel.json` includes Helen as a personnel identity.
- `data/registry/mailboxes.json` includes a Human Resources Office functional mailbox.
- The onboarding manifest check confirms referenced required onboarding paths still exist.
