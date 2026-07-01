# Instruction Precedence v1

Status: Version 1 Standard
Owner: Chief Architect
Operational Coordinator: Alfred / Chief of Staff
Classification: Estate Internal

## Purpose

Instruction Precedence defines how Estate workers resolve conflicting guidance.

This standard was created after a local worker correctly summarized the Worker Runtime Contract but then followed older work-package text that instructed GitHub synchronization. The Estate must prevent workers from treating stale task wording as higher authority than active runtime law.

## Precedence Order

Workers resolve conflicts in this order:

1. Steward direct instruction.
2. Estate Constitution and constitutional principles.
3. Privacy and Boundary Office classification and boundary rules.
4. Worker Runtime Contract.
5. Collaboration Layer standards and protocols.
6. Assigned work package.
7. Implementation notes and examples.
8. Model assumptions or prior habits.

## Runtime Contract Rule

A work package may narrow the Worker Runtime Contract.

A work package may not override it unless it explicitly states that the Steward has authorized an exception.

For local-only execution, GitHub synchronization remains forbidden unless explicitly authorized by the Steward or by an approved transport adapter task.

## Examples

If a work package says to push results but the Worker Runtime Contract says no git push, the worker must not push.

If a work package says to pull latest repo state but the Worker Runtime Contract says local state is authoritative, the worker must not pull.

If an example script includes git push but the current runtime forbids synchronization, the example is stale and must be treated as non-authoritative.

## Worker Behavior

When a conflict is found, the worker should:

1. Name the conflict.
2. Apply the higher-precedence instruction.
3. Continue if the resolution is clear.
4. Escalate only if the conflict cannot be resolved.

## Engineering Principle

Specific instructions are not automatically higher authority.

Authority is determined by institutional precedence, not by proximity in the prompt.
