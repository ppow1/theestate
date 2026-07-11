# WP-4026 Local Model Assignment Contract

This staged contract defines resident-aware local model assignment semantics for later WP-4031 installation. It is intentionally uninstalled and must remain subordinate to the Estate model-control registry.

## Staged behaviors

- Resident assignments are ordered before capability defaults, then deterministic candidate priority.
- Provider/model availability is supplied by the authorized model-control layer; the staged selector does not probe services directly.
- Cloud or hosted providers are marked `prohibited` when no-cloud mode is enabled and are never selected during failover.
- `cold`, `starting`, `unknown`, `offline`, `missing`, `timeout`, and `prohibited` states are surfaced truthfully instead of being hidden behind fallback.
- Model-change and evaluation events are written to a staged audit log for integration into the Estate audit stream.
- Comparative evaluation records are advisory only and explicitly `self_authorizing: false`.

## Integration handoff

WP-4031 should wire these APIs into model-control and resident-chat integrations, preserving the existing Estate model-control authority and replacing the in-memory staged audit list with durable audit records.
