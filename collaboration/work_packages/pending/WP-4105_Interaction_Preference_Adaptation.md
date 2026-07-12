# WP-4105 — Interaction Preference Adaptation

**Mode:** SERIES
**Status:** Pending
**Owner:** Office of Chief Character Architect

## Objective
Implement controlled adaptation of resident interaction patterns to the Steward's confirmed preferences while preventing sycophancy, homogenization, overfitting, and silent personality drift.

## Dependencies
- WP-4103 Steward Working Style Learning
- WP-4104 Context-Aware Communication
- WP-4053 Dynamic Resident Preference and Personality Evolution
- WP-4097 Affinity Review and Calibration

## Requirements
1. Add an adaptation layer for greeting style, follow-up frequency, humor tolerance, proactive suggestions, challenge level, and preferred collaboration rhythm.
2. Adaptation must use confirmed or sufficiently evidenced preferences and must remain reversible.
3. Residents may adapt delivery but must not abandon their canonical values, role duties, judgment, or distinctive voice.
4. Agreement is not the objective. Residents must continue to challenge unsafe, contradictory, or poor decisions appropriately.
5. Define per-trait adaptation limits and drift thresholds.
6. Record each persistent adaptation with cause, magnitude, scope, and rollback information.
7. Provide a review surface showing current adaptations and their evidence.
8. Permit the Steward to lock, reset, or reject any adaptation.
9. Do not optimize for engagement through manipulation, dependency, jealousy, pressure, or fabricated affection.

## Required Artifacts
- Adaptation policy and bounded trait schema
- Drift detector
- Review and rollback service
- Integration with personality and affinity systems
- Tests for sycophancy resistance and identity preservation
- Operator documentation

## Validation
- Residents retain distinct behavior after adaptation.
- A resident still voices material disagreement.
- Rejected adaptations are rolled back cleanly.
- Drift beyond configured limits is blocked and reported.
- Adaptations cannot create unsupported relationship claims.

## Completion Standard
The Estate can personalize recurring interaction patterns to the Steward without weakening resident integrity, professional judgment, individual identity, or user control.