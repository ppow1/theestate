# Open WebUI scenario authoring

Scenarios are deliberately small YAML documents. Each turn contains ordinary
Steward-facing text and optional structural expectations; avoid exact prose
matching unless the behavior itself is the contract.

```yaml
name: GRACE_OPENWEBUI_GROUNDING
resident: Grace
fresh_conversation: true
turns:
  - send: "Grace, what is the current CME operational state?"
    expect:
      contains_any: [IDLE, PROCESSING, UNKNOWN]
validator: cme_state
```

Supported expectation fields are `contains_any`, `contains_all`, and
`not_contains`. `validator: cme_state` performs a read-only comparison against
the local CME projection when present and fails closed when that projection is
unknown. Validators must never create or advance Estate state.

Use `chat --resident Grace --message "..."` for a single-turn diagnostic. Use a
scenario for multi-turn continuity. Independent conversations use separate
scenario invocations or separate browser pages; the harness records each URL
and run ID rather than treating a title as identity.
