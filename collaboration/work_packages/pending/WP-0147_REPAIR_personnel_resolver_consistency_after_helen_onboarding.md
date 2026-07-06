# REPAIR TASK WP-0147 — Personnel Resolver Consistency After Helen Onboarding

## Codex Command

Read `collaboration/work_packages/pending/WP-0147_REPAIR_personnel_resolver_consistency_after_helen_onboarding.md` and do exactly what it says.

## Numbering Boundary

WP-0147 is in the assistant/Steward support repair range.

Do not renumber this into the WP-0200 through WP-0250 block. That block is reserved for Chief Architect #3's Office Controls workstream. Work package numbers are range-owned, not chronological; chronology comes from timestamps and Git history.

## Mode

REPAIR. Personnel resolver / HR onboarding consistency repair.

## Mission

Repair the Estate personnel resolver so newly onboarded personnel and previously onboarded Chief Architect #5 resolve consistently by display name, role title, employee id, mailbox id, and canonical actor form.

This repair follows a successful Helen HR onboarding run from WP-0146, where Helen onboarded Chief Architect #6, Ingrid, and the Chief Character Architect, but subsequent `personnel-resolve` checks failed for some display-name lookups.

## Background

Helen was used operationally to onboard the following personnel:

- Chief Architect #6
  - Employee ID: 9
  - Mailbox ID: 9
  - Onboarding packet: `collaboration/messages/msg_helen_onboarding_employee_0009_chief_architect__6.json`
  - Summary receipt: `operations/hr/onboarding_runs/0009_chief_architect__6_summary.md`

- Ingrid
  - Employee ID: 10
  - Mailbox ID: 10
  - Resident ID: `RES-000002`
  - Onboarding packet: `collaboration/messages/msg_helen_onboarding_employee_0010_ingrid.json`
  - Summary receipt: `operations/hr/onboarding_runs/0010_ingrid_summary.md`

- Chief Character Architect
  - Employee ID: 11
  - Mailbox ID: 11
  - Office: Office of Character Architecture
  - Role: Chief Character Architect
  - Onboarding packet: `collaboration/messages/msg_helen_onboarding_employee_0011_chief_character_architect.json`
  - Summary receipt: `operations/hr/onboarding_runs/0011_chief_character_architect_summary.md`

Helen also refused to onboard Chief Architect #5 because a personnel entry already exists. That refusal appears correct, but `personnel-resolve --actor "Chief Architect #5" --json` currently fails to resolve.

## Observed Failures

After the onboarding run, these commands failed:

```powershell
python -m estate.cli.main personnel-resolve --actor "Chief Architect #5" --json
python -m estate.cli.main personnel-resolve --actor "Chief Architect #6" --json
python -m estate.cli.main personnel-resolve --actor "Chief Character Architect" --json
```

Observed failures were of the form:

```json
{
  "actor": "Chief Architect #6",
  "resolved": false,
  "warnings": ["unresolved actor: Chief Architect #6"]
}
```

Ingrid resolved successfully:

```json
{
  "actor": "Ingrid",
  "resolved": true,
  "employee_id": 10,
  "mailbox_id": 10,
  "resident_id": "RES-000002"
}
```

This suggests the issue is not that Helen's onboarding pipeline failed. It is likely a resolver/index/normalization issue around names containing `#`, numeric titles, officer titles, display names, aliases, or newly created personnel records.

## Chief Architect #5 Context

Chief Architect #5 likely already exists due to prior WP-0124 onboarding work. Evidence exists in the repository under paths such as:

- `operations/onboarding/WP-0124_chief_architect_5_hiring_onboarding_report.md`
- `runtime/onboarding/WP-0124_chief_architect_5_hiring_onboarding_report.json`
- `operations/onboarding/WP-0124_helen_hr_onboarding_action.md`
- `runtime/onboarding/WP-0124_helen_hr_onboarding_action.json`
- `collaboration/messages/msg_helen_20260705_0001_ca5_hiring_onboarding_notice.json`
- `collaboration/work_packages/completions/WP-0124_codex_done.json`
- `operations/work_packages/backlog_continuity_CA3_to_CA5.md`

Treat Chief Architect #5 as an existing employee until proven otherwise. Do not create a duplicate Chief Architect #5.

## Required Work

### 1. Inspect resolver and registry implementation

Inspect before changing:

- `src/estate/core/personnel_identity.py`
- `src/estate/cli/main.py` personnel-resolve command
- any mailbox resolver or collaboration routing modules
- `data/registry/personnel.json`
- `data/registry/mailboxes.json`
- `collaboration/mailboxes/index.json`
- recent Helen onboarding artifacts created by WP-0146
- WP-0124 Chief Architect #5 onboarding artifacts

### 2. Determine the exact failure mode

Determine whether the resolver failure is caused by:

- display-name normalization not handling `#`;
- role/title values not treated as aliases;
- new entries created by Helen lacking required fields;
- mailbox index not updated in a format the resolver expects;
- personnel registry schema drift;
- duplicate/conflicting Chief Architect #5 records;
- stale runtime index rather than source registry;
- another specific defect.

Document the root cause in the completion receipt.

### 3. Repair resolver behavior conservatively

The resolver should support resolving personnel by at least:

- display name, e.g. `Chief Architect #6`;
- display name without hash, e.g. `Chief Architect 6`;
- normalized variants if already supported by Estate conventions;
- canonical actor, e.g. `employee.9`;
- mailbox actor, e.g. `mailbox.9`;
- resident name when linked, e.g. `Ingrid`;
- existing role/title aliases where safe.

Do not create broad fuzzy matching that can route to the wrong person. Prefer deterministic normalization and explicit aliases.

### 4. Reconcile Chief Architect #5

Find the existing Chief Architect #5 personnel record or onboarding evidence.

If Chief Architect #5 has a valid personnel entry:

- ensure it has employee id, mailbox id, display name, office, role, and any required alias fields;
- ensure the mailbox registry/index references it correctly;
- ensure `personnel-resolve --actor "Chief Architect #5" --json` resolves.

If the record is incomplete:

- repair the missing fields using existing WP-0124 evidence;
- do not create a second Chief Architect #5.

If evidence is insufficient:

- report exactly what is missing and leave Chief Architect #5 unresolved rather than inventing identity data.

### 5. Verify new Helen-created employees

Ensure the following resolve correctly:

```powershell
python -m estate.cli.main personnel-resolve --actor "Chief Architect #6" --json
python -m estate.cli.main personnel-resolve --actor "Ingrid" --json
python -m estate.cli.main personnel-resolve --actor "Chief Character Architect" --json
```

Also verify canonical forms where available:

```powershell
python -m estate.cli.main personnel-resolve --actor "employee.9" --json
python -m estate.cli.main personnel-resolve --actor "employee.10" --json
python -m estate.cli.main personnel-resolve --actor "employee.11" --json
python -m estate.cli.main personnel-resolve --actor "mailbox.9" --json
python -m estate.cli.main personnel-resolve --actor "mailbox.10" --json
python -m estate.cli.main personnel-resolve --actor "mailbox.11" --json
```

### 6. Preserve Helen onboarding artifacts

Do not delete or rewrite Helen's valid onboarding outputs for Chief Architect #6, Ingrid, or Chief Character Architect unless required to repair a malformed field.

Do not treat this as a failed Helen onboarding. Treat it as a resolver consistency repair unless evidence proves otherwise.

### 7. Tests

Add or update tests covering:

1. Personnel resolve by display name for `Chief Architect #6`.
2. Personnel resolve by display name variant `Chief Architect 6` if normalization supports it.
3. Personnel resolve by display name for `Chief Character Architect`.
4. Personnel resolve by `Ingrid` preserving resident linkage.
5. Personnel resolve by canonical `employee.N` and `mailbox.N` forms for Helen-created employees.
6. Resolver does not create duplicate Chief Architect #5.
7. Resolver handles existing Chief Architect #5 or reports incomplete evidence explicitly.
8. Existing personnel resolver behavior remains passing.

Use isolated temporary fixtures where possible. Do not make tests depend on local runtime-generated artifacts.

## Constraints

- Do not duplicate Chief Architect #5.
- Do not remove or rewrite valid onboarding history.
- Do not modify Office UI / WP-0213 noun-to-verb work.
- Do not modify Helen onboarding workflow unless a small compatibility fix is necessary.
- Do not use broad unsafe fuzzy matching.
- Do not rely on ignored runtime artifacts as source of truth.
- Do not invent missing identity data; derive from authoritative records or report insufficiency.

## Validation

Run focused tests for personnel identity, mailbox routing, Helen onboarding, and resolver behavior.

Suggested commands:

```powershell
$env:PYTHONPATH = "src"
python -m pytest tests -q
python -m estate.cli.main personnel-resolve --actor "Chief Architect #5" --json
python -m estate.cli.main personnel-resolve --actor "Chief Architect #6" --json
python -m estate.cli.main personnel-resolve --actor "Ingrid" --json
python -m estate.cli.main personnel-resolve --actor "Chief Character Architect" --json
python -m estate.cli.main personnel-resolve --actor "employee.9" --json
python -m estate.cli.main personnel-resolve --actor "mailbox.9" --json
```

If full tests are too slow, run the focused resolver/HR tests and document that limitation.

## Expected Outputs

- Resolver/code fix if needed.
- Registry/mailbox reconciliation if needed.
- Tests for resolver consistency.
- Completion artifact:
  `collaboration/work_packages/completions/WP-0147_codex_done.json`

## Acceptance Criteria

WP-0147 is complete when:

1. `personnel-resolve "Chief Architect #6"` resolves to Employee ID 9 / Mailbox ID 9.
2. `personnel-resolve "Ingrid"` still resolves to Employee ID 10 / Mailbox ID 10 / resident ID RES-000002.
3. `personnel-resolve "Chief Character Architect"` resolves to Employee ID 11 / Mailbox ID 11.
4. Chief Architect #5 is either resolved to the existing valid employee record or explicitly reported as incomplete with no duplicate created.
5. Canonical `employee.N` and `mailbox.N` forms resolve for newly onboarded employees.
6. Tests protect the fixed behavior.
7. Helen onboarding artifacts remain intact.
8. WP-0213 and Office control surfaces are untouched.

## Completion Signal

Before finishing, create `collaboration/work_packages/completions/WP-0147_codex_done.json` with:

- `work_package_id`: `WP-0147`
- `codex_status`: `done`
- `completed_at`
- `branch`
- `pull_request_url_or_not_applicable_reason`
- `merge_authority_or_equivalent`
- `summary`
- `root_cause`
- `files_changed`
- `tests_run`
- `known_limitations`
- `ready_for_ca_review`: true

## Merge Class

Class A if limited to personnel resolver, registry consistency, tests, and reconciliation. Escalate to Class B if changing personnel governance, registry schema semantics, mailbox routing contracts, or resident authority behavior.
