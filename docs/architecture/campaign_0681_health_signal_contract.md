# CAMPAIGN-0681 normalized health signal contract

## Purpose and authority boundary

`estate.core.health_signal_integration` is a rebuildable, read-only projection
over canonical Estate evidence. It does not persist health, probe a process,
change a resident lifecycle, update a service registry, dispatch work, or grant
authority. Its results are observations and campaign-impact facts only.

The adapter reuses the operational vocabulary required by WP-0689 while
preserving each domain's canonical identity and source references. A signal
never authorizes an action (`authorizes_action` is always false). Its
`progression_effect` is one of `observation_only`, `blocks_progression`, or
`requires_protected_review`; those values describe impact and routing, not an
action permission.

## `estate.health-signal.v1`

Every normalized signal contains:

| Field | Meaning |
|---|---|
| `subject_type`, `subject_id` | Domain type and stable canonical identity. |
| `health_domain` | `resident`, `service`, `runtime`, `provider_environment`, or `validation`. |
| `normalized_state` | `healthy`, `degraded`, `unavailable`, `failed`, `unknown`, `stale`, or `contradictory`. |
| `reported_state`, `severity` | Normalized source report and operational severity. |
| `observed_timestamp`, `source_timestamp`, `expires_at` | Projection time, source time, and computed or explicit expiry. |
| `freshness` | `current`, `stale`, or `unknown`. |
| `canonical_evidence_references` | Stable source paths or evidence identifiers. |
| `source_kind`, `source_precedence` | Provenance class and deterministic precedence rank. |
| `dependency_or_campaign_impact`, `required_dependency` | Bounded dependency/campaign context. |
| `explanation` | Concise human-readable result. |
| `uncertainty_or_contradiction_warnings` | Missing, stale, conflicting, or qualified evidence. |
| `responsible_lane`, `reevaluation_trigger` | Destination for review and condition for another observation. |
| `progression_effect`, `authorizes_action` | Impact only; never authority. |
| `derivation_rule` | Named rule that produced the result. |

The aggregate adds sorted signals, state counts, the worst visible state,
blocker-ready facts, and optional canonical campaign/package identifiers. It is
deterministic for unchanged evidence and a fixed observation time.

## Reconciliation and campaign-impact rules

1. Current canonical registries and schema-valid receipts rank above durable
   repository records, direct observations, runtime heartbeats, status boards,
   dashboards, and inference, in that order.
2. Explicit failure, shutdown, refusal, pause, or unavailability wins over an
   optimistic claim within the same evidence class.
3. Equally authoritative, current healthy and negative evidence is
   `contradictory`; it fails closed and retains every reference.
4. Durable authoritative evidence wins over an irreconcilable runtime or UI
   claim. The lower-ranked evidence remains in provenance.
5. Evidence past its expiry is `stale`, never current health. Missing evidence
   is `unknown`, never assumed healthy.
6. A later healthy report clears known negative evidence only when
   `recovery_clears` names the negative evidence reference.
7. A required dependency in an unknown, stale, contradictory, unavailable, or
   failed state blocks progression. A local non-required degradation remains an
   observation unless another canonical dependency rule says otherwise.
8. Failed or contradictory evidence is always emitted as a blocker-ready fact.
   A healthy aggregate cannot conceal a worse signal or required dependency.
9. Facts recommend only their existing responsible lane. They do not dispatch,
   retry, staff, accept, merge, deploy, spend, or disclose.

## Canonical adapters

- Resident adapter consumes resident lifecycle state; interaction evidence is
  only a warning/context and cannot establish readiness.
- Service adapter consumes service-health-registry entries and their canonical
  dependency summaries. It does not mutate the registry or status board.
- Worker and operations-runtime adapters consume heartbeat/cycle evidence and
  distinguish process evidence from functional readiness.
- Provider/environment adapter consumes the existing provider health output and
  does not create a provider registry.
- Validation adapter keeps validation health distinct from execution completion,
  review, and institutional acceptance.

Callers should read the canonical source using its existing API, pass the record
and source reference to an adapter, reconcile same-subject signals, and aggregate
the result for WP-0692 or WP-0693. They must supply a fixed `observed_at` for
repeatable replay.
