# WP-0654 — Wire `estate-main` Production Readiness Policy and Fail-Closed Intake

## Status

Pending implementation.

## Owner

Office of Chief Architect, implemented through Engineering in the existing Operational Readiness Closure Controller and canonical operational-target metadata.

## Objective

Repair the existing canonical Operational Readiness Closure Controller in place so the `estate-main` production target always loads and enforces its canonical production-readiness policy, publication requirements, live validation, observation requirements, and allowed remediation handlers.

This is a defect repair and integration completion for WP-0650 through WP-0653. Do not create a replacement controller, second policy system, parallel target registry, new scheduler, new queue, or new institutional structure.

## Confirmed Live Failure

Live acceptance case `orc-12044699f410df08` for WP-0653 incorrectly reached `operationally_ready` while:

- `readiness_policy` was empty;
- `publication` was empty;
- `publish_controller_mutation` was absent from `allowed_remediations`;
- validation was only `python -m compileall src/estate/core/operational_readiness_closure.py`;
- observation required one immediate cycle;
- elapsed observation time was zero;
- no health checks were declared;
- local `main` remained ahead of `origin/main`;
- `origin/main` did not contain the local controller-authored commit.

The controller mechanisms added by WP-0653 existed, but the canonical `estate-main` target and intake path did not load or enforce them.

## Required Outcome

After this repair, every readiness case targeting `estate-main` must fail closed unless canonical production metadata is present and complete.

The controller must not permit caller-supplied or default values to weaken canonical target policy.

A case for `estate-main` may reach `operationally_ready` only after all applicable gates are proven:

1. canonical target policy loaded;
2. required merge commit present in deployed target ancestry;
3. controller-authored canonical mutations published upstream;
4. upstream fetched and verified to contain the published commit;
5. local and upstream branch synchronized;
6. working tree clean;
7. declared live validation passed against the actual target;
8. declared reachability and health checks passed;
9. declared observation cycles and elapsed-duration requirements passed;
10. restart evidence passed when policy requires it;
11. no unresolved blockers remain;
12. institutional acceptance remains separate.

## Canonical `estate-main` Target Policy

Use or extend the existing canonical operational-target metadata. Do not create a second registry.

The `estate-main` target must explicitly declare at least:

- target identity and repository;
- production environment classification;
- managed checkout path;
- base branch and upstream;
- live target path;
- publication required;
- publication authorized under the existing non-destructive authority model;
- allowed remediation handlers including `publish_controller_mutation` where applicable;
- the canonical validation recipe for the controller/runtime change;
- reachability and health checks;
- observation policy with explicit cycle count;
- minimum elapsed time or a reviewed non-applicable rationale;
- restart-event requirement or an explicit non-applicable rationale;
- acceptance authority;
- evidence location.

Do not silently use compile-only fallback validation or one-cycle zero-duration observation for `estate-main`.

## Fail-Closed Intake

Repair all readiness intake paths, including manual CLI intake and Merge Discovery intake.

For a production target:

- canonical target metadata is authoritative;
- caller arguments may add case-specific facts but must not weaken or replace production policy;
- missing required metadata must create exact policy blockers;
- missing policy must prevent validation, observation, and readiness declaration;
- defaults suitable for non-production or repository-only targets must never be applied to `estate-main`;
- case persistence must retain the resolved canonical policy so restart or resume does not lose it;
- existing cases with empty or weakened policy must be rehydrated from current canonical target metadata before further processing.

## False-Readiness Correction

The controller must detect prior readiness verdicts that do not satisfy current canonical policy.

For case `orc-12044699f410df08`, and generically for equivalent cases:

- preserve the original evidence;
- mark the prior verdict superseded or invalidated with a reason;
- return the case to the correct active or blocked state;
- do not delete or rewrite historical evidence;
- require publication and all production gates before issuing a new verdict.

Do not hard-code this case ID into production logic. Use generic policy-version and evidence-completeness checks.

## Unpublished Commit Recovery

The live repository may contain attributable controller-authored commits ahead of upstream, including the current acceptance residue.

The controller must:

1. verify the checkout is clean;
2. verify branch and upstream identity;
3. verify ahead commits are attributable to authorized controller remediations or otherwise explicitly authorized;
4. fetch upstream;
5. refuse divergence, dirty state, ambiguous authorship, or non-fast-forward publication;
6. invoke `publish_controller_mutation` when target policy permits;
7. push without force;
8. fetch again;
9. verify upstream ancestry contains the published local HEAD;
10. verify ahead/behind is `0 0`;
11. record complete publication evidence;
12. resume the same readiness case automatically.

## State and Verdict Requirements

The controller must not enter or retain `operationally_ready` when any of the following are true:

- production policy missing or incomplete;
- publication required but not verified;
- local branch ahead of or behind upstream;
- working tree dirty;
- validation recipe is fallback-only without explicit sufficiency rationale;
- required health or reachability evidence missing;
- observation cycles or elapsed time incomplete;
- required restart evidence missing;
- deployed target does not contain the required merge commit.

Verdict fields must be derived from evidence, including:

- policy source and version/hash;
- local and upstream revisions;
- publication status and evidence;
- validation recipe and evidence;
- health/reachability evidence;
- observation requirements and progress;
- superseded verdict references where applicable.

## Office and CLI Visibility

Extend the existing Office and CLI surfaces only.

Expose:

- canonical policy loaded or missing;
- policy source and version/hash;
- publication required/authorized/status;
- local and upstream revisions and ahead/behind state;
- validation policy and result;
- observation requirements and progress;
- invalidated/superseded readiness verdicts;
- exact next action or blocker.

Do not create a new dashboard.

## Safety and Authority

Preserve all existing restrictions:

- no force push;
- no force reset;
- no discarded local work;
- no history rewriting;
- no branch deletion;
- no branch-protection bypass;
- no fabricated credentials;
- no arbitrary generated shell execution;
- no speculative repair;
- no automatic institutional acceptance.

## Required Tests

Add focused tests proving:

1. `estate-main` resolves canonical production policy on every intake path;
2. manual intake cannot weaken canonical policy;
3. Merge Discovery intake receives the same policy;
4. persisted legacy cases are rehydrated with current canonical policy;
5. missing policy fails closed;
6. compile-only fallback cannot pass production readiness;
7. zero-duration one-cycle observation cannot pass without explicit rationale;
8. unpublished attributable controller commits invoke governed publication;
9. upstream containment and `0 0` synchronization are required;
10. unauthorized or divergent publication blocks safely;
11. false readiness verdicts are preserved and superseded, not deleted;
12. institutional acceptance remains false;
13. Office and CLI surfaces show policy and publication truthfully.

## Live Windows Acceptance

Run live acceptance on the configured Windows Estate environment.

The acceptance must use a fresh or correctly reopened readiness case and prove:

- `estate-main` loads non-empty canonical production policy;
- `publish_controller_mutation` is available when authorized;
- existing safe attributable local commits are published without manual `git push`;
- `origin/main` contains the resulting local HEAD;
- local and remote are `0 0` ahead/behind;
- the checkout remains clean;
- the controller refuses readiness until explicit live validation and observation gates pass;
- the old false readiness verdict is invalidated or superseded with preserved evidence;
- the case resumes automatically after publication;
- the final verdict is evidence-backed;
- institutional acceptance remains separate.

## Deliverables

- in-place controller repair;
- canonical `estate-main` target metadata update;
- intake and legacy-case rehydration repair;
- false-verdict supersession logic;
- publication recovery integration;
- tests;
- validation recipe;
- live Windows acceptance evidence;
- updated Office/CLI projection;
- completion receipt.

## Completion Standard

This work is complete only when a live Windows acceptance demonstrates the full path without manual Git publication or policy injection.

A test-only or Linux-only simulation is insufficient for production completion.

## Work package filename

`WP-0654_Wire_Estate_Main_Production_Readiness_Policy_and_Fail_Closed_Intake.md`

## Repository path

`collaboration/work_packages/pending/WP-0654_Wire_Estate_Main_Production_Readiness_Policy_and_Fail_Closed_Intake.md`

## Codex handoff command

Use the GitHub repository `https://github.com/ppow1/theestate`, branch `main`, and implement this complete work package from its repository-relative path. Create an implementation branch from current `main`, preserve the existing canonical controller, run all required tests and live Windows acceptance, push the branch, and open a pull request against `main`.