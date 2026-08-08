# Open WebUI diagnostic impact packet

```yaml
component: canonical-openwebui
change: explicit-frontend-static-roots-and-asset-readiness
version: 0.10.2
failure_before: RESIDENT_SURFACE_UNAVAILABLE
failure_evidence: root-200-critical-static-assets-404
healthy_probe: OPENWEBUI_READY
current_boundary: LOGIN_REQUIRED
data_root: A:\AI\OpenWebUI\EstateCanonicalData
executable: A:\AI\OpenWebUI\.venv\Scripts\open-webui.exe
read_only_validator: tools/openwebui_asset_readiness.py
operator_acceptance: tools/openwebui_operator_acceptance.cjs
```

This packet is provider-neutral and intentionally does not depend on the
unfinished Living Diagnostics implementation. It identifies the changed
component, expected behavior, failure class, and validation boundary without
including credentials, cookies, database contents, or browser profile state.
