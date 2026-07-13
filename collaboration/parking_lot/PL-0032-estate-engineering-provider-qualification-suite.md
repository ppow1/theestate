# PL-0032 — Estate Engineering Provider Qualification Suite

Status: Captured  
Category: Engineering Capacity / Provider Qualification  
Priority: Strategic  
Originator: Chief Architect #5 / Steward  
Date captured: 2026-07-13  
Target milestone: After Benchmark 001 fair rerun is complete and the immediate Engineering Department readiness decision has been made

## Idea

Develop a reusable Estate Engineering Provider Qualification Suite that evaluates Codex, local Ollama models, future local coding workers, and other execution providers against a governed series of identical software-engineering assignments.

Candidate qualification areas include:

- bounded Python implementation;
- repository refactoring;
- multi-file defect repair;
- test-driven development;
- architecture-to-code implementation;
- documentation synthesis;
- performance optimization;
- Git and pull-request workflow quality.

The suite would preserve canonical benchmark packets, provider-specific execution evidence, timing, tokens, repair attempts, validation results, code-quality review, security and boundary compliance, and reproducible comparative scorecards.

## Why It Is Parked

The idea is valuable, but it is not part of the current bounded assignment.

The active need is a road-sign answer showing where Codex, the local RTX-4090/Ollama worker, and the Chief Architect reference stand today on one fair apples-to-apples Benchmark 001 run.

Expanding into a multi-benchmark qualification program now would interrupt that work and delay the immediate provider-capability decision.

## Promotion Condition

Promote only after all of the following are true:

1. WP-0546 has corrected canonical benchmark-packet equivalence.
2. Benchmark 001 has been rerun with identical immutable input for Codex, local Ollama, and the Chief Architect reference.
3. The comparison report has been completed and accepted by the Steward.
4. The Engineering Department has an immediate provider-use decision from that evidence.
5. The Steward explicitly authorizes broader qualification-suite work.

## Explicit Non-Action

Do not create additional benchmark packages, qualification campaigns, provider scorecards, or suite architecture from this item during the current Benchmark 001 correction and rerun.

## Related Evidence

- `collaboration/work_packages/pending/WP-0545_PARALLEL_INDEPENDENT_Engineering_Provider_Benchmark_001.md`
- `collaboration/work_packages/pending/WP-0546_PROVIDER_BENCHMARK_CANONICAL_PACKET_AND_FAIR_RERUN.md`
- preserved pilot local run `20260713T022800Z-474aacb0`
