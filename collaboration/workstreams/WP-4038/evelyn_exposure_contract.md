# WP-4038 Evelyn Exposure Contract

This workstream stages Evelyn's `estate/evelyn` model entitlement, voice profile, portrait profile, and Open WebUI descriptor for future install handoff.

## Guarantees

- The package is staged and uninstalled.
- No active shared gateway, registry, scheduler, queue, or authority system is modified.
- `estate/evelyn` remains restricted to the Steward Relationship Layer.
- Gateway registration is explicitly false in the staged entitlement.
- Open WebUI metadata is descriptor-only and grants no permissions.
- Voice and portrait metadata preserve Evelyn's adult identity and avoid childlike or generic-assistant presentation.

## Install Handoff Requirements

A future install package must:

1. Re-run the staged tests.
2. Confirm Steward approval for audience and model-provider assignment.
3. Wire the existing shared gateway and registry rather than creating a second gateway.
4. Preserve denial-by-default private-memory semantics from WP-4037.
5. Record manual Open WebUI validation truthfully after live validation occurs.
