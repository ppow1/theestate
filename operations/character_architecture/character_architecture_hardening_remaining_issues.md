# Character Architecture Hardening Remaining Issues

Date: 2026-07-12

## Remaining issues

1. Broad repository pytest still has existing functional failures after collection repair; these are outside the duplicate-module collection blocker and should be triaged by focused subsystem owners.
2. Grace activation remains intentionally incomplete. A future Steward-authorized activation package must define readiness, gateway exposure, validation evidence, and rollback conditions.
3. Historical documents and generated briefings may still mention older pending queues or previous Grace activation attempts; they should be regenerated or annotated when their owning workflows next run.
4. Workstream staged/proposed tests remain preserved under `collaboration/workstreams/` for review, but are not part of default canonical pytest collection.
