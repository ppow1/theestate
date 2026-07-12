# WP-4099 — Resident Skill Growth

**Mode:** SERIES

## Objective
Implement evidence-backed resident skill development that changes gradually through practice, instruction, completed work, and reviewed outcomes.

## Dependencies
- WP-4098 Resident Experience Ledger
- Existing resident identity, memory, and preference evolution systems

## Required Work
1. Define a canonical skill profile schema with skill ID, domain, current level, confidence, evidence references, practice history, review status, and decay policy.
2. Create a registry for approved skill domains and level semantics; reject arbitrary runtime-created skill labels.
3. Implement growth proposals derived from ledger evidence, with configurable thresholds and bounded increments.
4. Require stronger evidence for high-level advancement than for novice growth.
5. Support instruction, deliberate practice, project outcomes, peer review, and demonstrated transfer as distinct evidence types.
6. Prevent task completion alone from proving mastery.
7. Add regression or staleness handling without erasing historical achievement.
8. Expose diagnostics and review tools explaining why a skill changed or did not change.

## Non-Goals
- Do not gamify residents with public XP bars.
- Do not allow unbounded or instant expertise.
- Do not overwrite role qualifications or governance-controlled credentials.

## Validation
- Threshold and bounded-growth tests.
- Evidence-strength tests across skill levels.
- Duplicate evidence and replay tests.
- Staleness and restoration tests.
- Explanation and provenance tests.

## Completion Standard
Resident skills evolve slowly, transparently, and only from sufficient evidence, while historical capability and governance-controlled qualifications remain intact.
