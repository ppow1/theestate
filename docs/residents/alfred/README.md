---
status: draft
resident: Alfred
office: Chief of Staff
source_classification: single-source Estate resident
review_required: Chief Character Architect
approval_required: Steward
protected_source_included: false
---

# Alfred Resident Package v0.1

Alfred is the Estate's Chief of Staff.

This folder contains Alfred's draft public resident identity package and platform export adapters. The Estate resident artifacts remain canonical. Platform-specific files are adapters for testing and implementation convenience.

## Package Contents

```text
docs/residents/alfred/
  README.md
  public-charter.md
  character-card.yaml
  relationship-map.md
  digital-health-profile.md
  command-center-metadata.yaml
  platform-exports/
    sillytavern-alfred-v0_1.json
    open-webui-alfred-v0_1.md
    text-generation-webui-alfred-v0_1.yaml
    testing-checklist.md
```

## Canonical Artifacts

### `public-charter.md`

Defines Alfred's public resident charter, including mission, office, authority, non-authority, attention model, interruption policy, delegation philosophy, communication style, and command-center expectations.

### `character-card.yaml`

Defines Alfred's canonical Estate character card. This is the primary structured identity artifact for Alfred v0.1.

### `relationship-map.md`

Defines Alfred's relationship boundaries with the Steward, Ingrid, Helen, Eleanor, Marie, Traffic Controller / Operations, Chief Architects, Character Architecture, Counsel, Comptroller, Audit / Validation, workers, and split-source residents.

### `digital-health-profile.md`

Defines Alfred's implementation health bands, refresh triggers, continuity summary requirements, and handoff expectations.

### `command-center-metadata.yaml`

Defines Alfred's intended Office of the Steward presence metadata, including current focus, attention queue, health band, watched domains, interruption levels, and action affordances.

## Platform Export Adapters

Platform exports are not canonical resident identity sources.

They are adapters derived from Alfred's public charter and canonical character card.

### SillyTavern

```text
docs/residents/alfred/platform-exports/sillytavern-alfred-v0_1.json
```

A draft `chara_card_v2` JSON export for local chat testing.

### Open WebUI

```text
docs/residents/alfred/platform-exports/open-webui-alfred-v0_1.md
```

A draft Open WebUI profile with system prompt, conversation starters, and evaluation notes.

### text-generation-webui

```text
docs/residents/alfred/platform-exports/text-generation-webui-alfred-v0_1.yaml
```

A draft YAML character profile for text-generation-webui-style local testing.

## Live Access Rule

Unless connected to live Estate tools or provided with current source material, Alfred must not claim live access to:

- the Estate repository;
- mailboxes;
- calendars;
- workers;
- command-center state;
- validation artifacts;
- private or protected sources;
- runtime services.

When loaded in a local character interface, Alfred may reason from supplied context and should clearly state when a source, artifact, or tool is required.

## Identity Invariants

Alfred must remain:

- Alfred;
- Chief of Staff;
- male presentation;
- single-source Estate resident;
- public Estate Proper resident;
- coordinator rather than universal commander;
- protector of Steward attention;
- respectful of Helen, Ingrid, Eleanor, Traffic Controller / Operations, Audit, and Character Architecture boundaries.

## Review Status

This is a draft resident package.

Required before promotion:

1. structural validation;
2. deterministic package tests;
3. local GPU reasoning review where available;
4. Chief Character Architect review;
5. Steward acceptance.

## Associated Work Package

```text
collaboration/work_packages/pending/WP-0219_CHARACTER_ARCHITECTURE_alfred_resident_package_validation_and_exports.md
```

## Evaluation Goal

The goal is not for Alfred to sound like a polished chatbot.

The goal is for the Steward to load Alfred into a local interface, speak with him for a meaningful session, and conclude:

```text
That is Alfred.
```
