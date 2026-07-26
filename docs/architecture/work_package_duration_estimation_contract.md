# Work Package Duration Estimation Contract

Status: supporting design for pending WP-4214  
Source: PL-0015  
Authority: read-only planning; no scheduling, dispatch, or installation authority

## Contract purpose

This contract fixes the semantic boundary for a future staged duration estimator. It complements existing PTM schedule projections: PTM may carry estimate fields, while WP-4214 defines how a defensible estimate is requested, calculated, explained, compared with actual outcomes, and calibrated. The estimator must run entirely under `collaboration/workstreams/WP-4214/` until a separate install-handoff is approved.

## Time model

| Component | Start boundary | End boundary | Treatment |
|---|---|---|---|
| Queue | trustworthy eligibility/assignment | trustworthy execution start | Wall-clock only; unknown when either boundary is absent. |
| Active engineering | evidenced active attempt intervals | evidenced stop/interruption intervals | Union overlaps; exclude waits only with evidence. |
| Review | review-ready evidence | review decision evidence | Separate from active effort. |
| Integration | review approval | merge/install checkpoint | Separate from active effort. |
| Blocked | evidenced block start | evidenced unblock/terminal event | Report separately; never silently count as active. |
| Elapsed | earliest supported lifecycle boundary | selected terminal boundary | Do not sum overlapping components. |

Interrupted, blocked, abandoned, and reassigned attempts retain their disposition and linked intervals. Multi-commit and multi-PR work is correlated to attempts/package, not treated as independent packages. Document creation/modification time cannot establish start, stop, or duration.

## Evidence and confidence

Reliability descends from correlated authoritative telemetry; complete receipts plus merged-PR and validation evidence; correlated repository commits/merges; PR lifecycle evidence; and authorized annotations. Document timestamps are contextual only. Conflicts remain recorded and produce a deterministic warning or unknown result.

Confidence is categorical, versioned, and based on comparable sample count, evidence reliability, recency, feature completeness, and interval coverage. `not_estimable` is a valid result. Bounds are rounded to the estimator version's declared granularity and satisfy lower <= expected <= upper.

## Baseline and calibration

The first estimator uses versioned rules plus deterministic bucket/nearest-neighbor comparisons. It publishes drivers, selected neighbors, exclusions, evidence cutoff, component ranges, and unadjusted/adjusted values. No machine learning is authorized.

Worker-specific adjustment is allowed only after five comparable validated outcomes spanning three packages. It is estimation metadata, not a performance judgment, and must follow package-complexity estimation. Otherwise the worker-class baseline applies.

Each eligible terminal outcome creates an append-only predicted-versus-actual comparison. Small-sample reporting includes signed/absolute error, eligible sample count, median absolute error, defined percentage errors with denominators, and interval coverage. Candidate versions replay the same frozen evidence snapshot and retain an explicit rollback pointer.

## Record relationships

`estimate_request` references a work package and immutable evidence cutoff. `feature_vector` records supplied/derived/unknown inputs. `estimate_result` references both plus estimator/config versions and optional `worker_profile_ref`. `actual_execution_outcome` contains package/attempt intervals and evidence. `estimate_actual_comparison` links one result to one outcome without rewriting either. `calibration_history` identifies the frozen comparison set, metrics, trigger, incumbent, candidate, decision, and rollback target. Every record includes schema/version provenance and append-only correction/supersession linkage.

## Operator and integration boundary

Evaluation is read-only. Diagnostics explain freshness, missing/conflicting evidence, thresholds, calibration state, and inability to estimate. Overrides are append-only annotations displayed separately from estimator truth. PL-0014 telemetry is an optional future evidence source; repository evidence supports bootstrap. PL-0016 may later consume the result contract. Neither relationship authorizes edits or calls to production runtime, scheduling, dispatch, Alfred, Helen, Open WebUI, Local Compute, Evelyn, residents, workers, registries, or queues.
