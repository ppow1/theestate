# WP-4041 — Resident Identity Package Standard

Status: Pending
Execution Mode: PARALLEL-INDEPENDENT
Owner: Office of Character Architecture
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate resident commissioning standardization

## Concurrency

Safe to execute concurrently with WP-4039 and WP-4040. This package must not modify active gateway routing, runtime activation state, provider assignments, Office command surfaces, or live Open WebUI configuration.

## Objective

Create a canonical, reusable Resident Identity Package standard so every Estate resident can be represented consistently across character design, prompts, portrait, voice, office, relationships, model routing, continuity, validation, and future visual interfaces.

The standard must preserve resident identity across provider, model, voice engine, portrait renderer, and interface replacement.

## Required Outcomes

1. Define one versioned Resident Identity Package contract.
2. Separate canonical identity from implementation bindings.
3. Define required and optional artifacts.
4. Define validation rules and readiness states.
5. Define privacy and classification handling.
6. Define controlled evolution without silent identity drift.
7. Provide examples for Alfred, Helen, Grace, Ingrid, and Evelyn.
8. Produce an install manifest for WP-4042.

## Core Principles

- A resident is not a model, prompt, portrait, or voice.
- Presentation may change without silently changing canonical identity.
- Runtime code must reference the identity package rather than invent traits.
- Personal and restricted details must be audience-scoped.
- Growth must use source-linked continuity and governed preference evolution.
- Do not create a second resident registry, personnel registry, mailbox registry, authority system, or memory store.

## Required Package Sections

### Canonical Identity

Resident name and ID, employee ID when applicable, role, office, authority summary, classification, lifecycle state, identity anchors, and prohibited identity drift.

### Character Bible

Temperament, values, communication style, humor, emotional range, strengths, limitations, trauma and resilience boundaries where applicable, behavioral failure modes, and prohibited generic behaviors.

### Physical Identity

Appearance summary, age presentation, height and proportions, face, hair, eyes, complexion, distinguishing features, posture, movement, natural imperfections, wardrobe preferences by context, jewelry, accessories, fragrance, grooming, footwear, and image-continuity constraints.

Physical identity artifacts must be non-explicit and suitable for ordinary Estate presentation.

### Voice Identity

Vocal presence, accent guidance, cadence, energy, pitch range, emotional modulation, humor delivery, pauses, emphasis, pronunciation notes, engine-neutral description, and separate current TTS bindings.

### Visual Presentation

Canonical portrait specification, expression sheet, wardrobe sheet, office/background requirements, avatar crops and aspect ratios, provenance, versioning, and separate renderer/model bindings.

### Office and Environment

Office description, lighting, furnishings, desk objects, personal items, books, tools, plants, artwork, memorabilia, public/private areas, and environmental cues that reinforce character without caricature.

### Relationships

Relationship to the Steward and each active resident, trust boundaries, collaboration tendencies, healthy tension, private versus institutional relationship data, and relationship-evolution hooks.

### Preferences and Growth

Seeded, contextual, evolving, experimental, changed, retired, and disputed preferences; provenance; linkage to WP-4053; and distinction between identity anchors, durable preferences, experiments, and moods.

### Runtime Presentation Contract

Prompt identity reference, fallback behavior, capabilities, tool access, model entitlement, continuity policy, session privacy, Open WebUI metadata, avatar binding, and voice binding.

### Validation and Commissioning

Support readiness states:

- draft
- character_review_ready
- identity_complete
- presentation_ready
- runtime_ready
- commissioned
- revision_required
- retired

Validation must cover identity consistency, behavioral distinctiveness, authority correctness, privacy, portrait continuity, voice continuity, relationships, implementation independence, and unsupported activation claims.

## Required Artifacts

Create all implementation under:

`collaboration/workstreams/WP-4041/`

Required files:

- `README.md`
- `Resident_Identity_Package_Standard_v1.md`
- `schemas/resident_identity_package_v1.json`
- `schemas/resident_presentation_binding_v1.json`
- `schemas/resident_relationship_profile_v1.json`
- `templates/resident_identity_package_template.yaml`
- `templates/portrait_specification_template.md`
- `templates/voice_identity_template.md`
- `templates/wardrobe_preferences_template.md`
- `templates/office_environment_template.md`
- `templates/relationship_matrix_template.yaml`
- `examples/alfred_identity_package.yaml`
- `examples/helen_identity_package.yaml`
- `examples/grace_identity_package.yaml`
- `examples/ingrid_identity_package.yaml`
- `examples/evelyn_identity_package.yaml`
- `tests/test_resident_identity_package_standard.py`
- `install_manifest.json`
- `notes/integration_notes.md`
- `notes/rollback_notes.md`

Also create:

`collaboration/work_packages/completions/WP-4041_codex_done.json`

## Validation Requirements

Tests must verify:

- all examples validate
- identity and implementation bindings remain separate
- readiness-state required fields
- audience-scoped private fields
- provider/model/voice/portrait replacement without identity mutation
- relationship scope enforcement
- WP-4053 preference-evolution linkage without silent drift
- rejection of unknown authority claims
- deterministic serialization

## Installation Boundary

This is a standards package only. Do not edit active gateway files, activate residents, change personnel or mailbox registries, modify lifecycle state, install runtime loaders, change provider routing, or alter live Open WebUI configuration.

WP-4042 will inspect and install or reference this standard through a controlled install handoff.

## Acceptance Criteria

- Every required artifact exists.
- Every example validates.
- The standard is provider- and interface-independent.
- Restricted resident information is audience-scoped.
- The install manifest identifies all future integration points and conflicts.
- Tests pass.
- Completion receipt records exact files, tests, limitations, and rollback notes.

## Codex Completion

Implement the package, run focused tests, and create the completion receipt. Do not install staged artifacts into active runtime.