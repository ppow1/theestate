# WP-0623 - Automatic Merge and Receipt Discovery

Status: Proposed  
Priority: Critical  
Owner: Chief Architect #6  
Classification: Estate Internal  
Created: 2026-07-09

## Mission

Complete the missing front end of the automatic validation loop.

WP-0621 can process post-merge audit requests. WP-0622 can resolve and bind targets. WP-0623 must discover newly merged or locally promoted work packages and create those audit requests automatically.

Required flow:

```text
new merge or promotion detected
  -> work package identified
  -> completion receipt correlated
  -> duplicate/history check
  -> post-merge audit request created
  -> Operations Runtime processes request
  -> validation, Ring 2 preparation, and verdict follow
```

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is repository implementation across Git discovery, completion receipts, Background Operations, Operations Runtime, Post-Merge Audit, CLI, tests, and documentation.
```

Local runtime required:

```text
false for implementation; true for live demonstration after merge
```

Capacity note:

```text
Do not use Codex CLI for normal implementation. Deterministic tests must not require network access.
```

## Architectural Boundary

Merge discovery is observation and request generation only.

It may observe local Git history and completion receipts, correlate work-package identity, record discovery state, and create governed audit requests.

It must not merge, commit, repair, approve, execute providers, execute dispatch work, or invent identity when evidence is ambiguous.

## Required Scope

Implement:

1. Local Git merge/promotion discovery.
2. Completion-receipt discovery.
3. Work-package identity correlation.
4. Cursoring and deduplication.
5. Discovery records and audit candidates.
6. Automatic post-merge audit request creation.
7. Operations Runtime and Background Operations integration.
8. CLI commands for scan, status, candidates, and replay.
9. Office visibility.
10. Deterministic tests and documentation.

## Discovery Sources

Use local evidence:

```text
local main Git history
merge commits
recent commits changing completion receipts
collaboration/work_packages/completions/*.json
pending work-package files
validation recipes
PR metadata already present in receipts
```

GitHub API or webhook hosting is not required for v1.

## Discovery Cursor

Maintain one cursor per operational target.

Suggested artifact:

```text
runtime/merge_discovery/targets/<target_id>/cursor.json
```

Fields:

```text
target_id
base_branch
last_scanned_commit
last_scanned_at
last_discovery_count
last_request_count
status
warnings
errors
```

The first scan must use a bounded lookback, such as 100 commits or 72 hours.

## Work-Package Correlation

Use evidence in this order:

1. Completion receipt `work_package_id`.
2. Work-package ID in changed completion-receipt filename.
3. Work-package ID in commit subject/body.
4. Work-package ID in changed pending/completion path.
5. Explicit operator mapping.

Conflicting IDs must produce `ambiguous`; do not choose silently.

## Discovery Record

Create a normalized record with:

```text
discovery_id
target_id
source_kind
source_commit
source_reference
work_package_id
completion_receipt_path
correlation_method
state
duplicate_of
audit_request_id
created_at
warnings
errors
metadata
```

Allowed states:

```text
discovered
request_created
already_processed
ambiguous
ignored
blocked
failed
```

## Deduplication

Do not create duplicate audit requests for:

```text
target_id + work_package_id + source_commit
```

Also suppress a request when the same work package already has a final verdict for the same or newer commit.

## Audit Request Creation

Create requests compatible with WP-0621/WP-0622:

```text
audit_id
target_id
work_package_id
source_kind
source_reference
expected_files
metadata
state: pending
```

Metadata should include discovery ID, source commit, completion receipt path, and correlation method.

Use canonical target IDs internally.

## Operations Runtime Integration

A runtime cycle must be able to:

```text
scan merges
create audit requests
process audit requests
publish verdicts
```

Support a command equivalent to:

```powershell
python -m estate.cli.main operations-runtime run-once --discover-merges --process-audits --json
```

Add metrics:

```text
merge_commits_scanned
work_packages_discovered
discoveries_ambiguous
discoveries_ignored
audit_requests_created_from_merges
duplicate_audit_requests_suppressed
```

## CA5 Wave Demonstration

After merge, run bounded discovery against recent CA5 work:

```text
WP-0504
WP-0505
WP-0506
```

Discover whichever packages have sufficient local Git and receipt evidence. Create audit requests and feed them into the automatic validation pipeline. Do not fabricate missing candidates.

## CLI Requirements

Suggested commands:

```powershell
python -m estate.cli.main merge-discovery scan --target estate-main --json
python -m estate.cli.main merge-discovery status --target estate-main --json
python -m estate.cli.main merge-discovery candidates --target estate-main --json
python -m estate.cli.main merge-discovery replay --target estate-main --max-commits 50 --json
python -m estate.cli.main operations-runtime run-once --discover-merges --process-audits --json
```

Follow existing CLI conventions if names differ.

## Office Visibility

Expose:

```text
merge_discovery_available
last_merge_scan_at
last_scanned_commit
merge_commits_scanned
work_packages_discovered
pending_discovery_candidates
ambiguous_discoveries
latest_discovered_work_package
latest_created_audit_request
duplicate_requests_suppressed
```

## Out of Scope

Do not add GitHub webhook hosting, hard dependency on GitHub API polling, automatic merge/commit/repair, provider execution, dispatch execution, Steward acceptance, a second audit queue, or a second target registry.

## Expected Artifacts

Expected files:

```text
src/estate/core/merge_discovery.py
src/estate/core/merge_discovery_runtime.py
tests/test_merge_discovery.py
tests/test_merge_discovery_runtime.py
docs/integration/automatic_merge_and_receipt_discovery.md
```

Expected integration touchpoints:

```text
src/estate/core/background_operations.py
src/estate/core/background_operations_runtime.py
src/estate/core/operations_runtime.py
src/estate/core/operations_runtime_service.py
src/estate/core/post_merge_audit_processor.py
src/estate/core/steward_command_center.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
```

## Test Requirements

Tests must cover:

- first bounded scan creates cursor,
- later scan processes only new commits,
- receipt resolves work-package ID,
- changed receipt filename resolves work-package ID,
- commit message fallback works,
- conflicting IDs produce `ambiguous`,
- duplicate tuple suppresses repeat request,
- existing final verdict suppresses redundant request,
- incomplete receipt creates candidate with warning,
- canonical target ID is used,
- request is compatible with WP-0621,
- runtime can discover then process,
- Office summary exposes discovery metrics,
- provider execution remains false,
- dispatch execution remains false.

## Validation Rings

### Ring 0

```powershell
Clear-Host
cd A:\theestate
Test-Path src\estate\core\merge_discovery.py
Test-Path src\estate\core\merge_discovery_runtime.py
Test-Path tests\test_merge_discovery.py
Test-Path tests\test_merge_discovery_runtime.py
Test-Path docs\integration\automatic_merge_and_receipt_discovery.md
python -m py_compile src\estate\core\merge_discovery.py
python -m py_compile src\estate\core\merge_discovery_runtime.py
```

### Ring 1

```powershell
Clear-Host
cd A:\theestate
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_merge_discovery.py tests/test_merge_discovery_runtime.py tests/test_post_merge_audit_processor.py tests/test_post_merge_validation_pipeline.py --basetemp Temp/pytest-merge-discovery
python -m estate.cli.main validate-work-package --id WP-0623 --json
```

### Ring 2

Review whether merge discovery creates trustworthy audit requests from local evidence, suppresses duplicates, handles ambiguity safely, and preserves execution and acceptance boundaries.

### Ring 4

Chief Architect / Steward acceptance confirms merges and promotions can now enter the automatic validation pipeline without manual request creation.

## Completion Receipt

Create:

```text
collaboration/work_packages/completions/WP-0623_codex_done.json
```

Receipt must report commits scanned, work packages discovered, audit requests created, duplicates suppressed, ambiguous discoveries, demonstration candidates, demonstration verdicts, and false values for provider/dispatch execution.

## Promotion Criteria

Ready when merge and receipt discovery works, cursoring and deduplication work, eligible CA5 packages enter the audit pipeline automatically, deterministic tests pass, production readiness is true, Ring 2 recommends Chief Architect review, and no provider or dispatch execution occurs.
