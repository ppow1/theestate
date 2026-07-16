# Engineering Notebook Integration Standard v1

Status: Gate C operational contract  
Owner: Chief Architect

## Role

The Engineering Notebook is durable architectural and execution memory. It explains decisions and discoveries; it is never an inbox, task queue, scheduler, status registry, approval record, or substitute for PTM, Dispatch, validation, Git/PR, mailbox, parking-lot, or acceptance evidence. Notebook entries are append-only; corrections supersede an entry and retain both.

Notebook entries live in the existing repository decision/architecture/operations documentation surfaces appropriate to their subject. A campaign may maintain a small index of links, but must not copy canonical state into a private notebook store.

## Required entry envelope

Each entry contains:

- unique title/date, author/office, and entry type;
- literal `campaign_id` and applicable `work_package_id`/`attempt_id`;
- observation time and whether facts are verified, inherited, inferred, or uncertain;
- concise context, decision/discovery, rejected alternatives, rationale and consequences;
- affected contracts and whether a Chief Architect decision is required;
- at least one durable related reference: commit, PR, canonical message, evidence manifest/report, Dispatch/run, decision, or parking-lot item;
- source paths/URIs and immutable commit/content digests where material;
- follow-up route and canonical work/decision record (never an unchecked notebook task);
- supersedes/superseded-by links.

## Entry types and routing

| Type | Required focus | Canonical follow-through |
|---|---|---|
| architecture decision/rejected alternative | constraints, options, authority, consequences | accepted ADR/Chief Architect decision |
| contract freeze | exact contract/version, participants, unresolved choices | campaign integration-gate decision |
| implementation discovery | observed behavior, reproduction, affected commit | package amendment, defect, or evidence manifest |
| integration hazard | collision, dependency, rollback and urgency | PTM blocker/risk and branch owner |
| provider qualification/behavior | provider/version, request class, environment and evidence expiry | canonical capability/health/qualification record |
| validation anomaly | recipe, commit, expected/actual result and reconciliation | validation report/reconciliation record |
| deferred work | why excluded and promotion condition | `operations/boards/parking_lot.md` plus detailed PL record when needed |
| operational lesson | evidence, boundary and reusable recommendation | operating standard proposal, not automatic policy |
| closure observation | outcomes, surprises, residual risks and follow-ups | campaign acceptance package/reflection |

## Quality and continuity

Entries link rather than paste mutable dashboards or raw external run corpora. Sensitive data follows its canonical classification and retention rules. Campaign closure verifies that material decisions, anomalies, hazards and lessons have indexed evidence; omission is an acceptance-package gap, not permission to rewrite history. A renewed worker reads the campaign Notebook index after canonical governance and current-state sources; notebook prose never overrides them.
