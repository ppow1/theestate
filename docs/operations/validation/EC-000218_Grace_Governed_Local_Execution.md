# EC-000218 — Grace governed local execution

Status: **Implementation complete; live browser acceptance blocked**

## Implemented boundary

The resident gateway now recognizes only an explicit bounded local-text
request for Grace. Ordinary conversation remains on the normal resident
conversation path. Ambiguous execution wording returns an explicit blocked
state and never creates a Dispatch request.

An accepted bounded request uses the existing
`GraceHelenEngineeringComposition`: Grace objective/action records are created,
Helen determines `text_generation` readiness, PTM readiness is resolved and
revalidated, Engineering creates the commission and authorization, the current
compute evidence selects a compatible physical resource, the existing
reservation ledger protects it, and Dispatch invokes the registered Qwen
adapter. The adapter receives only the registered UUID-bound runtime lane.
Composition-owned reconciliation then validates the provider result and returns
the Grace receipt.

## Live boundary result

The approved blue/green controller was pointed at an EC-000218 source-root
candidate configuration. Candidate ports were isolated (`8767`, `11436`,
`8081`) and the controller verified Grace and gateway identity. Candidate Grace
readiness was false because the runtime reported
`governed_local_execution_enabled=false` and `provider_effects_enabled=false`.
The controller stopped and reconciled the candidate processes. The dirty
primary checkout was not used as candidate evidence.

Consequently no live provider model invocation and no Playwright conversation
was attempted. The next acceptance requires an already-authorized candidate
Grace runtime configuration that enables governed local execution, fresh lane
health/capacity, and a safe RTX 4090 admission margin. No P100 fallback is
permitted.
