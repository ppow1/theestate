# Open WebUI frontend asset repair receipt — 2026-08-08

## Symptom

The canonical service at `127.0.0.1:8080` returned the Open WebUI HTML shell,
but `/static/loader.js`, `/static/custom.css`, and `/static/splash.png` returned
404. The Playwright harness consequently reported
`RESIDENT_SURFACE_UNAVAILABLE`.

## Root cause

The installed Open WebUI package is version `0.10.2`. Its frontend build is
under `open_webui\frontend`, while the served static root is
`open_webui\static`. The existing canonical starter set only `DATA_DIR`, so
the frontend/static roots were implicit and the running process did not expose
the top-level frontend assets.

## Repair

`tools/start_openwebui_canonical.ps1` now explicitly sets:

- `FRONTEND_BUILD_DIR` to the installed package frontend;
- `STATIC_DIR` to the installed package static directory;
- `DATABASE_URL` to `EstateCanonicalData\webui.db`.

It also fails closed if the executable, database, frontend index, or static
root is absent. No Open WebUI database, resident configuration, credentials,
or Grace/CME/Comms8 source was changed.

## Evidence

Before restart, the read-only asset probe recorded root `200` and all three
critical assets `404` (`OPENWEBUI_NOT_READY`). After the verified single
canonical-process restart, all three returned `200` with content types
JavaScript, CSS, and PNG; the probe returned `OPENWEBUI_READY`.

Detached restart evidence:
`cme-owner-20260808T113755920915Z-7a83faa1be` — exit `0`, completion marker
observed.

Playwright now reaches the real rendered Open WebUI login surface and reports
`LOGIN_REQUIRED`, which is the correct remaining authentication boundary.
