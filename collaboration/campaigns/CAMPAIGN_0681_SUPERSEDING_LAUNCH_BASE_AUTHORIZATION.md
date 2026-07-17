# CAMPAIGN-0681 — Superseding Launch-Base Authorization

Status: Authorized for launch  
Campaign: CAMPAIGN-0681 — Estate Operationalization  
Authorization date: 2026-07-17  
Repository: `ppow1/theestate`  
Base branch: `main`  
Superseding verified base commit: `3c212df1ea957883a25c9cd4618fc7babc7e9be0`

## Chief Architect determination

The Chief Architect has reviewed the repository history from the previously recorded G0 base commit `a182c5586558a361876bebe24698e7c666043323` through `3c212df1ea957883a25c9cd4618fc7babc7e9be0`.

The intervening changes are approved CAMPAIGN-0681 activation, authority-record, charter-reconciliation, namespace-resolution, and execution-manifest restoration changes. They do not constitute campaign implementation work and do not invalidate the approved package topology, protected boundaries, or launch assumptions.

Commit `3c212df1ea957883a25c9cd4618fc7babc7e9be0` is therefore the exact superseding human-authorized launch base for CAMPAIGN-0681.

## Baseline reconciliation

The following earlier values are historical and no longer control campaign launch:

- Original G0 verified base: `a182c5586558a361876bebe24698e7c666043323`
- Manifest reconciliation ancestor: `4b4cdad294bd290ffc9a75d99bd91aec98a15c4d`

The manifest ancestor remains valid for ancestry verification, but it is not the final human launch authorization. This record supplies that final authority at `3c212df1ea957883a25c9cd4618fc7babc7e9be0`.

## Authorization-record descendant rule

The commit that adds this authorization record necessarily follows the superseding verified base. Codex may launch from the repository commit containing this record, or from a later descendant, only when all changes after `3c212df1ea957883a25c9cd4618fc7babc7e9be0` are limited to this authorization record and corresponding non-implementation authority-reference updates.

Any unrelated repository change after the superseding base requires a new comparison and, when it affects launch assumptions, another explicit authorization.

## Steward confirmation

The Steward confirms the previously granted bounded-action authorization remains effective for CAMPAIGN-0681 at this superseding launch base. The campaign may perform only the mechanical execution, communication, checkpointing, retry, recovery, validation, and evidence-recording actions explicitly described by the campaign and its work packages.

All protected authority remains retained. The campaign must stop for merge, deployment, spending, privacy or disclosure approval, staffing authority, architectural approval, engineering acceptance, campaign acceptance, constitutional change, or any other protected institutional decision.

## Effective decision

CAMPAIGN-0681 is authorized to create or use only `campaign/0681-estate-operationalization` from the superseding launch base, subject to the authorization-record descendant rule above.

The local Codex checkout alias `work`, absence of a local `main` branch, and absence of a configured remote are not blockers when:

1. the checkout commit is the authorized base or an allowed authority-record-only descendant;
2. the working tree is clean;
3. the manifest parses successfully;
4. all package and authority paths exist; and
5. the campaign branch has not been created from an unverified commit.

No automatic merge, deployment, work-package acceptance, campaign acceptance, spending, staffing, disclosure, campaign closure, or other protected decision is authorized.