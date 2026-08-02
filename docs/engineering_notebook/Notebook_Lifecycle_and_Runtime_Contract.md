# Notebook Lifecycle and Runtime Contract

1. Create from an authorized objective and source references.
2. Ground against current repository and runtime evidence.
3. Activate exactly one bounded stage.
4. Require pre-action acknowledgment of objective, stage, workspace, writes,
   blocker, validation, and prohibitions.
5. Execute only bounded tools.
6. Run validation and record actual results.
7. Accept or reject a worker update proposal.
8. Atomically write a revisioned verified state and append a receipt.
9. Compact context into safe facts and explicit omissions.
10. Create a handoff record and terminate the session.
11. Build a fresh packet and require acknowledgment before resume.
12. Mark completed only after final validation; archive with evidence and a
    recoverable digest chain.

The runtime functions in `estate.core.engineering_notebook` implement this
minimum contract. No new orchestration loop is introduced.

## Fail-closed transitions

Stale/conflicted state, missing authority, unsafe references, unsupported claims,
scope changes, failed required validation, retry exhaustion, secret-like text,
replay/out-of-order updates, partial-write failure, or an acknowledgment
mismatch stop tool execution. A blocked notebook may be updated only with
observed blocker evidence or an authoritative resolution. Worker proposals
cannot refresh freshness, alter authority, or grant institutional acceptance.
