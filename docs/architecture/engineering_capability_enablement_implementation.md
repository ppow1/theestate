# Capability Enablement Implementation Boundary

The implementation composes these owners:

```text
Grace objective/inquiry
  -> CapabilityEnablementLifecycle
  -> Helen evidence assessment and gap
  -> worker specification / creation proposal
  -> PTM-owned enabling-project dependency reference
  -> existing Dispatch and adapter handoff
  -> registered codex.execution.cli adapter
  -> provider receipt + artifact validation
  -> Helen re-evaluation
  -> Grace original-project resumption
```

`src/estate/core/engineering_capability_enablement.py` owns the new
correlation records and state transitions only. Helen remains the workforce
assessment authority; the provider catalog remains the technical declaration
source; PTM/orchestrator remains the project/dependency owner; Dispatch remains
the execution boundary; the adapter owns invocation evidence; validation and
institutional acceptance remain separate.

The lifecycle is append-only for enablement records. Re-evaluation creates a
new evidence record and Grace resumes the immutable original objective only when
all required capability facts are fresh and affirmative. A failed or partial
enablement leaves the original objective blocked.
