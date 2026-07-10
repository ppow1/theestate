# WP-0629 - Background Service Registry and Control Surface

Status: Proposed  
Priority: High  
Owner: Chief Architect #6  
Classification: Estate Internal  
Created: 2026-07-10

## Mission

Provide a canonical registry and real control surface for all background services and monitored targets.

## Required Behavior

Each service entry must expose identity, owner, enabled state, pause state, priority, cadence, triggers, dependencies, health, last run, next run, latest result, and supported controls.

Required controls:

- enable / disable
- pause / resume
- run now
- change cadence
- change priority
- inspect health
- inspect last result
- place or clear an operational hold

Controls must invoke canonical handlers and persist durable state. No display-only actions.

## Monitored Target Controls

Support adding, enabling, disabling, pausing, and removing monitored repositories or operational targets without changing source code.

## Office Contract

Expose callable functions, status artifacts, input contracts, and truthful result contracts for CA5 WP-0516, WP-0519, WP-0520, and WP-0521.

## Expected Artifacts

- `src/estate/core/background_service_registry.py`
- `src/estate/core/background_service_control.py`
- `tests/test_background_service_registry.py`
- `tests/test_background_service_control.py`
- `docs/integration/background_service_registry_and_control_surface.md`

## Test Requirements

Prove persistence, enable/disable, pause/resume, run-now, cadence and priority changes, target management, invalid action rejection, and Office status truthfulness.

## Validation

```powershell
Clear-Host
cd A:\theestate
python -m py_compile src\estate\core\background_service_registry.py src\estate\core\background_service_control.py
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_background_service_registry.py tests/test_background_service_control.py --basetemp Temp/pytest-service-control
python -m estate.cli.main validate-work-package --id WP-0629 --json
```

## Promotion Criteria

Ready when services and targets can be governed through durable real controls without code edits or hidden authority.
