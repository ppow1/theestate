# Estate Stream Deck service lifecycle

The Estate Stream Deck MVP controls use the governed service runtime under
`A:\AI\Tools\EstateStreamDeckMVP\Core`.

## Lifecycle contract

- Start first checks the configured endpoint, process identity, and port owner.
- A healthy recognized instance returns `already_running`; it does not create a
  second service or launcher console.
- A port owned by an unrecognized process fails closed.
- Concurrent starts for the same service are serialized by the service-level
  start mutex.
- Stop targets only the service's configured process identity, owned port
  processes, and exact governed wrapper name. It does not sweep arbitrary
  Python, Node, CUDA, or shell processes.
- Restart is the governed stop followed by the governed start.
- Health/status is READY only when the endpoint and configured process identity
  agree; duplicate or foreign ownership is degraded/ERR.

The Stream Deck plugin launches the `.cmd` action with a transient `cmd /c`
process. It does not use `cmd /k start`, so repeated button presses do not
accumulate persistent wrapper consoles.

## Button family

| Control | Governed service/action | Lifecycle behavior |
| --- | --- | --- |
| CORE START / STOP / RESTART | Ollama, Resident Gateway, Open WebUI | Aggregate governed lifecycle; excludes P100/SillyTavern, TextGen, ComfyUI, Comms8, and Codex. |
| RGW START | `resident_gateway` on `11435` | Identity-checked and idempotent. |
| WEBUI START | `open_webui` on `8080` | Identity-checked and idempotent; preserves canonical data. |
| TEXT GEN START | `textgen` on its configured health ports | Static lifecycle contract; no workload is started by audit tests. |
| COMFYUI START | `comfyui` on `8188` | Static lifecycle contract; no workload is started by audit tests. |
| CORE HEALTH / runtime indicator | Governed status probes | Uses endpoint plus process/port identity, not port-open alone. |

Open WebUI must retain:

```text
WorkingDirectory = A:\AI\OpenWebUI
DATA_DIR         = A:\AI\OpenWebUI\EstateCanonicalData
Database         = A:\AI\OpenWebUI\EstateCanonicalData\webui.db
```

The package-default Open WebUI data directory is not authoritative. Missing
canonical state, foreign port ownership, or an unverifiable process identity
must prevent launch; there is no automatic fallback or restore.

