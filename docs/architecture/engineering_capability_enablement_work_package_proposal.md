# Capability Enablement Work-Package Proposal

Status: Proposed; no new work-package IDs assigned.

## Numbering and ownership reconciliation

The repository already contains overlapping pending scopes:

- WP-0671: Engineering intake, decomposition, and readiness;
- WP-0672: execution lanes, provider routing, and Gate-B identity;
- WP-0673: evidence, validation, integration, and acceptance;
- WP-0695: Helen staffing and capability request integration;
- WP-0697: Engineering operational projection under CAMPAIGN-0681;
- WP-0604: provider registration and capability discovery;
- WP-0613: provider-neutral adapter contract;
- WP-0536/WP-0537: project intake and workforce role/staffing runtime.

Because CAMPAIGN-0670 and CAMPAIGN-0681 have separate package graphs and the
namespace already contains unresolved legacy duplicates, this proposal does not
claim a new WP number. The Chief Architect should either amend the existing
packages or issue a new package after the campaign namespace authority resolves
ownership. A new package must not silently compete with the listed packages.

## Proposed sequence

### Phase 1 — Contract reconciliation

Amend or complete WP-0671, WP-0695, and the CAMPAIGN-0681/WP-0697 integration
surface to adopt the capability inquiry, assessment, gap, specification,
dependency, registration, re-evaluation, and resumption schemas. Freeze IDs,
source ownership, freshness, and conflict behavior.

### Phase 2 — Capability and worker specification records

Implement the smallest adapters on `GraceHelenEngineeringComposition` and
`HelenWorkforceStore` that persist the proposed records. Add a bounded advisory
Engineering consultation path through existing messages/mailboxes. No provider
execution or catalog mutation occurs in this phase.

### Phase 3 — Enablement project composition

Reuse PTM/orchestrator intake, dependency, readiness, scheduling, and the
existing work-package lifecycle to create a separate enabling project. Link the
original objective immutably. Exercise proposal rejection, blocked bootstrap,
supersession, and resume waiting states.

### Phase 4 — Adapter registration and qualification

Amend WP-0672/WP-0613/WP-0604 as needed to define adapter registration result,
versioned capability claims, health checks, cancellation, receipt/artifact
schema, and qualification evidence. This phase is the first point at which a
concrete adapter may be implemented, subject to a separate approved package.

### Phase 5 — Helen verification and original-project resumption

Implement fresh evidence re-evaluation, dependency satisfaction, and Grace
resumption. Prove that the original request continues with a new attempt and
does not require repeated Steward intake. Validate through WP-0673 and the
existing acceptance/readiness lifecycle.

## Candidate package boundaries

| Candidate | Reuse/owner | Output |
|---|---|---|
| Capability contract and gap records | WP-0671 + WP-0695; Grace/Helen owners | Schemas, records, tests, conflict rules |
| Specification consultation and enablement dependency | WP-0671 + PTM; Engineering advisory, Grace project creation | Consultation and dependency records |
| Provider/adapter registration | WP-0672 + WP-0604 + WP-0613; Chief Architect/Gate B | Registration result and adapter evidence |
| Re-evaluation/resumption | WP-0673 + WP-0697; Helen/Grace/PTM | Re-evaluation and resumed original attempt |

## Non-goals

No provider is selected for implementation here. No live adapter is registered.
No catalog, health, capacity, Dispatch, scheduler, personnel, or acceptance
system is duplicated.
