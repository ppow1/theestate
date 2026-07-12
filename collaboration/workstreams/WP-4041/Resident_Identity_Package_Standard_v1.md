# Resident Identity Package Standard v1

## Purpose

A Resident Identity Package (RIP) is the canonical, versioned representation of an Estate resident. A resident is not a model, prompt, portrait, voice, tool bundle, mailbox, or registry row. Runtime systems must reference the package and must not invent identity traits at the point of presentation.

## Versioned Contract

- Contract name: `estate.resident_identity_package`
- Contract version: `1.0.0`
- Package schema: `schemas/resident_identity_package_v1.json`
- Presentation binding schema: `schemas/resident_presentation_binding_v1.json`
- Relationship profile schema: `schemas/resident_relationship_profile_v1.json`

## Canonical Identity

Required fields: resident name and ID, employee ID when applicable, role, office, authority summary, classification, lifecycle state, identity anchors, and prohibited identity drift. Authority claims are limited to `none`, `advisory`, `operational_support`, `office_delegate`, and `steward_delegated`.

## Separation of Canonical Identity and Bindings

Canonical identity is stable. Implementation bindings live under `implementation_bindings` and may be replaced without changing `canonical_identity`, `character_bible`, `physical_identity`, `voice_identity`, `office_environment`, `relationships`, or `preferences_and_growth`.

## Required and Optional Artifacts

Required package sections are canonical identity, character bible, physical identity, voice identity, visual presentation, office and environment, relationships, preferences and growth, runtime presentation contract, validation and commissioning, privacy, and provenance. Optional supporting artifacts include expression sheets, wardrobe sheets, office background sheets, portrait renderer recipes, TTS presets, and UI crop metadata.

## Privacy and Classification

Private, personal, restricted, or sensitive relationship details must be audience-scoped. Allowed audience scopes are `public`, `resident`, `steward`, `office`, and `restricted`. No restricted data may appear in public runtime presentation.

## Preferences and Growth

Preferences must be categorized as `identity_anchor`, `durable`, `seeded`, `contextual`, `evolving`, `experimental`, `changed`, `retired`, or `disputed`. Evolving, changed, retired, and disputed preferences must link to WP-4053 continuity or preference-evolution evidence. Moods are not durable identity.

## Readiness States

Supported states: `draft`, `character_review_ready`, `identity_complete`, `presentation_ready`, `runtime_ready`, `commissioned`, `revision_required`, and `retired`. Higher readiness states require progressively complete identity, presentation, runtime, validation, privacy, and commissioning evidence.

## Validation Rules

Validation covers identity consistency, behavioral distinctiveness, authority correctness, privacy scope, portrait continuity, voice continuity, relationship scope, implementation independence, WP-4053 preference linkage, unsupported activation claims, and deterministic serialization.

## Controlled Evolution

Identity changes require a package version bump, source-linked provenance, validation, and reviewer acknowledgement. Renderer, provider, model, voice engine, and interface replacements must not mutate canonical identity.
