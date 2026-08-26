# Historical Branch Register

Status: current authority classification
Purpose: prevent branch existence from being mistaken for authorization

This is a lightweight register, not branch archaeology. The current remote
branch lists were checked without inspecting the contents of unknown branches.
Under [Repository Branch Authority](Repository_Branch_Authority.md), every
non-main branch is historical/non-authoritative unless a current work package
explicitly names it.

## theestate

| Remote ref | Classification | Rule |
| --- | --- | --- |
| `origin/main` | **AUTHORITATIVE** | Default documentation and development authority |
| `origin/codex/riverview-bounded-doorbell` | **HISTORICAL / NON-AUTHORITATIVE** | **NO NEW DOCUMENTATION / NO NEW DEVELOPMENT** |
| Any other non-main remote ref | **HISTORICAL / NON-AUTHORITATIVE** | Unknown until a future package explicitly authorizes it; do not use for new work |

## Riverview

| Remote ref | Classification | Rule |
| --- | --- | --- |
| `origin/main` | **AUTHORITATIVE** | Default implementation authority |
| `origin/codex/c484-operator-persistent-service` | **HISTORICAL / NON-AUTHORITATIVE** | Do not resume development |
| `origin/codex/rv-0083-estate-doorbell-bridge` | **HISTORICAL / NON-AUTHORITATIVE** | Do not resume development |
| `origin/codex/rv-0083-estate-doorbell-bridge-final` | **HISTORICAL / NON-AUTHORITATIVE** | Do not resume development |
| `origin/codex/rv-0083-riverview-owned-doorbell` | **HISTORICAL / NON-AUTHORITATIVE** | Do not resume development |
| `origin/codex/rv-0083-runtime-root-correction` | **HISTORICAL / NON-AUTHORITATIVE** | Do not resume development |
| Any other old `origin/codex/*` ref | **HISTORICAL / NON-AUTHORITATIVE** | Unknown until a future package explicitly authorizes it; do not use for new work |

No remote branch is deleted by this register. A future package that explicitly
authorizes a non-main branch must state the repository, exact branch, purpose,
and duration of that authority.
