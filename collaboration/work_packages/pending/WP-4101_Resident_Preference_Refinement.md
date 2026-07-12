# WP-4101 — Resident Preference Refinement

**Mode:** SERIES

## Objective
Refine resident preferences into nuanced, evidence-backed tastes while preserving the authority and safeguards of WP-4053.

## Dependencies
- WP-4053 Dynamic Resident Preference and Personality Evolution
- WP-4098 Resident Experience Ledger
- WP-4099 Resident Skill Growth
- WP-4100 Resident Confidence Evolution

## Required Work
1. Extend the existing preference model with context, strength, stability, provenance, exceptions, and last-reviewed metadata.
2. Support refinement from broad tastes into bounded subpreferences without creating duplicate preference authorities.
3. Require repeated or high-significance evidence before durable preference change.
4. Distinguish temporary mood, situational choice, experimentation, aversion, and stable preference.
5. Support resident self-correction and explicit uncertainty.
6. Preserve authored identity anchors and protected traits from accidental drift.
7. Add conflict resolution when evidence supports incompatible preference claims.
8. Provide review and inspection output showing source evidence and change history.

## Non-Goals
- Do not infer intimate or sensitive preferences from weak evidence.
- Do not make residents mirror the Steward automatically.
- Do not replace authored character identity with accumulated telemetry.

## Validation
- Context and exception tests.
- Temporary-versus-durable classification tests.
- Protected-trait tests.
- Contradictory evidence and rollback tests.
- Cross-surface consistency tests.

## Completion Standard
Resident tastes become more specific and believable over time while remaining evidence-based, inspectable, privacy-aware, and governed by the existing personality-evolution architecture.
