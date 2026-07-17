# WP-0697 — Engineering Department Operational Integration

## Campaign
CAMPAIGN-0681 — Estate Operationalization

## Purpose
Integrate Engineering Department execution signals, ownership boundaries, work-package state, and implementation evidence into the Estate operational model without creating a second engineering workflow.

## Objectives
- Map canonical Engineering Department records into the operational state contract established by WP-0689.
- Expose current engineering capacity, active implementation lanes, blocked work, review state, and validation posture.
- Preserve existing Engineering authority, acceptance, dispatch, and repository conventions.
- Provide Grace and authorized operational surfaces with read-only visibility into engineering momentum and limiting dependencies.

## Required Work
1. Identify canonical Engineering Department sources for work-package state, campaign membership, ownership, review, validation, and acceptance.
2. Define adapters from those sources into the shared operational event and state vocabulary.
3. Define freshness, provenance, confidence, and conflict-handling rules for engineering signals.
4. Define the minimum operational projection for active, queued, blocked, validating, accepted, paused, and abandoned work.
5. Ensure all projected state links back to authoritative repository evidence.

## Constraints
- Do not redefine Engineering Department governance.
- Do not grant Grace, Helen, Alfred, or an observer authority to dispatch, accept, merge, or close Engineering work.
- Do not duplicate PTM, campaign, work-package, PR, review, or validation systems.
- Operational projections are derived views, not authoritative records.

## Deliverables
- Canonical Engineering signal inventory.
- Engineering-to-operational-state mapping.
- Provenance and freshness contract.
- Read-only Engineering operational projection.
- Conflict and stale-signal behavior.
- Tests covering representative engineering state transitions.

## Acceptance Criteria
- Engineering work can be observed through the shared operational model.
- Every projected status is traceable to canonical evidence.
- Conflicting or stale evidence is surfaced rather than silently resolved.
- No new authority path or parallel engineering workflow is introduced.

## Dependencies
- WP-0688
- WP-0689
- WP-0690
- WP-0692
- WP-0693

## Constitutional Precedence
CAMPAIGN-0670, accepted Engineering deliverables, and existing Engineering governance remain authoritative. This work package only integrates Engineering signals into CAMPAIGN-0681 operational visibility.