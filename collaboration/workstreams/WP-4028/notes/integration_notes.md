# WP-4028 Integration Notes

This staged package is uninstalled and limited to `collaboration/workstreams/WP-4028/`.
WP-4031 should adapt the staged contracts into the existing AI Services,
background operations runtime, approval/audit flow, resident gateway status,
Office action payloads, and `src/estate/cli/main.py` rather than installing a
second registry, scheduler, event loop, or approval path.

## Required handoff points

- Feed authorized service-control health facts into `RuntimeFact` records.
- Preserve dependency ordering from `LocalAIServiceSupervisor.plan`.
- Route non-status `steps` through the existing approval and audit systems.
- Display `diagnostics`, `logs`, `recovery_hints`, `resident_impact`, and
  `resident_available` truthfully in resident and Office surfaces.
- Treat `auto_execute: false` as invariant for staged and deterministic tests.
- Keep bounded recovery attempts externalized through `RecoveryPolicy`.
