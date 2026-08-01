# ESTATE-OPS-001 Open WebUI State Inventory

All candidates were inspected read-only before state changes. A preservation
bundle was created at:

`A:\AI\Backups\Estate-Ops-001\20260731-205013`

It contains 20 discovered `webui.db*` files, installation configuration,
launcher state, and Stream Deck launch/control files.

| Candidate | Quick check | Admin users | Estate bridge objects |
|---|---|---:|---|
| `A:\AI\OpenWebUI\webui.db` | ok | 0 | none |
| package `open_webui\data\webui.db` | ok | 0 | none |
| `Before-Grace-Redeploy-2026-07-28_18-16-57\webui.db` | ok | 1 | none; redeployed |
| `Recovery-...\repaired\webui.db` | ok | 1 | none |
| `Recovery-...\previous-live\webui.db` | ok | 0 | none |
| `2026-07-27...\webui.db` | corrupt index | 1 | none |

The approved pre-redeploy database was copied using SQLite’s logical backup
API into:

`A:\AI\OpenWebUI\EstateCanonicalData\webui.db`

The canonical copy passed `quick_check`, retained the approved administrator,
and then received the existing Grace Tool, grounding Filter, and
`estate/grace-grounded-test` model association through
`scripts/deploy_openwebui_grace_bridge.py`. No SQLite tables were manually
edited.

Final canonical objects:

- administrator: `1f0449c8-3564-4a9f-a344-a8de330302fe`
- model: `estate/grace-grounded-test`, base `estate/grace`
- tool: `grace_runtime_bridge`
- filter: `grace_runtime_grounding`, active and non-global
