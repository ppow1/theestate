# WP-4068 — Resident Trust and Familiarity Evolution

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Resident Relationship Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4051 — Resident Relationship Graph Runtime
- WP-4053 — Dynamic Resident Preference and Personality Evolution
- WP-4063 through WP-4067 — Resident Memory Architecture

## Objective

Implement evidence-backed trust and familiarity evolution on top of the canonical relationship graph so relationships can mature over time without allowing a single conversation, joke, disagreement, or model improvisation to rewrite durable state.

## Required Work

1. Define typed trust and familiarity dimensions with bounded ranges, source lineage, effective dates, confidence, disclosure class, and review state.
2. Reuse the WP-4051 relationship graph and WP-4053 proposal/promotion mechanisms; do not create a competing relationship store or growth engine.
3. Accept evidence from authorized interactions, canonical messages, shared work, approved memories, and explicit Steward or resident declarations according to policy.
4. Distinguish proposed change, observed pattern, approved durable change, temporary context, and rejected change.
5. Support asymmetric trust and familiarity.
6. Apply decay, uncertainty, and contradiction handling without fabricating emotional change.
7. Keep private relationship evolution out of shared surfaces unless explicitly authorized.
8. Expose inspectable diagnostics and rollback lineage.

## Acceptance Tests

1. Repeated evidence may produce a reviewable proposal but not an automatic durable promotion.
2. One flirtatious or hostile turn cannot rewrite trust or familiarity.
3. Asymmetric relationships remain asymmetric.
4. Provider/model changes do not reset approved relationship state.
5. Private Evelyn–Steward evolution remains restricted.
6. Contradictory evidence produces review state rather than arbitrary resolution.
7. Rollback restores the prior approved edge state.

## Deliverables

- trust/familiarity extension schema;
- evidence aggregation and change-proposal logic;
- approval/promotion and rollback integration;
- privacy-filtered runtime loader;
- diagnostics, tests, documentation, and completion receipt.

## Constraints

- Do not create a second relationship graph, preference engine, memory store, or privacy authority.
- Do not infer durable emotional state solely from conversation tone.
- Do not convert familiarity into authority.

## Completion Standard

WP-4068 is complete only when trust and familiarity can evolve through source-lined, reviewable, privacy-scoped proposals on the canonical relationship graph; durable changes require governed promotion; asymmetry and uncertainty remain explicit; and transient model behavior cannot silently rewrite relationships.
