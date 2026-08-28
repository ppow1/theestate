# Estate Operations Runtime Hidden Console Correction Report

Date: 2026-08-02  
Repository: `ppow1/theestate`  
Starting origin/main: `9ae35bb6666eaed5fbea895f5892afa6864165ff`  
Branch: `agent/hidden-console-runtime-host`

## Root cause and exact launch path

The observed path was:

`Estate Operations Runtime Host` scheduled task → `powershell.exe -File run_operations_runtime_host.ps1` → `python.exe -m estate.cli.main operations-runtime host run-foreground` → `OperationsRuntimeService` → `OperationsRuntime.run_cycle` → `PostMergeAuditProcessor` → `PostMergeValidationPipeline` → `validate_work_package` → `work_package_validation._run_command` → `subprocess.run(command, shell=True, ...)`.

The final call passed recipe text such as `pytest -q tests/test_operational...` with `shell=True`. On Windows, Python implements that string-shell invocation through `cmd.exe /c`, producing the observed child process. The host and scheduled task were the source path; no `os.system`, `Start-Process`, or `ProcessStartInfo` call was involved in validation.

## Correction

Background runtime commands now use `src/estate/core/background_process.py`.

On Windows, the helper supplies `CREATE_NO_WINDOW` and `STARTUPINFO` with `STARTF_USESHOWWINDOW` and `SW_HIDE`. Simple shell-free commands are parsed into argv and run with `shell=False`; shell syntax remains supported and is still hidden. Stdout, stderr, return code, timeout state, command identity, and duration remain captured.

The detached host child uses the same Windows no-window flags. Scheduled-task installation emits `powershell.exe -WindowStyle Hidden` for the launcher. Foreground/operator-visible commands were not redirected through this helper.

## Files changed

- `src/estate/core/background_process.py`
- `src/estate/core/work_package_validation.py`
- `src/estate/core/post_merge_validation_pipeline.py`
- `src/estate/core/operations_runtime_host.py`
- `tests/test_background_process.py`
- `tests/test_work_package_validation.py`
- `tests/test_operations_runtime_host.py`

## Tests

- Focused runtime/audit set: **67 passed**.
- Adjacent post-merge, host, audit, and merge-discovery set: **23 passed**.
- `git diff --check`: passed.

Coverage includes hidden Windows process configuration, direct pytest argv execution, shell-dependent recipe fallback, output and stderr capture, nonzero exit codes, timeout evidence, host launch flags, scheduled launcher flags, foreground/non-Windows behavior, and existing runtime/audit flows.

## Controlled Windows integration proof

An isolated child-process proof used the new background launch configuration. The recorded result was:

```json
{
  "child_pid": 8876,
  "returncode": 7,
  "stdout": "stdout-proof\n",
  "stderr": "stderr-proof\n",
  "hidden_kwargs": {"creationflags": 134217728, "has_startupinfo": true},
  "tree_observation": {
    "Name": "python.exe",
    "ParentProcessId": 2404,
    "CommandLine": "C:\\Python314\\python.exe -c ..."
  }
}
```

The tree contained no `cmd.exe` wrapper. The focused pytest validation tests also completed successfully with result capture intact.

The live task was inspected read-only during review:

- Task: `Estate Operations Runtime Host`
- Status: `Running`
- Scheduled task state: `Enabled`
- Current installed command still references the canonical launcher; this review worktree did not rewrite or restart the live task.

After this correction is deployed, reinstalling/updating the task through the existing host installer will add `-WindowStyle Hidden` to the task command. The child-process correction itself is applied by the runtime code.

## Before/after process-tree evidence

Before/source evidence: the validation call used `subprocess.run(..., shell=True, ...)`, which on Windows creates `cmd.exe /c "pytest ..."`.

After controlled evidence: direct `python.exe` child, hidden creation flags, exit code 7, stdout/stderr retained, and no `cmd.exe` intermediary.

## Validation results and limitations

Merge discovery, auto-admission, audit processing, receipts, reconciliation, runtime health code paths, and scheduled-task startup behavior remain intact; the relevant existing tests passed. No live audit or merge was triggered, and no Estate runtime state was changed by this review proof.

The controlled proof verifies exact Windows process configuration and process-tree shape. A desktop GUI assertion is not automated here. The installed task’s persisted command is only changed when the existing installation path is run; the source correction does not silently mutate the live scheduled task.
