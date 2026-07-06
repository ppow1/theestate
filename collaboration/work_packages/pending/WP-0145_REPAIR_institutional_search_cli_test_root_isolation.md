# REPAIR TASK WP-0145 — Institutional Search CLI Test Root Isolation

## Codex Command

Read `collaboration/work_packages/pending/WP-0145_REPAIR_institutional_search_cli_test_root_isolation.md` and do exactly what it says.

## Numbering Boundary

WP-0145 is in the assistant/Steward support repair range.

Do not renumber this into the WP-0200 through WP-0250 block. That block is reserved for Chief Architect #3's staged Office Controls workstream. Work package numbers are now range-owned, not chronological; chronology comes from timestamps and Git history.

## Mode

REPAIR. Focused test and CLI root-isolation repair.

## Mission

Fix the single failing institutional search test reported during the repository-boundary repair without weakening the repository-boundary changes.

PR #154 reported:

- `PYTHONPATH=src python -m pytest tests -q` produced `431 passed, 1 failed`.
- The failing test was `tests/test_institutional_search.py::test_cli_json_output`.
- The focused test batch produced `89 passed, 1 failed` with the same failure.
- The failure occurred because the `estate-search` CLI returned a repository documentation result instead of the temporary `tmp_path` document created by the test.

## Root Cause to Verify

The institutional search core supports an explicit root parameter:

- `build_institutional_search_index(root=...)`
- `search_institutional_index(query, root=..., refresh=...)`

The test creates a temporary Estate-like tree, changes the process working directory to `tmp_path`, invokes the CLI, and expects the CLI to search that temporary tree.

However, the CLI handler currently calls institutional search without passing a root:

```python
result = search_institutional_index(args.query, refresh=not getattr(args, "no_refresh", False))
```

Because `estate.core.institutional_search.estate_root()` prefers the imported `ESTATE_ROOT` when it exists, the CLI searches the real repository instead of the test's temporary working directory. That makes the test non-isolated and allows repository documents containing `Chief Architect` to outrank or replace the temporary memo.

## Required Fix

Make `estate-search` root selection explicit and testable.

Recommended implementation:

1. Add an optional CLI argument to `estate-search`:

```text
--root PATH
```

2. Update `cmd_estate_search` so it passes an explicit root into `search_institutional_index`.

Suggested behavior:

```python
root = Path(args.root) if getattr(args, "root", None) else Path.cwd()
result = search_institutional_index(
    args.query,
    root=root,
    refresh=not getattr(args, "no_refresh", False),
)
```

This preserves ordinary local use when the operator is in `A:\theestate`, keeps tests isolated under `tmp_path`, and gives operators an explicit `--root` escape hatch when they need to search a specific Estate checkout from another working directory.

3. Ensure `Path` is already imported in `src/estate/cli/main.py`; if not, import it.

4. Update or add tests so these cases are covered:

- Existing `test_cli_json_output` passes when `monkeypatch.chdir(tmp_path)` is used.
- `estate-search QUERY --json --root <tmp_path>` searches the specified root even if current working directory is elsewhere.
- Existing direct core tests for `build_institutional_search_index` and `search_institutional_index` continue to pass.

## Constraints

- Do not revert WP-0205 repository-boundary changes from PR #154.
- Do not re-track live runtime projections.
- Do not make search indexes authoritative source material.
- Do not use WP-0200 through WP-0250 numbering.
- Do not introduce external services or network calls.
- Do not change search result ranking unless necessary to fix root isolation.
- Do not weaken the local-only runtime boundary established for Ingrid's future security posture.

## Validation

Run at minimum:

```powershell
$env:PYTHONPATH = "src"
python -m pytest tests/test_institutional_search.py -q
python -m pytest tests/test_steward_command_center.py tests/test_assignment_queue.py tests/test_institutional_search.py tests/test_production_readiness_validation.py tests/test_resident_interaction.py -q
```

If time allows, run:

```powershell
$env:PYTHONPATH = "src"
python -m pytest tests -q
```

Also verify that the repository-boundary behavior still holds:

```powershell
git status --short
python -m estate.cli.main estate-search "Chief Architect" --json
python -m estate.cli.main estate-search "Chief Architect" --json --root .
git status --short
```

The search commands should not dirty tracked live runtime projections.

## Expected Outputs

- Minimal code change in `src/estate/cli/main.py` or the appropriate CLI module.
- Updated/added tests in `tests/test_institutional_search.py`.
- Completion artifact:
  `collaboration/work_packages/completions/WP-0145_codex_done.json`

## Acceptance Criteria

- `tests/test_institutional_search.py::test_cli_json_output` passes.
- The focused batch that failed in PR #154 passes.
- Full suite is green or any unrelated remaining failures are explicitly documented.
- `estate-search` behaves predictably from a temporary test root and from the normal Estate root.
- WP-0205 repository-boundary protection remains intact.

## Completion Signal

Before finishing, create `collaboration/work_packages/completions/WP-0145_codex_done.json` with:

- `work_package_id`: `WP-0145`
- `codex_status`: `done`
- `completed_at`
- `branch`
- `pull_request_url_or_not_applicable_reason`
- `merge_authority_or_equivalent`
- `summary`
- `files_changed`
- `tests_run`
- `known_limitations`
- `ready_for_ca_review`: true

## Merge Class

Class A if the repair only changes CLI root selection and test coverage. Escalate to Class B if the repair changes search ranking, artifact classification, source-of-truth semantics, or repository-boundary policy.
