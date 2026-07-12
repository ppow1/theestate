# Engineering Provider Health

Generated: 2026-07-12T01:34:29Z

Advisory only: this surface does not dispatch or submit provider prompts.

Provider | Health | Auth | Fresh | Last success | Last failure | Latency | Failure rate | Active | Queue | Capacity | Dispatch eligible | Reasons / warnings
codex_cloud_web | unknown | unknown | False |  |  | None | 0.0 | 0 | 0 | unknown | False | capability registry is missing; capacity evidence is missing or stale; remote Codex polling skipped by WP-0534 policy
codex_cli_openai | offline | unknown | False |  |  | None | 0.0 | 0 | 0 | unknown | False | provider runtime unavailable or manually offline; capability registry is missing; capacity evidence is missing or stale; codex executable not found
local_ollama_gpu | offline | unknown | False |  |  | None | 0.0 | 0 | 0 | unknown | False | provider runtime unavailable or manually offline; capacity evidence is missing or stale; ollama executable not found
local_gpu_runtime | unknown | unknown | False |  |  | None | 0.0 | 0 | 0 | unknown | False | capacity evidence is missing or stale; nvidia-smi executable not found
