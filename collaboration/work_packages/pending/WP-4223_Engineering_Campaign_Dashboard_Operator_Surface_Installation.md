# WP-4223 — Engineering Campaign Dashboard Operator Surface Installation

- **Status:** implemented; validation evidence recorded on the WP-4223 branch
- **Depends on:** WP-4220, WP-4221, WP-4222
- **Canonical surface:** local Office of the Steward command center
- **Authority:** read-only, advisory Estate operator presentation

WP-4223 installs a thin adapter in the existing local command center. The adapter invokes
WP-4222 provider discovery and composition, which consumes WP-4220 and WP-4221. It neither
scans authoritative records nor supplies reconciliation, scheduling, assignment, dispatch,
merge, acceptance, Git, or lifecycle mutation behavior.

The surface exposes snapshot, panel, summary, health, compatibility, diagnostics, and manual
refresh reads. API access requires the existing local operator boundary plus an explicit
`X-Estate-Operator-Role` of `estate_operator` or `steward`. The Office remains loopback-only.
Refresh writes only a last-known-valid presentation cache and metadata-only audit events.

Acceptance requires focused adapter/Office tests, predecessor regressions, deterministic
output, truthful required/optional provider failure, authorization rejection, safe diagnostics,
and tested disable rollback. Parking Lot and WIP records are outside this package.
