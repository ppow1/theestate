# PTM-backed Grace, Engineering, and Dispatch Integration

Status: bounded integration work package; live Qwen execution and institutional acceptance remain outside this package.

## Canonical path

`GraceHelenEngineeringComposition` is the production composition entry point. `commission_engineering()` resolves and binds a PTM readiness projection after Helen assessment and before writing an Engineering commission. Only `ready` or validly `waived` PTM states can create the commission. Missing, unknown, not-ready, blocked, stale, expired, malformed, contradictory, or drifted PTM evidence leaves Grace waiting or blocked and creates no commission.

`governed_commission_and_dispatch()` is the bounded operational entry point for tests and later governed runners. It creates the commission, accepts it through Engineering, and authorizes the canonical Dispatch queue. It never invokes a provider and never grants institutional acceptance.

## PTM evidence binding

`estate.core.ptm_readiness_integration` owns the consumer binding and revalidation seam. It uses `PtmProductionReadinessResolver`, `read_readiness()`, the canonical freshness policy, and the waiver-authority registry. Consumers carry immutable resolution ID, projection path/digest, state, source high-watermark, policy identity/digest, waiver-registry identity/digest, timestamps, dependency references, and waiver references. They do not recalculate readiness.

The capability-enablement production construction uses `PtmCapabilityDependencyResolver`. It maps only a current valid PTM resolution into the existing canonical dependency seam; it does not synthesize readiness when PTM evidence is absent.

## Dispatch boundary

Immediately before queue insertion, `execution_dispatch.enqueue_dispatch_request()` revalidates the commission’s PTM binding. The queue item records the same binding and revalidation result. Changed high-watermarks, policy or registry digests, expired projections, identity mismatch, malformed projections, and non-ready states fail closed. A durable rejection record is written under `runtime/grace_helen_engineering/dispatch_rejections/`; the canonical Dispatch queue is not mutated and no provider is invoked.

## Completion boundary

Engineering validation and completion records carry the Dispatch ID, PTM resolution ID/digest, source high-watermark, provider receipt, artifact references, validation evidence, and reconciliation outcome. Completion is recorded only after provider-result validation and reconciliation succeed. Rejected completion attempts produce bounded completion-rejection evidence. Grace’s terminal receipt preserves the PTM resolution reference and `institutional_acceptance_state: not_granted`.

The PTM authority is not held locked across the workflow. Immutable references and immediate Dispatch revalidation address the resolution-to-queue TOCTOU boundary. A later PTM change does not rewrite historical completion evidence; it blocks stale retries or continuation.
