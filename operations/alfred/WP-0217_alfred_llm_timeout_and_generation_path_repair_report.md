# WP-0217 Alfred LLM Timeout and Generation Path Repair Report

## Root cause
Alfred's provider discovery path could correctly find Ollama and select `qwen3:8b`, but the generation path still used a fixed 12 second request timeout. That is too short for a local 8B Ollama model on Windows during cold model load or after reboot, so `/api/generate` could time out even after `/api/tags` succeeded. The response contract then reported `status: completed` while returning deterministic fallback text, which made a failed LLM generation look like a completed conversational answer.

## Files changed
- `src/estate/core/resident_interaction.py`
- `src/estate/core/steward_command_center.py`
- `src/estate/core/work_package_validation.py`
- `tests/test_resident_interaction.py`
- `tests/test_steward_command_center.py`
- `operations/alfred/WP-0217_alfred_llm_timeout_and_generation_path_repair_report.md`
- `runtime/residents/alfred/WP-0217_alfred_llm_timeout_and_generation_path_repair_report.json`
- `collaboration/work_packages/completions/WP-0217_codex_done.json`

## Timeout policy
Alfred now reads `ESTATE_ALFRED_OLLAMA_TIMEOUT_SECONDS`, bounded from 1 to 300 seconds, before local Ollama generation. The safe default is 60 seconds, chosen because a Windows/Ollama cold load of an 8B model can exceed the previous 12 second fixed timeout while still being a normal reachable local generation path.

## Prompt/context size findings
The prompt already used a bounded context packet, but the embedded context slice was reduced and the final prompt is capped at 6000 characters. Diagnostics now record prompt size information per response so future failures can distinguish prompt bloat from provider or cold-load issues.

## Diagnostic changes
Alfred diagnostics now include provider reachability, selected provider/model, generation attempted/result, timeout seconds, prompt size summary, fallback state, fallback reason, and recovery hint. Timeout failures are classified as `generation_result: timeout` with a clear `Local Ollama invocation timed out after N seconds` reason.

## UI changes
The Office Alfred panel now displays generation result, timeout seconds, prompt size summary, and recovery hint. Per-turn display labels degraded fallback responses and no longer implies generation succeeded when the LLM call failed.

## Tests run
- `PYTHONPATH=src pytest tests/test_resident_interaction.py -q`
- `PYTHONPATH=src pytest tests/test_steward_command_center.py::test_wp0139_alfred_ui_has_failure_timeout_and_diagnostics_state -q`

## Validation commands run
- `PYTHONPATH=src pytest tests/test_resident_interaction.py tests/test_steward_command_center.py -q`
- `PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q`
- `PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0217 --json`
- `PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json`

## Local smoke test instructions
```powershell
CLS
Set-Location A:\theestate
$env:PYTHONPATH="A:\theestate\src"
$env:ESTATE_ALFRED_OLLAMA_TIMEOUT_SECONDS="60"
python -m estate.cli.main alfred-llm-diagnostics --json
python -m estate.cli.main resident-chat send --resident alfred --message "Alfred, give me a short operational greeting and say whether this came from the local LLM." --json
```
Expected result: when Ollama is reachable and the selected model is available, the chat response reports `mode: local_llm`, `generation_result: succeeded`, and `fallback_used: false`. If cold loading exceeds the timeout, the response reports degraded fallback with `generation_result: timeout` and a retry/warm-model recovery hint.

## Known limitations
- CI/Codex validation uses mocks and does not require a real Ollama daemon.
- A local machine with very slow disk/GPU/CPU initialization may still need a larger `ESTATE_ALFRED_OLLAMA_TIMEOUT_SECONDS` within the 300 second guardrail.

## Recommended next action
Steward should run the local PowerShell smoke test with Ollama and `qwen3:8b` installed, then retry once after a cold-load timeout to confirm the warmed model path returns a real local LLM response.
