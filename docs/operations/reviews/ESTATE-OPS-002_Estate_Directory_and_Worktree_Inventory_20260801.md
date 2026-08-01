# ESTATE-OPS-002 Estate Directory and Worktree Inventory

Inventory date: 2026-08-01  
Scope: Phases 1–4 only  
Repository used for inspection: `A:\theestate-wp4233`  
Retained baseline: `origin/main` = `2417654679c6db1221b18e7a44384e0a13751364`

## Safety boundary

This inventory is read-only. No directory, worktree, stash, launcher, runtime,
database, tool, or process was deleted, moved, reset, cleaned, stashed, or
stopped. `A:\theestate` was not modified. The operational Estate remained on
active blue while the inventory ran.

The active post-PR-509 status was healthy: blue active; Grace, Resident
Gateway, and Open WebUI semantically ready; canonical database
`A:\AI\OpenWebUI\EstateCanonicalData\webui.db`.

## Git topology observed

The canonical Git common repository is `A:\theestate\.git`. Registered linked
worktrees are:

| Path | Branch/identity | HEAD | Upstream state | Working state | Proposed disposition |
|---|---|---|---|---|---|
| `A:\theestate` | `feature/evelyn-multimodel-tpose-pipeline` | `d2e11d56a2cc73663ed0c1d8fffb31ae400e9ac9` | `origin/feature/...`, ahead 1/behind 0 | dirty; 3,570 untracked; 16 stashes | retain-active |
| `A:\EstateRuntime\bootstrap\estate-main` | detached | `69f2111b89932d395e7cbb38ff585425dea61ddb` | none | not separately classified as a candidate worktree | archive-evidence |
| `A:\theestate-main` | `codex/grace-production-campaign-authoring` | `f245cd57d19d65de8280eb9ac50ce1d70004f5fb` | clean, 0/0; PR #488 merged | clean | safe-delete-after-review |
| `A:\theestate-wp4229` | `codex/wp-4229-production-runtime` | `1c3421b4e2b2d1dd7bf9148699fbf777960762d9` | clean, 0/0; PR #486 merged | clean | safe-delete-after-review |
| `A:\theestate-wp4230` | `codex/wp-4230-open-webui` | `8847aa96877b191e39d4e2de02060d6d33b22b36` | clean, 0/0; PR #489 merged | clean | safe-delete-after-review |
| `A:\theestate-wp4231` | `codex/wp-4231-estate-ui` | `bee18d858dec68cd9d388ef52a4c870d5812614b` | clean, 0/0; PR #487 merged | clean | safe-delete-after-review |
| `A:\theestate-wp4231-maincheck` | detached | `7532e5f794fcc45b9e72eb00069fe5678ae77346` | none | clean | safe-delete-after-review |
| `A:\theestate-wp4232` | `wp-4232-dual-surface-acceptance` | `9ed81a20249498327d2f3b1c0ccd5ebd831062e2` | upstream `origin/main`, ahead 113/behind 0 | clean, unique branch history | archive-unique-work |
| `A:\theestate-wp4232-final` | `wp-4232-final-bounded-live-acceptance` | `b27446c9aeaf161142a3ab878acdfa63c8db7f0a` | clean, 0/0; PR #492 merged | clean | safe-delete-after-review |
| `A:\theestate-wp4232-u1` | `wp-4232-u1-provider-admission` | `fb82763bdecff6472e25c06a6a1dce81c84ed578` | clean, 0/0; PR #491 merged | clean | safe-delete-after-review |
| `A:\theestate-wp4233` | `main` | `2417654679c6db1221b18e7a44384e0a13751364` | clean, 0/0 with `origin/main` | clean | canonical-blue |

All linked worktrees share the `A:\theestate\.git` common directory. The
ordinary copy `A:\theestate-chatgpt-conversation-archive` is a separate Git
repository at `472f476bcf097e147bcf9dfa48343472ad129d0a`, branch
`work/chatgpt-conversation-archive`, clean and 0/0 against its retained
upstream; it contains retained conversation material and is not a deployment
worktree.

`A:\theestate-wp4232` is the key preservation blocker: `git rev-list HEAD
--not --remotes` reported 113 commits. No archive branch, bundle, or patch was
created in this phase.

## Filesystem inventory

Sizes are recursive file-byte totals; generated trees with an intentionally
bounded read-only scan are marked `scan incomplete` rather than guessed.

| Path | Type | Bytes | Files | Git/nested state | Unique evidence or relationship | Disposition |
|---|---|---:|---:|---|---|---|
| `A:\theestate` | repository/common Git directory | 2,397,895,966 | 41,167 | 126 nested `.git` directories; dirty | shared Git common dir, dirty user work, stashes | retain-active |
| `A:\theestate-wp4233` | linked worktree | 171,555,417 | 9,744 | 4,300 ignored | current canonical source/controller and blue runtime root | canonical-blue |
| `A:\theestate-main` | linked worktree | 109,945,326 | 9,193 | 3,954 ignored | merged Grace campaign branch | safe-delete-after-review |
| `A:\theestate-wp4229` | linked worktree | 99,880,664 | 5,280 | 39 ignored | merged Grace runtime implementation | safe-delete-after-review |
| `A:\theestate-wp4230` | linked worktree | 100,625,641 | 5,328 | 79 ignored | merged Open WebUI integration | safe-delete-after-review |
| `A:\theestate-wp4231` | linked worktree | 104,407,220 | 5,469 | 220 ignored | merged Estate UI branch | safe-delete-after-review |
| `A:\theestate-wp4231-maincheck` | linked detached worktree | 102,624,135 | 5,380 | 141 ignored | validation checkpoint; no branch | safe-delete-after-review |
| `A:\theestate-wp4232` | linked worktree | 99,751,695 | 5,277 | 21 ignored | 113 unique commits; acceptance history | archive-unique-work |
| `A:\theestate-wp4232-final` | linked worktree | 100,057,302 | 5,286 | 14 ignored | merged bounded acceptance | safe-delete-after-review |
| `A:\theestate-wp4232-u1` | linked worktree | 99,776,322 | 5,270 | 1 ignored | merged provider admission | safe-delete-after-review |
| `A:\theestate-acceptance-validation-temp` | ordinary validation tree | 1,619,115 | 1,479 | 18 nested `.git` dirs | validation output; not Git-tracked | archive-evidence |
| `A:\theestate-campaign-0681-tmp-20260718` | ordinary campaign temp tree | 7,008,616 | 5,554 | 54 nested `.git` dirs | campaign evidence and generated copies | archive-evidence |
| `A:\theestate-predeploy-tests` | ordinary test tree | 1,003,903 | 932 | 19 nested `.git` dirs | predeployment test material | archive-evidence |
| `A:\theestate-chatgpt-conversation-archive` | separate repository/archive | 321,736,092 | 7,429 | 1 nested `.git`; clean | conversation archive; separate upstream branch | archive-evidence |
| `A:\EstateRuntime` | runtime/evidence tree | scan incomplete | scan incomplete | includes bootstrap linked worktree, host copy, temp, validation, workspaces | evidence-heavy generated runtime corpus | archive-evidence |
| `A:\EstateValidation` | validation/archive tree | scan incomplete | scan incomplete | noncanonical validation material | retained validation evidence | archive-evidence |
| `A:\temp` | unknown general temp tree | not measured | not measured | outside Estate-specific scope | contains generic tab files; ownership uncertain | unresolved-Steward-decision |

## Codex-created test and evidence directories

The following were inventoried under `A:\theestate` and remain untouched:
`.pytest-u1-final1` (716,072 bytes/59 files), `.pytest-u1-full1`
(719,648/59), `.pytest-u1-run2` (74,806/55), `.pytest-u1-run3`
(536,578/57), `.pytest-wp4232-final1` (719,638/59),
`.pytest-wp4233-finaltests` (722,019/65), `.pytest-wp4233-focused`
(80,765/61), `.pytest-wp4233-gateway` (396,320/26),
`.pytest-wp4233-relevant` (1,248,611/167), `.pytest-wp4233-run1`
(64,903/45), `.pytest-wp4233-run2` (64,903/45), `pytest-basetemp`
(334,348/359), `pytest-basetemp-baseline` (2,131,783/861),
`pytest-basetemp-baseline-final` (2,197,413/877), `pytest-basetemp-full`
(8,274,615/5,472), `pytest-basetemp-full-2` (14,841,411/6,569),
`pytest-basetemp-wp` (1,404,623/292), `u1-evidence-test` (230,895/1), and
`.wp4232-worktree` (148,435,014/5,402). These are evidence or generated
worktree material and are proposed for `archive-evidence`, except the
`.wp4232-worktree` copy, which is `unresolved-Steward-decision` until its
nested Git content is reconciled.

Under canonical `A:\theestate-wp4233`, the read-only scan found `.pytest_cache`
(240,261/5), `.pytest-broader-activation-temp` (772,346/582),
`.pytest-broader-temp` (777,542/586), `.pytest-final-temp` (639,576/323),
`.pytest-tmp-activation` (640,052/323), and empty `_qwen_test_temp`; these are
ignored local test state and remain `retain-active` until a separate approved
cleanup decision, because this package does not authorize cleaning the active
canonical worktree.

## Estate tools and runtime copies under `A:\AI\Tools`

| Path | Bytes / files | Observed role | References or evidence | Disposition |
|---|---:|---|---|---|
| `A:\AI\Tools\EstateStreamDeckMVP` | 154,473,164 / 325 | active operator surface | canonical bindings invoke `A:\theestate-wp4233`; legacy scripts still contain `A:\theestate` | retain-active |
| `A:\AI\Tools\EstateStreamDeckPlugin` | 5,218,905 / 438 | active Stream Deck plugin | current plugin/build material | retain-active |
| `A:\AI\Tools\EstateStreamDeckPlugin-Archive` | 159,587 / 55 | historical plugin archive | backups only | archive-evidence |
| `A:\AI\Tools\EstateStreamDeckBuild-PR509-2209` | 168,904 / 39 | PR #509 build evidence | historical build | archive-evidence |
| `A:\AI\Tools\EstateStreamDeckBuild-PR509-2214` | 311,749 / 56 | PR #509 build evidence | historical build | archive-evidence |
| `A:\AI\Tools\EstateStreamDeckBuild-PR509-2222` | 314,113 / 56 | PR #509 build evidence | historical build | archive-evidence |
| `A:\AI\Tools\EngineeringWorkerRuntime` | 34,170 / 4 | active supporting runtime | Estate-related worker tool; not canonical three-service controller | retain-active |
| `A:\AI\Tools\estate-chat-walker-v0.2` | 9,198 / 5 | historical chat tool | no active canonical reference found | archive-evidence |
| `A:\AI\Tools\Estate-Chat-Walker-v0.3` | 9,126 / 5 | historical chat tool | no active canonical reference found | archive-evidence |
| `A:\AI\Tools\Estate-Chat-Walker-v0.4` | 10,312 / 5 | historical chat tool | no active canonical reference found | archive-evidence |
| `A:\AI\Tools\estate-chat-walker-v0.5` | 12,039 / 5 | latest chat tool copy | no active canonical reference found | retain-active |

## Active references and process boundary

The live managed processes reference only `A:\theestate-wp4233`:

- Grace Momentum PID 30804: `scripts\run_grace_momentum_runtime.py`, port 8766;
- Resident Gateway PID 7176: canonical CLI with `--root A:\theestate-wp4233`,
  port 11435;
- canonical status process PID 35164 invoked from `A:\theestate-wp4233`.

An operator helper process from `A:\theestate\tools\operator-deck` was
observed, and legacy Stream Deck scripts/configuration still reference
`A:\theestate`. The active canonical binding artifact points to
`A:\theestate-wp4233`, but these stale references must be resolved before any
retirement. No Open WebUI process was stopped or changed during inventory.

## Stashes

The canonical common repository has 16 stashes, including Grace image routing,
pre-WP-4130 synchronization, resident runtime validation, command-surface
repairs, generated/runtime artifacts, and local resident authority decisions.
They remain untouched. No stash was dropped, applied, exported, or rewritten.

## Phase 4 conclusion

The current deployment is one canonical source root plus runtime slots, not yet
two deliberate Git deployment worktrees. The proposed topology and retirement
plan therefore remain proposals requiring Steward review. No deletion or
worktree retirement is authorized by this report.

## Steward-corrected topology and final decision table

The earlier proposal that treated `A:\theestate-wp4233` as permanent
canonical-blue is superseded. It is a transitional source/runtime root only.
The final architecture is:

| Final role | Stable path | State boundary | Decision |
|---|---|---|---|
| Common | `A:\theestate-common` | Git-connected source, schemas, policies, docs, tests, templates, migrations, non-secret config only | create later; no Live runtime |
| Blue | `A:\theestate-blue` | non-Live candidate/test ports only | create later from Common |
| Green | `A:\theestate-green` | peer non-Live candidate/test ports only | create later from Common |
| Live | `A:\theestate-live` | promoted operational release; Grace 8766, Gateway 11435, WebUI 8080 | create/select later from validated release |
| Standard data | `A:\theestate-data` | persistent operational data outside code worktrees | reserve later; no migration now |
| Sensitive data | `A:\theestate-sensitive-data` | external sensitive data; placeholder levels restricted, highly-restricted, classification-pending, quarantine | reserve later; no classification standard now |
| Backup | `A:\theestate-backup` | offline/read-only last-known-good recovery material | define later; do not create now |
| Current WebUI state | `A:\AI\OpenWebUI\EstateCanonicalData` | existing shared canonical state; no per-slot copies | retain in place |

The current active process remains rooted at `A:\theestate-wp4233`; this is
allowed only as a transitional condition. Its final disposition is
`safe-delete-after-review` after stable named paths are created, tested,
referenced, and promoted. No work-package-numbered path is part of the final
permanent topology.

`A:\theestate` is not safe to designate as the final Common path in place. It
is dirty, contains 3,570 untracked files, 126 nested `.git` directories, and
16 stashes. The safest proposed migration is to create a clean
`A:\theestate-common` from the retained remote/main source, verify that it
contains only code and non-secret configuration, then create Blue and Green
from that Common. Preserve the existing common repository, dirty branch,
stashes, and unique work separately before any retirement decision.

The separate `A:\theestate\.wp4232-worktree` is not a registered worktree. It
is an independent clone on branch `wp-4232-dual-surface-acceptance`, at
`b064dac95856156a5fd9c1fe35b9959e58abfb10`, synchronized to
`origin/wp-4232-dual-surface-acceptance`, with only untracked `.pytest-wp4232`
content. It is duplicate WP-4232 source plus test evidence and is classified
`archive-evidence`; it is not the owner of the 113 commits found in the linked
`A:\theestate-wp4232` worktree.

The 113 commits in `A:\theestate-wp4232` are classified
`archive-unique-work`. They are the local WP-4232 dual-surface acceptance
history after the common repository's retained remote refs diverged. The
proposed preservation method is a reviewed commit manifest plus a named
archive branch or Git bundle, excluding generated files, databases,
credentials, private data, and ignored output. No preservation artifact was
created in this phase.

## Corrected migration and promotion map

1. **Current state:** Live services remain on the PR-509 transitional source
   `A:\theestate-wp4233`; persistent WebUI state remains at
   `A:\AI\OpenWebUI\EstateCanonicalData`; old worktrees and tools remain
   untouched.
2. **Common creation:** after Steward approval, create a clean Git-connected
   `A:\theestate-common` from retained source history. Copy no runtime output,
   operational data, resident memory, database, credentials, private
   documents, models, or generated artifacts.
3. **Blue creation:** create `A:\theestate-blue` as a clean candidate worktree
   from Common. It uses only candidate/test ports; the initial proposed
   candidate triplet is Grace 8767, Gateway 11436, and WebUI 8081.
4. **Green creation:** create `A:\theestate-green` as a peer candidate worktree
   from Common. It must use a distinct candidate triplet reserved by the
   controller; a concrete second triplet is a later implementation decision,
   not an authorization to create or run it now.
5. **Validation:** build, integration, semantic readiness, operator, and
   authenticated-path checks run in Blue or Green only. Neither candidate
   claims the Live/public ports.
6. **Promotion:** package a complete validated release from Blue or Green,
   select/create `A:\theestate-live` at that release, start all three services
   on 8766/11435/8080, verify readiness, and record source commit, release
   manifest, state identity, and prior Live release. Nothing is developed
   directly in Live.
7. **Backup:** before promotion, proposed `A:\theestate-backup` contents are
   read-only release manifests, source commit/tree identity, controller and
   launcher manifests, prior Live rollback metadata, and separately governed
   persistent-state recovery material. It is not an active worktree and is not
   created here.
8. **Standard data:** future operational data belongs under
   `A:\theestate-data`, but the existing canonical Open WebUI state is not
   relocated by this package.
9. **Sensitive data:** reserve, without implementing policy, the four levels
   under `A:\theestate-sensitive-data`: `restricted`, `highly-restricted`,
   `classification-pending`, and `quarantine`. Ingrid later refines the
   classification model and access policy.

## Rollback and path-reference sequence

Promotion rollback stops admission of the new Live release, preserves the
prior Live release, restores/selects that prior release, leaves persistent data
unchanged, restarts the complete three-service surface, and re-runs semantic
readiness and authenticated correlation. Code rollback never silently rolls
back data. Any data migration requires separate governance, backup, forward
and backward compatibility, and an explicit rollback plan.

Before retiring any work-package path, inventory and update source roots,
working directories, Stream Deck actions, services, scheduled tasks, manifests,
status/PID records, scripts, tests, and documentation in a controlled sequence:
Common first, then Blue/Green candidate references, then explicit Live
promotion references. Prove no active process or launcher refers to the old
path before retirement. No launcher was modified in this phase.

## Work-package path retirement criteria and measurable space

`A:\theestate-wp4229`, `wp4230`, `wp4231`, `wp4231-maincheck`,
`wp4232-final`, and `wp4232-u1` are clean merged worktrees with retained remote
branches. Their measured directory totals sum to 717,316,610 bytes (about
684.1 MiB) as a gross upper bound for later worktree removal; shared Git object
storage means actual reclaimed disk will be lower.

The measured totals for all listed old linked worktrees except the unique
WP-4232 worktree and current WP-4233 total 988,623,722 bytes (about 942.9
MiB), before evidence/archive retention. Evidence trees are not counted as
reclaimable. These are planning measurements only.

Every work-package-numbered path must meet all of these conditions before a
Steward-approved disposition is executed: no active process/cwd/reference;
no registered worktree dependency; clean or preserved dirty/untracked state;
all unique commits and evidence hashed and recoverable; remote branch/PR
relationship recorded; no credentials, databases, private data, or required
runtime state inside; replacement stable path proven; and explicit approval of
the named path and disposition. Ingrid's future data-classification work is
not part of this package.

## Blocking migration-safety addendum

The exact recommended Git model is a normal primary source worktree at
`A:\theestate-common` with one common `.git` directory and linked candidate
worktrees `A:\theestate-blue` and `A:\theestate-green`. A bare repository is
rejected because Common must contain inspectable source files. The existing
`A:\theestate` repository cannot be repurposed in place while dirty: it has
566 refs, 16 stashes, enabled reflogs, registered worktrees, local branch and
remote configuration, nested repositories, and dirty/untracked content.

The future migration must preserve all refs and objects, separately capture
dirty/untracked content, retain the old reflogs and `.git` as recovery until
acceptance, and recreate worktree registrations rather than copying stale
admin records. A Git bundle alone is insufficient.

Live is not a Git worktree. The exact recommended model is an immutable
versioned release directory under `A:\theestate-live` with an atomic
`active-release.json` binding release ID, source commit, configuration/state
identity, and authorization. Blue and Green remain candidate-only and never
take Live ports. The current `A:\theestate-wp4233` public-port runtime is
transitional and must not be copied into either final candidate.

The source/runtime boundary review identified generated and operational state
under `runtime/production`, `runtime/resident_interactions`,
`runtime/resident_conversations`, `runtime/residents`, `runtime/mailboxes`,
`runtime/operations`, `runtime/execution_*`, `runtime/engineering_*`,
`runtime/codex_bridge`, `runtime/validation`, and related runtime trees. These
must be externalized to standard or sensitive data/evidence boundaries in a
later governed operation. Source-authored registries, schemas, policies, and
visual manifests remain Common content. The existing canonical WebUI database
and secret key remain external and are not relocated here.

The complete blocking-review report defines promotion, rollback, backup,
checkpoint, data-boundary, path-reference, WP-4232 preservation, and final
destructive-authorization requirements. It also confirms that full-tree scans
or archival duplication of very large evidence corpora are not prerequisites
for beginning a safe migration; targeted metadata, hash manifests, and
bounded evidence selection are sufficient until a separately approved archive
operation.
