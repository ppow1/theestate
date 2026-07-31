# ENG-OPS-001 Implementation Closure

Starting main: `c3d5f3990e86123d5623462c03e5c39be3d50aec`  
Campaign branch: `engineering/complete-governed-engineering-first-live-task`  
Final pushed HEAD before this report-only finalization: `6c642be1`  
Commits: `00db8ff2`, `272151b7`, `c9ef01c5`, `6c642be1`

## Scope and production path

The campaign completed the existing governed path:

`Grace → Helen → PTM → Engineering commission → Engineering authorization →
Operations decision → Dispatch queue → final adapter handoff → registered
provider adapter → Engineering validation/reconciliation → Grace terminal
receipt`.

The source-of-truth matrix is [ENG-OPS-001_Source_of_Truth_Matrix_20260731.md](ENG-OPS-001_Source_of_Truth_Matrix_20260731.md).

## Defects corrected

The merged foundation dropped Qwen-required execution metadata between
`authorize_dispatch()` and the adapter. The correction adds a closed,
versioned Qwen execution extension derived from canonical Helen evidence,
provider configuration, and Grace-bound exact outputs. It propagates through
the commission, Engineering authorization, Operations decision, Dispatch,
and provider-neutral adapter request.

The final handoff now revalidates the extension, canonical Helen evidence,
provider configuration, model/adapter identity, exact artifact and receipt
paths, and fresh evidence timestamps. Reconciliation result-evidence fields
were also added to the closed Dispatch metadata schema so completed queue
records remain schema-valid.

Arbitrary caller metadata cannot override Grace authority. The registered
adapter remains the only production provider execution surface; the injected
adapter seam remains explicitly test-only.

## Contracts and schemas

- `estate.qwen-local-text.execution-extension.v1` — new closed Qwen extension.
- `estate.engineering.commission-execution-authority.v1` — binds the extension.
- `estate.engineering.authorization.v1` — requires and validates the extension
  for the technical authorization.
- `estate.operations-control.decision.v1` — carries the closed extension for
  technical execution.
- `estate.dispatch.execution-metadata.v1` — carries the extension and declares
  post-reconciliation result evidence.
- `estate.execution-provider-adapter.request.v1` — carries the extension as a
  provider-neutral request field.

The canonical registry contains seven unique authority schemas. Draft 2020-12
validation and `FormatChecker` passed, including all final live authority
records.

## Automated validation

- Final changed-scope matrix: **205 passed**.
- Python compilation: passed.
- Tracked JSON parsing: 1,460 files inspected; two known malformed fixtures
  remain unchanged and outside this execution path.
- Schema registry uniqueness and `$ref` resolution: passed.
- `git diff --check`: passed.
- Known Windows path-separator failure reproduced on both starting commit and
  campaign head in `tests/test_execution_result_reconciliation_runtime.py`;
  it is unrelated and unchanged.

## Preservation

- No source changes were made during the live run; implementation changes are
  limited to this campaign branch.
- Qwen source and configuration remain configured for `qwen3:8b`.
- No model was downloaded or changed.
- PR #503 and its failed-preflight report were not rewritten.
- Historical Qwen evidence was not reused or modified.
- Institutional acceptance remains `not_granted`.
- All 16 stashes remain preserved.
- `A:\theestate` was not modified.

## Status

The first live task succeeded; complete lifecycle evidence is in
[Qwen_First_Live_Task_6561985c223d405c8c9b1d41562af5fb_20260731.md](../validation/Qwen_First_Live_Task_6561985c223d405c8c9b1d41562af5fb_20260731.md).

The next Steward action is blocking review of the campaign PR; merge remains
outside this work package execution.
