# PL-0030 — Automated Reflection Point and Renewal Package Generator

**Category:** Institutional Continuity / Automation  
**Priority:** High  
**Originator:** Chief Architect / Steward  
**Date Captured:** 2026-07-15  
**Status:** Captured  
**Target Milestone:** Reflection-point process operationalization  
**Promotion Condition:** Promote when a future renewal is scheduled or when manual renewal packaging is repeated again.

## Idea

Create an official Estate command for repeatable officeholder Reflection Point and renewal packaging, rather than reconstructing the process manually from memory.

Possible command surfaces:

```text
estate reflection-point create
estate office renew <officeholder>
```

The command should use the canonical process and template already stored at:

- `docs/operations/ChatGPT_Worker_Reflection_and_Continuity_Process_v1.md`
- `docs/templates/ChatGPT_Worker_Reflection_Continuity_Template_v1.md`

## Intended Behavior

The command should:

1. Verify repository branch, commit, upstream, and working-tree state.
2. Identify the officeholder and office-specific onboarding manifest.
3. Collect a bounded, role-specific institutional onboarding corpus.
4. Generate the Reflection Point Continuity Package.
5. Generate the Execution Handoff Addendum.
6. Generate the Office Onboarding Collection and reading order.
7. Generate the Renewal Startup Seed.
8. Produce an attachment manifest with hashes and structural checks.
9. Detect missing, empty, duplicate, suspiciously truncated, or stale required files.
10. Build the Renewal Core ZIP and supplemental package.
11. Compute and report SHA-256 values.
12. Print the exact new-chat attachment and startup instructions.
13. Preserve the prior implementation as read-only fallback until the renewed implementation completes its first bounded assignment.

## Architectural Constraints

- Do not redesign the canonical reflection and continuity process.
- Do not treat transcript accumulation as continuity.
- Do not grant new authority during renewal.
- Keep canonical onboarding separate from implementation-specific continuity.
- Label inherited claims by evidence class.
- Do not mark a package ready when mandatory structural checks fail.
- Prefer deterministic, reproducible output from the same repository state.

## Rationale

The process already exists and works, but it is difficult to locate and has repeatedly been reconstructed from memory. Automation would make future renewals faster, safer, repeatable, and independently auditable while preserving the existing institutional process rather than replacing it.
