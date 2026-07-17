# WP-0696 — Alfred Communication and Mailbox Routing Integration

Status: Pending  
Priority: High  
Owner: Chief Architect  
Execution lane: Codex  
Primary campaign: CAMPAIGN-0681 — Estate Operationalization  
Depends on: WP-0690, WP-0693  
Integration gate: G3 — Office Integration

## Objective

Integrate operational coordination with Alfred's existing communication and mailbox-routing responsibilities so blockers, requests, acknowledgements, escalations, and decisions reach the correct office durably without making Alfred the execution authority or creating a competing messaging system.

## Required Outcomes

The implementation shall:

1. map classified operational needs to the proper canonical destination;
2. create or route repository-backed messages using existing schemas and mailbox indexes;
3. preserve source, destination, campaign, package, priority, classification, evidence, and acknowledgement requirements;
4. distinguish notification, coordination request, staffing request, execution request, blocker escalation, acceptance request, and protected decision request;
5. prevent mailbox state from being treated as authoritative work status;
6. support acknowledgement and response correlation where canonically available;
7. detect unresolved, misrouted, duplicated, stale, or conflicting messages;
8. fail closed rather than guessing mailbox IDs, personnel IDs, office authority, or destination.

## Scope

- routing rules and destination resolution;
- repository-backed message adapter;
- mailbox discovery and correlation;
- acknowledgement and response linkage;
- duplicate and stale-message handling;
- tests for routing, authority, and status boundaries.

## Non-Goals

This package shall not:

- create a new messaging, notification, mailbox, or queue system;
- make Alfred the owner of campaign execution, staffing, architecture, acceptance, merge, or deployment;
- treat sending, receiving, or acknowledging a message as completion of the underlying work;
- infer IDs or authority from titles alone;
- overwrite authoritative campaign, package, staffing, validation, or acceptance state.

## Acceptance Criteria

WP-0696 is complete when representative operational events can be routed through canonical repository-backed messages to the correct offices, acknowledgements and responses can be correlated, and tests prove that communication routing does not become execution or acceptance authority.

## Required Evidence

- implemented routing and message integration;
- representative message fixtures for each supported message type;
- destination-resolution and fail-closed tests;
- duplicate, stale, and misrouting tests;
- completion receipt suitable for CAMPAIGN-0681 G3 review.
