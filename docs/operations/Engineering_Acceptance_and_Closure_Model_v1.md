# Engineering Acceptance and Closure Model v1

## Non-equivalent states

| State | Meaning | Authority and source |
|---|---|---|
| Worker completion | Worker asserts bounded implementation/evidence submission is ready. | Worker acknowledgement and package receipt. |
| Provider completion | Provider attempt reached its terminal result and was reconciled. | Existing provider attempt/result reconciliation. |
| Validation pass | Named recipe passed for a specific SHA/environment. | Independent validation report/validator acknowledgement. |
| Integration completion | Approved PR was merged and post-merge checks recorded. | Repository merged commit, PR, integration evidence. |
| Chief Architect engineering acceptance | Architecture, implementation, and engineering evidence are accepted for the stated scope. | Separate Chief Architect decision referencing exact commits/reports. |
| Steward final institutional acceptance | Institution accepts the governed outcome where Steward authority is required. | Separate Steward decision; never inferred from engineering acceptance. |
| Operational-readiness closure | Existing controller's required operational gates closed for the deployment/operation scope. | Existing operational-readiness closure report and authorized acknowledgements. |
| Archival closure | Evidence is indexed, retained, continuity handed off, and no open action is hidden. | Archive/continuity record after all required earlier states. |

States may be not required for a particular scope only through a recorded N/A rationale by the authority responsible for that stage. Chronological progress does not grant authority. A merged PR can be rejected; an accepted engineering design can remain operationally unready; readiness does not grant institutional acceptance; a receipt does not establish any protected state.

## Acceptance preparation and decision

The preparation packet identifies campaign/package, scope, immutable commits and PR, dependency and contract disposition, all validation/checkpoint/readiness reports, unresolved warnings with owners, rollback, receipt paths, and requested decision. It also lists every absent or N/A stage. The Chief Architect may accept, accept with explicit bounded conditions, reject to a named lifecycle stage, or block pending evidence. Conditions have owner, due/review trigger, and closure evidence.

The Steward's final institutional acceptance is requested only where campaign authority requires it and only after engineering acceptance and applicable readiness evidence are presented. Neither Engineering, a provider, Grace, Helen, Alfred, a validator, nor automation signs for Chief Architect or Steward authority.

## Closure and rollback

Package archival closure requires preserved source/merge identifiers, receipts, validation and decision records, resolved duplicate/stale evidence, continuity owner, and indexed recovery instructions. Campaign archival closure additionally requires every included package to have an explicit terminal disposition, campaign checkpoints to link actual merged commits, open conditions to remain visible, and the campaign's own acceptance authority to act. Archiving does not rewrite a rejected or failed history.

If a regression occurs after acceptance, preserve the original decision, record the regression, execute the governed repair or rollback, invalidate only the evidence stages actually affected, and seek renewed validation/readiness/acceptance where their bound commit or environment changed.

