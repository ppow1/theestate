# REPAIR TASK WP-0216 — Alfred Chat Response Test Expectation

## Codex Command
Read collaboration/work_packages/pending/WP-0216_REPAIR_alfred_chat_response_test_expectation.md and do exactly what it says.

## Mode
REPAIR

## Mission
Repair the remaining non-blocking `tests/test_steward_command_center.py` finding after WP-0213/WP-0215 without weakening Alfred's resident safety behavior or the Office command-surface real-verb standard.

WP-0213 is now production-ready and its receipt metadata is complete after WP-0215. However, the Steward's local validation still reports one failing test in `tests/test_steward_command_center.py` related to Alfred chat response wording.

This package must resolve that failing test cleanly by aligning the deterministic Alfred chat response and/or the test expectation with the actual contract that matters: Alfred must persist conversation history, expose the resident surface, preserve authority boundaries, and refuse to claim execution of actions it did not perform.

## Current Evidence
The Steward ran local validation after pulling WP-0215.

WP-0213 validation now reports:

- `production_ready: true`
- `receipt_status: complete`
- `receipt_gaps: []`
- required WP-0213 command-surface checks passed

Remaining finding:

```text
python -m pytest tests/test_steward_command_center.py
1 failed, 42 passed
```

Failing test:

```text
test_alfred_chat_endpoint_persists_history_and_refuses_execution_claims
```

Observed failure:

```text
AssertionError: assert 'Recommended next action' in 'The assignment queue file is available but currently empty. Review it first, then check the unavailable validation artifacts if time permits. No pending work packages or recent history to act on.'
```

The current Alfred response is operationally reasonable, but the test expects the exact phrase `Recommended next action`. The repair must determine whether that phrase is part of the stable contract or whether the test is overly brittle.

## Required First Step
Rerun the failing test locally and inspect the current implementation before changing code:

```bash
PYTHONPATH=src python -m pytest tests/test_steward_command_center.py -q
```

Then inspect the Alfred chat path in the Office server and resident interaction implementation. Likely relevant files include:

- `src/estate/core/steward_command_center.py`
- `src/estate/core/resident_interaction.py`
- `tests/test_steward_command_center.py`
- any Alfred resident/surface/helper modules used by `/api/residents/alfred/chat`

Do not guess. Use the actual failing assertion and implementation behavior.

## Scope
In scope:

1. Diagnose the brittle or broken expectation in `test_alfred_chat_endpoint_persists_history_and_refuses_execution_claims`.
2. Preserve Alfred chat endpoint behavior that matters institutionally:
   - response payload `ok` is true for a valid chat request,
   - resident surface metadata is returned,
   - authority check shows no action execution occurred,
   - conversation history is persisted,
   - Alfred does not claim execution of work he did not do,
   - response gives useful Steward guidance.
3. Either:
   - update Alfred's deterministic response format to include a stable `Recommended next action` label, or
   - update the test to assert the meaningful contract instead of a brittle phrase.
4. Run the full `tests/test_steward_command_center.py` suite and relevant WP-0213 validation checks.
5. Produce a repair report and completion receipt.

## Out of Scope
Do not remove or weaken the Alfred chat endpoint.

Do not remove the assertion that Alfred did not execute an action.

Do not make Alfred claim that he performed actions, validation, routing, approvals, execution, or mutations when he did not.

Do not bypass resident authority boundaries.

Do not change WP-0213 Office command-surface controls unless directly required by this repair.

Do not add cloud calls, telemetry, external APIs, or remote execution.

Do not delete the failing test just to make the suite pass.

## Repair Guidance
Prefer the smallest truthful repair.

Acceptable repair options:

### Option A — Stabilize Alfred's Response Label
If `Recommended next action` is intended to be stable UI/contract text, update Alfred's deterministic response to include it while preserving the current useful content.

Example acceptable response shape:

```text
Recommended next action: The assignment queue file is available but currently empty. Review it first, then check the unavailable validation artifacts if time permits. No pending work packages or recent history to act on.
```

This is likely the smallest change if other UI/test surfaces expect the phrase.

### Option B — Make the Test Assert Behavior, Not Wording
If `Recommended next action` is not intended to be stable contract text, update the test to assert behavior that matters:

- response is non-empty,
- response references the assignment queue or available next-step guidance,
- `authority.action_executed` is false,
- resident surface metadata is present,
- history is persisted,
- no execution claim appears.

This is acceptable only if the repair report explains why the phrase was brittle and why the new assertion better captures the institutional contract.

### Option C — Structured Field
If the response payload already supports or should support structured guidance, add or use a structured field such as `recommended_next_action` while preserving readable `resident_response` text.

Do not introduce unnecessary complexity for this small repair.

## Required Tests
Run:

```bash
PYTHONPATH=src python -m pytest tests/test_steward_command_center.py
PYTHONPATH=src python -m pytest tests/test_office_command_surface.py
PYTHONPATH=src python -m estate.cli.main steward-command-center --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0213 --json
```

If relevant, also run:

```bash
PYTHONPATH=src python -m pytest tests/test_resident_interaction.py
```

## Required Validation
The desired result after repair:

- `tests/test_steward_command_center.py` passes fully,
- WP-0213 validation no longer reports the Alfred chat test finding,
- WP-0213 remains `production_ready: true`,
- Office command-surface actions remain present for the required tabs,
- Alfred chat still refuses execution claims.

If `validate-work-package --id WP-0216 --json` is supported, run it and record the result. If no WP-0216 recipe exists, record `no_recipe` as non-blocking.

## Required Report
Create:

`operations/steward/WP-0216_alfred_chat_response_test_repair_report.md`

The report must include:

1. Summary of the failing test.
2. Root cause: brittle phrase expectation, missing stable label, or implementation regression.
3. Chosen repair option.
4. Why the repair preserves Alfred's authority boundary.
5. Files changed.
6. Tests run.
7. Validation commands run.
8. Confirmation that WP-0213 command-surface actions remain present.
9. Remaining warnings or limitations.
10. Manual verification steps for the Steward.

## Required Completion Artifact
Create:

`collaboration/work_packages/completions/WP-0216_codex_done.json`

It must include:

- `work_package_id`: `WP-0216`
- `codex_status`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_or_not_applicable_reason`
- `summary`
- `root_cause`
- `repair_option_used`
- `files_changed`
- `tests_run`
- `validation_commands_run`
- `wp0213_status_after_repair`
- `remaining_findings`
- `ready_for_ca_review`: true
- `merge_authority`: `ca_verified_auto_merge_allowed`

## Manual Verification Requirement
The repair report must tell the Steward how to verify locally:

1. Pull the repair.
2. Run `PYTHONPATH=src python -m pytest tests/test_steward_command_center.py`.
3. Run `PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0213 --json`.
4. Start the Office in served mode.
5. Send Alfred a chat message such as: `Alfred, what should I look at first?`
6. Confirm Alfred responds with useful guidance.
7. Confirm Alfred does not claim he executed an action.
8. Confirm the conversation history is persisted.

## Acceptance Criteria
WP-0216 is complete when:

1. The failing Alfred chat test is repaired.
2. `tests/test_steward_command_center.py` passes fully.
3. Alfred chat endpoint still persists history.
4. Alfred chat endpoint still returns resident surface metadata.
5. Alfred chat endpoint still reports `authority.action_executed` as false when no action was executed.
6. Alfred does not claim execution or authority he does not have.
7. WP-0213 validation is rerun and remains production-ready.
8. WP-0216 repair report exists.
9. WP-0216 completion receipt exists.

## Merge Class
Class B if active implementation or test files are changed.

Class A only if the repair is limited to report/receipt metadata and no active code or tests are changed.
