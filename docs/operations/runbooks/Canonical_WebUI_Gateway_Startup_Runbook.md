# Canonical Open WebUI startup and frontend readiness

The canonical local deployment is:

- executable: `A:\AI\OpenWebUI\.venv\Scripts\open-webui.exe`
- data: `A:\AI\OpenWebUI\EstateCanonicalData`
- URL: `http://127.0.0.1:8080`

Port availability alone is not readiness. The canonical starter must bind the
installed package's frontend and static roots explicitly and preserve the
canonical database through `DATA_DIR`/`DATABASE_URL`.

```powershell
CLS
cd A:\theestate-openwebui-acceptance
python tools/openwebui_asset_readiness.py --url http://127.0.0.1:8080
node tools/openwebui_operator_acceptance.cjs readiness --headed --url http://127.0.0.1:8080
```

`OPENWEBUI_READY` from the deterministic probe requires root HTML `200` and
`/static/loader.js`, `/static/custom.css`, and `/static/splash.png` `200`.
The Playwright probe additionally waits for the hydrated semantic UI and
distinguishes `LOGIN_REQUIRED` from a deployment failure.

Grace has a second, operator-facing readiness checkpoint. `PERSISTED_MODEL_READY`
means the canonical records and authenticated `/api/models` catalog contain
`estate/grace-grounded-test`, backed by `estate/grace`. `OPERATOR_VISIBLE_MODEL_READY`
means the authenticated operator can open the real model picker, see the
Estate Grace surface, select it, and use the composer. A database row or HTTP
200 response alone is not UI readiness.

Run the focused acceptance through the detached process boundary:

```powershell
python tools/cme_owner_isolation.py launch --timeout-seconds 180 -- node tools/openwebui_operator_acceptance.cjs scenario scenarios/grace_openwebui_basic.yaml --headed
```

The bounded restart helper validates that port 8080 is owned by the canonical
executable before stopping it, invokes `tools/start_openwebui_canonical.ps1`,
and waits for the listener to return. It never deletes or migrates
`EstateCanonicalData`.
