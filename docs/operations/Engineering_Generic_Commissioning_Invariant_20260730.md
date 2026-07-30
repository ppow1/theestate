# Engineering Generic Commissioning Invariant

**Date:** 2026-07-30  
**Campaign:** Grace–Engineering Operational Activation  
**Status:** GOVERNING CONSTRAINT

## 1. Core invariant

Production Engineering behavior must never be hard-coded to a bicycle, an image, ComfyUI, or any other specific test object, artifact type, or provider.

The bicycle exists only as an acceptance-test payload.

The production flow is:

`Grace objective -> Dispatch commission -> Engineering interpretation -> Engineering planning -> Engineering provider selection -> Provider execution -> Engineering validation -> Grace completion report`

Grace communicates the objective, constraints, acceptance criteria, authority boundaries, and required evidence through Dispatch. Grace does not choose the execution provider and does not encode a bicycle-specific implementation path.

Engineering receives a generic commission object. Engineering must determine:

- what kind of work the commission requires;
- what artifact or outcome must be produced;
- which capabilities are needed;
- which registered provider or combination of providers is appropriate;
- what execution plan should be followed;
- what commission-specific validation is required;
- whether to retry, block, escalate, or report completion.

## 2. Bicycle boundary

The bicycle may appear only in:

- acceptance-test fixtures;
- test input data;
- test assertions;
- test documentation describing the first institutional proof.

The bicycle must not appear in:

- production routing conditions;
- provider-selection rules;
- worker prompts as a fixed task;
- default artifact assumptions;
- production validation logic;
- status-transition logic;
- provider adapters except as ordinary user-supplied payload content;
- Grace orchestration logic;
- Dispatch lifecycle rules.

A production branch such as `if objective contains bicycle then use ComfyUI` is prohibited.

## 3. Generic commission contract

The Dispatch payload presented to Engineering must remain domain-neutral and should carry, at minimum:

- commission identifier;
- originating Grace objective identifier;
- requested outcome;
- constraints;
- acceptance criteria;
- authority boundaries;
- required evidence;
- deadline or priority when applicable;
- allowed or prohibited capabilities when policy requires them;
- escalation target.

Provider identity may be absent. When absent, Engineering owns provider selection. When policy or the Steward explicitly constrains providers, Engineering must honor those constraints without treating them as a domain-specific hard-coded route.

## 4. Required Engineering behavior

For every commission, Engineering must:

1. Interpret the generic commission.
2. Classify the work domain and required capabilities.
3. Produce a durable plan.
4. Inspect the provider registry.
5. Select the provider or provider chain based on capabilities, constraints, availability, cost, risk, and validation requirements.
6. Execute through the selected adapter.
7. Capture provider receipts and produced artifacts.
8. Validate the result against the commission's own acceptance criteria.
9. Retry, escalate, block, fail, or complete truthfully.
10. Return a completion report to Grace without transferring final Steward acceptance authority.

## 5. Test requirement

The bicycle test proves only that the generic mechanism can process one image-generation commission.

After it passes, at least two non-bicycle tests from different domains must pass through the same production code path without adding domain-specific routing logic. Suitable examples include:

- generating a textual engineering specification;
- inspecting a repository and proposing a code change;
- producing a simple CAD-oriented task plan;
- researching a procurement request;
- preparing a validated data transformation.

The exact follow-on tests may change, but they must demonstrate that the worker is generic rather than bicycle-shaped.

## 6. Completion gate

The Minimum Viable Engineering Worker is not acceptable if bicycle removal from the test suite would break production behavior.

The implementation is acceptable only when:

- production code contains no bicycle-specific logic;
- Grace remains provider-agnostic;
- Dispatch carries a generic commission;
- Engineering owns interpretation, planning, and provider selection;
- validation is derived from the commission's acceptance criteria;
- the bicycle passes as ordinary test data;
- materially different commissions pass through the same architecture.
