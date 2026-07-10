# WP-0521 - Office End-to-End Regression, Recovery, and Operational Acceptance

Status: Proposed
Priority: High
Owner: Chief Architect #5
Classification: Estate Internal

## Mission

Prove the Office of the Steward works as a real local command center across all repaired control surfaces and produce an operational readiness verdict with a narrow remaining-defect inventory.

## Required Demonstrations

Demonstrate through real Office controls:

- Settings persistence across reload and restart;
- execution-session controls;
- Parking Lot reorder, status change, and governed promotion;
- personnel and org-chart detail navigation;
- Alfred Enter-to-send chat and conversation recovery;
- Mission Control action routing;
- project and work-package operations;
- validation and audit operations;
- mailbox and notification actions;
- approved AI-service controls;
- cross-surface search and command navigation;
- truthful recovery from malformed input, handler failure, stale state, unavailable local service, and interrupted requests.

## Required Outputs

Produce:

```text
runtime/steward/office_end_to_end_regression.json
runtime/steward/office_operational_readiness.json
operations/steward/office_operational_readiness.md
runtime/steward/office_remaining_defects.json
collaboration/work_packages/completions/WP-0521_codex_done.json
```

Register a WP-0521 validation recipe and create deterministic browser/HTTP-level regression tests.

## Acceptance Standard

A workflow passes only when the browser reaches the canonical handler, legitimate state or durable evidence changes, the refreshed Office shows the result, persistence survives reload where required, and failures are reported truthfully.

## Boundaries

Do not grant institutional acceptance automatically. This package may produce an operational readiness verdict and evidence for Chief Architect and Steward review. It must not create a parallel Office, test framework, authority layer, provider router, queue, registry, or event system.

## Test Requirements

Run the complete repaired Office suite in an isolated Estate root using fake providers and fake service runners where required. Prove duplicate-submit protection, idempotency where promised, safe retry, reload persistence, diagnostics visibility, and cross-surface navigation.

## Acceptance Criteria

1. Every repaired control surface completes its primary workflow end to end.
2. No retained actionable element is a decorative placeholder.
3. Shared shell, navigation, forms, and action transport remain reliable.
4. Failure and recovery paths are demonstrated.
5. Reload and restart persistence are verified.
6. Remaining defects are explicit, prioritized, and narrow.
7. Operational readiness verdict is evidence, not institutional acceptance.
8. Full regression and WP-0521 validation pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0521_Office_End_to_End_Regression_Recovery_and_Operational_Acceptance.md and do exactly what it says.
```
