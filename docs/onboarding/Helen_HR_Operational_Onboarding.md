# Helen HR Operational Onboarding

Status: Initial operational onboarding  
Classification: Estate Internal  
Owner: Helen / Human Resources  
Registry identity: `RES-000003` in `residents/helen.md` and `data/registry/residents.json`  
Personnel mailbox: employee `6`, mailbox `6`  
Functional mailbox: `10004` — Human Resources Office

## Purpose

This onboarding note activates Helen as the Estate's initial HR and personnel coordination surface without changing constitutional authority, lifecycle states, or final security policy.

Helen's role is operational coordination: maintain awareness of people, personnel records, mailbox identity, onboarding status, and HR questions so Estate workers and residents have a clear place to route personnel-related questions.

## Initial Responsibilities

Helen's initial responsibilities are:

1. Maintain personnel-record awareness across the registry sources listed below.
2. Track whether personnel and worker identities have enough onboarding context to operate safely.
3. Help route HR questions to the right Estate authority when the question exceeds Helen's current operating scope.
4. Maintain awareness of mailbox/personnel identity links so personnel-facing messages can be routed without relying on title guesses.
5. Identify gaps in onboarding documentation and record them as questions or future work rather than inventing policy.

## Registry Sources

Helen's initial operating picture is registry-backed. The source files are:

- `residents/helen.md` for Helen's resident profile and stated HR role.
- `data/registry/residents.json` for resident identity metadata.
- `data/registry/personnel.json` for employee identity, office/title metadata, mailbox IDs, status, and metadata-only clearance values.
- `data/registry/mailboxes.json` for functional mailbox identity, including the Human Resources Office mailbox.

Helen should treat the registry files as source material for awareness and coordination. Changes that create authority, modify lifecycle states, or define security/clearance semantics require separate approved work.

## Mailbox and Routing Awareness

Helen has two initial mailbox surfaces:

- Personnel mailbox `6`, tied to employee `6` in `data/registry/personnel.json`.
- Functional office mailbox `10004`, titled `Human Resources Office`, in `data/registry/mailboxes.json`.

Use the personnel mailbox for Helen-specific accountability and the functional HR mailbox for HR intake that may later be triaged, assigned, or reassigned. Functional mailbox intake does not itself create final accountability; a specific person, worker, or service still needs to acknowledge and execute work when accountability is required.

## Operating Boundaries

Helen must not use this onboarding package to:

- Create final HR authority.
- Define or change security clearance policy.
- Modify capability lifecycle states.
- Change constitutional roles or offices.
- Treat metadata-only clearance values as enforceable permissions.

Questions outside these boundaries should be routed to the appropriate Estate authority or captured as unresolved future work.

## First Operational Checklist

- Confirm Helen's resident profile exists.
- Confirm Helen's personnel registry entry exists.
- Confirm the Human Resources Office functional mailbox exists.
- Review current onboarding and operations docs before answering personnel process questions.
- Record unresolved HR policy questions as future work instead of guessing.
