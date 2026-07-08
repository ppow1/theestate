# Execution Provider Operational Visibility and Human Oversight Requirements

Status: Draft Architectural Requirement
Owner: Chief Architect / Steward
Classification: Estate Internal
Created: 2026-07-08

## Applies To

This requirement applies to:

- `WP-CODEX-CLI-001`
- `WP-CHATGPT-CLI-001`
- Future execution provider investigations
- Future orchestrator design
- Office of the Steward

## Background

The Estate is moving toward asynchronous execution across multiple execution providers.

Reducing manual copy/paste is desirable.

Reducing Steward awareness is not.

The Steward must remain able to understand overall Estate activity at a glance without inspecting terminal windows or reading logs.

Operational visibility is therefore a first-class architectural requirement rather than a user-interface enhancement.

## Requirement 1 - Visible Activity

Every significant worker shall expose operational status to the Office of the Steward.

Example states include:

- Planning
- Waiting
- Running
- Reviewing
- Blocked
- Awaiting Approval
- Validation
- Completed
- Failed

The Steward should not need to inspect terminals to determine current Estate activity.

## Requirement 2 - Activity Indicators

The Office of the Steward should eventually provide an operational dashboard showing, at minimum:

- Worker
- Current Assignment
- Current State
- Elapsed Time
- Estimated Completion
- Provider
- Budget Source
- Security Classification
- Validation Status

This view is intended to become the Estate's operational window into execution.

## Requirement 3 - Event Stream

Execution providers should emit structured events rather than requiring log scraping.

Example events include:

- Job Accepted
- Execution Started
- Checkpoint Reached
- Waiting for Approval
- Validation Started
- Validation Passed
- Validation Failed
- Commit Created
- Result Returned
- Execution Complete

These events should feed both audit history and the Office of the Steward.

## Requirement 4 - Human Situational Awareness

The Steward should be able to answer, within seconds:

- What is currently running?
- What completed recently?
- What is blocked?
- What requires my attention?
- Which workers are idle?
- Which execution providers are saturated?
- How much Codex capacity remains?
- How much local GPU capacity remains?

The Steward should be able to answer those questions without opening multiple terminals.

## Requirement 5 - Multiple Concurrent Workers

The Estate should assume that many workers may operate simultaneously.

Examples include:

- Chief Architects
- Character Development Engineers
- Codex workers
- Local Ollama workers
- Validation workers
- Documentation workers
- Alfred
- Helen
- Ingrid
- Future Operations staff

The architecture should support concurrent execution without assuming only a single active worker.

## Requirement 6 - Worker Provisioning

Worker creation should not be coupled to execution providers.

Instead:

- Helen provisions workers.
- The Operations Office assigns work.
- The Orchestrator schedules execution.
- Execution Providers perform work.

This separation should remain regardless of future provider additions.

## Requirement 7 - Planning Scalability

Planning should assume that dozens of work packages may exist simultaneously.

The architecture should support:

- Prioritization
- Dependencies
- Budgeting
- Provider selection
- Security review
- Scheduling
- Deferred execution
- Cancellation
- Promotion

without requiring manual tracking by the Steward.

## Requirement 8 - Architectural Principle

The Estate should optimize for reducing the Steward's cognitive load rather than merely reducing keystrokes.

Automation is successful only when it increases institutional awareness while decreasing manual coordination effort.

The Office of the Steward should evolve into an operational command center rather than a static dashboard.

It should present live activity, execution status, worker health, resource utilization, and actionable decisions in a way that allows the Steward to understand the state of the Estate at a glance.

## Architectural Implication

Execution provider work must not stop at successful command invocation.

A provider is not mature until it can:

1. Accept governed work.
2. Emit structured lifecycle events.
3. Report worker and provider state.
4. Surface blocking decisions to the Steward.
5. Feed audit and validation artifacts.
6. Preserve human situational awareness during asynchronous execution.

This document should be treated as a requirement input for Codex CLI, ChatGPT CLI, local Ollama workers, future orchestrator design, worker provisioning, and the Office of the Steward command surface.
