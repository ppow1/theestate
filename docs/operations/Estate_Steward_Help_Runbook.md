# Estate Steward Help Runbook

Use `python scripts/steward_help.py ask "Grace, what Skills are available?"` for a read-only current answer, or `python scripts/steward_help.py snapshot` to regenerate the JSON snapshot and dated Cheat Sheet. The normal conversational forms are:

- `Grace, help.`
- `Grace, what can we do?`
- `Grace, show my commands.`
- `Grace, what Skills are available?`
- `What can Engineering do right now?`
- `What can Helen do?`
- `Can we transcribe audio?`
- `How do I ask for <outcome>?`

Answers distinguish operational now, authorization required, registered but unavailable, temporarily unavailable, capability gap, prohibited, planned, and institutional acceptance. Help and discovery never execute a Skill. For an action, ask for a proposal first, then make a separate explicit governed request with exact scope, output, authority, and approval requirements.
