# WP-4062 — Stateful Chat Runner and Work-Package Queue

Status: Pending
Execution Mode: PARALLEL_INDEPENDENT
Owner: Office of Character Architecture / Operational Tooling Integration
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Depends On

- Existing Estate work-package lifecycle and completion-receipt conventions
- Existing ChatGPT worker continuity and Reflection Point process

## Objective

Implement a stateful Chat Runner that executes bounded ChatGPT work queues with explicit progress, recovery, timeout, verification, and human-control semantics, replacing blind timed `Go` injection and reducing Steward babysitting.

## Required Work

1. Define a bounded job manifest containing worker/chat target, ordered prompts, expected artifacts, timeout, retry policy, stop conditions, and completion checks.
2. Track queued, submitted, acknowledged, running, awaiting-user-action, completed, failed, timed-out, cancelled, and recovered states.
3. Require evidence of turn completion before submitting the next prompt; keyboard injection alone is not completion evidence.
4. Detect browser/session unresponsiveness, lost turns, authorization prompts, context degradation, and repeated refresh requirements.
5. Support pause, resume, cancel, bounded retry, checkpoint, and manual takeover without duplicating submissions.
6. Persist progress markers and receipts so a restart can recover safely.
7. Integrate with work-package dispatch manifests and exact Codex/ChatGPT command formats without inventing execution state.
8. Protect credentials, private content, and browser/session boundaries; do not scrape or store hidden reasoning.
9. Produce a visible operator dashboard or machine-readable status surface.
10. Keep old implementations read-only after renewal unless explicitly selected as fallback.

## Acceptance Tests

1. A multi-prompt bounded queue advances only after verifiable completion signals.
2. Browser unresponsiveness pauses or recovers without duplicate prompt submission.
3. Restart resumes from the last durable checkpoint.
4. Authorization or user-decision states stop safely and surface the required action.
5. Cancellation prevents later queued prompts from firing.
6. A failed artifact verification blocks dependent work.
7. Runner state distinguishes submitted, completed, committed, implemented, validated, and accepted.
8. No hidden reasoning, credentials, or unrelated private transcripts are persisted.
9. The Steward can inspect and override every active job.

## Deliverables

- job-manifest and state schemas;
- durable queue and checkpoint engine;
- completion-signal and artifact-verification adapters;
- pause/resume/cancel/recovery controls;
- operator status surface;
- tests, threat model, documentation, and completion receipt.

## Constraints

- Do not create an autonomous institutional authority.
- Do not claim background execution where no runner process exists.
- Do not use blind coordinate automation as the sole control mechanism.
- Do not bypass ChatGPT, Codex, repository, privacy, or work-package governance.
- Do not allow unbounded prompt loops.

## Completion Standard

WP-4062 is complete only when the Estate can run bounded ChatGPT work queues with durable state, verifiable progression, safe recovery, explicit human control, artifact-aware dependency blocking, and honest lifecycle reporting; browser failure no longer causes silent duplicate or lost work; and the runner reduces coordination load without becoming a new authority.