# WP-4104 — Context-Aware Communication

**Mode:** SERIES
**Status:** Pending
**Owner:** Office of Chief Character Architect

## Objective
Use verified Steward working-style preferences and current interaction context to select an appropriate communication mode without suppressing material facts or inventing emotional certainty.

## Dependencies
- WP-4103 Steward Working Style Learning
- WP-4047 Resident Conversation Isolation
- WP-4054 Multi-Resident Turn Management

## Requirements
1. Implement a communication-policy service that considers surface, office, urgency, task complexity, current session state, and verified Steward preferences.
2. Support bounded modes such as concise execution, normal collaboration, detailed review, incident response, and reflective discussion.
3. Mode selection must be explainable and logged with the evidence used.
4. Urgent risks, blockers, contradictions, and uncertainty may never be hidden merely to satisfy a brevity preference.
5. Residents must retain their individual voice while adapting structure, pacing, and amount of detail.
6. Do not infer fatigue, anger, distress, or other internal states without explicit evidence; use neutral uncertainty where needed.
7. Allow the Steward to override the current mode immediately.
8. Keep adaptation scoped to the active conversation unless a verified persistent preference applies.
9. Provide deterministic fallback behavior when preference or context data is unavailable.

## Required Artifacts
- Communication mode schema
- Policy evaluator and explanation record
- Resident-facing adapter
- Override mechanism
- Tests covering urgency, ambiguity, and conflicting preferences
- Operator documentation

## Validation
- A concise preference does not remove critical warnings.
- Two residents preserve distinct voices under the same mode.
- Explicit mode changes apply immediately.
- Unsupported emotional assumptions are not introduced.
- Missing context falls back safely and consistently.

## Completion Standard
Residents can adapt how they communicate with the Steward based on verified context and preferences while preserving truthfulness, individual character, and full disclosure of material information.