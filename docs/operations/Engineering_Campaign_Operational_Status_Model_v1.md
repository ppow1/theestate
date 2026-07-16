# Engineering Campaign Operational Status Model v1

Status: Gate C operational contract  
Owner: Chief Architect  
Campaign: `CAMPAIGN_0670_ENGINEERING_DEPARTMENT_OPERATIONALIZATION`

## Purpose and invariants

This is the one canonical **view contract**, not a database, queue, scheduler, or authority. A view is a timestamped, read-only projection of the sources below. It may cache source references, digests, observation times, and conflicts, but may never write a lifecycle decision back to a source or resolve disagreement by precedence alone. Work packages remain the execution unit; campaigns remain the coordination unit.

Every row preserves literal `campaign_id` and `work_package_id` (nullable only for campaign rows), source high-watermark, `observed_at`, and `projection_version`. Missing, stale, or contradictory material fields produce `unknown`/`conflict`, suppress the next executable action, and fail closed.

## Field-to-authority map

| Displayed field | Single authoritative source | Projection rule |
|---|---|---|
| campaign/package ID and definition | `collaboration/campaigns/*.md`; `collaboration/work_packages/*` under PTM identity contracts | Show literal IDs plus path/digest; directory placement is not state |
| lifecycle state | canonical PTM/orchestrator event/projection contract | Display observed state and event ID; never infer completion from a receipt |
| owner/responsible office | canonical assignment/workforce record; campaign definition for authority owner | Show assignment version; definitions state authority, not live staffing |
| execution lane/provider | package lane declaration; selection record in provider routing runtime | Distinguish preferred lane, selected provider, reservation, Dispatch, and actual run |
| readiness/dependencies | PTM/orchestrator eligibility and dependency records | `unknown`, expired, or conflict is not ready |
| branch/PR/integration | Git refs and hosting-provider PR/review/merge records | Bind to base/head commits; PR creation is not integration |
| validation | registered recipe reports, reconciliation, and readiness records | Show each phase/verdict separately and commit/digest tested |
| acceptance | explicit Chief Architect decision record | Absence is `awaiting_acceptance`; never inferred from tests, merge, or receipt |
| blocker class/age | canonical PTM/Grace blocker event referenced to package | Age = observation time − first unresolved blocker timestamp; retain class/owner |
| next authorized action | derived from current eligible state and named authority contracts | Show action, actor, prerequisites, source refs; blank when conflicting |
| evidence links | WP-0673 evidence manifest and canonical referenced records | Links/digests only; dashboard is not evidence storage |
| last material transition/time | latest canonical lifecycle event by event time/high-watermark | Show event ID, actor, authority and source time, not file mtime |
| continuity/reflection | `operations/continuity/*` artifacts governed by the master process | Show artifact type, officeholder implementation, verification and handoff state |

Package Markdown, completion receipts, boards, mail, Notebook entries, and generated reports are evidence or communication unless the table names them as the authority for that field. They cannot mutate PTM state.

## Lifecycle projection

Use the WP-0671 lifecycle and readiness values and WP-0673 validation/acceptance phases without collapsing them. At minimum expose: intake disposition; planning; readiness (`ready`, `not_ready`, `blocked`, `waived`, `unknown`); assignment; routing/selection; Dispatch; execution; package validation; PR review; merge; post-merge validation/reconciliation/readiness; package acceptance; integration-gate decision; and campaign acceptance preparation/decision.

For each package expose a compact record containing all mapped fields, attempts, predecessor/supersession links, blocker owner and aging, and the exact next authorized action. The campaign record aggregates package counts and gate evidence but does not manufacture a campaign state from a percentage. Gate release and acceptance remain explicit Chief Architect decisions.

## Reconciliation and staleness

A reconciliation run compares campaign definitions, Pending/claimed/completed paths, PTM records, branches, PRs, receipts, evidence manifests, validation reports, boards, messages, and runtime projections by literal IDs and commit/digest. It reports, without repairing:

- definition status or directory contradicting PTM state;
- receipt without matching definition/evidence/explicit acceptance;
- branch or open PR without live package ownership, or ownership without branch/PR disposition;
- PR head differing from validated commit;
- merge without post-merge checkpoint, or validation without a matching recipe/digest;
- board, message, Notebook, or dashboard assertion newer than its cited canonical event;
- dependency/readiness state inconsistent with predecessor acceptance;
- continuity handoff without a current assignment/branch transfer decision.

Default stale thresholds are report parameters, never governance: readiness/provider observations use their own expiry; an active package with no material event for 2 business days is flagged; an unresolved blocker for 1 business day is aging; a closed PR/merged branch not reconciled within 1 business day is orphan-risk. Reports state the applied policy and clock. Any material contradiction yields `conflict`, routes a reconciliation notice to the record owner, and blocks downstream automation until the authorized source is superseded or corrected.

## Recovery test

A fresh Chief Architect must be able to start from the campaign dashboard specification, follow every source link, identify the current package/gate state, verified commit, open blockers, outstanding authority decision, last transition, and next authorized action without chat history. If any element depends on chat, a filename, or an uncited dashboard value, recovery fails.
