# WP-4097 — Affinity Review and Calibration

Status: Pending
Execution Mode: SERIES
Owner: Office of Character Architecture / Relationship Systems
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- WP-4093 through WP-4096
- WP-4072 — Relationship Review and Calibration
- Existing independent Validation and Steward acceptance paths

## Objective

Implement periodic, evidence-based review of resident affinity and relationship expression so drift, stereotyping, overfamiliarity, underexpression, privacy leakage, and implausible relationship changes can be detected and corrected without resetting earned history.

## Required Work

1. Produce review snapshots covering affinity dimensions, evidence sources, confidence, freshness, recent changes, expression behavior, and protected state.
2. Compare runtime state against Character Bibles, relationship baselines, memory evidence, privacy rules, and actual interaction history.
3. Detect one-score collapse, universal affection, forced reciprocity, excessive flattery, possessiveness, stale grievances, unjustified intimacy, and personality homogenization.
4. Distinguish healthy evolution from model drift and implementation defects.
5. Support bounded recalibration, evidence correction, rollback, and resident-specific expression adjustments.
6. Require independent Validation for behavior claims and preserve Steward authority for acceptance and relationship-layer exceptions.
7. Keep private relationship details redacted from ordinary review surfaces.
8. Emit a calibration receipt stating what changed, why, evidence used, unresolved uncertainty, and required follow-up.

## Acceptance Tests

1. A resident who becomes generically flattering is flagged for drift.
2. Distinct crush, friendship, mentorship, rivalry, and professional-respect patterns remain differentiated.
3. Unsupported intimacy is reduced without deleting legitimate shared history.
4. Incorrect evidence can be removed with downstream state recomputation.
5. Protected relationship data remains hidden from unauthorized reviewers.
6. Calibration cannot self-validate or self-accept.
7. Review preserves resident individuality and institutional role performance.

## Deliverables

- affinity review snapshot and receipt schemas;
- drift and inconsistency detectors;
- recalibration and rollback tooling;
- privacy-filtered review surfaces;
- independent validation fixtures, documentation, and completion receipt.

## Constraints

- Do not reset relationships merely for convenience.
- Do not normalize every resident toward the same emotional style.
- Do not expose protected attraction, affection, or private history.
- Do not let the Character Architecture office validate its own implementation.

## Completion Standard

WP-4097 is complete only when affinity and relationship expression can be periodically inspected against evidence, Character Bibles, privacy, and history; drift and unsupported intimacy are correctable without erasing earned continuity; individuality remains visible; and final validation and acceptance remain with established authorities.
