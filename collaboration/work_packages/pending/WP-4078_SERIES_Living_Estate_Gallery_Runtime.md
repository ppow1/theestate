# WP-4078 — Living Estate Gallery Runtime

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Visual Systems Integration
Execution Target: Codex
Classification: Estate Internal
Priority: High

## Depends On

- WP-4073 — Resident Visual Identity Framework
- WP-4074 — Estate Wardrobe Runtime
- WP-4075 — Canonical Estate Location Library
- WP-4076 — Character Presentation and Pose Framework
- WP-4077 — Visual Continuity Runtime

## Objective

Implement one governed Living Estate Gallery runtime that turns approved resident and location imagery into a persistent, source-lined visual history rather than a collection of disconnected generations.

## Required Work

1. Define canonical gallery-item, collection, event, participant, location, wardrobe, continuity, classification, and source-lineage schemas.
2. Register only approved visual artifacts generated through or reconciled with the canonical visual identity and continuity systems.
3. Support resident portraits, staff group images, ceremonies, project milestones, daily-life scenes, seasonal events, and historical moments.
4. Record creation time, depicted time, participants, location, wardrobe, visual-state version, prompt/model lineage where permitted, review state, and supersession status.
5. Preserve private or restricted imagery under Ingrid-governed disclosure rules.
6. Distinguish canonical visual evidence, illustrative concept art, historical reconstruction, projection, and rejected generation.
7. Expose gallery queries by resident, date, event, location, relationship, and collection without leaking protected metadata.
8. Integrate with Estate surfaces without making the gallery a second resident registry, memory system, or document authority.

## Acceptance Tests

1. Approved images register with complete source lineage and continuity metadata.
2. Rejected or unreviewed generations cannot appear as canonical visual history.
3. Private resident or Steward imagery is unavailable to unauthorized surfaces.
4. A resident remains visually recognizable across multiple gallery items and model changes.
5. Historical reconstruction is clearly labeled and never presented as direct evidence.
6. Gallery searches return deterministic, privacy-filtered results.
7. Superseded visual artifacts remain auditable without appearing as current references.
8. Missing lineage or identity mismatch blocks canonical registration.

## Deliverables

- gallery schemas and storage/index contracts;
- governed registration and review workflow;
- privacy-filtered query interfaces;
- Estate surface integration;
- fixtures, tests, documentation, and completion receipt.

## Constraints

- Do not create a second identity, memory, privacy, or archival authority.
- Do not treat every generated image as canonical.
- Do not expose private visual material through shared surfaces.
- Do not discard rejected or superseded lineage needed for audit.

## Completion Standard

WP-4078 is complete only when approved Estate imagery can be registered, classified, queried, and displayed as a persistent visual history with reliable resident continuity, complete lineage, explicit authority state, and privacy-safe access.