# CAMPAIGN-0681 Gap and Conflict Register

Status: WP-0688 evidence for G1
Observed at: 2026-07-17
Disposition rule: unresolved or conflicting evidence fails closed.

| ID | Severity | Affected packages | Repository evidence | Gap or conflict | Recommended disposition | Decision authority |
|---|---|---|---|---|---|---|
| C0681-001 | Critical | WP-0688–0707 | `CAMPAIGN_0670_ACCEPTANCE_PACKAGE.md`; bounded-reuse authorization | CAMPAIGN-0670 deliverables are integrated and reusable only as qualified artifacts, but CAMPAIGN-0670 is explicitly unaccepted with gates and protected conditions open | label every reuse as integrated specification/completion submission/provisional evidence; stop if protected acceptance is required | Chief Architect and Steward in the existing CAMPAIGN-0670 lane |
| C0681-002 | High | WP-0689, 0692, 0698, 0704 | package Markdown, `completed/`, `completions/`, Git and validation reports | package body status, directory, receipt, Git integration, validation and acceptance may disagree | preserve all sources and explicit precedence/conflict facts; never infer acceptance | Chief Architect for G1 contract; protected accepter for final disposition |
| C0681-003 | High | WP-0692, 0697, 0700 | PTM contracts, orchestrator schedule runtime, operations schedulers, governed provider scheduler | multiple schedule-like surfaces can be mistaken for a campaign scheduler | bind dependency/readiness to PTM/orchestrator; treat provider scheduler as reservation-only; keep legacy views read-only | Chief Architect |
| C0681-004 | High | WP-0689, 0692, 0700, 0702 | operational events/status, operational campaign runtime, PTM projection drafts | existing operational state seams overlap and no accepted single cross-Estate precedence contract exists | WP-0689 creates only a rebuildable normalization/projection contract with source provenance and conflict visibility | Chief Architect at G1 |
| C0681-005 | High | WP-0690, 0693–0697, 0701 | office charters, appointments, personnel registry and campaign-specific authority records | broad charter summaries and campaign-specific assignments can differ; identities/titles do not prove authority | require exact action-specific evidence; fail closed and name required owner | Chief Architect at G1; Steward for protected authority changes |
| C0681-006 | Medium | WP-0691, 0692, 0698 | resident/service/provider/worker health stores and generated boards | heterogeneous freshness and unknown-state behavior are not normalized | retain observed/effective times; distinguish healthy, degraded, unavailable, stale and unknown | Chief Architect for contract; canonical health owners for sources |
| C0681-007 | High | WP-0698, 0702, 0704–0707 | receipts, recipes, reports, reconciliation, PR and readiness records | completion, validation, integration, readiness and acceptance are easily collapsed | represent each as a separate evidence class and transition; require exact commit binding | Chief Architect / named acceptance authority |
| C0681-008 | Medium | WP-0693, 0696, 0700 | repository messages, mailbox index and operational blockers | messages can be misused as state or approval and routing can be confused with action | messages carry canonical references only; substantive decisions remain in their canonical lane | Alfred for routing; substantive decision owner |
| C0681-009 | Medium | WP-0694, 0700, 0703 | Grace runtime, office decision support, CAMPAIGN-0680 pending campaign | overlapping views can become a new dashboard truth or Operations Center store | reuse read-only decision-support patterns; project from canonical facts and disclose freshness | Chief Architect; Steward for protected surface decisions |
| C0681-010 | High | WP-0690, 0695, 0700, 0701 | Helen workforce, provider capability/capacity and authority records | automatic staffing/spending may be inferred from operational eligibility | taxonomy must distinguish request from decision and require explicit delegated authority | Helen / Steward or named budget authority |
| C0681-011 | Medium | WP-0699, 0700, 0702 | WP-0678 checkpoints, runtime recovery/replay, chat/terminal state | recovery evidence is fragmented and conversational memory is non-authoritative | durable checkpoints record exact head, validations, failures, retries and next permitted action | Chief Architect for campaign contract |
| C0681-012 | High | WP-0697 | manifest namespace resolution | two WP-0697 paths and an unrelated legacy receipt exist | exact manifest path `WP-0697_ENGINEERING_DEPARTMENT_OPERATIONAL_INTEGRATION.md` controls; never reuse legacy receipt | Chief Architect resolution already recorded |
| C0681-013 | Resolved prerequisite | WP-0688, 0691, 0698 | `tests/test_service_health_registry.py`, `tests/test_estate_capability_registry.py`; prerequisite commit `6bc8047` | The CLI isolation defect was repaired without changing WP-0688 runtime scope: explicit/environment roots and fixture working-directory context now precede the production fallback | retain the repair commit and its passing isolated and affected-subsystem validation as prerequisite evidence | Chief Architect repair authorization exercised; no further decision required for WP-0688 |

## Duplication audit

| Prohibited duplicate | Existing canonical seam | WP-0688 finding |
|---|---|---|
| Registry | personnel, capability, provider, resident, service-health and canonical package records | no new registry is required |
| Queue / Dispatch | Execution Dispatch plus canonical mailbox intake for communication | no new work or escalation queue is required |
| Scheduler | PTM/orchestrator dependency/readiness with existing operations invocation | precedence must be clarified, not replaced |
| Validator | work-package recipes, pytest, reconciliation and readiness | normalize evidence only |
| Dashboard | office decision support, operations/readiness/Steward views and CAMPAIGN-0680 patterns | derived view only; no new truth source |
| Mailbox | repository messages and mailbox index/control/sync | structured references suffice |
| State store | canonical domain records, operational events/campaign runtime and rebuildable PTM projections | WP-0689 must remain derived and rebuildable |
| Acceptance path | campaign/package acceptance records and protected gates | no inferred or automatic acceptance |

## G1 freeze recommendation

G1 may be released only if WP-0689 preserves source authority and conflict visibility
and WP-0690 fails closed on missing authority. The register contains no direct
contradiction to the authorized WP-0688–WP-0690 execution, but every item remains a
design constraint and residual risk until its owning later package or protected
authority records a disposition.
