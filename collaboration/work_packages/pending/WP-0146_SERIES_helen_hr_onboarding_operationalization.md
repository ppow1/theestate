# SERIES TASK WP-0146 — Helen HR Onboarding Operationalization

## Codex Command

Read `collaboration/work_packages/pending/WP-0146_SERIES_helen_hr_onboarding_operationalization.md` and do exactly what it says.

## Numbering Boundary

WP-0146 is in the assistant/Steward support repair and operationalization range.

Do not renumber this into the WP-0200 through WP-0250 block. That block is reserved for Chief Architect #3's Office Controls workstream. Work package numbers are range-owned, not chronological; chronology comes from timestamps and Git history.

## Mode

SERIES. Helen HR backend/CLI operationalization.

## Mission

Make Helen operational enough to perform real command-line HR onboarding for new Estate personnel without touching the Office of the Steward UI controls, WP-0213, or the noun-to-verbs Office control repair.

Helen should become the bounded HR hiring/onboarding engine for the next staffing wave, beginning with Ingrid and followed by additional Chief Architects and the Chief Character / Resident Development Engineer.

## Background

The Steward tested Helen from the command line and confirmed that Helen can already produce a bounded local onboarding/personnel operational summary and a dry-run onboarding for Ingrid.

Observed Helen dry-run output included:

- Helen resident identity resolved as `RES-000003`.
- Helen role: Human Resources / assignment fit, performance, health, capability, reassignment.
- Personnel registry available with 9 visible records.
- Authority boundary correctly denies automatic work-package execution.
- Authority boundary allows non-authoritative summarize behavior.
- Dry-run onboarding for Ingrid succeeded with `ok: true`.
- Candidate Ingrid was assigned Employee ID 9 and Mailbox ID 9 in dry-run.
- Helen prepared personnel entry, mailbox folders, onboarding packet, resolver visibility, and audit artifacts.
- Helen reported missing supporting runtime artifacts such as mailbox index, mailbox synchronization duty, onboarding manifest, onboarding status, and resident cards.

This proves Helen has a usable HR workflow foundation, but it needs to be operationalized carefully before real onboarding is used to staff Ingrid, Chief Architect #5, Chief Architect #6, and the Chief Character / Resident Development Engineer.

## Strategic Reason

This is now a staffing and institutional-load problem, not only an Alfred tuning problem.

Chief Architect #3 and Chief Architect #4 are carrying too much accumulated context. Their context load is becoming a bottleneck. The Estate needs Helen to help stand up additional personnel so responsibilities can be distributed across offices and workers.

Helen should perform onboarding through a repeatable HR workflow rather than one-off manual edits.

## Hard Boundary With WP-0213

This work must not interfere with WP-0213, which is responsible for implementing real Office operational verbs after the noun-to-verb control-surface failure.

Do not modify:

- `src/estate/core/steward_command_center.py`
- Office UI rendering
- browser/served Office controls
- `office_*_actions.py` modules installed by WP-0212
- WP-0213 files or workstream artifacts
- AI Services / Models UI
- any visible Office control button or handler wiring

This package is command-line/backend HR only.

## Scope

In scope:

1. Inspect Helen's current command-line HR onboarding implementation.
2. Strengthen dry-run onboarding output and validation.
3. Ensure real onboarding can be executed safely from CLI with explicit Steward authorization.
4. Ensure Helen creates or updates the correct source artifacts for personnel, mailbox, onboarding packet, and HR audit result.
5. Ensure missing runtime/support artifacts are either generated where appropriate or reported clearly as non-blocking/blocking.
6. Add clear human-readable HR onboarding summary receipts.
7. Add tests for Helen dry-run and real onboarding behavior using isolated temporary roots where feasible.
8. Preserve resident authority boundaries: Helen may orchestrate approved onboarding but may not invent Steward authorization or execute unrelated work packages.

Out of scope:

- Office UI changes.
- WP-0213 implementation.
- Starting/stopping AI services.
- Creating autonomous workers.
- Redesigning personnel governance.
- Creating Ingrid's complete security office.
- Creating a backup/export system.

## Required Functional Outcomes

### 1. Helen command-line readiness check

Provide or strengthen a command-line check that confirms Helen can perform HR onboarding duties.

Existing commands may already include:

```powershell
python -m estate.cli.main helen-duty --json
python -m estate.cli.main helen-onboard ... --dry-run --json
```

Use existing CLI conventions. Do not add duplicate commands if appropriate commands already exist.

### 2. Dry-run onboarding must be trustworthy

Dry-run onboarding must clearly show:

- candidate name;
- proposed employee ID;
- proposed mailbox ID;
- department;
- office;
- role;
- classification;
- package type;
- Steward authorization reference;
- artifacts that would be created;
- registry/mailbox/resolver impact;
- blocking vs non-blocking missing artifacts;
- whether any source files were actually modified.

Dry-run must not silently mutate authoritative source files unless the current design intentionally writes separate dry-run artifacts. If dry-run writes preview artifacts, those artifacts must be clearly labeled as dry-run/non-authoritative.

### 3. Real onboarding must be gated

Real onboarding must require explicit Steward authorization text/reference.

Helen must not complete onboarding by assertion. She must record the authorization reference used.

The real onboarding path should create/update appropriate artifacts such as:

- personnel registry entry;
- mailbox registry entry if applicable;
- mailbox directory/folders;
- onboarding packet message;
- HR onboarding run/audit artifact;
- resolver-visible identity confirmation;
- mailbox visibility confirmation.

### 4. HR summary receipt

At the end of dry-run and real onboarding, produce a human-readable HR summary receipt.

Suggested output path pattern:

```text
operations/hr/onboarding_runs/<employee_id>_<slug>_summary.md
```

The summary should include:

```text
Hiring Summary
Candidate:
Employee ID:
Mailbox ID:
Office:
Role:
Status: dry_run_complete | onboarded | blocked
Artifacts created or previewed:
Outstanding items:
Authority reference:
Next actions:
```

### 5. Missing support artifacts

Helen currently reports these as missing:

- `runtime/mailboxes/index.json`
- `runtime/mailboxes/synchronization_duty.json`
- `data/onboarding/manifest.json`
- `runtime/onboarding/status.json`
- `runtime/residents/cards.json`

Codex must classify each as one of:

- required blocker for real onboarding;
- non-blocking runtime projection;
- should be generated by an existing command;
- should be a later work package.

Do not invent large new subsystems here. If generation already exists, call or wire the existing generator. If not, report the gap clearly.

### 6. Staffing targets for validation

Use dry-run tests or safe fixtures to validate the intended next hires:

- Ingrid — Security Manager / Boundary Guardian, Office of Security and Boundary.
- Chief Architect #5 — Office of Chief Architect.
- Chief Architect #6 — Office of Chief Architect.
- Chief Character / Resident Development Engineer — resident character, voice, behavior, boundaries, and personality consistency.

Do not necessarily perform real onboarding for all four in this package unless Steward has explicitly authorized real creation. The package must make Helen capable of doing it safely.

### 7. Authority boundary preservation

Helen's authority boundary must remain explicit:

- Helen may summarize onboarding/personnel operational state.
- Helen may identify onboarding blockers.
- Helen may surface HR-related artifacts.
- Helen may orchestrate an explicitly authorized onboarding workflow.
- Helen may not create HR governance.
- Helen may not authorize personnel changes herself.
- Helen may not execute work packages automatically.

## Files To Inspect

Inspect existing HR/resident/personnel systems before changing anything:

- `src/estate/core/hr_onboarding.py`
- `src/estate/core/helen_duty.py`
- `src/estate/cli/main.py`
- `src/estate/core/personnel_identity.py`
- `src/estate/core/resident_authority.py`
- `data/registry/personnel.json`
- `data/registry/mailboxes.json`
- `data/registry/residents.json`
- `collaboration/mailboxes/`
- `collaboration/messages/`
- `operations/hr/`
- `runtime/hr/`
- relevant tests covering Helen, HR onboarding, personnel resolution, mailbox visibility, and resident authority.

## Validation

Run focused tests covering Helen/HR onboarding and any touched registry/resolver code.

At minimum, run relevant tests discovered in the repository. If exact test names differ, document what was run.

Suggested commands:

```powershell
$env:PYTHONPATH = "src"
python -m pytest tests -q
python -m estate.cli.main helen-duty --json
python -m estate.cli.main helen-onboard `
  --name "Ingrid" `
  --department "Security and Boundary" `
  --office "Office of Security and Boundary" `
  --role "Security Manager / Boundary Guardian" `
  --classification "Estate Internal" `
  --package-type "standard" `
  --steward-authorization "Steward authorization dry-run validation for WP-0146" `
  --dry-run `
  --json
```

If real onboarding is tested, do it only in an isolated test root or with explicit Steward authorization for the real repository.

## Expected Outputs

- Strengthened Helen HR onboarding implementation if needed.
- Strengthened Helen CLI/dry-run/real-run behavior if needed.
- Human-readable onboarding summary receipt generation.
- Tests for dry-run and gated real onboarding behavior.
- Documentation or report classifying missing supporting artifacts.
- Completion artifact:
  `collaboration/work_packages/completions/WP-0146_codex_done.json`

## Acceptance Criteria

WP-0146 is complete when:

1. Helen can perform a trustworthy CLI dry-run onboarding for Ingrid and the next staffing targets.
2. Helen can perform real onboarding only with explicit Steward authorization.
3. Helen produces personnel/mailbox/onboarding/audit artifacts through the existing HR pipeline.
4. Helen produces a human-readable hiring summary receipt.
5. Missing support artifacts are classified as blockers, non-blocking runtime projections, generated-by-existing-command, or future work.
6. Helen's authority boundaries remain intact.
7. No Office UI, WP-0213, or noun-to-verbs control work is modified.
8. Tests pass or any unrelated failures are documented clearly.

## Completion Signal

Before finishing, create `collaboration/work_packages/completions/WP-0146_codex_done.json` with:

- `work_package_id`: `WP-0146`
- `codex_status`: `done`
- `completed_at`
- `branch`
- `pull_request_url_or_not_applicable_reason`
- `merge_authority_or_equivalent`
- `summary`
- `files_changed`
- `tests_run`
- `known_limitations`
- `ready_for_ca_review`: true

## Merge Class

Class A if limited to Helen HR CLI/backend behavior, tests, and receipts. Escalate to Class B if the repair changes personnel governance, registry schemas, resident authority semantics, or Office UI behavior.
