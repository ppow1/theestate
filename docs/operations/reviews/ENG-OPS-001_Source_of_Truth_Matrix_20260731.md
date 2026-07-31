# ENG-OPS-001 Source-of-Truth Matrix

This matrix records the canonical owner and production path for the bounded
Engineering execution contract. It is part of the implementation evidence for
the first governed live task campaign.

| Field | Canonical owner / creation record | Governing contract | Production path | Final consumer | Freshness / binding |
|---|---|---|---|---|---|
| Requested capability | Helen determination from Grace capability inquiry | Helen determination record; Qwen extension schema | Inquiry → Helen assessment → commission extension → Dispatch → adapter request | Qwen capability gate | Helen evidence observed/expiry; provider catalog support |
| Qualification, availability, capacity, authorization evidence | Helen determination | Helen determination payload | Helen assessment → commission | Engineering and final handoff | Determination timestamps and evidence references |
| Provider health evidence | Helen determination plus canonical provider health record | Provider health record; Qwen extension | Health observation → Helen assessment → extension → final handoff | Qwen preflight and adapter | Fresh observed/expiry; exact repository-relative evidence path |
| Provider identity | Engineering selection constrained by provider catalog | Provider catalog and Dispatch metadata schema | Commission/authorization → Dispatch → adapter request | Registered adapter resolver | Exact provider ID match |
| Adapter identity/version | Registered provider catalog and provider configuration | Qwen execution extension schema | Engineering authorization → Operations decision → Dispatch → adapter request | Catalog resolver | Exact adapter ID/version match |
| Model identity | Qwen provider configuration | Provider configuration and Qwen extension schema | Config → Engineering extension → final handoff → adapter | Qwen adapter | `qwen3:8b`; configuration match |
| Prompt source/type/digest | Immutable Grace action bytes | Commission authority schema | Grace action → commission → authorization → Dispatch → adapter request | Final handoff prompt-byte recheck | SHA-256 recalculated at handoff |
| Exact read scope | Grace action execution authority | Commission authority schema | Grace action → commission → Dispatch → adapter request | Handoff path validator and adapter | Repository-relative, exact ordering, no broadening |
| Exact write scope | Grace action execution authority | Commission authority schema | Grace action → commission → authorization → Dispatch → adapter request | Qwen publication gate | Exact output set; create-once |
| Expected outputs | Grace action execution authority | Commission authority schema | Grace action → commission → authorization → Dispatch → adapter request | Qwen publication gate | Artifact and receipt paths must be exact |
| Artifact path | Grace action output authority, checked against Qwen extension | Qwen extension schema | Grace action → commission → Dispatch → adapter request | Qwen adapter | One bounded non-runtime output; collision fails closed |
| Provider receipt path | Grace action output authority, checked against Qwen extension | Qwen extension schema | Grace action → commission → Dispatch → adapter request | Qwen adapter and completion reconciliation | One exact JSON path under `runtime/engineering_adapter_receipts/` |
| PTM resolution/digest | PTM production resolver and ledger projection | Closed PTM binding schema | PTM → commission → authorization → Dispatch → final revalidation | Final handoff | State, policy, registry, high-watermark, expiry revalidated |
| Engineering commission | Engineering | Commission and execution-authority schemas | Grace/Helen/PTM → commission | Authorization and handoff | Immutable idempotency; exact authority |
| Engineering authorization | Engineering | Engineering authorization schema | Commission → create-once authorization → Dispatch | Final handoff | Canonical digest and cross-record correlations |
| Operations decision | Operations Control record | Operations decision schema | Authorization flow → durable decision → Dispatch | Final handoff | Canonical reference, digest, parent decision, expiry |
| Dispatch identity | Dispatch queue | Dispatch request and metadata schemas | Authorization → queue insertion | Handoff runtime | Create-once, exact provider metadata |
| Adapter request identity | Handoff runtime | Adapter request schema | Dispatch → `prepare_handoff()` → durable request | Registered adapter runtime | Create-once request publication |
| Provider receipt identity | Qwen adapter | Provider receipt contract | Adapter → receipt publication | Result validation and reconciliation | Receipt contains no full prompt; artifact SHA-256 must match |
| Completion/reconciliation | Engineering | Completion and reconciliation runtime | Adapter result → validation → reconciliation → completion | Grace terminal receipt | Validation and provider receipt required |

Provider-specific execution data is now a closed Qwen extension rather than an
unconstrained metadata override. The adapter remains responsible for execution
behavior only; it cannot create authority, select a model, or broaden scope.

