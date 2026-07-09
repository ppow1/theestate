# WP-0226 - Alfred Estate and Engineering Department Boundary

Status: Proposed
Priority: Critical
Owner: Office of Character Architecture
Primary Consumers: Steward, Alfred, Helen, Engineering Department, CueMastery workstream
Classification: Estate Internal
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is a narrow architectural correction package. Recent resident work risks implying that Alfred is directly responsible for CueMastery. The Steward clarified that Alfred worries about the Estate. The Estate is bringing the Engineering Department online, and the Engineering Department will take on engineering tasks associated with CueMastery.
```

Local runtime required:

```text
false
```

## Codex Command

```text
Read this work package and do exactly what it says.
```

## Mission

Capture and enforce this responsibility boundary:

```text
Alfred worries about the Estate.
Alfred does not own CueMastery.

The Estate is bringing up and bringing online the Engineering Department.
The Engineering Department will take on the engineering tasks associated with CueMastery.

CueMastery is an engineering project/workstream.
Alfred may brief Estate-level status, surface blockers, route attention, and protect the Steward's focus, but Alfred should not be framed as directly responsible for CueMastery execution.
```

This correction belongs in WP-0226 because WP-0225 is a nomenclature repair package and may already be in flight or merged. Do not modify WP-0225 as the carrier for this architectural boundary.

## Steward Intent

The Steward identified this principle:

```text
Residents belong to the Estate.
Projects belong to departments.
Engineering projects belong to the Engineering Department.
```

Alfred's role is Chief of Staff for the Estate, not project manager for CueMastery.

## Scope

### Required Outcome 1 - Boundary Artifact

Create:

```text
docs/character-architecture/Alfred_Estate_Engineering_Boundary_v0_1.md
```

The artifact must state:

- Alfred worries about the Estate;
- Alfred is Chief of Staff / resident support for Estate coordination;
- Alfred does not own CueMastery execution;
- the Estate is bringing the Engineering Department online;
- the Engineering Department owns engineering task execution;
- CueMastery is an Engineering Department project/workstream;
- Alfred may brief, route, surface blockers, and coordinate Estate-level readiness;
- Alfred must not be framed as directly executing or managing CueMastery work unless a future governance decision explicitly changes that boundary.

### Required Outcome 2 - Update Affected Language

Search active artifacts for language that implies Alfred directly owns, executes, or manages CueMastery work.

Update those references so Alfred is responsible for Estate coordination while Engineering owns CueMastery engineering execution.

Likely affected areas include Alfred runtime/integration documents, Helen resident documents, CueMastery return-gate documents, WP-0224 outputs, and related tests/fixtures. File names may differ depending on whether WP-0225 has landed. Search the repository rather than relying only on this list.

Do not redesign CueMastery or the Engineering Department.

### Required Outcome 3 - Tests

Add deterministic tests.

Suggested path:

```text
tests/character_architecture/test_alfred_estate_engineering_boundary.py
```

Tests should verify:

- the boundary artifact exists;
- it states that Alfred worries about the Estate or Estate-level coordination;
- it states that Alfred does not own CueMastery execution;
- it states that the Engineering Department owns or takes on CueMastery engineering tasks;
- active Alfred language does not frame Alfred as the direct owner/executor/project manager of CueMastery.

### Required Outcome 4 - Validation Recipe

Add a WP-0226 validation recipe if consistent with current validation registry conventions.

Expected local validation command:

```powershell
CLS
$ErrorActionPreference = "Stop"
Set-Location "A:\theestate"
python -m estate.cli.main validate-work-package --id WP-0226 --json
```

The recipe must include:

- boundary artifact exists;
- deterministic boundary tests pass;
- completion receipt exists;
- Alfred / Engineering / CueMastery boundary is present.

### Required Outcome 5 - Completion Receipt

Create:

```text
collaboration/work_packages/completions/WP-0226_codex_cloud_web_done.json
```

The receipt must include:

- work_package_id;
- provider;
- files changed;
- boundary summary;
- tests run;
- validation commands run;
- known limitations;
- recommended next action.

## Out Of Scope

This package must not:

- modify WP-0225 as the carrier for this boundary;
- redesign CueMastery;
- redesign or fully implement the Engineering Department;
- make Alfred responsible for CueMastery execution;
- create new residents;
- create a new runtime;
- alter WP-0617 ownership of background operations;
- expand resident architecture beyond the boundary correction.

## Acceptance Criteria

Accept this package only if:

- Alfred is clearly positioned as Estate-level Chief of Staff / coordinator;
- CueMastery is clearly positioned as an Engineering Department project/workstream;
- Engineering is identified as the institutional owner for CueMastery engineering tasks;
- Alfred is not framed as directly responsible for CueMastery execution;
- tests pass;
- WP-0226 validation passes;
- completion receipt exists;
- no unrelated architecture expansion occurs.

## Expected Next Step After Completion

After this boundary correction, return to the prior execution path:

```text
Continue standing up Alfred and Helen enough to support Estate coordination and Engineering Department bring-up, then let Engineering take on CueMastery work through normal Estate channels.
```
