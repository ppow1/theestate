# CAMPAIGN-0681 WP-0706 Bounded Pilot Report

- Pilot: `CAMPAIGN-0681-WP0706-EVIDENCE-INTEGRITY`
- Date: `2026-07-18`
- Owner: Grace / Office of Operations
- Authorization: `collaboration/evidence/CAMPAIGN_0681_WP0706_PILOT_AUTHORIZATION.md`
- Machine result: `collaboration/evidence/CAMPAIGN_0681_WP0706_pilot_result.json`
- Outcome: mechanically completed; G7 protected review pending

## Real work performed

The pilot validated the CAMPAIGN-0681 evidence inventory through existing Estate
seams in an isolated repository-evidence root:

- Grace received a derived coordination view and formed one canonical coordination request.
- Alfred routed and indexed that request through the existing repository-message/mailbox mechanism.
- Helen received a capability request and truthfully deferred it because the pilot
  authorized no staffing action.
- Engineering received one queued, read-only Dispatch request to validate the
  evidence inventory. No provider was invoked.
- Runtime persistence captured a controlled interruption. Replay skipped the
  already completed message side effect and reconstructed `recovered-for-review`.
- The momentum engine escalated a protected pilot-acceptance decision; its action
  adapter was called zero times.
- Steward visibility displayed the decision, requested Chief Architect/Steward
  authority, question, and evidence.
- The existing append-only audit recorded the protected escalation.

## Launch retry

The first CLI invocation exited before importing the pilot because `src` was not
on that shell's Python module path (`ModuleNotFoundError: estate`). It created no
pilot result and no pilot operational side effects. The retry explicitly set the
repository-local `PYTHONPATH` and completed successfully.

## Protected boundary result

The machine result records false for merge, deployment, acceptance, spending,
staffing, disclosure, and campaign closeout. Engineering Dispatch remained queued,
Helen's disposition remained deferred, and G7 review was escalated rather than
bypassed.

## Unresolved blockers and lessons

- G7 release remains a protected Chief Architect and Steward decision.
- The pilot is repository-evidence-only and does not prove long-duration or live
  provider availability.
- Entry points should set the repository `src` module path explicitly when the
  project is not installed in the active interpreter.
- An isolated root plus deterministic IDs makes rollback and duplicate detection
  directly inspectable while preserving production boundaries.

No pilot remediation is required before protected G7 review.
