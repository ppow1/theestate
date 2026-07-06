# SERIES TASK WP-0136 — Establish the Office of Character Architecture

## Codex Command

Read collaboration/work_packages/pending/WP-0136_SERIES_establish_office_of_character_architecture.md and do exactly what it says.

## Mode

SERIES

## Mission

Make official, through Estate governance artifacts, the Office of Character Architecture and the officer role of Chief Character Architect.

This work package ratifies a new constitutional office under Steward authority. The office is responsible for resident and worker character architecture, including identity design, traits, behavioral arcs, intelligence profiles, inter-resident relationship mapping, model/cognition recommendations, and implementation-pattern recommendations.

## Steward Decision to Encode

The Steward has decided that the Estate needs a permanent office for character architecture.

Canonical office name:

```text
Office of Character Architecture
```

Canonical officer title:

```text
Chief Character Architect
```

Do not substitute the title `Chief Character Designer`, `Character Designer Engineer`, or `Character Development Engineer` unless documenting them as prior informal names that have now been superseded.

## Problem Statement

The Estate now contains residents, workers, local models, service surfaces, authority boundaries, and emerging resident-specific implementations. As the number of residents grows, the Estate needs a dedicated office responsible for designing and preserving character continuity, behavioral identity, cognition shape, capability boundaries, relationship dynamics, and implementation notes.

Without this office, character decisions risk becoming scattered across resident prompts, service manifests, implementation code, and ad hoc conversation records.

## Constitutional Intent

The Office of Character Architecture is an institutional office, not merely a creative role.

It exists to define how Estate residents and workers are designed as characters and cognitive participants, while preserving alignment with Estate governance, authority boundaries, resident APIs, service control, and Steward ratification.

## Required Constitutional Definition

Add governance language equivalent to the following in the most canonical Estate Constitution/governance location:

```text
Office of Character Architecture

The Office of Character Architecture is responsible for the design, specification, and continuity of Estate resident and worker identities, character systems, interpersonal dynamics, cognitive profiles, and implementation patterns.

The officer occupying this office is the Chief Character Architect.

The Chief Character Architect defines and maintains character architecture for Estate residents and workers, including personality traits, behavioral boundaries, emotional and developmental arcs, intelligence profiles, skill domains, relational interlocks, collaboration patterns, and long-term character evolution.

The Office may recommend technical substrates required to support a resident or worker, including prompt-only behavior, structured state, Python-backed logic, resident APIs, local services, dedicated LLM models, model preferences, memory systems, or other approved local execution mechanisms.

The Chief Character Architect may design and recommend resident capabilities, personality, model preferences, and implementation patterns, but may not independently grant operational authority, approve privileged execution, alter constitutional office powers, bypass Steward approval, or override Estate governance.
```

Adapt wording to fit existing constitutional style, but preserve the substance.

## Required Duties

The Office of Character Architecture must be documented as responsible for at least:

1. Designing resident and worker character profiles.
2. Defining traits, temperament, voice, strengths, weaknesses, and limitations.
3. Defining emotional, behavioral, developmental, and narrative arcs.
4. Defining intelligence level, reasoning style, specialty domains, and learning boundaries.
5. Designing how residents and workers interlock, collaborate, defer, conflict, escalate, and complement one another.
6. Maintaining continuity of resident identity across implementation changes.
7. Recommending model assignments or model capabilities needed for a resident or worker.
8. Recommending whether a resident or worker requires prompt-only behavior, structured memory, Python-backed logic, service access, resident APIs, or dedicated runtime state.
9. Coordinating with Engineering when character behavior requires code, tools, services, APIs, runtime state, tests, or implementation changes.
10. Coordinating with Governance when character behavior touches authority, autonomy, escalation, office powers, or constitutional boundaries.
11. Producing and maintaining character briefs, resident design records, relationship maps, continuity notes, and implementation recommendations.
12. Reviewing new resident proposals for character coherence and institutional fit before implementation.

## Boundaries and Prohibitions

The Office of Character Architecture must not be granted unrestricted authority.

Document these boundaries:

1. The Chief Character Architect does not grant operational authority.
2. The Chief Character Architect does not execute privileged actions.
3. The Chief Character Architect does not bypass Steward approval.
4. The Chief Character Architect does not override office authority boundaries.
5. The Chief Character Architect does not unilaterally assign service/model access where governance requires approval.
6. Technical implementation recommendations must be routed through Engineering, Governance, or the appropriate Estate office before becoming operational behavior.
7. Model recommendations are recommendations until approved through the relevant model/service authority path.

## Required Repository Updates

Inspect existing repository structure and update the canonical locations rather than inventing duplicates.

Likely locations to inspect include, but are not limited to:

```text
docs/
operations/
governance/
operations/residents/
operations/staff/
collaboration/
```

Update whichever canonical artifacts currently define:

- constitutional offices;
- governance structure;
- staff roster;
- resident/worker design responsibilities;
- office/occupant/implementation/state model;
- onboarding/orientation material if appropriate.

If no canonical file exists for one of those concepts, create the smallest necessary artifact and document why.

## Required New or Updated Artifacts

Create or update a canonical office record for:

```text
Office of Character Architecture
Chief Character Architect
```

Create or update a role/job description artifact containing:

- office name;
- officer title;
- mission;
- duties;
- authority boundaries;
- coordination requirements;
- deliverables;
- relationship to Engineering;
- relationship to Governance;
- relationship to resident APIs, local models, and AI services;
- notes on Steward ratification.

Create an operations report:

```text
operations/governance/WP-0136_office_of_character_architecture_report.md
```

Create a machine-readable report:

```text
runtime/governance/WP-0136_office_of_character_architecture_report.json
```

If the repository uses different canonical paths for governance reports, use those paths and document the choice.

## Required Completion Artifact

Create:

```text
collaboration/work_packages/completions/WP-0136_codex_done.json
```

It must include:

```json
{
  "work_package_id": "WP-0136",
  "codex_status": "done",
  "office_name": "Office of Character Architecture",
  "officer_title": "Chief Character Architect",
  "summary": "...",
  "governance_files_updated": [],
  "staff_or_roster_files_updated": [],
  "role_description_files": [],
  "report_path": "...",
  "machine_report_path": "...",
  "tests_run": [],
  "validation_commands_run": [],
  "known_limitations": [],
  "ready_for_ca_review": true,
  "merge_authority": "ca_verified_auto_merge_allowed"
}
```

## Required Validation

Run or document equivalent repository validation commands.

At minimum, run:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0136 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If canonical command names differ, use existing validation commands and document the mapping.

## Acceptance Criteria

WP-0136 is complete when:

1. The Office of Character Architecture is documented as an official Estate office.
2. The Chief Character Architect is documented as the canonical officer title.
3. Governance/constitution artifacts reflect the office and its boundaries.
4. Roster/staff or office records are updated where appropriate.
5. The role has a clear job description and deliverables.
6. The office is explicitly bounded from granting authority, executing privileged actions, or bypassing Steward approval.
7. Coordination with Engineering, Governance, resident APIs, local model selection, and AI services is documented.
8. WP-0136 report and completion artifacts exist.
9. Required validation commands have been run or documented.

## Merge Class

Class A. Escalate only if implementation requires changing existing constitutional power distribution, Steward authority, resident authority semantics, office hierarchy, production-readiness semantics, or worker autonomy rules beyond adding this office and its bounded responsibilities.
