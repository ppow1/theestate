# Codex CLI Capability Discovery, Provider Registry, and Polling Policy

Codex CLI is represented in the shared provider catalog as `codex.execution.cli`. The catalog is the source of truth for provider identity, advertised capabilities, classification ceiling, boundary review, and Office-safe descriptor data.

## Registry ownership

- Provider catalog: `config/providers/catalog.json`
- Provider ID: `codex.execution.cli`
- Advertised capabilities: `repository_implementation`, `code_review`
- Office status export: `runtime/providers/catalog_status.json`

Capability discovery reports local runtime metadata only. It must not automatically promote the catalog descriptor status because installed binaries, authentication, quota, and Steward authorization can differ per workstation.

## Discovery command

```powershell
.\estate.bat codex-cli-capability-discovery --json
```

For deterministic validation without probing the local executable:

```powershell
python -m estate.cli.main codex-cli-capability-discovery --no-probe --json
```

The command writes:

- `runtime/providers/codex_cli_capability_discovery.json`
- `runtime/providers/codex_cli_capability_discovery.md`
- `operations/engineering_capacity/codex_cli_capability_discovery.md`

## Polling policy

Automated Codex CLI status polling remains `manual_or_disabled_until_billing_delta_verified`.

Allowed automated probes are metadata-only commands such as `--version`, `--help`, and `exec --help`. Prompt submission, provider work execution, and frequent status polling are disallowed until the Estate has measured evidence that status checks do not consume quota, tokens, messages, or other limited capacity.

## Boundary notes

Discovery is advisory and does not execute provider work. Provider execution remains governed by the Codex bridge, live execution gate, dispatch lifecycle, and Steward authorization controls.
