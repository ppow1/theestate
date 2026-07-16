# WP-0677 PTM reconciliation and production transition baseline

Status: Reconciled; production implementation not started  
Prepared: 2026-07-16  
Decision owner: Chief Architect, with Steward authority retained where protected

## Executive finding

The PTM sprint completed **implementation preparation**, not the PTM product. All
28 accepted PTM packages have completion receipts and implementation-ready
contracts or validation plans. Those receipts prove that the package work was
performed; they do not prove that a PTM event store, adapters, projections,
workspace, scheduler integration, financial system, KPI runtime, migration, or
rollout exists in production.

The first production campaign is therefore a bounded read-only discovery and
projection pilot. It is defined by `PTM-PROD-01` and its three executable work
packages. Starting it requires the normal Chief Architect review/launch action;
this reconciliation does not silently launch or accept it.

## Authoritative structural verification

The canonical verifier is `scripts/ptm/Test-EstatePtmRepository.ps1`. Its result
is authoritative for repository structure. WP-0676 recorded a clean independent
fixture check because PowerShell was unavailable in its Linux environment. In
this execution environment, the canonical command could not be executed because
PowerShell is absent; an attempt to acquire a temporary PowerShell binary was
rejected by the upstream host with HTTP 403. Consequently:

- no substitute result is represented as a canonical PASS;
- the last recorded structural evidence remains the WP-0676 completion receipt;
- production launch has an explicit `PTM-PROD-G0` gate requiring a fresh
  canonical PASS; and
- any canonical verifier failure overrides this report and blocks launch.

The production campaign manifest is deliberately separate from the completed
28-package planning manifests. The verifier's accepted package graph is not
rewritten to make planning completion look like product implementation.

## Reconciliation inventory

| Evidence set | Reconciled state | Meaning | Production gap |
| --- | --- | --- | --- |
| PTM specification acceptance | Accepted planning baseline | Permits preparation and preserves authority boundaries | Does not authorize implementation or merge |
| 28 Pending package files | Retained at manifest paths | Canonical executable-source paths used by the accepted manifests | Their `Pending` headings are historical source state, not current product backlog |
| 28 package completion receipts | Present | Package deliverables completed through ROLL-PTM-001B | Receipts predominantly close plans/contracts, not production code |
| PTM-00 through PTM-07 campaign handoffs | Completed preparation/execution campaign | Dependency-ordered package instructions remain audit evidence | Must not be re-run as if they were the production build |
| Architecture contracts and gate plans | Implementation-ready | Frozen inputs for production packages | Require code, tests, integration evidence, and protected acceptance |
| Canonical verifier | Governing structural check | Validates manifests, membership, paths, dependency graph, routing, and receipts | Does not validate runtime behavior or institutional acceptance |

## Cleanup decisions

1. **Do not move or delete completed Pending files.** The accepted manifests and
   verifier intentionally reference them. Their completion receipts are the
   state-transition evidence.
2. **Do not edit the accepted 28-package manifests for production work.** A new,
   explicitly versioned manifest avoids conflating preparation with build work.
3. **Do not claim rollout.** ROLL-PTM receipts deliver rollout plans and gates;
   no production deployment is evidenced.
4. **Keep drafts as provenance.** Draft, promoted Pending file, bounded planning
   artifact, and receipt form a traceable evidence chain.
5. **Resolve status ambiguity in indexes, not history.** The production handoff
   index identifies the old campaign as closed preparation evidence and the new
   campaign as awaiting launch.

## Frozen governance boundaries

- Existing Parking Lot, work-package, Dispatch, validation, acceptance, Helen,
  Grace, Traffic Controller, and activity records remain authoritative in their
  domains.
- PTM adapters are read-only in the first campaign and projections cannot write
  back to source systems.
- No second queue, registry, scheduler, validator, acceptance path, command bus,
  or governance authority may be created.
- Codex is an execution provider, not an office or acceptance authority.
- Chief Architect retains engineering review and acceptance; the Steward retains
  protected and final institutional authority.
- Frozen event, ID, command, projection, intake, route, scheduling, dispatch,
  validation, financial, KPI, migration, and rollout contracts require a
  stop/replan record before alteration.

## Production transition gates

| Gate | Required evidence | Fail-closed result |
| --- | --- | --- |
| `PTM-PROD-G0` launch | Fresh canonical verifier PASS; clean branch; Chief Architect launch decision; package dependencies present | Campaign remains `awaiting_launch` |
| `PTM-PROD-G1` adapter freeze | Source inventory coverage, deterministic fixtures, read-only enforcement, uncertainty preserved | Projection package cannot begin |
| `PTM-PROD-G2` pilot acceptance preparation | Rebuild equivalence, provenance, freshness/staleness behavior, security review, targeted tests | No merge, rollout, or Phase 2 fan-out |

## First production campaign disposition

`PTM-PROD-01` implements only roadmap Phase 1:

1. `PROD-PTM-001A` builds the reusable read-only adapter boundary and source
   adapters for the bounded pilot.
2. `PROD-PTM-001B` builds deterministic adapter fixtures and contract tests after
   the adapter boundary freezes.
3. `PROD-PTM-001C` builds an ephemeral read-only pilot projection and report,
   using selected source records without introducing the Phase 2 event ledger.

Phase 2 and later campaigns remain ungenerated until Gate G2 evidence is
reviewed. This makes the first set executable without pretending the entire
roadmap is ready for an undifferentiated implementation launch.

## Residual conditions

- A fresh canonical verifier PASS is outstanding in a PowerShell-capable
  environment and is a hard launch prerequisite.
- Production paths named by the work packages are target seams; implementers
  must stop and replan if current repository mechanisms require a frozen
  contract change.
- This baseline is prepared for review, not itself Chief Architect acceptance,
  Steward approval, deployment authorization, or rollout acceptance.
