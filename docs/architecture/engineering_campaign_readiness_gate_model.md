# Engineering Campaign Readiness Gate Model

Status: Gate B contract
Campaign: CAMPAIGN_0670_ENGINEERING_DEPARTMENT_OPERATIONALIZATION
Work package: WP-0671

## Rule

This model adds Engineering policy checks to the canonical PTM/orchestrator readiness and schedule contract; it is not a scheduler or registry. Each campaign and package receives a readiness projection referencing canonical evidence. State is `ready`, `not_ready`, `blocked`, `waived`, or `unknown`. Execution is eligible only when every applicable gate is `pass` or validly `waived`; `unknown`, stale, conflicting, failed or expired evidence fails closed.

A readiness record includes campaign/package IDs, evaluated time, evaluator, source high-watermark, branch/base commit when known, gate results, evidence references/digests, expiry, waivers, conflicts and overall state. PTM/orchestrator owns machine-readable eligibility. Chief Architect architecture acceptance is a mandatory input, not inferred from PTM state.

## Gates, evidence and authority

| Gate | Required evidence | Decision authority | Verification |
|---|---|---|---|
| Architecture | accepted charter/ADR, scope/non-goals, decomposition and collision review | Chief Architect | manual decision reference; artifact/digest machine-checkable |
| Staffing | assigned owner, required qualifications, availability/capacity evidence | Helen supplies evidence; authorized staffing owner assigns; Chief Architect accepts adequacy | canonical workforce/assignment reference |
| Dependencies | every typed predecessor accepted/merged or explicitly waived; acyclic graph | canonical dependency authority; Chief Architect approves Engineering waiver | machine-check IDs/states; manual waiver signature |
| Provider capability | lane requirements and current capability/health evidence; selection remains separate | provider-routing/capability authority under WP-0672 contract | canonical catalog/health refs with observation time |
| Test environment | environment identity, fixtures, access, validation recipe and reproducibility check | validation owner; protected environment owner where applicable | exact preflight command or manual attestation named |
| Data and privacy | data classification, minimization, retention, secrets/PII boundary and approved handling | designated data/privacy authority | policy decision and bounded data references |
| Budget | estimate, approved ceiling, cost center and exception threshold | designated budget/protected-approval authority | canonical approval ID, amount/version/expiry |
| Protected approvals | security, legal, production, irreversible migration or other campaign-declared approval | authority named by governing policy; never provider/worker | durable approval/waiver reference |
| Validation plan | exact recipe, expected evidence, acceptance mapping and rollback check | Chief Architect accepts sufficiency; validator later records verdict | recipe/path/digest machine-checkable |
| Branch/collision | base, owner, allowed paths, collision resolution and release event | Chief Architect/integration owner | repository and collision table checks |

Architecture has no waiver for ordinary execution: no campaign reaches execution without explicit Chief Architect acceptance. A protected-policy authority alone may waive its governed gate, and the waiver must state scope, rationale, expiry and compensating controls. Staffing recommendations, provider recommendations, Grace checkpoints and test success are not approvals.

## Evaluation sequence

1. Resolve campaign/package IDs and primary campaign from canonical artifacts.
2. Verify parent authority and accepted architecture.
3. Evaluate dependencies and shared-file/branch controls.
4. Evaluate staffing, provider capability, environment, data/privacy, budget and protected approvals.
5. Verify validation and rollback plans.
6. Publish source-backed eligibility to the canonical PTM/orchestrator projection.
7. Dispatch may occur only from that eligible state through canonical Dispatch; a provider reservation or recommendation cannot trigger work.

Evidence changes, expiry, parent amendment, branch/base change, dependency regression, staffing loss, provider-health change, validation-recipe change or conflict invalidates the affected result and triggers reevaluation. Readiness never survives a material campaign amendment by default.

## Manual and machine-checkable dependencies

Machine-checkable evidence declares `source_ref`, `expected_state`, `observed_state`, `observed_at`, and a deterministic command/query. Manual evidence declares `verification: manual`, authority identity, decision reference, scope and time. A prose assertion without these fields evaluates `unknown`.

## Gate-B handoff to WP-0672

WP-0672 must preserve the same campaign/package/attempt IDs and treat provider recommendation, selection, reservation, Dispatch authorization and live confirmation as separate evidence. It may define lane capability requirements, but cannot weaken these readiness gates or treat availability as authorization. Scheduling eligibility belongs to PTM/orchestrator; provider scheduling is limited to a time-bounded reservation for an already eligible assignment.
