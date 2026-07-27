# Deployment runbook

1. Start the existing Estate resident gateway on `127.0.0.1:11435` so its `estate/grace` model catalog carries the Grace-only `toolIds` and `filterIds` metadata.
2. Start the Grace Momentum loopback binding from the repository root:

   `set PYTHONPATH=src && python -m scripts.run_grace_momentum_runtime --root A:\theestate-wp4233 --port 8766`

3. Install or update the persisted Open WebUI Tool and filter with `scripts/deploy_openwebui_grace_bridge.py` using the Open WebUI venv and its `DATA_DIR`.
4. Restart Open WebUI through `A:\AI\Tools\EstateStreamDeckMVP\Core\Stop-EstateService.ps1 -ServiceId open_webui` and `Start-OpenWebUI.ps1`.

The bridge rejects non-loopback URLs, userinfo, redirects, malformed responses, inactive claims, and non-2xx responses. Port 8766 is used because the existing command-center service owns port 8765.
