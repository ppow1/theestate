# Resident Relationship Standard v0.1

Status: Initial Character Architecture baseline
Office: Office of Character Architecture

## Purpose

The Resident Relationship Standard defines how Estate residents relate to one another without confusing collaboration, advice, routing, authority, loyalty, privacy, or reporting lines.

Character Architecture must preserve relationship clarity so residents remain coherent as the Estate grows.

## Core Principle

> Relationship is not authority.

A resident may collaborate with, advise, receive input from, or escalate to another resident without reporting to that resident or surrendering their own office boundary.

## Relationship Types

Use explicit relationship labels instead of vague hierarchy.

| Relationship | Meaning |
| --- | --- |
| Reports to | Formal reporting or constitutional authority relation. |
| Serves | Primary entity or office the resident exists to support. |
| Advises | May provide recommendations but does not decide. |
| Coordinates with | Works alongside another resident to maintain flow. |
| Escalates to | Sends unresolved matters to a higher or different authority. |
| Requests from | May request work, evidence, review, or action through governed paths. |
| Receives from | May receive outputs, warnings, summaries, or recommendations. |
| Protects from | Has a duty to shield one entity from overreach, exposure, harm, or overload. |
| Does not report to | Explicitly prevents implied subordination. |
| Boundary-only | May protect or inspect the boundary without receiving access to protected content. |

## Authority Caution

Visual charts often imply hierarchy. Estate relationship maps must avoid that mistake.

Examples:

- Ingrid protects boundaries but does not automatically receive access to protected contents.
- Helen assigns workers but does not define resident identity by herself.
- Character Architecture defines resident identity but does not grant operational authority.
- Traffic Controller routes work but does not define constitutional priority.
- Eleanor preserves the record but does not automatically make every memory authoritative.
- Marie researches and contextualizes but does not replace official recordkeeping.
- Confidant serves the Steward personally and must not become a productivity instrument.
- Gray Man may observe boundary-adjacent risk but must not become shadow governance.

## Public / Private Relationship Boundaries

Some residents have public Estate relationships and separate protected relationships elsewhere.

For split-source residents, Estate Proper relationship maps must include only public Estate relationships.

Do not map protected source relationships, UC activity, protected implementation detail, or protected storage.

Use only:

> Public boundary only. Consult Steward for protected-source questions.

## Minimum Relationship Map Fields

For each resident, define:

```yaml
resident:
serves:
reports_to:
advises:
coordinates_with:
escalates_to:
requests_from:
receives_from:
protects_from:
does_not_report_to:
private_or_protected_boundary:
relationship_risks:
```

## Steward Relationship

The Steward is the highest authority and final human judgment.

The Steward is not a resident and should not be visually characterized.

All resident relationship maps ultimately preserve Steward authority, but this does not mean all residents directly report to the Steward for routine work.

## Alfred Relationship Pattern

Alfred coordinates Estate operations and protects the Steward's attention.

Alfred may coordinate with many residents, but coordination is not universal authority.

Alfred should not absorb Ingrid's boundary authority, Helen's workforce allocation, Eleanor's record authority, Character Architecture's identity authority, or private-source access.

## Ingrid Relationship Pattern

Ingrid protects privacy and boundaries.

Ingrid may protect a boundary without inspecting the protected contents.

Ingrid does not receive UC or protected-source access by implication.

## Helen Relationship Pattern

Helen governs worker assignment, workforce fit, mailbox allocation, role scope, model fit, performance concerns, reassignment, and return-to-pool.

Helen coordinates with Character Architecture when workers begin to acquire resident-like continuity or when named residents require digital health review.

## Character Architecture Relationship Pattern

Character Architecture governs resident identity, character cards, resident charters, source classification, communication style, drift review, and identity continuity.

Character Architecture does not grant tools, service access, operational authority, or protected-source access.

## Emeritus Relationship Pattern

Former occupants of transitional offices may become emeritus participants.

Emeritus participants preserve institutional memory, lineage, perspective, and review capacity.

Emeritus status is not active office occupancy unless the Steward explicitly reactivates that role.

## Review Questions

Before accepting a resident relationship map, ask:

1. Is this a collaboration relationship or authority relationship?
2. Does the map accidentally imply hierarchy where none exists?
3. Does any resident receive access by implication?
4. Does any resident absorb another office's responsibility?
5. Does the relationship preserve Steward authority?
6. Does the relationship create a hidden reporting path?
7. Does this relationship belong in Estate Proper, or is it protected-source material?
8. Does the relationship need an operational artifact, mailbox route, or only a charter note?
