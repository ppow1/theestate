
Estate Collaboration Standard v1

Status: Operational Standard

1. Purpose

This standard governs how Estate participants collaborate through repository and local transport infrastructure.

2. Collaboration Is Infrastructure

Collaboration documents support the infrastructure.

They are not the infrastructure by themselves.

The infrastructure consists of:

Message queues.
Work package lifecycle.
Worker claim state.
Review state.
Promotion state.
Transport adapters.
Boundary enforcement interfaces.
Future Alfred automation.
3. Standard Rules

All work should have:

A clear mission.
Scope.
Do-not-touch boundaries.
Required reading.
Expected deliverables.
Acceptance criteria.
Classification.
Completion notes.
4. Manual Work and Automation

The Estate applies the Rule of Three.

If a manual process has been performed three times, or is reasonably expected to recur more than three times, and is time consuming, difficult, error-prone, or cognitively expensive, the Estate should evaluate automation.

Automate stable patterns, not experimental ones.

5. Transport Independence

Do not design Estate collaboration as GitHub-only.

GitHub is an adapter.

The Communication Bus concept must survive transport replacement.

6. Boundary First

Outbound communication must pass through boundary review.

Default-deny applies.

7. Auditability

Collaboration state should be inspectable.

Audit should eventually validate:

Message envelope shape.
Required fields.
Work state.
Promotion records.
Classification presence.
Git cleanliness.
History alignment.
8. Steward Protection

The Collaboration Layer exists to reduce Steward workload.

If collaboration infrastructure causes Pat to do more repetitive routing, copy/paste, or reconstruction, the infrastructure is not yet successful.
