# Canonical WebUI/Gateway Blue/Green Promotion and Rollback

## Slot model

- `blue`: public ports `11435` and `8080`.
- `green`: candidate ports `11436` and `8081`.
- Both slots use the canonical source root and one shared explicit Open WebUI
  database. State is not slot-cloned.

Each slot manifest records source root, source commit, executable/runtime
version, state/database identity, bridge deployment version, ports, validation
status, and validation evidence.

## Promotion

```powershell
python scripts\canonical_webui_gateway.py start --slot green
python scripts\canonical_webui_gateway.py promote --slot green
```

Promotion requires a validated candidate. The controller revalidates the
candidate, stops its isolated processes and the managed active slot, starts the
candidate on public ports, revalidates both applications, then atomically
publishes `active-slot.json`. A failed candidate cannot replace active state.

## Rollback

```powershell
python scripts\canonical_webui_gateway.py rollback
```

Rollback requires a recorded previous validated slot, stops the current
managed slot, starts the previous slot on public ports, revalidates, and then
publishes the rollback promotion record. The shared database path and identity
remain unchanged.

OperatorDeck window-slot and window-promotion files are separate desktop
placement controls and are not deployment evidence.
