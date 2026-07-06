# WP-0134 AI Services Windows Batch Launcher Repair Report

## Current git commit

669d9c58bb7520cd1039a25f19167570f19bd76a

## Files changed

- `runtime/ai_services/implementations/textgen/service.manifest.json`
- `src/estate/ai_services/execution.py`
- `src/estate/ai_services/control.py`
- `tests/test_ai_services_control_plane.py`
- `operations/ai_services/WP-0134_ai_services_windows_batch_launcher_repair_report.md`
- `runtime/ai_services/WP-0134_ai_services_windows_batch_launcher_repair_report.json`
- `collaboration/work_packages/completions/WP-0134_codex_done.json`

## Final TextGen launcher manifest shape

TextGen `load_model` now declares a structured Windows batch operation instead of a nested PowerShell command template:

```json
{
  "command_type": "windows_batch",
  "working_directory": "A:\\AI\\TextGen\\textgen-4.9",
  "launcher": "textgen.bat",
  "arguments": [
    "--nowebui",
    "--listen",
    "--model",
    "{model}",
    "--loader",
    "llama.cpp"
  ]
}
```

## Batch launcher execution design

The control plane now asks execution planning for a structured command. For `command_type = windows_batch`, the execution adapter validates the launcher as a local `.bat` or `.cmd` filename, substitutes bounded model arguments, and produces `cmd.exe /d /c textgen.bat ...` with `shell = false`. The manifest working directory is passed separately as the subprocess `cwd`, preserving the successful direct-launch semantics without raw shell-string interpolation.

## Model-name safety behavior

Model substitution reuses the existing safe model-name pattern and rejects empty values, path traversal, `/`, `\\`, and shell metacharacters because those characters are outside `^[A-Za-z0-9._+-]+$`. Manifest argument rendering passes each argument as a separate list element rather than interpolating a shell command string.

## Health-check preservation

WP-0133 lifecycle-aware health semantics remain intact. Process PID creation is still recorded as `process_started`, then the TextGen health endpoint `http://127.0.0.1:5000/v1/models` must respond before execution succeeds. If the endpoint does not respond, the result remains `health_failed` with diagnostics and non-running state.

## CLI behavior

Approved CLI execution remains:

```text
ai-services load-model --service textgen --model Qwen3-8B-Q6_K.gguf --approved-by steward --health-timeout-seconds 20 --health-interval-seconds 2 --json
```

Dry-run output now exposes the structured Windows batch plan, including `working_directory`, `launcher`, rendered `arguments`, and `subprocess_args`.

## Tests run

- `PYTHONPATH=src pytest tests/test_ai_services_control_plane.py -q`
- `PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q`
- `PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0134 --json`
- `PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json`

## Validation commands run

The required validation commands were run after implementation and artifact creation. `validate-work-package --id WP-0134 --json` exited 1 because no WP-0134 validation recipe is registered; receipt validation is complete and report artifacts were written. `validation-production-readiness --json` exited 0 and reports WP-0134 blocked only by the missing/no_recipe validation recipe.

## Known limitations

- This change does not install, update, move, or validate the actual third-party TextGen application or model files.
- Tests mock process execution and health checks; they intentionally do not launch TextGen.
- Runtime success still depends on the local Windows host having TextGen installed at `A:\AI\TextGen\textgen-4.9` and port 5000 available.

## Recommended next action

Have CA review and merge WP-0134, then run the approved TextGen load-model CLI command on the Windows host with the local TextGen installation available to verify end-to-end launch and health success.
