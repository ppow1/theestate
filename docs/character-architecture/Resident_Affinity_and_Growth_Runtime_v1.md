# Resident Affinity and Growth Runtime v1

Campaign 06 implements WP-4093 through WP-4102 as an evidence-backed runtime for resident relationships and development.

The runtime extends the canonical relationship layer with directional affinity dimensions, trust and respect evidence, friendship and mentorship evaluation, protective support proposals, an append-only experience ledger, evidence-reviewed skill growth, domain confidence, governed preference refinement, and candidate/accepted milestones.

## Boundaries

- Affinity, confidence, skill, support, preference, and milestone state never grants authority, consent, access, privacy bypass, task priority, credentials, or governance rights.
- Protected dimensions such as attraction and private affection are redacted unless the caller has restricted/private/admin clearance.
- The experience ledger is append-only; corrections supersede records rather than mutating or deleting them.
- Skill growth and milestones remain reviewable proposals unless accepted by the appropriate institution.
- Support behavior offers bounded help and routes urgent concerns to existing institutions.

## Persistence and migration

- `runtime/resident_affinity/affinity_graph.json` stores migrated and current directional affinity state.
- `runtime/resident_growth/experience_ledger.jsonl` stores append-only experience events.
- `runtime/resident_growth/skill_profiles.json`, `confidence_profiles.json`, `preference_refinements.json`, and `milestones.json` store reviewed growth projections.
- Legacy relationship hints from `data/relationships/resident_relationships.json` migrate into bounded familiarity dimensions with source lineage.
