# ENG-OPS-005 Remaining Blockers Closure

## Codex routing

The Codex bridge now permits only immutable Grace action JSON records under `runtime/operations/grace/actions/` as prompt sources; other runtime, secret, and broad paths remain denied. Codex requests use the registered `codex.execution.cli` adapter, explicit `default` profile, `workspace-write` only when exact output scope requires it, approval policy `never`, and no bypass/cloud/full-access flags. Adapter-owned receipts remain in the governed write scope but are removed from the child-process write scope.

Fresh successful Codex lifecycle: objective `grace-obj-65a36ca8e2ff`, action `grace-act-8ce147bcb3b8`, capability `capreq-a6b867f49ff6`, Helen `heldet-312509e977d7`, PTM `res_01KYX5CA2EPMZY4RX47V34MNTV`, commission `engcom-b393ce6d709e`, authorization `engauth-2930d1a6b41d`, Dispatch `dispatch-7cb29dc31359`, completion `engcomp-e6fa2f3a1582`, Grace receipt `gracereceipt-0533cc7e4ebd`, one live Codex invocation.

## Steward technical intake

`estate grace-operations conduct --technical-request-file` now validates complete bounded intake, creates fresh Helen evidence, resolves fresh PTM readiness when no resolution is supplied, creates the Engineering commission/authorization and Operations decision, and queues Dispatch. It cannot synthesize broad scopes or grant acceptance. The canonical request fixture is `docs/operations/validation/ENG-OPS-005_Steward_Intake_Request_20260731.json`.

Fresh CLI lifecycle: objective `grace-obj-a2af3f0d2806`, action `grace-act-13f5f990694e`, capability `capreq-81c7e1c9fa2a`, Helen `heldet-15a2a0014588`, PTM `res_01KYX5ES03G8QDXSBYGEKPNWV6`, commission `engcom-d241862a765c`, authorization `engauth-f793760a5792`, Dispatch `dispatch-832a7ad8b8d6`, completion `engcomp-2dd8268f769d`, Grace receipt `gracereceipt-2bfa24fa1d7e`, one live Codex invocation.

## Failure injection

The Qwen adapter supports transport, timeout, malformed-response, and declared-failure injection only when `ESTATE_ENABLE_PROVIDER_FAILURE_INJECTION=1` and the request binds the mode to both commission and Dispatch. It does not mutate Ollama, model, catalog, or global provider state. The transport scenario used commission `engcom-1ee8bbafc913`, authorization `engauth-d35f2fccdbf7`, Dispatch `dispatch-c19c45eb392b`, one attempted adapter invocation, durable failure receipt, no artifact, rejected completion, Grace state `failed`, and acceptance `not_granted`.

Equivalent replay of the completed Codex lifecycle returned the same commission, authorization, and Dispatch with `provider_execution=already_completed`; no second provider call occurred. Fresh capability-gap and stale-PTM scenarios failed before commission/provider execution. A prohibited-scope scenario remained rejected before provider execution.
