# Deployment runbook

1. Start the existing Estate resident gateway on `127.0.0.1:11435` so its `estate/grace` model catalog carries the Grace-only `toolIds` and `filterIds` metadata.
2. Start the Grace Momentum loopback binding from the repository root:

   `set PYTHONPATH=src && python -m scripts.run_grace_momentum_runtime --root A:\theestate-wp4233 --port 8766 --mode governed_local_test`

   Then admit the approved local image adapter and verify readiness:

   `set PYTHONPATH=src && python scripts/enable_grace_local_image_execution.py --runtime http://127.0.0.1:8766`

3. Install or update the persisted Open WebUI Tool, filter, and `estate/grace-grounded-test` model associations with `scripts/deploy_openwebui_grace_bridge.py` using the Open WebUI venv and its `DATA_DIR`.
4. Restart Open WebUI through `A:\AI\Tools\EstateStreamDeckMVP\Core\Stop-EstateService.ps1 -ServiceId open_webui` and `Start-OpenWebUI.ps1`.

The bridge rejects non-loopback URLs, userinfo, redirects, malformed responses, inactive claims, and non-2xx responses. Port 8766 is used because the existing command-center service owns port 8765.

The admission step is intentionally separate from process startup. It requires Engineering authority and admits only `comfyui.local.image` at `http://127.0.0.1:8188`; network egress and spend remain disabled. If ComfyUI or readiness is unavailable, the command fails closed and no provider effect is claimed.

Failure and rollback behavior: every accepted assignment is persisted before Dispatch submission. Provider, reconciliation, validation, completion, progress, failure, and artifact records are written under `runtime/production/grace_momentum`. A provider error returns `disposition=failed` with the assignment and failure identifiers and a persisted reason; Grace does not claim dispatch or completion unless those records exist. `runtime.rollback` may revoke the admission and records the rollback audit event; already-created image artifacts are retained for audit and must be removed through the normal Estate artifact-retention process.
