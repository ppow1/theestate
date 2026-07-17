# CAMPAIGN-0681 — WP-0691 Repair and Superseding Launch Authorization

Status: Authorized  
Campaign: CAMPAIGN-0681 — Estate Operationalization  
Authorizing office: Chief Architect  
Authorization timestamp: 2026-07-17T11:39:11-04:00  
Repository: ppow1/theestate  
Base branch: main  
Campaign branch: campaign/0681-estate-operationalization

## Purpose

This record resolves the launch blocker caused by the truncated canonical WP-0691 artifact and explicitly authorizes CAMPAIGN-0681 to relaunch from the repaired baseline identified below.

## Repaired Baseline

Pre-repair base commit: $preRepairHead

WP-0691 repair commit: $repairCommit

The repair commit restores the complete authoritative specification for collaboration/work_packages/pending/WP-0691_Resident_and_Service_Health_Signal_Integration.md.

## Authorization

The authorizing office explicitly:

1. accepts the restored WP-0691 specification as the authoritative CAMPAIGN-0681 package definition;
2. supersedes any prior CAMPAIGN-0681 launch baseline that predates the repair commit;
3. authorizes creation or use of only $CampaignBranch from the commit containing this authorization record;
4. permits execution of WP-0688 through WP-0707 only in manifest dependency order and under all existing campaign gates;
5. preserves every protected stop concerning merge, deployment, acceptance, closure, staffing, budget, privacy, architecture, disclosure, and Steward authority;
6. does not authorize automatic merge, deployment, protected acceptance, campaign closure, spending, staffing, or disclosure.

The commit containing this authorization may be used as the campaign launch base because its only change beyond $repairCommit is this explicit authorization record.

## Required Launch Behavior

Codex must repeat full prerequisite verification before creating the campaign branch.

Any remaining missing, contradictory, stale, truncated, or unresolved authoritative artifact remains blocking.

CAMPAIGN-0681 must finish at awaiting protected review and acceptance. It must not merge.