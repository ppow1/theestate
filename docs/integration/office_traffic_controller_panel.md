# Office Traffic Controller Panel

Status: Implemented  
Classification: Estate Internal

## Purpose

The Office Traffic Controller panel makes the Traffic Controller / Operations Manager layer visible in the Office of the Steward. It summarizes current operations-control posture, recommendations, blocked movement, assignment gaps, provider capacity warnings, and recorded operations decisions without requiring the Steward to open raw runtime files.

The panel is a display and governed decision surface only. It does not run providers, schedule work, or implement Operations Manager core logic.

## Runtime Artifact Inputs

The panel reads these operations-control artifacts when present:

- `runtime/operations/control/status/latest.json`
- `runtime/operations/control/status/summary.json`
- `runtime/operations/control/status/summary.md`
- `runtime/operations/control/reviews/`
- `runtime/operations/control/decisions/`

When artifacts are absent, the Office shows an honest empty state with the expected paths and does not report a fake healthy posture.

## Panel Sections

The Office surface displays:

- operational posture,
- timestamp and freshness of the latest review,
- source artifacts inspected,
- items requiring Steward attention,
- boundary review requirements,
- blocked intake, assignment, and provider counts,
- assignment gaps,
- provider capacity warnings,
- recommended next actions,
- latest operations decisions,
- malformed artifact errors.

## Supported Controls

The panel exposes only controls backed by the local Office action surface and `OperationsControlRuntime.record_decision`:

- `assign`
- `reprioritize`
- `hold`
- `release`
- `defer`
- `cancel`
- `escalate`
- `request_boundary_review`
- `request_revision`
- `request_validation`

A control writes an operations decision artifact under `runtime/operations/control/decisions/`, refreshes operations-control summary artifacts, and may emit a compatible operational event through existing runtime helpers. Controls do not execute providers.

## Unavailable-Control Behavior

Unsupported recommendation actions are rendered as unavailable with a reason. The Office does not expose fake buttons and does not report fake success for actions without a safe local handler.

## Stale Behavior

The panel marks active operations posture stale when the latest review timestamp is older than 15 minutes. It also reports a 24-hour historical freshness state for summary context. If a timestamp cannot be parsed, freshness is marked uncertain instead of crashing the Office.

## Redaction Behavior

Public and Estate Internal summaries display normally. Restricted, Steward Only, and Local Only summaries are redacted by default unless metadata or the action marks `summary_safe: true`. Structural fields such as state, target type, target ID, classification, priority, and requirements remain visible unless the source artifact omits them.

The panel does not preview raw prompts, secrets, credentials, private source material, or raw local-only content.

## Relationship to WP-0610

WP-0610 provides the operations-control review, summary, and decision artifacts. This panel consumes those artifacts and invokes the existing decision runtime where a real governed Office control is available.

## Relationship to Office Activity and Intake Decision Panels

The panel is integrated into the existing Operational Activity workspace. The Office activity panel continues to show runtime activity and Orchestrator intake decisions, while the Traffic Controller panel adds operations-control posture and recommendations above that activity surface.
