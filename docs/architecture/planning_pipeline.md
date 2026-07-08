# Estate Planning Pipeline

Status: Architectural Design  
Work Package: WP-CHATGPT-CLI-001  
Author: Chief Architect #6  
Classification: Estate Internal

## Purpose

This document defines the canonical planning pipeline for ChatGPT-assisted planning and future Orchestrator-driven execution.

The goal is to preserve the Estate distinction between planning, implementation, validation, and institutionalization while reducing manual copy/paste and preserving Steward awareness.

## Architectural Position

The Estate should adopt a planning pipeline that separates:

- discussion,
- planning,
- architecture,
- work package authorship,
- execution scheduling,
- provider execution,
- validation,
- promotion,
- institutional recordkeeping.

ChatGPT may participate heavily in the planning stages.
Codex, local LLMs, Python, PowerShell, GitHub Actions, and future services may execute.
Alfred and the Orchestrator should route.
Helen provisions workers.
Ingrid governs boundaries.
Audit and Validation provide evidence.
The Office of the Steward provides operational visibility.

## Recommended Pipeline

1. Discussion
2. Planning
3. Architecture
4. Work Package
5. Repository / Local Filesystem Persistence
6. Git Pull or Local Context Refresh
7. Orchestrator Intake
8. Worker Provisioning
9. Execution Provider Selection
10. Execution
11. Event Emission
12. Audit
13. Validation
14. Review
15. Promotion
16. Institutional Record
17. Discovery Refresh

## Stage Definitions

### 1. Discussion

The Steward and a planning participant clarify intent.

ChatGPT is often the best fit for this stage because it can handle high-context discussion, evolving requirements, and policy reasoning.

### 2. Planning

The planning participant translates intent into structured options, risks, and recommended direction.

Planning must not imply implementation.

### 3. Architecture

Chief Architect evaluates whether the work belongs in an existing subsystem, requires new capability, or should be parked.

### 4. Work Package

A bounded work package is written with mission, scope, do-not-touch boundaries, required reading, deliverables, acceptance criteria, and definition of done.

### 5. Repository / Local Filesystem Persistence

The work package is persisted where the Estate can find it.

GitHub may be used for shared state. Local filesystem may be used for local authoritative state.

### 6. Git Pull or Local Context Refresh

If repository state has changed, local workers refresh context.

The Estate should prefer direct local reads where CLI access exists.

### 7. Orchestrator Intake

The Orchestrator receives or observes the work package.

The Orchestrator should not invent authority. It schedules and routes work according to Estate policy.

### 8. Worker Provisioning

Helen provisions or assigns appropriate workers.

Worker creation is separate from execution provider selection.

### 9. Execution Provider Selection

The Orchestrator selects the execution provider based on:

- task type,
- worker role,
- privacy classification,
- budget source,
- required capabilities,
- provider availability,
- queue depth,
- validation needs,
- expected latency.

### 10. Execution

The selected provider performs the work.

Providers may include:

- ChatGPT,
- Codex CLI,
- local LLM,
- Python,
- PowerShell,
- GitHub Actions,
- future services.

### 11. Event Emission

Execution providers emit structured events.

This is mandatory architectural direction for future integration.

Examples:

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

Events should feed:

- Office of the Steward activity view,
- audit history,
- runtime status,
- future performance analysis.

### 12. Audit

Audit checks whether the change satisfies structural and runtime expectations.

Audit is not the same as validation.

### 13. Validation

Validation exercises the capability in its intended workflow and preserves evidence.

A completed implementation is not operationally validated until this stage succeeds.

### 14. Review

Review may involve Chief Architect, Alfred, Ingrid, Helen, Audit, Validation, or the Steward depending on scope and classification.

### 15. Promotion

Approved output is promoted into shared institutional space.

Privacy and Boundary Office controls classification, outbound approval, and promotion permission.

### 16. Institutional Record

Formal history is recorded in the appropriate institutional records, such as ledger and devlog, when required.

### 17. Discovery Refresh

Discovery observes the new state so future workers do not rely on stale assumptions.

## Operational Visibility Requirement

The pipeline must be visible.

The Office of the Steward should eventually show:

- worker,
- current assignment,
- current state,
- elapsed time,
- estimated completion,
- provider,
- budget source,
- security classification,
- validation status.

The Steward should be able to answer within seconds:

- What is running?
- What completed recently?
- What is blocked?
- What requires attention?
- Which workers are idle?
- Which providers are saturated?
- How much Codex capacity remains?
- How much local GPU capacity remains?

## State Model

Recommended activity states:

- Planning
- Waiting
- Running
- Reviewing
- Blocked
- Awaiting Approval
- Validation
- Completed
- Failed
- Cancelled
- Deferred

These states should be available to Office UI, audit, and future orchestrator routing.

## Human Oversight Principle

The Estate should optimize for reducing Steward cognitive load rather than merely reducing keystrokes.

Automation is successful only when it increases institutional awareness while decreasing manual coordination effort.

## Concurrency Principle

The Estate should assume many workers may operate simultaneously.

Examples:

- Chief Architects
- Character Development Engineers
- Codex workers
- local Ollama workers
- Validation workers
- Documentation workers
- Alfred
- Helen
- Ingrid
- future Operations staff

The architecture must not assume only one active worker.

## Responsibility Separation

Worker creation should not be coupled to execution providers.

- Helen provisions workers.
- Operations Office assigns work.
- Orchestrator schedules execution.
- Execution Providers perform work.
- Office of the Steward displays activity and decisions.
- Audit and Validation provide evidence.
- Ingrid governs boundaries.
- Steward remains final authority.

## Recommendation

This pipeline should become institutional policy after operational validation through at least one end-to-end ChatGPT-planned, Codex-implemented, locally audited, and Office-visible work package.
