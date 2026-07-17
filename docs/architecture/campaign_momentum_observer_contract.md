# Campaign momentum observer contract

`estate.core.campaign_momentum_observer` is a rebuildable, read-only projection
over an authoritative campaign execution manifest and referenced evidence. Its
versioned machine contract is `estate.campaign-momentum-observation.v1`; the
same object can be rendered as Markdown. It is not a registry, scheduler,
dispatch mechanism, transition authority, or acceptance mechanism.

## Canonical reuse and discovery

The observer extends the repository-backed campaign manifest seam established
for CAMPAIGN-0681. Package identity, dependencies, gates, approved parallel
groups, package paths, and receipt paths come only from that manifest. Only a
manifest-declared receipt is discovered automatically. Caller adapters may pass
canonical event, validation, health, readiness, review, pause, blocker, and
acceptance evidence, but every decisive record must retain its repository
reference. Runtime claims and dashboards remain lower-precedence context.

The projection does not use file existence, package commits, dashboard prose,
or recommendations as acceptance. A declared completion receipt means
`complete_pending_acceptance`; only protected acceptance or closure evidence
means `accepted_closed`.

## Deterministic evidence precedence

Evidence is reconciled in this order:

1. protected acceptance, then closure records;
2. schema-valid receipts;
3. current canonical artifacts;
4. repository records;
5. runtime claims;
6. dashboards;
7. inference.

Within a source class explicit acceptance, failure, pause, blocking and gates
outrank optimistic progress. Equally authoritative current records that disagree
produce `indeterminate`. Stale-only evidence, missing references, unknown
dependencies, and progress claims with unmet dependencies also fail closed as
`indeterminate`. Dependency edges and parallel membership are never inferred.

## Observation object

The object contains campaign identity and canonical reference, observation
time, Git/base and manifest digest identity, overall momentum, ordered package
observations, dependency satisfaction, limiting chain, eligible and active sets,
blockers, degradation, review and protected-decision sets, warnings, complete
evidence lineage, explanations, and a follow-up destination. Every package and
campaign object declares that it authorizes no action.

Health evidence from `estate.health-signal.v1` can be adapted by later consumers
without changing this contract. WP-0693 can refine `blocker_type` and
`follow_up_destination`. Both remain observations rather than routing actions.

## Side-effect and determinism guarantee

Observation reads the manifest, declared receipts, and Git identity only. It
does not write canonical or runtime state and does not call campaign runtime,
PTM, Dispatch, validation, mailbox, or acceptance mutation seams. With a fixed
timestamp, manifest, repository identity, and evidence inputs, normalized JSON
and Markdown output are byte-stable.
