# Operations Board Implementation Recommendation

Status: Active
Owner: Worker #1
Classification: Estate Internal
Introduced By: EC-000086
Date: 2026-06-30

## Recommendation

Use a GitHub-first and local-first hybrid implementation.

GitHub stores approved Estate Internal board files.

The local filesystem remains the safe place for local-only runtime state, pre-review outputs, generated artifacts, prompts, and private work products.

## GitHub-First Role

GitHub is appropriate for:

- Operations Board markdown files.
- Shared institutional visibility.
- Lightweight review.
- Versioned operational history.
- Pulling the current board state onto local Estate machines.

GitHub is not the Communication Bus itself.

GitHub is the first shared transport adapter.

## Local-First Role

The local filesystem remains appropriate for:

- Local worker execution.
- Local 4090 output.
- Runtime state.
- Private artifacts.
- Draft work before review.
- Dead-letter handling.

Nothing local-only should be promoted to GitHub without classification and approval.

## Communication Protocol Integration

The Operations Board is the first operational client of the Estate Collaboration Protocol v1.

Integration pattern:

1. Work enters through a message envelope or work package.
2. Active operational commitments are summarized on the Daily Task Board.
3. Multi-day efforts are summarized on the Active Work Board.
4. Deferred ideas are stored in the Parking Lot.
5. Long-horizon direction is summarized on the Strategic Roadmap.
6. Completed or review-ready work remains traceable through collaboration messages, work packages, promotion records, and Git history.

## Non-Duplication Rule

Do not duplicate GitHub Issues.

The Operations Board should only track the operational state the Steward needs to understand quickly.

Implementation details may remain in work packages, commits, local files, or future issues.

## Automation Guidance

Do not automate the board immediately.

First allow manual updates to reveal stable patterns.

Apply the Rule of Three: if the same update pattern repeats at least three times and is cognitively expensive or error-prone, evaluate automation.

Initial automation candidates:

- Alfred daily briefing from board files.
- Audit validation for required board files.
- Discovery observation of board freshness.
- Parking Lot review reminders.
