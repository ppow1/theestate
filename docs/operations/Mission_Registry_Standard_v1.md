# Mission Registry Standard v1

Status: Active Standard
Owner: Chief Architect / Alfred Operations
Classification: Estate Internal
Introduced By: WP-0030
Date: 2026-07-02

## Purpose

The Mission Registry gives the Estate durable mission identifiers and human-readable mission titles for long-running initiatives that may span multiple chats, workers, work packages, documents, events, and audit records.

Missions are institutional tracking objects. They do not replace work package IDs, EC numbers, document IDs, audit evidence, promotion records, or Steward decisions.

## Mission ID Convention

Mission IDs use the format `MISSION-0001`.

- `MISSION` is the registry prefix for Estate missions.
- The numeric suffix is four digits, left-padded with zeroes.
- Numbers are assigned in ascending order and are not reused.
- A mission ID remains stable even if its title, owner, status, or related artifacts change.

Special-purpose prefixes such as `AO-0001` are not introduced by this standard. If a future approved standard creates a specialized mission namespace, it should map back to this registry rather than replacing existing `MISSION-####` IDs.

## Mission Registry Location

The machine-readable registry lives at:

- `data/registry/missions.json`

The registry is the durable index of mission records. This standard defines the intended fields and operating rules.

## Mission Record Fields

Each mission record should include these fields:

| Field | Type | Meaning |
|---|---|---|
| `mission_id` | string | Stable ID using the `MISSION-####` convention. |
| `mission_title` | string | Human-readable mission title. |
| `mission_type` | string | Small descriptive class such as `operations`, `pipeline`, `activation`, `onboarding`, or `strategic_initiative`. |
| `status` | string | Current posture. Recommended values: `active`, `planned`, `proposed`, `unresolved`, `completed`, or `superseded`. |
| `owner` | string | Role, office, or resident currently associated with coordination. This is not a new governance office. |
| `steward_authorization` | string | Conservative authorization note. Use `not_asserted`, `documented`, `proposed`, or another explicit descriptive value rather than implying approval. |
| `related_work_packages` | array of strings | Existing WP IDs or work package paths. This must preserve existing work package identifiers. |
| `related_documents` | array of strings | Stable document IDs or repository-relative document paths. |
| `related_artifacts` | array of strings | Repository-relative paths or artifact IDs for operational projections, registries, reports, or runtime records. |
| `created_at` | string | ISO date or timestamp when the mission record was first created. |
| `updated_at` | string | ISO date or timestamp for the latest registry update. |
| `notes` | string | Brief limitations, evidence notes, or operator guidance. |

## Status Guidance

Use statuses conservatively:

- `active` means existing artifacts show ongoing operational work.
- `planned` means artifacts identify expected future work but do not yet show active execution.
- `proposed` means the mission is a reasonable proposed grouping but still needs review.
- `unresolved` means evidence is insufficient or conflicting.
- `completed` means completion evidence exists for the mission scope.
- `superseded` means another mission or institutional structure replaced this record.

## Authority Boundaries

The Mission Registry is an index and coordination aid only.

It must not:

- create Steward approvals;
- replace work package IDs;
- replace EC numbers;
- replace audit evidence;
- create new governance offices;
- make generated projections authoritative;
- override the Document Registry, Artifact Provenance Model, or Generated Artifact Policy.

## Initial Registry Seeding Rules

Initial missions may be seeded only when existing artifacts support the mission title and relationship. When evidence is incomplete, the mission should be marked `proposed` or `unresolved`, and `steward_authorization` should avoid final approval language.

The first registry seed focuses on current Estate operating areas: operational stabilization, work package pipeline, Alfred activation, Helen onboarding, and autonomous operations / Steward recall planning where pending work packages indicate future work.
