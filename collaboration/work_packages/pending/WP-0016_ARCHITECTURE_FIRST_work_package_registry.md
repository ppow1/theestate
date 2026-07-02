# ARCHITECTURE-FIRST TASK WP-0016 — Work Package Registry

## Steward Command
Open `collaboration/work_packages/pending/WP-0016_ARCHITECTURE_FIRST_work_package_registry.md` in `ppow1/theestate` and execute the directions inside only after Chief Architect review authorizes implementation.

## Mode
ARCHITECTURE-FIRST. Do not implement until CA review defines the registry model.

## Mission
Design the Estate Work Package Registry so work packages become institutional objects rather than transient prompts.

## Required Architectural Decisions
Define fields for ID, title, status, mode, owner, source request, dependencies, Codex suitability, merge class, validation state, completion marker, CA review record, and relation to missions/boards.

## Expected Output
A design document or ADR proposal under `docs/operations/` or `Architecture/ADR/` with a follow-on Codex implementation package.

## Constraints
Do not implement a registry schema directly without architectural approval. Do not change governance or lifecycle states.

## Completion Signal
If producing design only, create `collaboration/work_packages/completions/WP-0016_architecture_done.json` with ready_for_codex_package=false unless an implementation package is also explicitly created.

## Merge Class
Class B — architecture/governance-adjacent. Requires CA review before implementation.
