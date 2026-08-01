# Canonical WebUI/Gateway Startup Runbook

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

It contains `active-slot.json`, slot manifests, process records, promotion and
rollback records, and bounded logs.
