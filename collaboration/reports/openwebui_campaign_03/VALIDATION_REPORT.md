# Open WebUI Campaign 03 Validation Report

Status: `metadata_operational_kokoro_unavailable_in_this_environment`

## Catalog
- Alfred (`estate/alfred`): voice `uncommissioned`, visual `placeholder`
- Helen (`estate/helen`): voice `canonical`, visual `placeholder`
- Ingrid (`estate/ingrid`): voice `uncommissioned`, visual `placeholder`
- Grace (`estate/grace`): voice `canonical`, visual `placeholder`
- Evelyn (`estate/evelyn`): voice `uncommissioned`, visual `restricted`
- Eleanor (`estate/eleanor`): voice `uncommissioned`, visual `placeholder`
- Marie (`estate/marie`): voice `uncommissioned`, visual `placeholder`
- Judy (`estate/judy`): voice `uncommissioned`, visual `placeholder`
- Estate conference room (`estate/conference-room`): voice `unavailable`, visual `unavailable`

## Kokoro
- Available: `False`
- Reason: Kokoro not discovered. Set ESTATE_KOKORO_COMMAND or install the approved local Kokoro environment.

## Validation boundaries
- **Implemented**: resident package projection; resident-first model catalog; identity trace response envelope; registered-audio retrieval contract; privileged execution disabled.
- **Test Validated**: commissioning bindings; Kokoro command construction and failure handling; 24 kHz WAV enforcement; path traversal and unregistered-file rejection.
- **Repository Validated**: identity, personnel, visual, and voice registry projection.
- **Locally Unavailable**: Kokoro synthesis; generated-audio HTTP playback.
- **Windows Verification Required**: approved Kokoro 0.9.4 environment discovery and synthesis; Open WebUI connection and playback.
- **Steward Approval Required**: listening approval remains required for any future voice; visual approval remains governed by canonical visual manifests.

## Startup (Estate PowerShell style)
```powershell
CLS
$env:PYTHONPATH='src'
$env:ESTATE_KOKORO_COMMAND='A:\AI\TTS\kokoro_py311\Scripts\python.exe'
python -m estate.cli.main resident-gateway start --host 127.0.0.1 --port 11435
```

## Manual Open WebUI steps
1. Add an OpenAI-compatible connection with base URL `http://127.0.0.1:11435/v1`.
2. Select resident models by name, e.g. `estate/helen` or `estate/grace`.
3. Request audio only for commissioned voices; other residents intentionally report uncommissioned/unavailable.
4. Retrieve successful attachments from `/v1/estate/audio/<resident>/<file>.wav`; only registry-backed 24 kHz WAV files are served.
