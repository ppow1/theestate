# Estate Steward Help Runbook

Use `python scripts/steward_help.py ask "Grace, what Skills are available?"` for a read-only current answer, `python -m estate.cli.main help ask "Grace, what Skills are available?" --json` through the established CLI, or `python scripts/steward_help.py snapshot` to regenerate the JSON snapshot and dated Cheat Sheet. The authenticated WebUI Grace/Helen conversation path uses the same snapshot route for qualifying help and inquiry phrases; it does not invoke model generation for those requests.

- `Grace, help.`
- `Grace, what can we do?`
- `Grace, show my commands.`
- `Grace, what Skills are available?`
- `What can Engineering do right now?`
- `What can Helen do?`
- `Can we transcribe audio?`
- `How do I ask for <outcome>?`

Answers distinguish operational now, authorization required, registered but unavailable, temporarily unavailable, capability gap, prohibited, planned, and institutional acceptance. Help and discovery never execute a Skill. For an action, ask for a proposal first, then make a separate explicit governed request with exact scope, output, authority, and approval requirements.
