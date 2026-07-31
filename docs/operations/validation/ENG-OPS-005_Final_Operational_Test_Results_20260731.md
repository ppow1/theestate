# ENG-OPS-005 Final Operational Test Results

Date: 2026-07-31. Branch: `engineering/close-remaining-operational-blockers`. Final implementation HEAD: `64848d44aa3ef32f983522328f1a9eff7c75f137`.

The final affected-module validation matrix passed **251 tests**. The eight-schema Draft 2020-12 registry validated with `FormatChecker`; compilation and `git diff --check` passed.

Fresh successes:

- Qwen retry: objective `grace-obj-68ed3119a3d7`, action `grace-act-9d4899d1b176`, capability `capreq-ade3f05d45fa`, Helen `heldet-569f615a41bd`, PTM `res_01KYX59RKJ1G3457XX0S48NVS2`, commission `engcom-ce303c591147`, authorization `engauth-960b370f89f0`, Dispatch `dispatch-1be3d96e1c1a`, completion `engcomp-ef51dc9269f4`. Artifact SHA-256 `54378fbd893f5c4ff7e9a9e99f9a9eb6313126729183dda37fa3f6cbbcaf98a1`; receipt SHA-256 `279fe4feae8be64da25521ce4ccc7ada469ca99af7225b2a026beb219f873c87`. Actual model `qwen3:8b`; one live call.
- Codex retry: artifact SHA-256 `08476a7dec3ede68bfa114e4686690cfa76103e7ff5aad4c60e744ac14260452`; receipt SHA-256 `34476bff190cefb632dce1640d762ccfc243cc2cc5df71aff2add3c801f8d862`; one live call.
- Steward intake: artifact SHA-256 `5b4e4957c2b05f9fe65ad327533a88bae6e9535155023818bf9f860749e1b7c9`; receipt SHA-256 `4f8aa0b86c7d55c0197d08078ff8add88408579cd4e005f94a88b345fd545cbe`; one live call.

Failure: transport injection receipt SHA-256 `181413596a7acd1bb142c0948ec9aa28023ad0f368c187e65cf7cf69bcaf3654`; no successful artifact or completion; Grace failed; acceptance remained not granted.

The Qwen retry and Codex/Steward outputs were exact create-once paths declared by authority. Receipts were parsed and correlated; Qwen actual model was observed as `qwen3:8b`. The first Qwen content-contract failure and first Codex receipt-scope block remain preserved as separate fresh evidence and were not reused.
