# Open WebUI Estate Resident Gateway Setup v0.1

Open WebUI is only the conversation surface. The Estate remains authoritative for resident identity, authority, memory, routing, diagnostics, and model selection.

## Prerequisites

- Estate repository checkout with local Python environment.
- Optional local Ollama service at `http://127.0.0.1:11434` with a text model installed.
- No cloud API key is required by the Estate gateway.

## Start the Gateway

```powershell
Set-Location A:\theestate
python -m estate.cli.main resident-gateway start --host 127.0.0.1 --port 11435
```

The gateway binds locally by default. If the port is occupied, choose another local port or stop the conflicting process.

## Open WebUI Connection

- Base URL: `http://127.0.0.1:11435/v1`
- API key: use any placeholder if Open WebUI requires one; the local Estate gateway does not require or record cloud credentials.

## Model Discovery

Open WebUI should discover:

- `estate/alfred`
- `estate/helen`

You can confirm directly:

```powershell
Invoke-RestMethod http://127.0.0.1:11435/v1/models | ConvertTo-Json -Depth 10
```

Grace is intentionally not exposed as an active model.

## Smoke Tests

Select `estate/alfred` and ask: `Who are you and what is your role?`

Select `estate/helen` and ask: `Who are you, what office do you serve, and what are your responsibilities?`

Helen should identify as Helen in Human Resources and Workforce Development. Responses include Estate metadata indicating provider, model, session, and fallback state.

## Troubleshooting

- Connection refused: start the resident gateway and verify host/port.
- No models: call `/v1/models` directly and refresh Open WebUI model cache.
- Provider unavailable: the gateway remains available but reports deterministic fallback when local Ollama is unreachable.
- Fallback mode: start Ollama, install the assigned model, or update Estate model-control assignments.
- Stale browser state: refresh Open WebUI, clear model cache, or re-save the OpenAI-compatible connection.

Streaming is not supported; non-streaming OpenAI-style chat completions are supported.
