# Operations Board Client v1

Status: Operational Client
Owner: Alfred / Chief of Staff
Classification: Estate Internal
Introduced By: EC-000086

## Purpose

The Operations Board is the first operational client of the Estate Collaboration Layer v1.

It exists to convert collaboration traffic into lightweight operational visibility.

The board does not replace the Communication Bus, work packages, promotion records, GitHub Issues, or local runtime state.

## Client Boundary

The Collaboration Layer owns:

- Message envelopes.
- Work package lifecycle.
- Claim state.
- Review state.
- Promotion records.
- Transport routing.

The Operations Board owns:

- Today's operational commitments.
- Current multi-day efforts.
- Deferred institutional ideas.
- Strategic roadmap visibility.
- Review cadence.

## Data Flow

1. Work enters the Collaboration Layer through a canonical message envelope or work package.
2. A worker claims and performs bounded work.
3. Review-ready operational state is summarized into the Operations Board.
4. Deferred ideas are recorded in the Parking Lot instead of becoming accidental active work.
5. Completed work remains traceable through Git history, completion notes, and promotion records where applicable.

## Board Paths

- operations/boards/daily_board.md
- operations/boards/active_work.md
- operations/boards/parking_lot.md
- operations/boards/roadmap.md
- operations/boards/review_cadence.md

## Transport Rule

GitHub may hold the approved Estate Internal board files.

Local-only artifacts remain local until classified and approved for promotion.

## Success Test

The Steward should be able to open the Operations Board and answer in under one minute:

- What is the Estate doing today?
- What is waiting?
- What is blocked?
- What ideas have been deferred?
- What should happen next?
