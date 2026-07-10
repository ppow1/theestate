# Engineering Capacity Runtime

The Engineering Capacity Runtime combines provider health/capacity evidence with local worker runtime evidence into an Office-readable dashboard.

## Artifacts

- `runtime/engineering_capacity/dashboard.json` - machine-readable dashboard.
- `runtime/engineering_capacity/dashboard.md` - runtime Markdown dashboard.
- `operations/engineering_capacity/runtime_dashboard.md` - staged Office install handoff.

## Command

```bash
python -m estate.cli.main engineering-capacity-dashboard
```

The runtime is advisory only. It does not launch workers, consume cloud Codex seats, or schedule work.
