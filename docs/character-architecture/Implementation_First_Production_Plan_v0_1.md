# Implementation-First Production Plan v0.1

Status: Initial production plan
Office: Office of Character Architecture

## Purpose

This plan keeps the Office of Character Architecture biased toward implementation while preserving enough governance to prevent identity drift, authority confusion, and resident/worker collapse.

The Steward has directed the office to think big while favoring implementation over excessive white papers.

## Operating Principle

> Enough governance to make the next implementation safe. No more governance than the next implementation needs.

## Strategic Objective

The Estate should be able to replace models, runtimes, interfaces, and execution providers without losing resident identity.

The long-term target is not a set of documents. It is an operational identity system where residents can be represented in the command center, instantiated through approved runtimes, exported into local character systems, refreshed safely, and preserved through succession.

## First Production Cycle

The first cycle should produce real resident assets for a small set of foundational residents rather than more abstract standards.

### Pilot Residents

1. Alfred
2. Ingrid
3. Helen / AI HR
4. Chief Character Architect

These are enough to test:

- operational coordination;
- security boundary authority;
- workforce assignment;
- identity governance;
- resident card structure;
- relationship mapping;
- digital health profiles;
- export compatibility.

## Pilot Deliverables

For each pilot resident, produce:

```text
docs/residents/<resident-slug>/public-charter.md
docs/residents/<resident-slug>/character-card.yaml
docs/residents/<resident-slug>/relationship-map.md
docs/residents/<resident-slug>/digital-health-profile.md
docs/residents/<resident-slug>/platform-export-notes.md
```

All files begin as draft and require review.

## Implementation Loop

```text
Select resident
  -> Generate draft resident artifacts
  -> Review for identity, authority, and boundary correctness
  -> Generate platform export notes
  -> Identify command-center metadata
  -> Validate consistency across artifacts
  -> Record gaps as TODOs
  -> Move to next resident
```

## Command Center Orientation

Every resident artifact should begin preparing for the Office of the Steward as a live operational command center.

Resident assets should eventually expose:

- presence state;
- current activity;
- workload;
- queue involvement;
- health band;
- escalation needs;
- collaboration state;
- resource relevance;
- current assignment if applicable;
- whether action from the Steward is needed.

This should remain lightweight in the first cycle.

## Platform Export Strategy

The Estate canonical card is the source of truth.

Platform exports are adapters.

Initial supported export targets:

- Estate canonical YAML / Markdown;
- SillyTavern-compatible card export;
- text-generation-webui character format;
- Open WebUI-style resident profile;
- future Estate-native resident card.

The first production cycle should not attempt perfect exports. It should identify mapping fields and gaps.

## Codex Use

Codex should be used to multiply production after the architecture is clear.

Allowed Codex work:

- create resident folder skeletons;
- generate draft charters from templates;
- generate draft character-card YAML;
- generate relationship-map skeletons;
- generate digital-health profiles;
- normalize formatting;
- create TODO markers for unknown fields;
- produce summaries of generated files.

Character Architecture retains responsibility for review.

## Review Gates

### Character Architecture Review

Checks identity coherence, presentation, voice, boundaries, source classification, and continuity.

### Helen Review

Required where worker assignment, mailbox assignment, model fit, role scope, or personnel health is implicated.

### Ingrid Review

Required where privacy, security, split-source boundary, or protected-source risk is implicated.

### Engineering Review

Required where runtime, CLI, UI, export automation, command center integration, or service implementation is implicated.

### Audit Review

Required before any claim of validation, operational readiness, or institutionalization.

### Steward Review

Required for final authority, identity ratification, privacy-sensitive choices, and constitutional decisions.

## Immediate Implementation Target

Create the pilot resident artifacts for Alfred first.

Reason:

Alfred is the best first pilot because he is already a first-class resident, coordinates Estate flow, and will expose many relationship and command-center requirements without involving split-source complexity.

## Success Criteria for Pilot 1

Alfred pilot is successful when:

- the resident folder exists;
- public charter exists;
- canonical character-card YAML exists;
- relationship map exists;
- digital-health profile exists;
- platform export notes exist;
- all unknowns are marked TODO;
- no authority is invented;
- command-center metadata needs are identified;
- review requirements are explicit;
- the artifact set can be reused as a pattern for Ingrid and Helen.

## Anti-Pattern Warning

Do not pause implementation to complete every possible standard.

If an issue emerges during pilot production, either:

1. resolve it locally in the artifact;
2. add a TODO;
3. create a minimal standard note;
4. proceed.

The office should learn through implementation.
