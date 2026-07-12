# WP-4103 — Steward Working Style Learning

**Mode:** SERIES
**Status:** Pending
**Owner:** Office of Chief Character Architect

## Objective
Implement a bounded runtime that learns the Steward's stable working-style preferences from explicit instructions and repeated evidence without treating guesses, one-off moods, or private inference as fact.

## Dependencies
- WP-4063 through WP-4067 memory runtime
- WP-4093 through WP-4097 affinity runtime
- Existing repository authority and privacy rules

## Requirements
1. Add a canonical working-style profile for the Steward with evidence-backed fields for preferred detail level, pacing, interruption tolerance, command style, review cadence, and tool/workflow preferences.
2. Every learned value must carry source, timestamp, confidence, scope, and last-confirmed metadata.
3. Explicit Steward instruction outranks inferred or historical behavior.
4. Repeated behavior may raise confidence only through a deterministic rule; a single interaction must not silently establish a permanent preference.
5. Separate global preferences from office-, project-, session-, and surface-specific preferences.
6. Provide APIs to read, propose, confirm, supersede, and retire profile entries.
7. Record changes in an append-only audit trail.
8. Do not store intimate, medical, financial, or unrelated personal facts in this profile.
9. Do not create a second memory or preference institution; integrate with existing memory and evolution systems.

## Required Artifacts
- Working-style schema and persistence adapter
- Evidence aggregation and confidence rules
- Read/update service
- Audit history
- Unit and integration tests
- Operator documentation

## Validation
- Explicit instructions override contrary inferences.
- Session-only preferences do not leak into global scope.
- Low-confidence proposals remain marked as proposals.
- Contradictory evidence is preserved and resolved deterministically.
- Unsupported sensitive fields are rejected.

## Completion Standard
The Estate can accurately retrieve and update a bounded, evidence-backed description of how the Steward prefers to work, while preserving provenance, scope, privacy, and manual control.