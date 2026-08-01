# Canonical WebUI/Gateway Stream Deck Operator Note

The active Estate Operations launch files are:

- `08-Start-Resident-Gateway.cmd` -> canonical controller, blue Gateway
  service start.
- `10-Start-OpenWebUI.cmd` -> canonical controller, blue WebUI service start.
- `12-Start-Estate-Surfaces.cmd` -> canonical controller, blue pair start.
- `13-Estate-Runtime-Status.cmd` -> canonical controller status.
- `16-Restart-Estate-Surfaces.cmd` -> canonical controller restart of the
  recorded active slot.
- `17-Service-Health.cmd` -> canonical controller status/readiness evidence.

The `.cmd` wrappers remain PowerShell wrappers; the `.ps1` actions now invoke:

```text
C:\Python314\python.exe A:\theestate-wp4233\scripts\canonical_webui_gateway.py
```

The old `Estate-Service-Control.ps1` remains on disk only as a preserved
rollback artifact. OperatorDeck `slot`, `cycle-slot`, `select-active`, and
`promote-selected` controls continue to mean window placement, not application
deployment.
