# Engineering Backlog Reconciliation and Execution Queue Design

## Decision

WP-4218 establishes a deterministic, read-only projection over existing Estate source authorities. The projection answers “what engineering work is ready, why, and with what conflicts?” It does not answer “what should the runtime execute?” and grants no assignment, dispatch, merge, installation, acceptance, or lifecycle-mutation authority.

## Reuse map

| Concern | Existing authority reused | WP-4218 behavior |
|---|---|---|
| Ideas | `operations/boards/parking_lot.md` | Reference and project lifecycle; never rewrite |
| Work contracts | `collaboration/work_packages/**` | Correlate status and acceptance criteria |
| WIP | active boards and `collaboration/workstreams/**` | Detect attempts, ownership, staleness, residual scope |
| Projects/tasks | Estate PTM roadmap and source-reference model | Project a queue; do not create another ledger |
| Runtime handoff | provider-neutral execution dispatch | Never enqueue or dispatch |
| Implementation evidence | Git/PR snapshots and changed artifacts | Correlate; merge is not acceptance |
| Validation/acceptance | validation reports, verdicts, receipts | Require coherent evidence for completion |

## Data-flow boundary

```text
read-only source adapters
        |
immutable normalized snapshot ---- policy/schema versions
        |                                  |
correlation + criterion evidence + lifecycle projection
        |
dependency graph --- lane/touch-point/risk/parallel analysis
        |
readiness + explainable priority
        |
validated immutable queue run (JSON) + deterministic Markdown view
```

Source artifacts remain canonical in their domains. Each output traces through a decision/reason code to normalized source records and their exact locators/digests. Candidate publication is transactional: validation failure retains the preceding valid run.

## Key invariants

1. One logical candidate may reference many source records; no evidence is discarded by deduplication.
2. No fuzzy match, missing host snapshot, pending filename, commit, merge, or receipt alone proves lifecycle state.
3. `requires` is the only dependency edge that drives topological readiness; cycles block rather than being heuristically broken.
4. Readiness requires known touch points, non-conflicting ownership, a validation plan, and satisfied dependencies.
5. Determinism covers normalized records, findings, graph, row order, score, and rendering; observation timestamps are isolated in the run envelope.
6. Queue rows are planning projections and cannot cause source mutation or runtime execution.
7. Every configuration change creates a new policy version and every correction appends history.

## Canonical run artifacts

A run directory contains `manifest.json`, `sources.json`, `findings.json`, `dependency_graph.json`, `queue.json`, `queue.md`, `diagnostics.json`, and `validation.json`. The manifest binds content digests, repository cutoff, optional provider snapshot cutoff, adapter/schema/policy versions, previous run, and publication verdict. `queue.json` is canonical within WP-4218; Markdown is a presentation rendering.

## Integration decision

The implementation begins only in `collaboration/workstreams/WP-4218/`. A later install package must decide whether and how the PTM or Office reads published projections. That package must prevent a second dispatch queue, define ownership and migrations, preserve offline behavior, supply rollback, and validate compatibility against existing project/task and dispatch contracts.
