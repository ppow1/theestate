# Audit Result Schema v1

Status: Version 1 Schema
Classification: Estate Internal

## Purpose

Defines the JSON result written by `workers/audit/run_audit_worker_once.ps1` after processing one audit request.

## Required Fields

- `request_id`
- `status`: `pass`, `fail`, or `error`
- `repository`
- `branch`
- `local_commit`
- `work_package_id`
- `audit_started_at`
- `audit_finished_at`
- `command_run`
- `exit_code`
- `summary`
- `full_audit_output`
- `stderr`
- `follow_up_required`
- `history_drift_detected`
- `classification`

## Notes

The local Estate audit remains authoritative.

GitHub is only a transport for request and result state after an authorized sync.

The audit worker must not repair history drift directly. History drift is reported and then handled through the History Queue / Drain workflow.
