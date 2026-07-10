# WP-0624 - Merge Discovery Consolidation and Backfill Control

Status: Proposed  
Priority: Critical  
Owner: Chief Architect #6  
Classification: Estate Internal  
Created: 2026-07-09

## Mission

Make WP-0623 safe for unattended operation.

The first live scan created 68 audit requests from 82 discoveries because proposal, implementation, receipt, and merge commits for the same work package were treated as separate audit candidates.

WP-0624 must consolidate those records into one canonical audit candidate per work package and promoted revision, control historical backfill, and cleanly quarantine or supersede the requests already created.

## Provider Assignment Guidance

Recommended implementation provider: `codex_cloud_web`  
Local runtime required: false for implementation; true for demonstration  
Capacity note: do not use Codex CLI for normal implementation.

## Required Behavior

### Evidence precedence

Use this order when several discoveries refer to the same work package:

```text
completion receipt commit
implementation commit
merge commit
proposal or pending-package commit
commit-message-only inference
```

The strongest eligible record becomes canonical. Weaker records become `superseded` and link to the canonical discovery.

### Canonical grouping

Group by:

```text
target_id + work_package_id + promoted_revision
```

Where promoted revision is the receipt or implementation revision selected by evidence precedence.

Create no more than one active audit request for a canonical group.

### Backfill control

The first scan must not automatically flood the live audit queue.

Support modes:

```text
observe
quarantine
admit
```

Default first-run historical discoveries to `quarantine` unless explicitly admitted.

Support limits:

```text
max_commits
max_age_hours
max_candidates
max_requests_per_cycle
minimum_evidence_level
```

Suggested defaults:

```text
max_commits: 50
max_age_hours: 48
max_candidates: 20
max_requests_per_cycle: 5
minimum_evidence_level: implementation
```

### Existing queue cleanup

Provide a governed reconciliation command for the 68 requests already created.

It must:

- identify canonical groups,
- retain one strongest request per group,
- mark weaker requests `superseded` or `quarantined`,
- preserve history,
- never delete evidence silently,
- never process superseded requests.

### Ambiguity handling

Ambiguous discoveries remain blocked for review.

Receipt evidence should outrank incidental references in commit messages or unrelated changed paths. A valid receipt for WP-X should not become ambiguous merely because the same commit mentions another WP in supporting files.

## Runtime Integration

Operations Runtime must process only admitted canonical requests.

Add metrics:

```text
canonical_candidates
superseded_discoveries
quarantined_discoveries
admitted_requests
requests_suppressed_by_grouping
backfill_limit_reached
```

## CLI Requirements

Add commands equivalent to:

```powershell
python -m estate.cli.main merge-discovery consolidate --target estate-main --json
python -m estate.cli.main merge-discovery quarantine-status --target estate-main --json
python -m estate.cli.main merge-discovery admit --target estate-main --work-package WP-0504 --json
python -m estate.cli.main merge-discovery reconcile-requests --target estate-main --json
python -m estate.cli.main operations-runtime run-once --discover-merges --process-audits --max-audit-requests 5 --json
```

Follow repository CLI conventions if names differ.

## Office Visibility

Expose:

```text
canonical_candidates
quarantined_candidates
superseded_discoveries
ambiguous_discoveries
admitted_requests
queue_limit
backfill_mode
latest_canonical_work_package
```

## Expected Artifacts

Expected files:

```text
src/estate/core/merge_discovery_consolidation.py
tests/test_merge_discovery_consolidation.py
docs/integration/merge_discovery_consolidation_and_backfill_control.md
```

Expected integration touchpoints:

```text
src/estate/core/merge_discovery.py
src/estate/core/merge_discovery_runtime.py
src/estate/core/operations_runtime.py
src/estate/core/post_merge_audit_processor.py
src/estate/core/steward_command_center.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
```

## Test Requirements

Tests must prove:

- proposal, implementation, receipt, and merge records consolidate,
- receipt evidence wins,
- only one active request exists per canonical group,
- weaker records are superseded with links,
- first-run backfill is quarantined,
- queue limits are enforced,
- explicit admission works,
- reconciliation preserves history,
- superseded requests are never processed,
- ambiguous discoveries stay blocked,
- CA5 WP-0504, WP-0505, and WP-0506 each produce at most one canonical request,
- provider and dispatch execution remain false.

## Validation

```powershell
Clear-Host
cd A:\theestate
python -m py_compile src\estate\core\merge_discovery_consolidation.py
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_merge_discovery.py tests/test_merge_discovery_runtime.py tests/test_merge_discovery_consolidation.py --basetemp Temp/pytest-merge-consolidation
python -m estate.cli.main validate-work-package --id WP-0624 --json
```

## Demonstration

After merge:

```powershell
Clear-Host
cd A:\theestate
git pull --ff-only origin main
python -m estate.cli.main merge-discovery reconcile-requests --target estate-main --json
python -m estate.cli.main merge-discovery consolidate --target estate-main --json
python -m estate.cli.main merge-discovery quarantine-status --target estate-main --json
python -m estate.cli.main operations-runtime run-once --discover-merges --process-audits --max-audit-requests 5 --json
```

Expected result:

```text
historical flood reduced to canonical candidates
WP-0504, WP-0505, and WP-0506 each appear once
weaker discoveries are superseded or quarantined
no more than five admitted requests are processed
no provider or dispatch execution occurs
```

## Completion Receipt

Create:

```text
collaboration/work_packages/completions/WP-0624_codex_done.json
```

Report canonical groups, superseded records, quarantined records, admitted requests, reconciled existing requests, queue limits, demonstration results, and false provider/dispatch execution values.

## Promotion Criteria

Ready when merge discovery can run continuously without flooding the audit queue, historical backfill is controlled, canonical grouping works, CA5 packages consolidate correctly, deterministic validation passes, and authority boundaries remain intact.
