# PL-0046 — Codex Bridge Visible Execution Observer

Status: Captured
Priority: Low
Category: Execution Visibility / Codex Bridge / Operator UX
Originator: Pat / Steward
Date Captured: 2026-08-11
Target Milestone: After current Codex Desk acceptance and Grace parallelism/notification integration

## Idea

Investigate whether Grace-dispatched Codex Bridge executions need an optional visible operator-observer mode in addition to the existing background `codex exec` execution path and Office/event/status visibility.

The current architectural boundary should remain unchanged unless evidence shows a real operator need:

- Grace owns workflow progression and routing.
- Codex Bridge owns bounded Codex execution and result capture.
- Background execution remains the default.
- The existing interactive C1/C2/C3 Codex TUI windows remain human-operated surfaces and should not become Grace's command channel.

## Question To Answer

When Grace dispatches a bounded Codex task to logical seat C1, C2, or C3, is Office/event/status telemetry sufficient, or is there meaningful value in allowing the Steward to turn on a visible observer stream in the corresponding Codex Desk top-row cell?

Potential modes to evaluate later:

- `silent` — normal background bridge execution, visible through Estate status/events only;
- `observe` — same bridge execution remains authoritative, but a seat-correlated read-only/live observer console shows request id, prompt/work-package identity, lifecycle events, execution output, validation, and completion;
- `interactive human` — existing C1/C2/C3 Codex TUI, owned by the Steward and not used as the automation transport.

## Guardrails

- Do not have Grace type into or take ownership of Patricia's existing interactive Codex TUI sessions.
- Do not replace the current Codex Bridge request/result/event contract.
- Do not create another execution subsystem.
- Do not make visible execution the default without evidence that it is operationally useful.
- Preserve logical seat identity and `CODEX_HOME` isolation.
- Any observer should mirror authoritative bridge execution rather than become a second execution channel.

## Evaluation Questions

When promoted, determine:

1. Does the Office of the Steward execution-status/event surface already provide enough visibility?
2. Is live terminal output useful during debugging, acceptance, or demonstrations?
3. Can a visible observer attach to the bridge stream without changing process ownership or execution semantics?
4. Should visibility be a per-request flag, an operator toggle, or remain entirely unnecessary?
5. Does adding an observer materially improve attention handling when a Codex task blocks or needs Steward input?

## Explicit Non-Action

This item is parked.

Do not interrupt current work to implement it.

Immediate priorities remain:

1. physically validate the CODEX DESK Stream Deck multi-press / long-press startup-shutdown contract;
2. wire a real Codex task into the existing Estate attention/notification path;
3. return to Grace parallelism after those acceptance points are proven.
