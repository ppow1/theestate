# ESTATE-CAP-003 — Merge PR #507 and Close Capability Onboarding Standard

## Objective

Complete the Estate Capability Onboarding Standard campaign by performing final merge authorization checks for PR #507, merging it normally if safe, validating the merged state, and recording a concise closeout.

This is not authorization to begin another implementation campaign or to implement any worked-example provider.

## Authorized scope

PR: #507  
Branch: `architecture/estate-capability-onboarding-standard`  
Reviewed head: `72313dacd172fcd42b8db57f0f5ddd877d0bb218`

The reviewed deliverables include:

- Estate-wide capability onboarding standard;
- executor-neutral implementation template;
- operator runbook;
- readiness checklist;
- worked examples;
- resident capability manifest schema;
- onboarding lint and regression tests;
- blocking-review report.

## Step 1 — Final merge verification

Confirm:

- PR #507 is open, ready for review, unmerged, mergeable, and targets `main`;
- head is exactly `72313dacd172fcd42b8db57f0f5ddd877d0bb218`;
- local and remote branch heads match;
- no unresolved review threads or submitted blocking review exists;
- no failed or pending required check is visible;
- the final diff contains only the intended onboarding-standard files, schema, lint/test changes, and review evidence;
- no Qwen Coder, Whisper, ComfyUI live execution, Historian, or Legal provider implementation is present;
- institutional acceptance is not granted;
- worktree is clean and all stashes are preserved.

If a new concrete blocker is discovered, stop and report it. Do not broaden scope.

## Step 2 — Merge

If final verification passes:

- merge PR #507 normally;
- do not squash or rewrite history unless repository policy requires it;
- switch to `main` and fast-forward to `origin/main`;
- confirm the merge commit is present;
- confirm PR #507 is merged and closed.

## Step 3 — Post-merge validation

Run a bounded post-merge validation sufficient to prove the merged standard is intact:

- onboarding/schema/work-package focused tests;
- resident capability manifest Draft 2020-12 validation with FormatChecker;
- onboarding template lint;
- incomplete-package negative lint;
- Python compilation for changed Python files;
- tracked JSON parsing for changed JSON/schema files;
- `git diff --check`;
- clean worktree confirmation.

Reconfirm the two temporary-root CLI failures remain inherited and unchanged if they are still present. Do not fix them in this closeout.

## Step 4 — Closeout report

Create one concise durable report under:

`docs/operations/reviews/ESTATE-CAP-003_PR507_Merge_and_Closeout_20260731.md`

Record:

- reviewed head;
- merge commit;
- final main head;
- files and contracts established;
- tests and validation results;
- inherited unrelated failures;
- confirmation that no worked-example provider was implemented or invoked;
- confirmation that institutional acceptance remains separate;
- confirmation that future capability onboarding should use the new standard, template, runbook, checklist, and resident manifest contract;
- exact next Steward action: use the framework for the next real capability request rather than creating another standards campaign.

Commit and push the closeout report directly on `main` after the merge.

## Preservation

- Do not implement any worked-example provider.
- Do not create another capability-onboarding architecture package.
- Do not grant institutional acceptance.
- Do not modify models or local services.
- Preserve stashes.
- Leave `A:\theestate` untouched.

## Completion condition

The campaign is complete when PR #507 is merged, post-merge validation passes, the closeout report is committed to `main`, local and remote `main` match, and the worktree is clean.

After completion, stop and wait for the Steward's next assignment.
