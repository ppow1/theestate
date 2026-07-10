# WP-0630 - Operational Event Subscription Fabric

Status: Proposed  
Priority: High  
Owner: Chief Architect #6  
Classification: Estate Internal  
Created: 2026-07-10

## Mission

Provide one shared event-subscription fabric so Estate services react to operational events without duplicate polling loops or private event systems.

## Required Behavior

Support publication, durable subscription, cursoring, replay, filtering, acknowledgment, dead-letter handling, duplicate suppression, bounded delivery, and subscriber health.

Initial event families:

- repository merge or promotion
- mailbox message arrival
- audit requested / completed / failed
- validation completed / failed
- Ring 2 evidence ready
- operational target changed
- service health changed
- resident or department duty completed
- Office attention required

## Boundaries

Use existing operational-event contracts where possible. Do not create a second authority layer, dispatch queue, or provider router.

## Office Contract

Expose callable functions, status artifacts, input contracts, and truthful result contracts for CA5 WP-0516, WP-0519, and WP-0521.

## Expected Artifacts

- `src/estate/core/operational_event_subscription.py`
- `src/estate/core/operational_event_delivery.py`
- `tests/test_operational_event_subscription.py`
- `tests/test_operational_event_delivery.py`
- `docs/integration/operational_event_subscription_fabric.md`

## Test Requirements

Prove publish/subscribe, replay, cursor recovery, duplicate suppression, dead-letter handling, subscriber failure isolation, and Office attention delivery.

## Validation

```powershell
Clear-Host
cd A:\theestate
python -m py_compile src\estate\core\operational_event_subscription.py src\estate\core\operational_event_delivery.py
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_operational_event_subscription.py tests/test_operational_event_delivery.py --basetemp Temp/pytest-event-subscriptions
python -m estate.cli.main validate-work-package --id WP-0630 --json
```

## Promotion Criteria

Ready when services can wake from shared events, recover from interruption, and avoid duplicate polling and duplicate delivery.
