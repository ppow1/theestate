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
- Estate multi-resident room (`estate/conference-room`): voice `None`, visual `None`

## Kokoro
- Available: `False`
- Reason: Kokoro not discovered. Set ESTATE_KOKORO_COMMAND or install the approved local Kokoro environment.

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
