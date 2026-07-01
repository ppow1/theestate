# ADR-0001: Estate Organizational Architecture

## Status
Accepted

## Context

The Estate is an organizational operating system rather than a conversational chatbot.

Its purpose is to allow executive-level delegation of missions while maintaining governance, persistent state, delegated authority, auditability, and continuous execution.

## Executive Authority

The user operates as Executive.

The Executive delegates missions rather than individual tasks.

A mission defines:

- Objectives
- Constraints
- Authority
- Approval Gates
- Deliverables
- Escalation Rules

The Executive is interrupted only when delegated authority has been exceeded.

## Organizational Hierarchy

Executive

- Division Directors
    - Program Directors
        - Project Managers
            - Team Leads
                - Workers

Division Directors are persistent.

Program Directors belong to departments.

Project Managers are created for individual projects.

Workers may be AI agents, tools, humans, or services.

## Mission-Based Execution

Projects begin with a Mission Order.

Mission Orders become the governing document for execution.

After approval the Project Manager may:

- Build work breakdown structures
- Assign workers
- Request revisions
- Coordinate specialists
- Integrate findings
- Produce reports

without requiring executive approval for every intermediate step.

## Delegated Authority

Managers may approve work inside delegated authority.

Managers may not:

- Spend money beyond authority
- Change project scope
- Commit external resources
- Ignore safety or legal requirements

Those actions require escalation.

## Persistent State

The database is the source of truth.

Conversation is NOT state.

LLM memory is NOT state.

Character cards are NOT state.

Persistent state includes:

- Estate
- Divisions
- Programs
- Projects
- Tasks
- Resources
- Agent Memory
- Approvals
- Events
- Artifacts
- Knowledge
- Dependencies
- Blockers

The Estate should always know:

- What is running
- What is blocked
- What is waiting
- Who owns it
- Current phase
- Critical path
- Next action

## Organizational Intelligence

Persistent State remembers.

LLMs reason.

The LLM never owns organizational state.

## Trigger Architecture

Agents sleep until activated.

Triggers include:

- Schedule
- Event
- State Change
- Resource Availability
- Dependency Completion
- Executive Request

Upon activation an agent:

1. Loads state
2. Collects facts
3. Consults specialists
4. Reasons
5. Produces structured output
6. Updates state
7. Emits events
8. Returns to idle

## Communication

Agent communication is structured.

Every inter-agent discussion has:

- Purpose
- Scope
- Maximum depth
- Transcript
- Audit trail
- Structured result

## State Driven Operation

Projects continue while the Executive is absent.

The Executive should be able to ask:

"Status Project 7"

and immediately receive:

- Phase
- Progress
- Blockers
- Waiting On
- Resource Usage
- Decisions Required
- Estimated Completion

without reconstructing chat history.

## Interfaces

Conversation is an interface.

Voice is an interface.

SillyTavern is an interface.

Dashboard is an interface.

CLI is an interface.

Mobile is an interface.

None of these interfaces ARE The Estate.

They are simply windows into it.

## Estate Core

The Estate consists of:

Persistent State Layer
Reasoning Layer
Execution Layer

Persistent State remembers.

Reasoning thinks.

Execution coordinates.

## Consequences

Executive delegation becomes practical.

Projects continue without constant supervision.

Managers coordinate workers.

State survives model replacement.

Front ends become interchangeable.

## Risks

- State synchronization
- Scheduling
- Worker lifecycle
- GPU scheduling
- Authority enforcement
- Auditability
- Memory consistency

## Future Work

- PostgreSQL implementation
- Event Bus
- Trigger Engine
- Memory Architecture
- Approval Engine
- Resource Scheduler
- Mission Order Schema
- Estate API
- Dashboard
- Voice Integration

## Summary

The Estate is an organizational operating system built around:

- Persistent State
- Delegated Authority
- Structured Execution
- Hierarchical Management
- Event-Driven Activation
- State-Driven Project Tracking
- Interchangeable AI Reasoning Engines

The Estate is not a chatbot.

The Estate is not SillyTavern.

The Estate is not TextGen.

Those are interfaces and infrastructure.

The Estate itself is the organization.
