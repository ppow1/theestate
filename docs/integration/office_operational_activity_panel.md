# Office Operational Activity Panel

Status: Implemented  
Work Package: WP-0602  
Classification: Estate Internal

## Purpose

The Office Operational Activity Panel is the first Steward-facing operational activity view for shared Estate worker/provider status. It lets the Steward see active, blocked, approval-gated, validation, completed, failed, cancelled, stale, missing, and malformed operational status without inspecting raw runtime files.

The panel is read-only. It does not write events, dispatch workers, approve work, or invent placeholder activity.

## Status Artifact Inputs

The loader reads the WP-0601 status artifacts from:

- `runtime/operations/status/latest.json`
- `runtime/operations/status/active.json`
- `runtime/operations/status/recent.json`
- `runtime/operations/status/summary.md`

`active.json` and `recent.json` are expected to contain lists of activity status objects. `latest.json` may contain a WP-0601 envelope with a `status` object. Missing files are reported as an honest empty state. Malformed JSON is reported per artifact while other readable files continue loading.

## Display Groups

The Office panel groups activity into:

1. Active
2. Awaiting Approval
3. Blocked / Attention Required
4. Validation
5. Recently Completed
6. Failed / Cancelled

Empty groups remain visible with a compact empty state so the Steward can distinguish “none found” from “panel failed.”

## Displayed Fields

For each activity, the panel displays structural operational fields when present:

- worker or worker role,
- provider or provider type,
- assignment, work package, request, or activity ID,
- current state,
- elapsed seconds,
- budget source,
- classification,
- validation status,
- whether Steward attention is required,
- safe message summary,
- artifact paths,
- freshness/stale state.

## Stale Behavior

The loader marks active/running-style status stale when `updated_at` is older than 15 minutes. Recent terminal activity is marked stale after 24 hours. If a timestamp cannot be parsed, the item is marked `uncertain` instead of crashing the Office.

## Classification Behavior

The panel applies safe display behavior for operational messages:

- `Public` and `Estate Internal` messages may display normally.
- `Restricted`, `Steward Only`, and `Local Only` messages are redacted by default.
- Sensitive messages may display only when `metadata.summary_safe` is `true`.
- Structural fields such as state, provider, classification, validation status, and attention requirement remain visible.

This is a UI safety rule, not a full Ingrid enforcement engine.

## Relationship to WP-0601

WP-0601 creates the operational event/status writer and runtime artifact contract. WP-0602 consumes those artifacts in the Office of the Steward. If the WP-0601 files are absent, this panel shows that absence honestly and lists expected paths.

## Test Command

Run the targeted tests with:

```bash
PYTHONPATH=src pytest -q tests/test_office_operational_activity.py
```

The repository audit remains:

```powershell
Clear-Host
cd A:\theestate
.\estate.bat audit
```
