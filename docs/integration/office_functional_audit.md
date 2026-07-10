# Office Functional Audit

WP-0511 adds `estate.core.office_functional_audit` as a deterministic audit of the Office of the Steward. The audit reads the canonical Office navigation and tab registries, renders the current Office HTML, inventories registered Office action controls, and classifies each surface as functional, partially functional, display-only, placeholder, broken, duplicative, or missing required capability.

Outputs:

- `runtime/steward/office_functional_audit.json`
- `runtime/steward/office_functional_audit_summary.json`
- `runtime/steward/office_repair_waves.json`
- `operations/steward/office_functional_audit.md`

Run:

```bash
PYTHONPATH=src python -m estate.core.office_functional_audit
```
