# Estate Branch Management Standard v1

Status: Operational Standard
Classification: Estate Internal

## Purpose

Define a consistent branch strategy that enables multiple Estate workers to operate in parallel while preserving `main` as the canonical institutional state.

## Principles

- `main` is the authoritative institutional branch.
- Active implementation never occurs directly on `main`.
- One work package per branch.
- One primary worker owns a branch until promotion or reassignment.
- Promotion requires successful local validation and audit.

## Branch Naming

- audit/*
- ops/*
- docs/*
- feature/*
- research/*
- hotfix/*

Branch names should clearly identify the work package or objective.

## Worker Ownership

Each implementation branch has a single accountable worker. Supporting workers contribute through the collaboration process rather than directly sharing branch ownership.

## Promotion Workflow

1. Complete the assigned work package.
2. Run the required local validation.
3. Execute the Estate local audit.
4. Reconcile the History Queue using the approved drain workflow.
5. Review results.
6. Promote by merging into `main`.

## Audit Traceability

Audit results shall record:

- Repository
- Branch
- Commit SHA
- Work Package ID
- Audit timestamp
- Audit result

This provides traceability from audit evidence to implementation history.

## Main Branch Policy

`main` represents published institutional state.

Routine development, experimentation, and worker implementation occur on isolated branches and are promoted only after validation.

## Relationship to Collaboration Layer

This standard complements:

- Worker Runtime Contract
- Instruction Precedence
- Communication Protocol
- History Queue / Drain Workflow
- Audit Worker v1

Together these establish a repeatable, auditable promotion process for parallel Estate development.