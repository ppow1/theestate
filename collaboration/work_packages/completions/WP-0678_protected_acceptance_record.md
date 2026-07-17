# WP-0678 Protected Acceptance Record

Status: Accepted and operationally authorized  
Work package: WP-0678 — Campaign-Level Codex Execution Capability  
Acceptance date: 2026-07-16  
Repository: `ppow1/theestate`  
Merged implementation PR: #414  
Merged implementation commit: `d5f1f5f4d2cd0f3d8ad983b06e90487c1fcd3a9d`

## Chief Architect decision

The Chief Architect accepts WP-0678 as satisfying its required campaign-level Codex execution capability.

Acceptance is based on the implemented and merged capability, the required architecture documentation, the completion receipt, and the recorded validation evidence demonstrating:

- one governed campaign manifest;
- one non-protected campaign branch;
- one bounded commit per atomic work package;
- dependency-aware sequential and explicitly approved parallel execution;
- mandatory internal review gates;
- durable restart, retry, reconciliation, and append-only transition evidence;
- fail-closed handling for branch mismatch, missing approval, invalid topology, gate bypass, partial failure, and duplicate commit recording;
- presentation of one campaign pull request without automatic merge or institutional acceptance;
- no duplicate scheduler, Dispatch queue, validator, mailbox, readiness system, repository-evidence system, or acceptance authority.

The Chief Architect authorizes operational use of this capability for approved campaigns that independently satisfy their own launch prerequisites and authority records.

## Steward decision

The Steward expressly accepts WP-0678 and authorizes the Estate to use the campaign-level Codex execution capability for approved Estate campaigns.

This authorization permits Codex to execute approved atomic work packages through the bounded campaign controller, on the declared campaign branch, in dependency order, with only explicitly approved parallel groups, durable checkpoints, review-gate pauses, and one bounded commit per work package.

This acceptance does not delegate or automate protected authority. Codex and the campaign controller remain execution mechanisms only. They may not independently approve campaigns, alter constitutional authority, merge, deploy, spend, staff, disclose protected information, accept work packages, or declare institutional acceptance.

## Accepted evidence

- `collaboration/work_packages/pending/WP-0678_Campaign_Level_Codex_Execution_Capability.md`
- `collaboration/work_packages/completions/WP-0678_completion_receipt.md`
- `src/estate/core/codex_campaign_execution.py`
- `tests/test_codex_campaign_execution.py`
- `docs/architecture/codex_campaign_execution_capability.md`
- Pull request #414
- Merge commit `d5f1f5f4d2cd0f3d8ad983b06e90487c1fcd3a9d`

## Validation basis

The merged pull request records successful execution of:

- `python -m pytest -q tests/test_codex_campaign_execution.py`
- `python -m pytest -q tests/test_codex_campaign_execution.py tests/test_operational_campaign_runtime.py tests/test_codex_bridge.py`
- `python -m compileall -q src/estate/core/codex_campaign_execution.py`

## Effective decision

WP-0678 is accepted, closed as a work package, and operationally authorized for use as a prerequisite capability by CAMPAIGN-0681 and later approved campaigns.

This record satisfies the previously missing protected acceptance evidence for WP-0678. It does not by itself launch CAMPAIGN-0681 or satisfy that campaign's separate Chief Architect launch approval, Steward protected-action authorization, base-commit verification, manifest activation, or readiness requirements.
