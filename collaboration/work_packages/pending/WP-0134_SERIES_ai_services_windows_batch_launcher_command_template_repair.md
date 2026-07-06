# SERIES TASK WP-0134 — AI Services Windows Batch Launcher Command Template Repair

## Codex Command

Read collaboration/work_packages/pending/WP-0134_SERIES_ai_services_windows_batch_launcher_command_template_repair.md and do exactly what it says.

## Mode

SERIES

## Mission

Repair AI Services Control Plane command execution for Windows batch launchers so manifest-declared `.bat` services such as TextGen launch through the correct Windows batch invocation semantics and remain healthy under control-plane execution.

WP-0133 correctly repaired lifecycle semantics: the control plane no longer treats PID creation as service success and now reports `health_failed` when the declared endpoint does not respond. Steward validation then proved TextGen itself works when launched directly from its application directory through the Windows batch launcher, and its OpenAI-compatible endpoint responds at `http://127.0.0.1:5000/v1/models`.

WP-0134 must repair the TextGen manifest/execution path so the same working launcher semantics are used by the AI Services Control Plane.

## Problem Statement

After WP-0133, the Estate correctly reported a TextGen health failure when launched by the control plane. The failure was not caused by TextGen, the model, or the health endpoint.

Manual diagnostic evidence showed that launching TextGen directly from `A:\AI\TextGen\textgen-4.9` with the local `textgen.bat` launcher and model `Qwen3-8B-Q6_K.gguf` successfully loaded the model and exposed the OpenAI-compatible API at:

```text
http://0.0.0.0:5000/v1
```

A follow-up endpoint check succeeded:

```json
{
  "object": "list",
  "data": [
    {
      "id": "Qwen3-8B-Q6_K.gguf",
      "object": "model",
      "created": 0,
      "owned_by": "user"
    }
  ]
}
```

The current Estate TextGen command template is a nested PowerShell command string that invokes the batch file indirectly. It does not reproduce the successful direct launch behavior.

The control plane should not use a brittle nested shell string when the service launcher is a Windows batch file. It should represent launcher type, working directory, executable, and arguments explicitly, then let the execution adapter invoke the launcher safely.

## Preconditions

1. Confirm WP-0131, WP-0132, and WP-0133 are merged.
2. Inspect `runtime/ai_services/implementations/textgen/service.manifest.json`.
3. Inspect `src/estate/ai_services/execution.py`, `control.py`, `manifest.py`, and `tests/test_ai_services_control_plane.py`.
4. Confirm TextGen endpoint health verification from WP-0133 remains in place.
5. Do not weaken lifecycle-aware health semantics.
6. Do not move model files.
7. Do not install, update, or remove TextGen or any third-party AI application.
8. Do not expose services outside loopback.
9. Do not add cloud API behavior.
10. Tests must use mocks and must not launch actual AI services.

If any precondition fails, stop and report the exact blocker.

## Scope

In scope:

1. Repair the TextGen service manifest command metadata so the control plane uses Windows batch-launch semantics with the correct working directory.
2. Add or refine execution adapter support for manifest-declared command type, shell/interpreter family, working directory, launcher, and argument substitution.
3. Prevent model names or manifest arguments from causing command injection.
4. Preserve TextGen model-name validation added by WP-0132.
5. Preserve endpoint health verification added by WP-0133.
6. Add tests proving `.bat` launchers are wrapped safely and consistently on Windows.
7. Add tests proving the TextGen planned command matches the successful direct-launch semantics.
8. Add tests proving health failure still reports failure when the endpoint does not respond.
9. Add WP-0134 report, validation recipe, and completion receipt.

Out of scope:

- Installing or updating TextGen.
- Changing TextGen model files.
- Moving or consolidating model files.
- Disabling Steward approval requirements.
- Removing post-launch health verification.
- Public network exposure.
- Cloud APIs.
- Full process supervisor redesign.
- ComfyUI workflow execution.
- SillyTavern session automation.

## Required Design

Represent launcher behavior explicitly rather than embedding a whole shell string in the command template.

A preferred manifest shape is equivalent to:

```json
{
  "operations": {
    "load_model": {
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
  }
}
```

The final implementation may follow existing manifest conventions, but it must avoid arbitrary shell-string interpolation where a structured command representation is straightforward.

For Windows `.bat` launchers, the resolved execution must use the correct Windows batch invocation semantics while keeping argument substitution safe and bounded.

## Required Behavior

### Planned command behavior

A dry-run TextGen model-load request must return a planned command or safe command description that clearly shows the `.bat` launcher will be invoked using Windows batch handling, with `A:\AI\TextGen\textgen-4.9` as the working directory and `Qwen3-8B-Q6_K.gguf` as the model argument.

### Execution behavior

A real approved TextGen model-load operation must:

1. validate the requested model name;
2. resolve the working directory from the manifest;
3. invoke the batch launcher through the correct Windows batch execution path;
4. continue to use WP-0133 post-launch health checks;
5. return success only when `http://127.0.0.1:5000/v1/models` responds;
6. return `health_failed` or equivalent if the endpoint does not respond.

### Security behavior

Model names and manifest argument substitution must remain safe. Reject path traversal, separators, shell metacharacters, or anything outside the existing safe model-name pattern.

Do not introduce raw unrestricted shell access for Alfred.

### State and audit behavior

State and audit semantics from WP-0133 must remain intact. A successful launch must record health success before execution success. A failed launch must preserve diagnostics.

## CLI Requirements

The following behavior must continue to work after this repair:

```text
ai-services load-model --service textgen --model Qwen3-8B-Q6_K.gguf --approved-by steward --health-timeout-seconds 20 --health-interval-seconds 2 --json
```

After this repair, if TextGen is not already occupying the port and the local installation is healthy, this command should launch TextGen and return lifecycle-aware success after the health endpoint responds.

Dry-run should also show the corrected launcher plan.

## Required Tests

Add or update tests for:

1. TextGen manifest exposes a structured Windows batch launcher operation or equivalent safe command metadata.
2. Planned TextGen model-load command uses Windows batch handling rather than nested PowerShell shell-string execution.
3. Working directory is resolved from the manifest and passed to the runner.
4. Model-name validation still rejects path traversal, separators, and shell metacharacters.
5. Batch launcher arguments are passed without unsafe shell interpolation.
6. Health success after batch launch returns execution success.
7. Health failure after batch launch returns health failure.
8. Existing WP-0131, WP-0132, and WP-0133 AI Services tests remain passing.
9. Work-package and production-readiness validation tests remain passing.

Use mocks for process execution and health checks. Tests must not launch actual third-party AI applications.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src pytest tests/test_ai_services_control_plane.py -q
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0134 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If CLI names differ, use existing canonical validation commands and document the mapping.

## Required Artifacts

Create:

```text
operations/ai_services/WP-0134_ai_services_windows_batch_launcher_repair_report.md
```

Create machine-readable companion:

```text
runtime/ai_services/WP-0134_ai_services_windows_batch_launcher_repair_report.json
```

The report must include:

- current git commit;
- files changed;
- final TextGen launcher manifest shape;
- batch launcher execution design;
- model-name safety behavior;
- health-check preservation;
- CLI behavior;
- tests run;
- validation commands run;
- known limitations;
- recommended next action.

## Required Outputs

- Repaired TextGen launcher manifest/operation representation.
- Safe Windows batch launcher execution support.
- Dry-run command plan matching direct successful launch semantics.
- Preserved WP-0133 health verification semantics.
- Updated tests.
- WP-0134 report Markdown and JSON.
- `collaboration/work_packages/completions/WP-0134_codex_done.json`.

## Completion Artifact

Create:

```text
collaboration/work_packages/completions/WP-0134_codex_done.json
```

It must include `work_package_id = WP-0134`, `codex_status = done`, summary, launcher manifest shape, batch execution behavior, TextGen command behavior, model-name safety behavior, health-check preservation, tests run, validation commands run, known limitations, recommended next action, `ready_for_ca_review = true`, and `merge_authority = ca_verified_auto_merge_allowed`.

## Acceptance Criteria

WP-0134 is complete when the AI Services Control Plane launches TextGen using Windows batch semantics equivalent to the manually validated direct launcher path, preserves Steward approval and post-launch health verification, rejects unsafe model names, and returns truthful lifecycle-aware results.

## Merge Class

Class A. Escalate only if implementation requires changing cloud model policy, public network exposure policy, resident API governance, memory/redaction policy, production-readiness semantics, Alfred authority boundaries, or third-party application installation/update/removal behavior.
