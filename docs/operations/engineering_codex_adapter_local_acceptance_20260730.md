# Controlled Codex Adapter Acceptance — 2026-07-30

This evidence records one disposable, local acceptance run. It is not
institutional acceptance, a merge, or a production deployment.

## Commission

- Adapter request: `adapter-engineering-acceptance-002`
- Dispatch: `dispatch-engineering-acceptance-002`
- Provider: `codex.execution.cli`
- Adapter: `codex-cli-execution-adapter` version `1.0.0`
- Sandbox: `workspace-write`
- Write scope: `engineering_acceptance_workspace/output`
- Expected output: `engineering_acceptance_workspace/output/result.md`
- Codex invocation: `codex --ask-for-approval never exec --sandbox workspace-write --color never --ephemeral --json -`

## Result

- Real installed Codex CLI invoked: yes
- Process exit code: `0`
- Adapter disposition: `completed`
- Provider receipt: `receipt-adapter-engineering-acceptance-002`
- Artifact SHA-256: `6d5b6d3ce947f6edabb0386af65be827d6cec7ac2c3150fcb36a434a97362a8c`
- Receipt SHA-256 before cleanup: `f968c55d4a797b4908134b9bdd5a4cd60d2c17d1e5693a88272ebc74975115d`
- Artifact content: `ENGINEERING_CODEX_ACCEPTANCE_OK`

The temporary work product and runtime receipt were removed after the hashes
and evidence were captured. No live service, database, provider catalog at
runtime, or production work package was modified by the acceptance commission.

## Boundary result

The adapter required an explicit output, verified the artifact path and digest,
and created a provider receipt. This proves the local invocation and evidence
contract only. Engineering validation, Chief Architect review, Steward review,
and institutional acceptance remain separate.

## Fail-closed acceptance

Request `adapter-engineering-failclosed-001` carried an explicit cancellation
request. The adapter returned `blocked`, `validation_status=failed`, and
`live_provider_called=false` before invoking Codex. This confirms cancellation
does not become a false completion.
