# Resident Runtime Identity Composition

WP-4043 installs a single provider-independent runtime identity-composition path for Estate resident inference surfaces.

## Canonical entry point

All active single-resident gateway calls and conference-room gateway calls compose identity through:

- `estate.core.resident_identity_composition.compose_resident_identity`

The composer returns an inspectable object with resident ID, surface ID, composition timestamp, identity hash, included and excluded context layers, source lineage, classification summary, missing-source diagnostics, contradictions, and bounded provider-ready context.

## Composition order

The runtime composer applies layers in this order:

1. resident core identity and lifecycle;
2. authority and capability context;
3. institutional registry context;
4. grounded Estate facts;
5. character context;
6. privacy and disclosure context;
7. relationship context;
8. conversation context;
9. task-specific instructions.

Conversation context is bounded and explicitly marked non-canonical. It cannot rewrite resident identity, office, authority, or institutional facts.

## Source precedence

Required identity and lifecycle facts come from `data/registry/residents.json`. Resident markdown profiles in `residents/` are optional character context. Authority data comes from `src/estate/core/resident_authority.py`. Bounded current operational facts come from sampled pending work-package paths.

When sources are missing or contradictory, diagnostics are retained in the composed object. Missing required identity fields and detected contradictions set `failed_closed` so downstream adapters can avoid unverified role claims.

## Privacy and shared-room behavior

The conference-room surface receives shareable identity and the active resident cast, but relationship/private continuity is excluded. Evelyn remains visible as an active resident while private Steward relationship continuity is not globalized into shared room context.
