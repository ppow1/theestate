# CORE-PTM-001A — Collaboration and Work-Package Source Inventory

Status: Complete inventory artifact
Date: 2026-07-16
Campaign: PTM-01 — Read-only source inventory
Launch group: G01A
Scope: `collaboration/work_packages/**`, `collaboration/parking_lot/**`, `collaboration/promotions/**`

## Purpose

This artifact records the read-only inventory for collaboration work-package, parking-lot, completion, receipt, promotion, and collaboration sources needed before PTM adapter contracts are finalized at Gate A. It is an implementation-preparation and validation artifact only. It does not authorize production PTM code, introduce a second queue or registry, or change governance authority.

## Authority and readiness baseline

- The accepted PTM baseline authorizes Codex-only preparation and execution for this cycle and excludes local RTX 4090 routing.
- `CORE-PTM-001A` depends on `SPEC-PTM-001`; the pending package states that dependencies have been accepted or explicitly waived by the Chief Architect before execution.
- The package manifest lists `CORE-PTM-001A` as `Executable Pending — Authorized for Codex handoff after dependencies pass`, in campaign `PTM-01`, launch group `G01A`, with pending path `collaboration/work_packages/pending/CORE-PTM-001A_Inventory_collaboration_and_work_package_sources.md`.
- The dependency manifest lists the hard dependency as `SPEC-PTM-001` and places `CORE-PTM-001A` in parallel-safe group `G01A` with `CORE-PTM-001B`.
- Gate A remains the integration checkpoint where `CORE-PTM-001C` merges the source inventory into read-only adapter contracts.

## Inventory method

Commands used for the repository-local inventory:

```bash
find collaboration/work_packages collaboration/parking_lot collaboration/promotions -maxdepth 3 -type f | sort
python - <<'PY'
from pathlib import Path
from collections import Counter
files=[Path(l.strip()) for l in open('/tmp/scope_files.txt')]
print('total',len(files))
for base in ['collaboration/work_packages','collaboration/parking_lot','collaboration/promotions']:
    sub=[p for p in files if str(p).startswith(base)]
    print(base,len(sub))
    c=Counter(p.parent.as_posix() for p in sub)
    for k,v in c.most_common(20): print(' ',v,k)
PY
```

The inventory was read-only. No source files in pending, parking-lot, promotions, or existing completion history were mutated by the inventory pass.

## Source counts observed

| Source area | Files observed | Notes for adapter planning |
|---|---:|---|
| `collaboration/work_packages/**` | 803 | Main work-package corpus, including pending packages, completion receipts, planning drafts, campaign instructions, open/claimed markers, queue files, and a small completed receipt set. |
| `collaboration/parking_lot/**` | 5 | Parking-lot candidates requiring governed intake/dedupe before canonical PTM promotion. |
| `collaboration/promotions/**` | 4 | Promotion folder structure currently contains only `.gitkeep` placeholders in root, approved, pending, and rejected states. |
| Total scoped files | 812 | Snapshot for Gate A inventory; future adapters should rescan rather than rely on static counts. |

## Work-package source categories

| Category | Current paths observed | Adapter relevance | Notes and constraints |
|---|---|---|---|
| Work-package queues | `collaboration/work_packages/codex_parallel_queue.md`, `collaboration/work_packages/codex_series_queue.md` | Read-only queue discovery and lifecycle status context. | Must not become a second dispatch queue. Existing queue semantics remain source evidence only. |
| Pending packages | `collaboration/work_packages/pending/*.md` | Primary source of executable package intent, status, ownership, scope, validation, and acceptance criteria. | Adapter should preserve source path, package ID, status, owner, lane, dependencies, and validation commands where present. |
| Completion receipts | `collaboration/work_packages/completions/*` | Evidence source for package completion, validation commands, deliverables, and notes. | Mixed Markdown/JSON naming is present; adapter should classify by extension and parse defensively. |
| Completed receipts | `collaboration/work_packages/completed/*` | Historical completion evidence, currently sparse relative to `completions/`. | Treat as an evidence source, not as canonical replacement for current package state. |
| Planning drafts | `collaboration/work_packages/planning/ptm_drafts/*.md` | Source planning baseline for PTM packages and future promotion evidence. | Planning drafts are non-executable unless promoted to Pending. |
| Planning manifests | `collaboration/work_packages/planning/estate_ptm_*_manifest.json` | Machine-readable package, campaign, and dependency context. | Downstream package `CORE-PTM-001C` should use these to reconcile inventory-derived adapter names. |
| Campaign instructions | `collaboration/work_packages/campaigns/ptm/*.md` | Campaign handoff containers and launch group instructions. | Campaigns authorize execution containers; work packages remain atomic evidence units. |
| Open and claimed markers | `collaboration/work_packages/open/*`, `collaboration/work_packages/claimed/*` | Lightweight lifecycle signal sources. | Current observed population is low; do not infer absence of work from these alone. |
| Legacy/root work-package files | `collaboration/work_packages/WP-2026-07-07-command-chair-macro-controller-integration.md`, root `.gitkeep` | Historical or special-case work-package sources. | Adapter should include root Markdown files in discovery rather than assuming all packages live under `pending/`. |

## Parking-lot and promotion source categories

| Category | Current paths observed | Adapter relevance | Notes and constraints |
|---|---|---|---|
| Parking-lot items | `collaboration/parking_lot/PL-0030-estate-performance-presentation-office.md`; `PL-0031-visual-estate-campaigns-11-20-motion-performance-canon.md`; `PL-0032-estate-engineering-provider-qualification-suite.md`; `PL-0033-stream-deck-operational-details-view.md`; `PL-OPS-0001-work-package-lifecycle-pending-cleanup.md` | Candidate intake source for governed PTM creation, dedupe, and prioritization. | Parking-lot items must remain candidates until accepted by governed intake; no private side list should be created. |
| Promotion placeholders | `collaboration/promotions/.gitkeep`; `approved/.gitkeep`; `pending/.gitkeep`; `rejected/.gitkeep` | Promotion-state directory contract source. | Current content is structural only; adapter should tolerate empty promotion state directories. |

## Adapter-readiness notes for CORE-PTM-001C

Recommended read-only adapter names and source responsibilities:

1. `work_package_pending_source`: enumerate pending Markdown work packages and extract package ID, status, owner, lane, scope, dependencies, validation, and acceptance criteria.
2. `work_package_completion_source`: enumerate `completions/` and `completed/` receipts, preserving source path, receipt format, validation evidence, and deliverable references.
3. `work_package_planning_source`: enumerate planning drafts, backlog, manifests, and campaign instructions as non-runtime planning context.
4. `work_package_queue_source`: enumerate queue and lifecycle marker files without creating or mutating queue state.
5. `parking_lot_candidate_source`: enumerate parking-lot Markdown files as intake candidates subject to future dedupe and confirmation gates.
6. `promotion_state_source`: enumerate promotion state directories and entries, tolerating `.gitkeep`-only state.

## Unknowns and evidence gaps

- Promotion directories currently expose structure but no substantive promotion records in the scoped snapshot.
- Completion evidence exists in both `completions/` and `completed/`; future projection logic should define precedence only after adapter contract freeze.
- Pending work packages are numerous and heterogeneous; robust extraction should prefer headings and explicit fields over strict positional assumptions.
- This package did not validate file links or Markdown syntax globally because no executable production files were touched and the package required read-only inventory plus evidence notes.

## Boundary confirmation

- No production PTM code was added.
- No second dispatch queue, registry, scheduler, or governance authority was introduced.
- The observed scope remains within `collaboration/work_packages/**`, `collaboration/parking_lot/**`, and `collaboration/promotions/**`.
- Active execution remained within the package estimate envelope and below the 60-minute exception threshold.
