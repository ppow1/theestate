# WP-0113 Helen Next-Batch Recommendation

Generated at: 2026-07-04T22:25:24+00:00

## Current Production-Readiness Totals After WP-0111 Repair

- total_work_packages_scanned: 100
- total_production_ready: 32
- total_blocked: 68
- total_missing_recipes: 48
- total_missing_receipts: 6
- total_incomplete_receipts: 52

## Helen Path Status After WP-0020 Readiness

WP-0020 Helen HR Operational Onboarding is production-ready; Helen is onboarded for HR artifacts/identity but is not yet fully online as a resident duty runner.

## Recommendation

1. Implement `WP-0106` — Resident Runtime Presence Model.
2. Implement `WP-0110` — Resident Action Authority Boundary before or alongside `WP-0106`.
3. Implement `WP-0107` — Alfred Online Duty Runner.
4. Implement `WP-0108` — Helen Online Duty Runner.
5. Implement `WP-0109` — Resident Conversation Session and Audit Trail.

## Why WP-0106 Comes Before WP-0108

WP-0108 needs a shared resident presence/status substrate so Helen online state is visible, auditable, and bounded before duty-runner behavior is added.

## WP-0110 Timing

Implement WP-0110 before or alongside WP-0106 so action authority limits are explicit before resident online/duty surfaces expand.

## Pending Implementation Boundary

WP-0107, WP-0108, and WP-0109 remain implementation packages, not validation-only repairs; WP-0106 and WP-0110 also remain pending implementation work. No WP-0106 through WP-0110 completion receipts are created by WP-0113.

## Recommended Next Work-Package Command

`Read collaboration/work_packages/pending/WP-0106_SERIES_resident_runtime_presence_model.md and implement it, coordinating WP-0110 authority-boundary review before or alongside the WP-0106 implementation.`
