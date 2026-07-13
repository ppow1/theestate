# Character Architecture Post-Hardening Validation Failure Ledger

Date: 2026-07-12

## Original observed failures

Initial canonical run in this campaign collected 1257 tests and found 18 failures in assignment queue rendering, background operations extension/runtime behavior, resident task visibility, Office settings/rendering, subprocess CLI imports, Operations Center bootstrap, provider catalog CLI subprocesses, resident cards, resident interaction intent distinction, and Steward Command Center navigation/roadmap rendering.

## Classification and final disposition

| Failure group | Root cause classification | Disposition |
|---|---|---|
| Assignment queue markdown header | Stale test/renderer contract drift after priority column introduction | Repaired renderer to preserve canonical queue table contract. |
| Background operations extension config | Runtime state path and compatibility config expectations diverged | Repaired runtime to keep externalized runtime config as authoritative while writing compatibility config during dry-run discovery and reading explicit compatibility fixtures. |
| Background operations no-trigger cycle / post-merge watch | Cross-runtime integration defect between default watches, explicit watch fixtures, and non-git temp roots | Repaired operational-target watch handling to avoid auto-triggering default non-git temp roots while preserving explicit governed audit watch behavior. |
| Resident task board waiting status | Stale-status inference overrode explicit waiting-on state | Repaired status classification so explicit waiting remains waiting and private fields remain filtered. |
| Office settings dark theme | HTML body did not materialize persisted appearance settings | Repaired body attribute rendering for non-default theme/accent/density. |
| Subprocess CLI imports | Pytest subprocesses did not inherit src-layout import path | Repaired test environment subprocess PYTHONPATH propagation and Operations Center bootstrap subprocess environment. |
| Operations Center bootstrap | Status polling depended on expensive full payload generation | Repaired bootstrap server status path with fast startup health mode while retaining full quiet-refresh status for normal server use. |
| Resident card / Office auxiliary panels | Renderer filtered panels absent from current navigation tabs | Repaired rendering to preserve auxiliary dashboard/personnel HTML without re-adding deprecated navigation tabs. |
| Resident interaction mode intent | Alfred mode question could be answered with role text despite local LLM metadata | Repaired mode-intent response to truthfully surface local_llm_generated. |
| Steward command center navigation and roadmap | Navigation had extra operational/personnel entries and roadmap boundary text lacked required no-promotion language | Repaired navigation/tab contract and roadmap authority warning. |

## Unresolved failures

None. The complete canonical suite passes after repair.
