# Canonical Grace Runtime/WebUI/Gateway Startup Runbook

## Authority

Run from `A:\theestate-wp4233`. The canonical source root is explicit in
`config/runtime/canonical_webui_gateway.json` and must match the current
checkout. The Gateway uses `C:\Python314\python.exe`; Open WebUI uses
`A:\AI\OpenWebUI\.venv\Scripts\open-webui.exe` version `0.10.2`.

Open WebUI state is explicitly bound to:

```text
DATA_DIR=A:\AI\OpenWebUI\EstateCanonicalData
DATABASE_URL=sqlite:///A:/AI/OpenWebUI/EstateCanonicalData/webui.db
```

The controller removes inherited `DATA_DIR`, `DATABASE_URL`, `PYTHONPATH`, and
`ESTATE_ROOT` before setting the approved values and secret key.

The managed public service set is three independent surfaces:

```text
Grace Momentum runtime: 127.0.0.1:8766
Resident Gateway:       127.0.0.1:11435
Open WebUI:              127.0.0.1:8080
```

Grace is started from the accepted `scripts/run_grace_momentum_runtime.py`
entry point in `governed_local_test` mode, using the existing
`runtime/production/grace_momentum` state and admission boundary. The Resident
Gateway is not the Grace runtime and port 11435 is never substituted for the
bridge endpoint at port 8766.

## Operator commands

```powershell
python scripts\canonical_webui_gateway.py status
python scripts\canonical_webui_gateway.py start --slot blue
python scripts\canonical_webui_gateway.py restart
python scripts\canonical_webui_gateway.py stop --slot blue
```

The Stream Deck buttons call the same controller through the updated external
launch files under `A:\AI\Tools\EstateStreamDeckMVP`.

## Readiness gates

Gateway readiness requires HTTP 200, an `estate/grace` catalog entry, Grace
metadata identifying resident `grace`, `resident_gateway_capable=true`, and
`privileged_actions_enabled=false`.

Grace runtime readiness requires authenticated `/v1/health` and `/v1/readiness`
responses, healthy persistence/replay/idempotency, the accepted mode, and a
ready governed runtime. Open WebUI readiness alone cannot make the Estate
healthy when Grace runtime readiness is absent.

Open WebUI readiness requires HTTP availability, SQLite `quick_check=ok`, an
administrator, the canonical database identity, model
`estate/grace-grounded-test` backed by `estate/grace`, tool
`grace_runtime_bridge`, active filter `grace_runtime_grounding`, and both
associations.

A listening port alone is never success.

## Evidence

State and slot evidence is written outside the repository at:

```text
A:\AI\Tools\EstateStreamDeckMVP\Core\state\canonical-runtime
```

It contains `active-slot.json`, slot manifests, process records for all three
services, promotion and rollback records, and bounded logs.
