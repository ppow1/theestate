# PL-0050 — Grace OpenWebUI Resident Selection Guard

Status: Captured
Priority: High
Category: Grace / Open WebUI / Acceptance Engineering
Originator: Pat / Steward
Date Captured: 2026-08-12
Target Milestone: Grace/Open WebUI acceptance hardening

## Idea

Prevent Grace acceptance tests from silently running against the wrong resident in Open WebUI.

During bounded-local intent acceptance, the real UI bounded-local request succeeded through Grace end to end. A subsequent parallelism request was not a valid Grace test because the attached Open WebUI session was on Alfred. Alfred returned coordination prose rather than executing the requested tasks. No GPU work started and no lane remained active, but the acceptance campaign ended in `GRACE_OPENWEBUI_PARTIAL` because resident selection invalidated that test.

The acceptance/operator path should explicitly prove that the intended resident is selected before submitting a resident-specific test, and should fail closed or automatically correct selection when the visible/session resident does not match the test target.

## Evidence From Current Acceptance

Bounded-local intent fix:

- Branch: `fix/grace-ui-bounded-intent`
- Commit: `f52c3a3feb794021a68614130ca539416e294f31`
- Draft PR: #530 — `Recognize natural bounded local text requests in Grace`
- Integration deployment source: `53df33210b525238f03c1110e8f8a5f54a59c8f2`
- Deployment result: successful; one file changed; rollback available
- Resident Gateway restarted through governed lifecycle and reported healthy
- Automated tests: 17 passed; compilation and `git diff --check` passed

Successful real UI bounded-local path:

- Objective: `grace-obj-deede097cdb1`
- Action: `grace-act-97f67242a190`
- PTM: `res_01KZVEDNXPYCHG54TEARDR8WAW`
- Helen: `heldet-35dbe0edb534`
- Commission: `engcom-62d400ca143d`
- Authorization: `engauth-0963c5037f38`
- Dispatch: `dispatch-7542620b0c3d`
- Adapter: `adapter-dispatch-7542620b0c3d`
- Grace receipt: `gracereceipt-8f3cf1ea4b59`
- Actual GPU UUID: `GPU-46f3fd00-5454-4536-4196-5d8b727e14f2`
- Placement matched: true
- Governed cleanup receipt: `gpu-cleanup-c4dd7764e7974e369ad4fbd5ab53c146`

Invalid parallelism test:

- Attached Open WebUI session selected Alfred instead of Grace.
- Alfred returned coordination prose instead of executing the Grace task.
- No GPU work started.
- No lane remained active.
- No retry was performed.
- Final campaign status: `GRACE_OPENWEBUI_PARTIAL`.

## Desired Behavior

Before a resident-specific Open WebUI acceptance scenario is submitted, the operator/harness should establish the intended resident identity using a deterministic UI/session signal rather than assuming the previous selection persisted.

Candidate behavior when promoted:

1. Read the currently selected resident/model from the Open WebUI session.
2. Compare it to the scenario's declared target resident.
3. If mismatched, either select the intended resident deterministically or stop before submission with a clear `RESIDENT_SELECTION_MISMATCH`-class result.
4. Re-read the selected resident after any selection action and prove the expected resident is active.
5. Record resident identity in the scenario evidence package alongside prompt, response, screenshots/traces, and runtime receipts.
6. Treat a response from the wrong resident as an invalid test rather than a functional failure of the intended resident.
7. Preserve fail-closed behavior if resident identity cannot be established reliably.

## Why It Is Parked

The immediate bounded-local intent defect has been implemented, deployed to integration, and successfully exercised through Grace. The remaining partial status is an acceptance/operator targeting issue, not evidence that the bounded-local fix failed.

Capture the lesson without interrupting the current acceptance campaign or broadening PR #530 beyond its intent-recognition scope.

## Promotion Condition

Promote when Grace/Open WebUI acceptance hardening resumes, or when the generalized browser operator work is promoted and resident-aware target selection becomes part of its Open WebUI adapter.

## Explicit Non-Action

Do not fold this resident-selection guard into PR #530 unless its existing contract explicitly owns Open WebUI resident selection.

Do not reinterpret Alfred's coordination response as a Grace execution failure.

Do not rerun GPU work merely to compensate for an unverified resident selection.

Do not make resident selection implicit state; acceptance evidence should state which resident actually received the request.

## Related Evidence

- Draft PR #530: bounded-local Grace intent recognition.
- PL-0041 — Generalized Browser Operator Automation.
- Current Grace/Open WebUI acceptance evidence and runtime receipts listed above.
- Canonical Parking Lot process: `AI_COMMUNICATION_HINTS.md`.
