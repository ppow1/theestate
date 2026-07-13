# Chief Character Architect Codex Campaign

## Campaign

Character Architecture Post-Hardening Validation and Repair

## Status

Ready for execution

## Authority and scope

PR #319 repaired canonical pytest collection and hardened Character Architecture runtime boundaries. Its full-suite validation collected 1255 tests and completed with 1233 passed and 22 functional failures.

This campaign is limited to identifying, classifying, repairing, and validating those remaining failures and any directly demonstrated Character Architecture integration defects. It must not activate Grace, redesign settled architecture, broaden into unrelated feature work, or treat historical pending-directory placement as execution authority.

## Required starting state

1. Begin from the latest `main` after PR #319.
2. Read completely:
   - `docs/character-architecture/Character_Architecture_Runtime_Hardening_v1.md`
   - `operations/character_architecture/character_architecture_hardening_verification_report.md`
   - `operations/character_architecture/character_architecture_hardening_remaining_issues.md`
   - `collaboration/work_packages/completions/WP-character-architecture-hardening_codex_done.json`
3. Confirm Grace remains appointed/onboarding, not operational, not gateway-exposed, and not Steward-activated.

## Objective

Establish a verified clean post-hardening baseline by resolving the 22 remaining full-suite failures, or by producing precise owner-routed blockers for failures that cannot be safely repaired within this campaign.

## Execution procedure

1. Run `python -m pytest -q` and capture the exact failing test list and traceback for every failure.
2. Classify each failure by subsystem and root cause.
3. Separate:
   - regressions introduced by Character Architecture campaigns or PR #319;
   - pre-existing failures exposed by repaired collection;
   - stale tests or fixtures;
   - environment-dependent failures;
   - genuine cross-runtime integration defects.
4. Repair all failures that are safely within Character Architecture scope.
5. For failures owned by another office or subsystem, do not redesign or silently patch around their authority. Create a precise remaining-issues entry with test name, traceback summary, owning subsystem, evidence, and recommended next action.
6. Re-run focused tests after each repair group.
7. Re-run the complete canonical suite.
8. Do not weaken assertions, skip tests, xfail tests, reduce discovery, or exclude additional test trees merely to produce a green result unless repository governance explicitly requires that behavior and the change is documented and justified.

## Mandatory validation

- `python -m pytest --collect-only -q`
- `python -m pytest -q`
- focused tests for every modified subsystem
- compile or static validation for every modified Python module
- explicit Grace lifecycle and gateway tests
- explicit resident memory, affinity/growth, presence/culture, visual runtime, and Steward-awareness integration tests

## Stop conditions

Stop and report rather than guessing when:

- a repair requires activation of Grace;
- a test contradicts repository governance or authoritative lifecycle state;
- a failure belongs to another office and cannot be safely repaired without changing its settled architecture;
- a migration, destructive data rewrite, or authority-boundary change is required;
- the same failure recurs after two evidence-based repair attempts.

## Deliverables

Produce one coherent branch and one pull request containing:

1. all safe repairs;
2. a failure ledger listing all original 22 failures and final disposition;
3. exact test commands and results;
4. a post-repair Character Architecture health report;
5. a remaining-issues report for any unresolved failures;
6. a completion receipt identifying files changed, tests run, known limitations, and review authority required.

## Completion condition

The campaign is complete only when either:

- the complete canonical suite passes; or
- every unresolved failure has a precise, evidence-backed owner, blocker, and next action, with no Character Architecture regression left unresolved.
