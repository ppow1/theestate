# WP-0697 — Codex Campaign Final-Gate Precedence and Specification Alignment

Status: Pending  
Priority: High  
Owner: Chief Architect  
Execution lane: Codex  
Campaign: Engineering campaign execution enablement  
Authority basis: Steward direction, CAMPAIGN-0670 Engineering Department Operationalization, and post-merge verification of PR #414 / WP-0678

## Objective

Correct the final-review-gate precedence defect in the campaign-level Codex execution controller, add regression coverage, and align the governing specification and architecture documentation so the runtime manifest is explicitly a derived execution representation of an already approved campaign rather than a second campaign authority.

## Authoritative Inputs

Read completely before making changes:

1. `collaboration/campaigns/CAMPAIGN_0670_ENGINEERING_DEPARTMENT_OPERATIONALIZATION.md`
2. `collaboration/work_packages/pending/WP-0678_Campaign_Level_Codex_Execution_Capability.md`
3. `collaboration/work_packages/completions/WP-0678_completion_receipt.md`
4. `docs/architecture/codex_campaign_execution_capability.md`
5. `src/estate/core/codex_campaign_execution.py`
6. `tests/test_codex_campaign_execution.py`
7. `AI_COMMUNICATION_HINTS.md`

## Constitutional Safeguard

Do not create a second scheduler, dispatch queue, validation path, campaign authority, acceptance authority, or constitutional role. `CodexCampaignManifest` and `CodexCampaignPackage` must remain derived runtime execution records sourced from an already approved authoritative campaign and its work packages. They may not supersede or redefine the canonical campaign documents, PTM, dispatch, readiness, validation, mailbox, repository-evidence, or acceptance systems.

## Defect to Correct

In `CodexCampaignExecution.record_commit()`, a final package that also completes an internal review gate can first place the campaign in `awaiting_review` and then be immediately overwritten to `awaiting_acceptance` because the all-packages-complete check runs afterward. This clears `active_gate` and permits the final review gate to be bypassed.

## Required Implementation

1. Preserve review-gate precedence when a completed package satisfies a configured gate, including when it is the final package.
2. When a gate is reached, the campaign must remain `awaiting_review` with `active_gate` populated until an identified reviewer approves it.
3. Update `approve_gate()` so:
   - if all packages are complete after approval, transition to `awaiting_acceptance`;
   - otherwise transition to `running`.
4. Add regression tests proving:
   - a gate attached to the final package cannot be bypassed;
   - `next_launches()` returns no work while the campaign awaits that gate;
   - approving the final gate transitions to `awaiting_acceptance`;
   - a non-final gate still resumes normal execution.
5. Preserve durable append-only transition history and record the gate approval event before final acceptance readiness.
6. Update `docs/architecture/codex_campaign_execution_capability.md` to state unambiguously that the runtime manifest and package records are derived execution views of canonical approved sources and create no competing governance.
7. Restore `WP-0678_Campaign_Level_Codex_Execution_Capability.md` as a complete, coherent canonical work-package document. Preserve its established intent and constitutional safeguard; do not broaden its scope or retroactively claim authority not present in CAMPAIGN-0670.
8. Update or add the appropriate completion evidence for WP-0697 without rewriting WP-0678's historical completion receipt except where a narrowly factual cross-reference is required.

## Validation

At minimum run:

- `python -m pytest -q tests/test_codex_campaign_execution.py`
- the relevant campaign-runtime and Codex bridge tests already used by WP-0678
- `python -m compileall -q src/estate/core/codex_campaign_execution.py`
- `git diff --check`

Report the exact commands and results in the completion receipt.

## Acceptance Criteria

This work package is complete only when:

- the final review gate cannot be bypassed;
- final gate approval transitions correctly to `awaiting_acceptance`;
- non-final gate behavior remains correct;
- regression tests pass;
- the runtime manifest is documented as derived and non-authoritative;
- WP-0678 is restored as a complete canonical specification;
- no duplicate campaign governance, scheduler, dispatch, validation, or acceptance mechanism is introduced;
- the working tree is clean after the bounded implementation commit.

## Deliverables

- corrected `src/estate/core/codex_campaign_execution.py`;
- updated regression tests;
- updated architecture documentation;
- restored complete WP-0678 specification;
- `collaboration/work_packages/completions/WP-0697_completion_receipt.md`.

## Codex Handoff

> Read `collaboration/work_packages/pending/WP-0697_Codex_Campaign_Final_Gate_Precedence_and_Specification_Alignment.md` and do exactly what it says. Do not merge.