# Capability Enablement Acceptance Scenarios

Status: Proposed test matrix; no runtime behavior is changed.

| Scenario | Required truthful result |
|---|---|
| All required capabilities available | Helen reports qualified, healthy, available, authorized; normal proposal proceeds. |
| Capability unavailable | Gap is recorded; original objective waits. |
| Declared but unqualified | Not available; qualification evidence is required. |
| Qualified but unhealthy | Not available; stale or failed health blocks execution. |
| Healthy but unavailable | Not available; capacity/assignment evidence is required. |
| Available but unauthorized | Not available for this scope; authorization is separate from recommendation. |
| Ambiguous capability mapping | `capability_unknown`; no silent provider selection. |
| Helen requests Engineering specification | Advisory consultation only; no project, approval, or Dispatch is created by consultation. |
| Proposal rejected | Proposal is rejected with authority evidence; no execution begins. |
| Enabling project blocked | Enabling project remains blocked with dependency/bootstrap reason. |
| Enabling project completed | Registration evidence is required before Helen can re-evaluate. |
| Registration succeeds | Versioned descriptor, capability claims, health, qualification, and receipt/artifact contracts are recorded. |
| Registration fails | Capability remains unavailable; original project remains blocked. |
| Re-evaluation still finds gap | Original objective remains blocked and preserves the new evidence. |
| Original project resumes | Grace creates a new linked readiness/Dispatch attempt without repeating the original request. |
| Original project remains blocked | No false completion or automatic retry without policy. |
| Recursive capability assumption | Enabling project cannot use the capability it is creating as bootstrap evidence. |
| Quiet completion | Used only where existing policy permits and all authority boundaries are satisfied. |
| Steward notification required | Escalates instead of silently closing. |
| Multiple enabling projects | Dependencies are distinct, correlated, and all must satisfy before resume. |
| Superseded capability proposal | Old proposal remains immutable and points to its successor. |
| Stale manifest or health evidence | Evidence is expired/unknown; no availability claim. |
| Provider descriptor and adapter disagree | Registration fails closed; no dispatch or completion. |
| Successful worker process with no artifact/receipt | Process success is not commission success; completion is rejected. |
