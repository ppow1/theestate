# ENG-OPS-003 Operational Test Results

## Successful live tasks

### Qwen retry

- Objective/action: `grace-obj-1b95b30986ca` / `grace-act-ff1cee327c0d`
- Capability/Helen: `capreq-ebd36d04512d` / `heldet-12251a8eabf5`
- PTM: `res_01KYX3R235C7GGWM00N9B35QYW`, `ready`
- Commission/authorization/Operations/Dispatch: `engcom-48ee2803f9c2`, `engauth-2596ec19b3fa`, `opdec-2f8bd2576b154aeb8a60fb17c7bedea6`, `dispatch-cb3069bd3cb6`
- Provider: `qwen.local.text`; adapter: `qwen-local-ollama-text-adapter@1.0.0`; actual model: `qwen3:8b`; live calls: 1
- Artifact: `docs/operations/validation/ENG-OPS-003_Scenario1_Qwen_Retry_6d743af281474640.md`
- Artifact SHA-256: `7a318fc13aa0160c6b5b9e55447d2b08b8cfd9bd5a202f0c62d649d2fe5f2137`
- Receipt: `runtime/engineering_adapter_receipts/eng-ops-003-s1-retry-6d743af281474640.json`
- Receipt SHA-256: `d6587840fc8fc15f1ef887b5cc7a98f63b432f8fd2f288b810a95bc2afd883a0`
- Completion/Grace receipt: `engcomp-be305c00b364` / `gracereceipt-1317adb21e00`

### Repeated Qwen success

- Objective/action: `grace-obj-6514e5f9dc73` / `grace-act-df6cbe2a8130`
- Capability/Helen: `capreq-c9d3486ebe03` / `heldet-eea9e19463ef`
- PTM: `res_01KYX4ANVWH6BQBQDW5S0EK5GB`, `ready`
- Commission/authorization/Operations/Dispatch: `engcom-9b3e36d1da8e`, `engauth-aa325eb5e63c`, `opdec-bf665f79390f4f62b5ccf4ae88ec51d2`, `dispatch-74392b86c598`
- Provider/adapter/model: `qwen.local.text` / `qwen-local-ollama-text-adapter@1.0.0` / `qwen3:8b`; live calls: 1
- Artifact: `docs/operations/validation/ENG-OPS-003_Repeat_Qwen_6c7fce8d1e194719.md`
- Artifact SHA-256: `ec3109a128ddbe7ccb3f6c2726f584c8ad2570d34ef2ee7e6f31448ce2dba6de`
- Receipt: `runtime/engineering_adapter_receipts/eng-ops-003-repeat-qwen-6c7fce8d1e194719.json`
- Receipt SHA-256: `86d010634f6bf3faeb2b98b9b8a429f4406238778cde3895bbf848a2edbb543b`
- Completion/Grace receipt: `engcomp-1c3e54b25534` / `gracereceipt-f5adb960dce5`

## Negative and boundary results

- Initial S1 artifact-content failure: one Qwen call, no artifact, truthful failure receipt, no Engineering completion; fresh retry passed.
- S2 Codex: no provider call; blocked by bridge profile and denied runtime prompt-source policy. No fake pass.
- S3: capability gap passed; no commission, Dispatch, or provider.
- S4: stale PTM evidence blocked before execution; no provider or outputs.
- S5: unsafe `.` read scope blocked at final handoff; no provider or outputs.
- S6: safe provider-failure injection unavailable without service/config mutation; recorded as unexecuted testability gap.
- S7: equivalent completed replay passed after `286bce85`; no duplicate commission, authorization, Dispatch, or provider call.
- S8: Steward CLI created the request and capability inquiry but cannot complete the technical lifecycle without manual record surgery; public-entry-point blocker recorded.

All live institutional acceptance states remained `not_granted`.
