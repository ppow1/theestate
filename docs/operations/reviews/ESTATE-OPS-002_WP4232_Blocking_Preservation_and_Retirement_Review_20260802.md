# ESTATE-OPS-002 WP-4232 Blocking Preservation and Retirement Review

Review date: 2026-08-02  
Repository: `ppow1/theestate`  
PR: #514, `docs: prepare WP-4232 preservation and retirement handoff`  
Reviewed base: `origin/main` = `e4e4828855bb468dfe3276730eb1dbe22bb89460`  
Reviewed head: `b58fada14d2d48aa9f3d14d58bc874c02a7b70f6`  
Review worktree: `A:\review-wp514` (fresh detached worktree)  
Source inspected read-only: `A:\theestate-wp4232`

## Executive result

The review separates four decisions:

| Question | Decision |
|---|---|
| Documentation accurate and mergeable? | **YES, after the factual corrections in this review** |
| Preservation plan technically sufficient? | **NO** — it still needs bounded shared-object/stash classification, approved retention, and tested recovery execution |
| Preservation artifacts ready to authorize? | **NO** — Steward must approve the retention root and artifact creation first |
| WP-4232 ready for destructive retirement? | **B. NOT READY** |

No merge, auto-merge, retirement, archive, bundle, tag, branch, stash action,
GC, migration, service change, or WP-4232 modification was performed.

## Files reviewed

### PR #514 changed files

1. `docs/operations/reviews/ESTATE-OPS-002_WP4232_Checksum_Manifest_20260802.md`
2. `docs/operations/reviews/ESTATE-OPS-002_WP4232_Git_History_Manifest_20260802.md`
3. `docs/operations/reviews/ESTATE-OPS-002_WP4232_Implementation_Closure_Report_20260802.md`
4. `docs/operations/reviews/ESTATE-OPS-002_WP4232_NonGit_Evidence_Manifest_20260802.md`
5. `docs/operations/reviews/ESTATE-OPS-002_WP4232_Preservation_Inventory_20260802.md`
6. `docs/operations/reviews/ESTATE-OPS-002_WP4232_Recovery_Runbook.md`
7. `docs/operations/reviews/ESTATE-OPS-002_WP4232_Restoration_Test_Report_20260802.md`
8. `docs/operations/reviews/ESTATE-OPS-002_WP4232_Retirement_Readiness_Report_20260802.md`

### Onboarding and governing records

`AI_HINTS.md`, `AI_COMMUNICATION_HINTS.md`, `AI_REFLECTION_HINTS.md`,
`AI_START_HERE.md`, the required governance onboarding set under
`docs/governance/`, and the governing ESTATE-OPS-002 records:

- `ESTATE-OPS-002_Estate_Directory_and_Worktree_Inventory_20260801.md`
- `ESTATE-OPS-002_Blocking_Architecture_and_Migration_Safety_Review_20260801.md`
- `ESTATE-OPS-002_Phase_5A_Post_Merge_Closeout_20260801.md`
- `ESTATE-OPS-002_Phase_5A_Worktree_Removal_Result_20260801.md`
- `ESTATE-OPS-002_Proposed_Deletion_and_Archive_Plan_20260801.md`

Current worktree, preservation, archive, evidence, recovery, and destructive
action procedures referenced by those records were also inspected.

## PR identity and hygiene

The required PR head is present and contains exactly the eight intended added
Markdown files relative to `origin/main`. There are no binaries, archives,
generated files, JSON changes, secrets, credentials, or personal-data payloads
in the PR diff. Markdown is readable and `git diff --check` passes. Paths,
SHAs, dates, and report names are otherwise consistent.

The PR body had a confirmed malformed line:

```text
current origin/main is ^[4e482...`n
```

It should be an ordinary inline-code SHA with a normal newline. This is a
blocking presentation defect and must be corrected in the PR body. The body
also accurately says the PR is **NOT READY** and that no preservation artifact
exists; it does not claim restoration or retirement completion.

## Git-history reconciliation

Independent read-only commands produced:

```text
WP-4232 HEAD                         9ed81a20249498327d2f3b1c0ccd5ebd831062e2
current origin/main                  e4e4828855bb468dfe3276730eb1dbe22bb89460
HEAD --not origin/main               0
origin/main --not HEAD               130
HEAD is ancestor of origin/main      yes
HEAD --not --all                     0
```

The WP branch and its remote branch both point to `9ed81a202494...`. The
current zero count is correct in present tense. `origin/main` contains the WP
branch through PR #490 merge commit
`93532a72bbe56246a1b14751cc46590362485ad6`, dated 2026-07-27 08:09 -0400.

The earlier report’s claim that 113 was historically valid but cannot be
reproduced against the cited baseline is incorrect. The cited baseline
`2417654679c6db1221b18e7a44384e0a13751364` already contains WP-4232 HEAD;
`9ed81a202494... --not 2417654679...` returns zero. The 113 value is
consistent with a reversed or differently scoped query, not 113 commits
historically unique to WP-4232. This factual defect was corrected in the Git
history and preservation inventory reports.

No replace refs, alternates, or grafts were present. Branches and remote refs
retain the WP tip. Reflogs retain prior WP and preservation-worktree entries.
These facts do not make non-Git evidence or unrelated unreachable objects safe
to discard.

## Shared unreachable-object findings

Read-only `git fsck --full --no-reflogs --unreachable --no-progress` against
the shared common repository reported:

| Object type | Count |
|---|---:|
| commits | 105 |
| trees | 455 |
| blobs | 302 |
| total | 862 |

The objects span 2026-07-01 through 2026-08-02. They are shared-repository
objects, not a WP-4232-only set. The commit subjects identify multiple classes:
old stash/index/untracked snapshots, abandoned or reflog-only work, and
WP-4232-era objects including the acceptance harness and provider-admission
blocker. The current object database also reports one zero-byte garbage temp
object, `.git/objects/c3/tmp_obj_Ngam48`; it was not touched.

Disposition: **protected and unresolved**. No GC or prune is safe. A bounded
follow-up must inventory every unreachable commit and its reachable object
closure, map object IDs to all branch/ref/reflog/stash evidence, identify
WP-4232 and other institutional material, and either preserve or explicitly
classify each set. A current unique-commit count of zero does not eliminate
this object-store risk.

## Stash safety

All 16 stash entries are present with the identities and messages observed in
the source repository; no stash was applied, dropped, renamed, or rewritten.
They are shared common-repository state, not owned by the WP-4232 worktree,
so removing that worktree would not directly remove stash reachability.

However, only `stash@{0}` is reachable from the current `refs/stash` tip.
The other 15 stash commits are listed through the stash reflog and are
reported unreachable when reflogs are excluded. They therefore require
protection from reflog expiry/GC and explicit classification before any shared
repository cleanup. This does not authorize exporting or altering them.

## Non-Git evidence

Read-only status of `A:\theestate-wp4232`:

- tracked modifications: none;
- staged changes: none;
- ordinary untracked files: none;
- ignored files: 21;
- submodules: none;
- WP-specific LFS files: none reported;
- local Git configuration: shared `A:\theestate\.git\config`, inspected but not captured as an artifact.

The 21 ignored paths in the PR manifest match the independent path inventory:
four `.pytest_cache` files, one generated conversation fixture, twelve source
bytecode files, and four test bytecode files. They are reproducible/generated,
but the fixture and validation cache remain protected until the Steward
decides whether they are institutional evidence or disposable output. The
manifest’s hashes and sizes are useful source evidence, not an archive.

No archive, checksum package, local-config capture, or recovery artifact has
been created. The proposed non-Git manifest is complete for the observed
ignored-file set, but it is not by itself sufficient for retirement.

## External references

`git grep` over the tracked repository found no `theestate-wp4232` reference.
No scheduled task action containing `A:\theestate-wp4232` or `wp4232` was
found in the accessible task inventory. The bounded search of the large
operator/runtime filesystem did not complete; therefore active launcher,
Stream Deck, shortcut, Open WebUI/Gateway, environment, and external evidence
dependencies are **not proven absent**. The review found no positive active
dependency, but repository absence is not proof of system-wide absence.

Retirement remains blocked until the existing bounded reference procedure is
completed across operator controls, startup/runtime manifests, scheduled tasks,
shortcuts, reports, and other worktrees, with each hit classified as active,
historical, fixture, stale, or harmless.

## Preservation-plan assessment

The smallest technically sufficient future package is not a redundant bundle
alone. It is:

1. a source/ref/tree/commit manifest for the WP tip and relevant refs;
2. a bounded classification manifest for shared unreachable objects and
   reflog-only stash history;
3. a separately hashed non-Git evidence archive containing only approved
   material, including the 21 ignored paths if retained;
4. a manifest and hash of repository-local configuration and worktree metadata
   where required for recovery;
5. recovery instructions and an isolated restoration test with explicit
   commit, tree, ref, file-hash, and clean-state criteria.

Because all committed WP history is currently reachable from `origin/main`, a
Git bundle is **optional for committed-history redundancy but useful for an
independent recovery package**. It is insufficient alone: it does not capture
ignored evidence, local configuration, reflog-only material, or stash context.
No bundle should be created until separately authorized.

## Retention-root assessment

No approved external Estate evidence or backup root was identified in the
reviewed governing records. `A:\theestate-backup` is explicitly a proposal,
not an approved or existing canonical root. The Steward must choose or approve
the root; this review does not invent one.

An approved root must be outside WP-4232 and disposable worktrees, have
sufficient free space, durable naming, access/classification controls,
checksum support, backup coverage, write-protection or immutability
expectations, and documented recovery ownership. Sensitive data, credentials,
databases, models, and unrelated user material require separate exclusion and
access decisions.

## Restoration-test assessment

The prior temporary clone reached the expected commit but timed out during
checkout. A new targeted fetch-and-checkout attempt also resolved the expected
WP tip before timeout but did not complete a clean checkout verification. The
cause is bounded operation time against the large shared object store and full
working tree; resolving a commit is not restoration success.

The future artifact test may be smaller: verify bundle/archive checksums,
`git bundle verify`, restore Git into a fresh temporary repository, verify the
named ref, tip, parent chain, tree IDs, and commit manifest, restore non-Git
files separately, recompute every file hash, and verify the restored tree is
clean and outside all runtime roots. Full production checkout is not required
if these properties are proven; a clean source checkout is required if the
retained evidence claim includes checkout usability.

## Findings

### BLOCKING

1. The original 113-history explanation was factually wrong against its own
   cited baseline. Corrected in the Git-history and preservation reports.
2. The shared object store is materially under-classified: 862 unreachable
   objects, including WP-era objects and 15 reflog-only stash commits. A zero
   WP-only count cannot support retirement or shared-object cleanup.
3. No approved retention root, preservation artifact, or verified artifact
   restoration exists. The plan is not technically executable to completion
   until those decisions and tests occur.
4. System-wide absence of active external references is unproven because the
   bounded operator/runtime scan timed out.
5. The PR body has malformed formatting around the recorded `origin/main` SHA.

### NON-BLOCKING

- Add exact object-classification counts and stash reachability distinction to
  the package (done in the factual corrections).
- Keep the current explicit “not run” and “not ready” language; it is clear
  and appropriately avoids overstating preservation.
- The restoration runbook could add a compact command transcript template for
  future operators.

## Steward decisions required

- Approve an existing compliant external evidence/backup root, or decide that
  no such root currently exists.
- Authorize creation of any bundle, preservation ref, non-Git archive, or
  object/stash classification package.
- Decide retention/disposition for the 21 ignored WP files after evidence and
  boundary review.
- Decide whether and how the 15 reflog-only stash histories are protected;
  this review does not alter them.
- Separately authorize destructive retirement of exactly
  `A:\theestate-wp4232` after all gates pass.

## Merge and retirement decisions

Documentation merge-readiness: **READY AFTER THE DOCUMENTATION-ONLY
CORRECTIONS IN THIS REVIEW ARE COMMITTED AND THE PR BODY SHA FORMATTING IS
FIXED**. This is a documentation decision only; it does not approve archive
creation or retirement.

Preservation-artifact readiness: **NOT READY TO AUTHORIZE**. Authorization is
blocked by the absent retention-root decision, unresolved shared objects/stash
reachability, and unverified restoration.

Final retirement decision: **B. NOT READY**.

WP-4232 must remain present and registered. No retirement command is authorized
by this report.

## Validation record

- `git diff --check`: pass.
- Review worktree cleanliness: pass after commit.
- Worktree registration: WP-4232 remains registered; no registration was changed.
- Stash identity check: all 16 identities/messages match the read-only baseline.
- Non-Git inventory: 0 tracked/staged/ordinary-untracked, 21 ignored; manifest paths match.
- Tracked JSON parse: two pre-existing malformed fixture files remain outside this PR: `collaboration/workstreams/WP-4219/fixtures/malformed_queue_input.json` and `collaboration/workstreams/WP-4227/fixtures/malformed_inputs.json`. No PR JSON was introduced or changed.
- Exact repository reference search: no tracked WP-4232 path hit; scheduled-task inventory had no hit; broad external scan remains incomplete.
- Secret/redaction scan of the PR Markdown: no credential or secret payload found; expected words such as “secret key” occur only in exclusion/safety prose.
