# ARCHITECTURE-FIRST TASK WP-0017 — Work Package State Machine

## Steward Command
Open `collaboration/work_packages/pending/WP-0017_ARCHITECTURE_FIRST_work_package_state_machine.md` in `ppow1/theestate` and execute the directions inside only after Chief Architect review authorizes implementation.

## Mode
ARCHITECTURE-FIRST. Depends conceptually on WP-0016 Work Package Registry.

## Mission
Design the canonical state machine for Estate work packages so packages can move through consistent, auditable states.

## Why This Is Next
The Estate is no longer just creating tasks. It is operating work across Codex, Chief Architects, Alfred, Audit, and the Steward. Work needs durable state transitions.

## Required Design Questions
Define states for proposed, approved, pending, assigned, in_progress, codex_done, ca_review_pending, ca_verified, merge_authorized, merged, validation_pending, operationally_validated, blocked, parked, superseded, and closed. Define allowed transitions and which office/role may trigger each transition.

## Expected Output
A design document or ADR proposal plus a follow-on Codex implementation package.

## Constraints
Do not implement state automation until the state model is reviewed. Do not redefine Estate lifecycle states.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0017_architecture_done.json` with status, summary, open_questions, and ready_for_codex_package.

## Merge Class
Class B — architecture/governance-adjacent.
