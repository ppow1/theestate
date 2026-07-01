# Synchronization Evidence v1

Status: Designed
Classification: Estate Internal

## Purpose

Define how the Estate records evidence that a worker, office occupant, service, or long-lived AI personnel has checked for relevant institutional updates.

This supports the command:

> Check for updates.

The purpose is not bureaucracy. The purpose is evidence over assumption.

## Principle

Synchronization is determined by authorization and operational relevance, not merely by organizational role.

The Estate should consider multiple dimensions when determining what updates a worker should receive:

- Security clearance
- Office or role
- Current assignment
- Active work packages
- Delegated authority
- Capability dependencies
- Explicit Steward instruction

Security clearance is a primary routing factor. A worker should receive only updates they are authorized to know and that are operationally relevant to their current responsibilities.

## Required vs Recommended Updates

Updates should be divided into two categories.

### Required Updates

Required updates affect authority, safety, policy, runtime behavior, assigned work, or institutional correctness.

Examples:

- Updated runtime contract
- Updated security or privacy rules
- Constitutional amendments affecting authority
- Changed work package instructions
- Audit requirements affecting current work

### Recommended Updates

Recommended updates may improve awareness but do not block the worker's current assignment.

Examples:

- New roadmap items
- Completed capabilities outside current work
- Architectural investigations outside current authority
- Operational summaries

## Synchronization Record

Synchronization evidence should be recorded as institutional state, not private worker memory.

Suggested location:

```text
collaboration/synchronization/
```

Suggested filename pattern:

```text
<worker_or_office_id>.sync.json
```

Example:

```json
{
  "subject_id": "CA3",
  "subject_type": "Office Occupant",
  "last_synchronized": "2026-07-01T20:15:00Z",
  "synchronization_scope": "Chief Architect",
  "clearance_level": "Estate Internal",
  "synchronization_baseline": "Architecture and Governance Current",
  "required_updates_status": "Complete",
  "recommended_updates_status": "Deferred",
  "assignment_specific_updates_status": "Complete",
  "references_examined": [
    "docs/onboarding/Check_For_Updates_v1.md",
    "docs/governance/Capability_Lifecycle_States_v1.md",
    "docs/collaboration/Branch_Management_Standard_v1.md"
  ],
  "outstanding_updates": [],
  "notes": "No blocking updates remain for current assignment."
}
```

## Baselines

A synchronization baseline identifies the institutional area that was checked.

Possible baselines include:

- General Estate
- Governance
- Architecture
- Collaboration Layer
- Security
- Audit
- Operations
- Assigned Work Package

Baselines may become more formal as the Estate matures.

## Usage

A worker asked to check for updates should:

1. Identify the relevant synchronization scope.
2. Determine applicable clearance and authorization limits.
3. Review required references.
4. Review recommended references as needed.
5. Report what was checked and what changed.
6. Record synchronization evidence when appropriate.

## Future Automation

Later systems may allow Alfred, Helen, Audit, or scheduling services to ask:

- Who is out of sync?
- Has this worker reviewed the latest ADRs?
- Is this worker cleared for the update they are requesting?
- Can this worker accept the proposed assignment?
- What required updates are still outstanding?

## Lifecycle

Check for Updates: Operational Pointer

Synchronization Evidence: Designed

Synchronization Records: Implementation Pending

Synchronization-aware Scheduling: Future Investigation
