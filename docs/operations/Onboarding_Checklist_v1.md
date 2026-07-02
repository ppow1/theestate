# Onboarding Checklist v1

Status: Implemented
Classification: Estate Internal
Owner: Steward / HR until Helen is onboarded

## Purpose

This checklist records the current minimum steps for bringing an Estate participant online.

## Core Principle

Identity is separate from office assignment.

A numeric ID identifies the participant. A title records the current or historical role. A mailbox provides institutional communication. Status records current operating state.

## Checklist

1. Steward authorization exists.
2. A plain numeric ID is assigned.
3. The ID is recorded in `data/registry/personnel.json`.
4. A mailbox ID is assigned.
5. For people and personas, mailbox ID normally matches the numeric ID.
6. Mailbox directories exist under `collaboration/mailboxes/<mailbox_id>/` with `inbox/`, `sent/`, and `archive/`.
7. Current title is recorded.
8. Current office or assignment is recorded.
9. Status is recorded.
10. Required onboarding materials are identified.
11. Required historical memoranda are identified when relevant.
12. A mailbox message or onboarding packet exists when onboarding is not yet complete.
13. The mailbox index can be regenerated so the mailbox becomes discoverable.

## Current Status Values

- `reserved` — Reserved identity; no operating behavior assigned.
- `active` — Active participant.
- `historical` — Historical occupant retained for institutional memory.
- `advisory` — Historical occupant retained for advisory review.
- `onboarding` — Identity issued, onboarding not yet complete.

## Current Seed Assignments

| ID | Mailbox | Identity | Status |
|---:|---:|---|---|
| 0 | 0 | Reserved / Special Institutional Identity | reserved |
| 1 | 1 | Steward / Founder | active |
| 2 | 2 | Chief Architect #1 | historical |
| 3 | 3 | Chief Architect #2 | advisory |
| 4 | 4 | Chief Architect #3 | active |
| 5 | 5 | Chief Architect #4 | onboarding |

## Current Review

- ID 0: reserved identity recorded; no mailbox activation needed.
- ID 1: active Steward identity; mailbox `0001` required.
- ID 2: historical Chief Architect #1; mailbox `0002` and final memorandum required.
- ID 3: advisory Chief Architect #2; mailbox `0003` and final memorandum required.
- ID 4: active Chief Architect #3; mailbox `0004` and CA1/CA2 memoranda required.
- ID 5: Chief Architect #4 onboarding; mailbox `0005`, onboarding packet, and CA1/CA2 memoranda required.

## Procedure

1. Confirm Steward authorization.
2. Assign the next numeric ID.
3. Add the registry entry.
4. Create mailbox directories.
5. Send an onboarding packet to the mailbox.
6. Regenerate `collaboration/mailboxes/index.json`.
7. Verify mailbox discovery.
8. Record completion or remaining gaps.
9. Change status from `onboarding` to `active` only after onboarding is complete.

## Future HR Ownership

When Helen / Human Resources is brought online, this checklist should transfer to HR ownership.
