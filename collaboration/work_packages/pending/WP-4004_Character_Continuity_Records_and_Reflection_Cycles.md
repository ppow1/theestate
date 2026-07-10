# WP-4004 — Character Continuity Records and Reflection Cycles

Status: Pending
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4002
Classification: Estate Internal

## Objective

Implement the first durable Character Continuity mechanism for long-lived residents using finite operational cycles, reflection, consolidation, and continuity artifacts.

## Core Rule

A mature resident becomes simpler and more coherent over time, not larger through endless prompt accumulation.

## Required Scope

Implement versioned records for:

- stable identity;
- current operating cycle;
- working journal summary;
- lessons retained;
- contradictions and unresolved drift;
- reflection outcome;
- continuity artifact;
- next-cycle initialization;
- protected/private classification metadata.

Add deterministic lifecycle states:

```text
active
reflection_due
in_reflection
continuity_ready
new_cycle_ready
archived
```

Implement:

- reflection eligibility rules;
- finite-cycle closure;
- continuity artifact generation from supplied evidence;
- explicit separation of working notes from long-term continuity;
- safe initialization of a new session/cycle;
- audit linkage between predecessor and successor cycles;
- Helen review hooks;
- Ingrid classification hooks;
- CLI inspection and tests.

## Deliverables

- core continuity model and local store;
- versioned JSON schemas;
- CLI surfaces for status, reflection preparation, continuity creation, and cycle start;
- examples for Alfred and Helen without exposing private content;
- `operations/validation/reports/WP-4004_character_continuity.md`;
- `collaboration/work_packages/completions/WP-4004_codex_done.json`.

## Boundaries

Do not create a new resident identity during cycle refresh. Do not copy unrestricted journals into continuity records. Do not automate psychological diagnosis. Do not replace Helen's workforce judgment or Ingrid's privacy authority.

## Acceptance Criteria

- one resident identity persists across cycles;
- continuity records are concise, versioned, and auditable;
- private material cannot leak into public continuity output;
- a new cycle can start without carrying the full prior transcript;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4004_Character_Continuity_Records_and_Reflection_Cycles.md and do exactly what it says.
```
