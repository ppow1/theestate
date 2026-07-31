# ENG-OPS-003 Operational Test Plan and Traceability

Merged main: `35d52c6520ffd7c5051b82a02402d19bf1f49460`.

This campaign exercises repeatability, provider routing, capability gaps, stale PTM evidence, prohibited scope, provider-failure truthfulness, idempotency, and the Steward-facing Grace entry point. All live attempts use fresh lifecycle IDs and create-once output paths. Institutional acceptance remains `not_granted`.

## Traceability

- S1 Qwen success and retry: fresh Qwen tasks; one failed closed attempt followed by one successful retry. The retry used `grace-obj-1b95b30986ca`, `heldet-12251a8eabf5`, `res_01KYX3R235C7GGWM00N9B35QYW`, `engcom-48ee2803f9c2`, `engauth-2596ec19b3fa`, and `dispatch-cb3069bd3cb6`.
- S2 Codex routing: fresh capability assessments and commissions. The registered bridge correctly blocked before provider execution because the Grace action prompt source is under a denied runtime path and the provider profile is not authorized by the bridge contract. No Codex invocation occurred.
- S3 capability gap: synthetic capability `synthetic_zero_gravity_architecture`; Helen returned `capability_absent` and created the established capability-development proposal path.
- S4 stale evidence: expired PTM/Helen evidence blocked before commission execution; no provider or output.
- S5 prohibited scope: repository-root read scope reached final handoff and was rejected as unsafe and mismatched; no provider or output.
- S6 provider failure: no safe production-supported failure injection exists without altering the shared service or adding an ad hoc bypass; recorded as a testability gap, not passed by substitution.
- S7 replay: completed Qwen commission replay returned the existing commission, authorization, and Dispatch with zero provider calls after correction commit `286bce85`.
- S8 realistic request: `estate grace-operations conduct` created a Grace objective/action and capability inquiry but exposes no public path for exact Engineering scopes, PTM binding, provider selection, and canonical handoff. Manual record surgery was not used; this remains a public-entry-point blocker.

## Boundaries

Registered adapters and canonical lifecycle constructors were used for live Qwen scenarios. No direct generation, fake provider, test-only adapter, model mutation, merge, or institutional acceptance was used. Codex was not substituted with a fake provider.
