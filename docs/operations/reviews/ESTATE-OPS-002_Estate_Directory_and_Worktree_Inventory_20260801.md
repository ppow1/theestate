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
