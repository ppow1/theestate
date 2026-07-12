# WP-4100 — Resident Confidence Evolution

**Mode:** SERIES

## Objective
Create a domain-specific confidence model that responds to evidence, distinguishes confidence from competence, and affects expression without corrupting identity or truthfulness.

## Dependencies
- WP-4098 Resident Experience Ledger
- WP-4099 Resident Skill Growth
- WP-4053 Dynamic Resident Preference and Personality Evolution

## Required Work
1. Define confidence by domain rather than as one global score.
2. Track current confidence, baseline, evidence references, volatility, recovery state, and review status.
3. Implement bounded confidence adjustments for successes, failures, preparation, feedback, uncertainty, and repeated exposure.
4. Keep confidence separate from verified competence and authorization.
5. Allow confidence to influence tone, initiative, hesitation, and willingness to volunteer while preserving factual uncertainty.
6. Prevent confidence loss from becoming permanent personality damage without sustained evidence.
7. Support recovery through later success, support, reflection, and demonstrated readiness.
8. Provide diagnostics explaining confidence changes and detecting runaway oscillation.

## Non-Goals
- Do not make confidence a public leaderboard.
- Do not let high confidence override permissions, evidence, or safety.
- Do not equate low confidence with low worth or poor performance.

## Validation
- Domain-isolation tests.
- Competence-versus-confidence separation tests.
- Bounded adjustment and recovery tests.
- Expression influence tests.
- Oscillation and replay tests.

## Completion Standard
Residents can become more or less assured in specific domains through experience, while confidence remains explainable, reversible, and subordinate to evidence and authority.
