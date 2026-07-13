# WP-0547 — Provider Benchmark Cross-Run Evidence Import

Status: Pending implementation
Officeholder: Chief Architect #5
Work-package range: WP-0500 through WP-0599
Repository: ppow1/theestate
Depends on: WP-0545, WP-0546

## Purpose

Add one bounded capability to the existing Engineering Provider Benchmark Harness: import an already completed, immutable, fair-comparison-eligible executor result from one benchmark run into a different shared comparison run without modifying, deleting, re-executing, or overwriting the source evidence.

This package exists only to complete Benchmark 001's immediate three-way road-sign comparison among Codex, local Ollama, and the Chief Architect reference.

Do not broaden this package into a provider qualification suite, benchmark campaign, scheduler, registry, execution authority, or evidence redesign.

## Verified Current State

The following fair Benchmark 001 results already exist under the same canonical packet SHA-256:

Canonical packet SHA-256:
`1c36bf618283b7d7481166e002a90f3c4be21b82cdb2bdda623c5c3c537a03a8`

Local Ollama source run:
`20260713T170302Z-883587d1`

Local executor result:
- provider: Ollama
- model: qwen2.5-coder:7b
- canonical-packet eligible: true
- validation status: failed
- generation wall-clock seconds: 23.810738
- prompt tokens: 1566
- output tokens: 899
- total tokens: 2465
- generation attempts: 1
- repair attempts: 0

Codex shared comparison run:
`20260713T170839Z-2f4d2cae`

Codex executor result:
- provider: Codex
- canonical-packet eligible: true
- validation status: passed
- visible unittest command passed all three test cases
- token metrics unavailable

The current comparison command only compares executor directories within one run ID. Therefore the validated local result cannot yet be included in the Codex comparison run without manual copying, which is not acceptable evidence handling.

## Exact Assignment

Extend the existing provider benchmark harness with a governed cross-run executor-result import operation.

The operation must:

1. Accept:
   - benchmark ID;
   - source run ID;
   - source executor name;
   - destination run ID;
   - optional destination executor name only when explicitly needed and non-conflicting.
2. Read the source executor's preserved files and metadata.
3. Verify the source and destination benchmark IDs and benchmark versions match.
4. Verify the source and destination canonical packet SHA-256 values match exactly.
5. Verify the source result is canonical-packet eligible.
6. Reject pilot, altered-packet, mismatched-packet, missing-hash, or ineligible evidence.
7. Reject import when the destination executor directory already contains non-identical result evidence.
8. Preserve source evidence unchanged.
9. Copy or materialize immutable imported evidence into the destination executor directory.
10. Create an import provenance receipt recording:
    - source run ID;
    - source executor;
    - destination run ID;
    - destination executor;
    - source metadata SHA-256;
    - copied-file SHA-256 values;
    - canonical packet SHA-256;
    - import timestamp;
    - import command;
    - import eligibility decision.
11. Mark the imported result as imported evidence without changing its measured execution metrics or validation outcome.
12. Allow the existing compare and report commands to include the imported result normally.

## Required CLI Surface

Implement a command equivalent to:

```text
provider-benchmark import-executor-result BENCHMARK_ID SOURCE_RUN_ID SOURCE_EXECUTOR DESTINATION_RUN_ID
```

For Benchmark 001, the expected command shape is:

```text
provider-benchmark import-executor-result benchmark-001 20260713T170302Z-883587d1 local 20260713T170839Z-2f4d2cae
```

The command must print a structured JSON receipt suitable for copying into the architectural review conversation.

## Evidence Rules

- Source files are immutable.
- Destination imports must not silently overwrite evidence.
- Import is not re-execution.
- Import is not validation.
- Import must preserve original timing, token, attempt, model, provider, test, and validation fields.
- The source run ID must remain visible in provenance.
- Missing metrics remain null or retain their original unavailable explanation.
- Imported failed results remain failed.
- Imported passed results remain passed.
- Comparison ranking must still refuse mismatched canonical packet hashes.

## Chief Architect Reference Import

Do not create a new reference implementation in this package.

Ensure the same cross-run import mechanism can import a previously prepared Chief Architect reference executor result into the shared comparison run after that result is finalized and validated under the identical canonical packet.

The existing governed `import-reference` path may remain, but the final shared comparison must be able to contain:

- codex;
- local;
- chief_architect;

under one destination run ID and one canonical packet hash.

## Tests

Add tests proving:

1. A fair eligible source executor result imports successfully.
2. Source evidence is byte-for-byte unchanged after import.
3. The import receipt contains source and destination provenance and hashes.
4. A canonical packet hash mismatch is rejected.
5. An ineligible pilot source is rejected.
6. A missing source result is rejected.
7. A conflicting destination executor directory is rejected.
8. An identical repeat import is idempotent or rejected clearly without mutation.
9. Imported failed validation remains failed.
10. Imported passed validation remains passed.
11. Existing compare includes both native and imported executor results.
12. Existing report renders both native and imported executor results.
13. Windows path handling works under `A:\theestate`.
14. The full existing provider-benchmark test suite remains green.

## Acceptance Criteria

WP-0547 is complete when:

- the governed cross-run import command exists;
- the fair local Benchmark 001 result is imported from `20260713T170302Z-883587d1` into `20260713T170839Z-2f4d2cae`;
- the imported local result retains its original failed validation and measured metrics;
- the Codex result remains unchanged and passed;
- both results appear in the same comparison report;
- the shared run remains canonical-packet eligible;
- no original evidence is modified;
- tests pass;
- exact commands for importing the Chief Architect reference and producing the final three-way report are documented.

## Non-Goals

Do not:

- design additional benchmarks;
- create a qualification suite;
- create a new comparison engine;
- change scoring weights;
- repair the local model result;
- rerun Codex;
- overwrite prior evidence;
- alter WP-0545 or WP-0546 doctrine beyond the minimum integration required;
- create duplicate evidence, provider, routing, scheduling, or authority systems.

## Required Completion Report

Report:

- branch name;
- pull request number;
- commit SHA;
- files changed;
- tests run and results;
- import command implemented;
- local source run and destination run;
- import receipt path;
- canonical packet SHA-256;
- comparison report path;
- exact Chief Architect reference import command;
- exact final compare and report commands;
- blockers or contradictions.
