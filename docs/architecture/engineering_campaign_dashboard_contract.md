# Engineering Campaign Dashboard Contract

Status: supporting architecture for pending WP-4219
Authority: read-only presentation contract; no runtime or installation authority

## Decision

WP-4219 defines one deterministic operator presentation over existing engineering evidence. WP-4218 is the primary queue/reconciliation provider; WP-4214 supplies duration semantics; WP-4215 supplies advisory concurrency/lane facts; and WP-4217 supplies local Git synchronization and conflict observations. The dashboard owns only view composition. It does not own, recalculate, repair, or mutate provider facts.

Existing CAMPAIGN-0670 status and WP-0703 Steward visibility work remain canonical for their campaign/Office purposes. A future WP-4219 renderer may follow their source-link, freshness, fail-closed, and recovery conventions, but cannot replace those surfaces or reproduce their controls. The Engineering Campaign Dashboard is narrower: engineering campaign planning, execution evidence, integration risk, and completion coherence.

## Architecture and authority map

```text
WP-4214 estimate artifact -------\
WP-4215 advisory plan ------------+--> compatibility/freshness gate
WP-4217 repository assessment ----+              |
WP-4218 queue/reconciliation -----/       immutable references
other governed evidence links ------------------|
                                                v
                                deterministic view-model policy
                                  /          |          \
                            panels       summaries      metrics
                                  \          |          /
                                   validated snapshot
                                          |
                         read-only reference rendering/export
```

| Display concern | Governing source | WP-4219 authority |
|---|---|---|
| queue/readiness/reconciliation/dependencies | WP-4218 published run | filter, order as specified, summarize and link |
| duration/actual semantics | WP-4214 published result | format range/confidence/freshness and aggregate compatible actuals |
| lanes/workers/parallel plan/merge sequence | WP-4215 published advisory plan | visualize capacity, utilization, opportunity and conditions |
| repository divergence/conflict recommendations | WP-4217 assessment | visualize observations, exposure and guidance |
| package/PL/WIP native facts | records referenced by WP-4218 | drill down; do not copy into a new authority |
| PR/commit/validation/receipt/acceptance | governed snapshots and evidence references | show distinct evidence stages and contradictions |
| lifecycle or protected decision | existing PTM/engineering authorities | no write or implied decision |

## Snapshot contract

A published snapshot contains:

- an envelope with ID, campaign scope, repository/provider cutoffs, observation time, provider/schema/policy/renderer versions and digests, predecessor, validation verdict, status and diagnostics;
- provider references and compatibility/freshness results;
- panel view-models for all required panels;
- definition-versioned metrics and reason-coded health indicators;
- deterministic Now/Next/Risk/Progress/Authority summaries;
- provenance edges from every value and sentence to provider records and renderer rules;
- an append-only diff from the preceding comparable snapshot.

Timestamps that vary by observation are isolated from logical output. Identical logical provider inputs and configuration produce identical normalized panel content, ordering, summaries, metric values, provenance, and reference rendering.

## Panel composition rules

1. **One cutoff:** a panel declares its provider cutoffs; facts from incompatible windows are not silently combined.
2. **One identity:** campaign, WP, attempt, PR, commit, validation and receipt IDs remain literal and linked.
3. **No evidence collapse:** authored, assigned, executing, merged, validated, accepted, complete and closed are separate facts.
4. **No favorable unknown:** missing provider/host/capacity/dependency facts become `unknown` or `unavailable`, never zero, healthy, ready or parallel-safe.
5. **No hidden recomputation:** provider categories, scores, graph edges, rankings and estimates are presented rather than recreated.
6. **Explain every aggregate:** denominator, exclusions, scope, definition version, cutoff and contributing rows are available.
7. **Accessible equivalence:** graph and color-coded status always have textual/table representations; future UI accessibility belongs to its install package.
8. **Presentation-only filtering:** filters never write source state, generate assignment, clear a blocker, promote Parking Lot work or initiate Git/merge activity.

## Freshness and degradation

The compatibility gate validates provider identity, schema range, campaign/repository scope, cutoff relationship, digest, and provider verdict. Panel requirements declare mandatory and optional providers. A mandatory stale/incompatible provider makes action guidance unavailable; the last valid information may remain visibly stale for investigation. Optional absence removes only the optional enrichment and is listed.

Snapshot status is:

- `fresh`: all mandatory provider contracts are compatible and within policy;
- `degraded`: core view is valid but optional enrichment is unavailable or a non-actionable conflict is present;
- `stale`: a mandatory freshness threshold expired;
- `invalid`: schema, digest, invariant, determinism or provenance validation failed;
- `unavailable`: no valid snapshot exists for the selected scope.

The dashboard cannot trigger provider mutation. Queue refresh means requesting existing provider workflows and composing their next immutable results.

## Health and metric semantics

Health is a policy-versioned explanation layer over displayed evidence, never a gate decision. Queue freshness, evidence completeness, dependency integrity, blocker pressure, lane load, validation coverage, merge exposure, repository synchronization, completion coherence and audit continuity each preserve `unknown`. Campaign health reports the worst applicable reason-coded condition under the configured rule and links every input.

Metrics preserve distinct populations. In particular, authored is not implemented, merged is not validated, validation is not acceptance, and a receipt is typed as authoring or implementation evidence. Duration distributions disclose sample size and semantics. Estimated completion is always a range/confidence from compatible providers. Lane utilization cannot be calculated without a declared capacity unit. Conflict exposure reports both raw affected items and the applicable versioned weighting.

## Failure and recovery behavior

Malformed provider data, missing provenance, incompatible cutoffs, duplicate identities, invalid graph references, arithmetic/denominator errors, or non-deterministic logical output fail candidate publication. The last valid snapshot remains addressable with its original status and an explicit candidate failure diagnostic. Corrections append and supersede; they do not rewrite history.

A fresh operator passes recovery when, without chat history, they can select a campaign and identify the queue cutoff, ready/blocked/WIP work, dependency and parallel conditions, lane load, merge/repository exposure, validation/completion distinctions, outstanding authority decisions, last material changes, and exact source evidence.

## Implementation and installation boundary

This document is architecture only. WP-4219 does not implement a renderer, runtime dashboard, browser interface, Open WebUI, React, HTML, CSS, JavaScript, scheduler, worker, Git operation, repository automation, or Office integration.

A future implementation package must stage all code, schemas, fixtures, tests and evidence beneath `collaboration/workstreams/WP-4219/`. A separate install package must select and reuse an existing operator surface, perform overlap review, define access and accessibility, migrations, security, performance, rollback and acceptance, and prove that no second queue, registry, controller, or authority is introduced.
