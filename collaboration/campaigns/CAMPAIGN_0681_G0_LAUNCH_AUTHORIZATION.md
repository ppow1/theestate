# CAMPAIGN-0681 — G0 Launch Authorization

Status: Authorized for launch  
Campaign: CAMPAIGN-0681 — Estate Operationalization  
Authorization date: 2026-07-16  
Repository: `ppow1/theestate`  
Base branch: `main`  
Verified base commit: `a182c5586558a361876bebe24698e7c666043323`  
Campaign source blob before launch activation: `dc640120dfdb169489cf109315970b7acf7e886e`  
Manifest blob before launch activation: `1ced5a00a880a58c20bfbad5289859ed64dd7d16`

## Prerequisite satisfaction

1. WP-0678 has been implemented, merged through PR #414, protected-accepted, and operationally authorized.
2. The Chief Architect has reviewed the CAMPAIGN-0681 charter, package decomposition, dependency graph, integration gates, protected boundaries, and single-handoff execution policy and approves campaign launch.
3. The Steward authorizes CAMPAIGN-0681 to proceed through its bounded execution model and approves the protected action classes only to the extent stated in this record.
4. The campaign must remain on `campaign/0681-estate-operationalization`, use one bounded commit per work package, stop at every configured gate, and produce one campaign pull request without automatic merge or acceptance.
5. Existing PTM, Dispatch, mailbox, repository-message, validation, readiness, evidence, office, and acceptance mechanisms remain authoritative and must be reused rather than duplicated.

## Chief Architect launch decision

The Chief Architect authorizes CAMPAIGN-0681 to launch from the recorded `main` base commit after the campaign charter and execution manifest are activated consistently with this record.

The approval covers execution of WP-0688 through WP-0707 in the manifest dependency order, including only the explicitly approved collision-free parallel groups. It does not authorize Codex or any provider to change architectural authority, bypass internal review gates, merge, deploy, accept work, or make protected institutional decisions.

## Steward protected-action authorization

The Steward authorizes the bounded mechanical execution, communication, checkpointing, retry, recovery, validation, and evidence-recording actions explicitly described by the campaign and its work packages.

The Steward retains all protected authority. The campaign must stop and request a separate decision whenever an action would require merge, deployment, spending, privacy or disclosure approval, staffing authority, architectural approval, engineering acceptance, campaign acceptance, constitutional change, or another protected institutional decision.

This authorization does not permit the Continuous Momentum Engine, Grace, Alfred, Helen, Engineering, Codex, a local worker, or any adapter to infer or manufacture authority beyond an existing canonical delegation.

## Launch identity and drift rule

The recorded base commit is the authorized launch baseline. The campaign charter and manifest activation commits necessarily follow this authorization record. Codex must verify that the activated charter and manifest reference this authorization and that no unrelated repository changes invalidate the package topology, protected boundaries, or launch assumptions.

If the current `main` commit has advanced beyond the activation changes, Codex must compare the intervening commits. It may proceed only when the changes are limited to the WP-0678 acceptance, this G0 authorization, and the corresponding CAMPAIGN-0681 activation updates, or when the Chief Architect records a superseding verified base.

## Effective decision

G0 governance approval is granted. CAMPAIGN-0681 becomes launchable only after:

- the campaign charter status is changed from draft to launch authorized;
- the amendment history references this authorization;
- the execution manifest status is changed to launch authorized;
- the manifest records the verified base commit and authority references; and
- Codex independently verifies the resulting repository state and package paths.

No automatic merge, deployment, work-package acceptance, campaign acceptance, or protected decision is authorized.