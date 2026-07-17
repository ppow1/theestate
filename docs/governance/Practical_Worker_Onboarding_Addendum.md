# Practical Worker Onboarding Addendum

Status: Canonical Governance Addendum  
Owner: Chief Architect  
Audience: New AI workers, Chief Architect sessions, Alfred-adjacent workers, local CLI workers, documentation workers, and future operators.

## Purpose

This addendum captures practical onboarding lessons discovered during Chief Architect #6 onboarding.

The purpose is to reduce Steward workload, prevent incomplete worker recovery, and make future onboarding less dependent on fragile transport assumptions.

This document supplements:

- `AI_START_HERE.md`
- `AI_HINTS.md`
- `docs/governance/Estate_Orientation_Handbook.md`
- `docs/governance/Estate_Vision_and_Architecture.md`
- `docs/governance/Estate_Manual.md`
- `docs/collaboration/Estate_Collaboration_Layer_v1.md`
- `docs/collaboration/Estate_Collaboration_Standard_v1.md`
- `docs/collaboration/Local_Execution_Adapter_Protocol_v1.md`

## 1. Direct Document Delivery

When onboarding a new worker, provide the required onboarding corpus directly whenever practical.

Preferred delivery methods:

1. Local CLI access to the Estate repository.
2. Direct document upload into the worker conversation.
3. Local filesystem access.
4. GitHub repository access when direct delivery is unavailable.

GitHub remains useful, but onboarding should not depend on a worker discovering the correct files through GitHub search or partial connector reads.

## 2. Repository Identity

Every onboarding package should explicitly identify the active Estate repository and local path.

Current canonical values:

- GitHub repository: `ppow1/theestate`
- Local repository path: `A:\theestate`
- Canonical entry point: `AI_START_HERE.md`

Workers should not be required to infer the repository owner, repository name, or local path.

## 3. Required Reading Package

A complete onboarding package should include, or explicitly point to, the current canonical reading set:

- `AI_START_HERE.md`
- `AI_HINTS.md`
- `docs/governance/Estate_Orientation_Handbook.md`
- `docs/governance/Estate_Vision_and_Architecture.md`
- `docs/governance/Estate_Manual.md`
- `docs/governance/visuals/README.md`
- `docs/governance/Capability_Lifecycle_States_v1.md`
- `docs/collaboration/Estate_Collaboration_Layer_v1.md`
- `docs/collaboration/Estate_Collaboration_Standard_v1.md`
- `docs/collaboration/Local_Execution_Adapter_Protocol_v1.md`

Additional role-specific reading should be listed in the worker package.

## 4. Worker Identity Assignment

When a worker receives an institutional role, onboarding must explicitly assign:

- Office
- Occupant designation
- Employee ID
- Mailbox ID
- Work package number range, if applicable

Workers should not infer these values from screenshots, adjacent worker identities, or conversation history.

Example:

- Office: Chief Architect
- Occupant: Chief Architect #6
- Employee ID: 6
- Mailbox ID: 6
- Work package range: `WP-0600` through `WP-0699`

## 5. Mailbox Orientation

Mailbox use is part of institutional onboarding.

Workers with local Estate access should be told:

- where mailbox policy lives,
- where mailbox state lives,
- how to retrieve messages,
- how to send replies,
- how read/unread or lifecycle state is represented,
- whether the target recipient is expected to be running or only able to receive durable messages.

A mailbox is an Estate communication resource. It is not a GitHub feature and not a ChatGPT conversation artifact.

The mailbox transport may be GitHub, local filesystem, CLI, or another future adapter. The mailbox identity and institutional communication rules remain stable.

## 6. Parking Lot Orientation

Workers should be introduced to the Parking Lot during onboarding.

They should understand that the Parking Lot is:

- a governed holding area for deferred ideas,
- not conversation memory,
- not the active work package queue,
- not a substitute for architecture review,
- a place where useful but non-current ideas can be preserved until promoted, rejected, or retired.

Workers should be given the canonical Parking Lot path and expected entry format before being asked to park items.

Current known path:

- `operations/boards/parking_lot.md`

## 7. Transport Independence

The Collaboration Layer is transport independent.

GitHub is an adapter. It is not the Communication Bus.

Local filesystem and CLI execution are expected to become primary operational paths where practical.

Workers should understand the distinction between:

- institutional concept,
- implementation transport,
- local authoritative state,
- promoted shared state.

Changing transport does not change the Office, Occupant, Implementation, State model.

## 8. Local-First Worker Startup

When local CLI access is available, a worker's startup sequence should generally be:

1. Read assignment.
2. Read required onboarding and role documents.
3. Confirm office identity and mailbox identity.
4. Inspect local repository state.
5. Check assigned mailbox.
6. Review active work package or message.
7. Run or request Discovery where current state matters.
8. Execute bounded work.
9. Run or request Audit where completion is claimed.
10. Produce artifacts, replies, and status updates through the appropriate local or institutional channel.

This sequence should reduce manual Steward routing and repeated explanation.

## 9. Implementation, Validation, and Institutionalization

Workers must distinguish capability lifecycle states:

- Designed
- Implemented
- Operationally Validated
- Institutionalized

Implementation alone does not prove operational success.

Operational validation requires exercising the capability in its intended workflow and preserving evidence of the result.

Institutionalization occurs only after the capability becomes part of normal Estate operating procedure.

## 10. Steward Protection Rule

Onboarding has failed if Pat must repeatedly explain:

- where the repository is,
- what files to read,
- who the worker is,
- where the worker mailbox is,
- how to park deferred ideas,
- whether GitHub is the Communication Bus,
- how implementation differs from validation.

Future onboarding should package these facts explicitly before the worker begins institutional work.

## Recommended Prompt Fragment

Use this fragment when onboarding future institutional workers:

```text
Repository: ppow1/theestate
Local path: A:\theestate
Canonical entry point: AI_START_HERE.md

Read the attached onboarding corpus or use local CLI access to read the files directly. Do not rely on GitHub discovery alone if direct document delivery is available.

Your office identity, employee ID, mailbox ID, and work package range are assigned explicitly below. Do not infer them.

Use local filesystem and CLI access as source of truth when available. GitHub is an adapter, not the Communication Bus.
```
