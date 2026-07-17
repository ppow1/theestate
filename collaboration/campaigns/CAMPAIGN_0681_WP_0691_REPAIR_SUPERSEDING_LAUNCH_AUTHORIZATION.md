# CAMPAIGN-0681 — Canonical Artifact Repair and Superseding Launch Authorization

Status: Authorized
Campaign: CAMPAIGN-0681 — Estate Operationalization
Authorizing office: Chief Architect
Authorization timestamp: 2026-07-17T12:59:27-04:00
Repository: ppow1/theestate
Base branch: main
Authorized campaign branch: campaign/0681-estate-operationalization

## Purpose

This authorization supersedes every earlier CAMPAIGN-0681 launch authorization that predates the completed canonical artifact repairs.

The earlier launch baseline was blocked because required canonical documents were truncated or incomplete.

## Verified Repaired Baseline

WP-0691 canonical repair commit:

c7be2c612bd229b1c732055dea098933beb9a689

Practical Worker Onboarding Addendum repair commit:

ded5417e9030d8e9ded5d7993a72718b8ed48830

The Practical Worker Onboarding Addendum was restored from its original historical canonical source commit:

69fd1debe5fe35437d418dbc9a221f7960b0eb5b

The repaired base branch is:

main

The repaired base commit immediately preceding this authorization is:

ded5417e9030d8e9ded5d7993a72718b8ed48830

## Superseding Authorization

The Chief Architect explicitly:

1. accepts the restored WP-0691 specification as canonical;
2. accepts the restored Practical Worker Onboarding Addendum as canonical;
3. supersedes all earlier CAMPAIGN-0681 launch authorizations that predate this record;
4. authorizes creation or continued use only of branch campaign/0681-estate-operationalization;
5. authorizes execution of WP-0688 through WP-0707 in manifest dependency and gate order;
6. requires one bounded implementation commit per work package;
7. requires validation evidence and completion receipts for every package;
8. requires Codex to stop at all protected review and acceptance gates;
9. does not authorize automatic merge;
10. does not authorize deployment;
11. does not authorize protected acceptance or campaign closure;
12. does not authorize spending, staffing, disclosure, or architectural redesign beyond the campaign mandate.

The commit containing this authorization becomes the sole authorized launch baseline for CAMPAIGN-0681.

## Required Codex Preflight

Before creating or switching to the campaign branch, Codex must:

1. verify repository identity is ppow1/theestate;
2. verify the working tree is clean;
3. verify local main matches origin/main;
4. verify HEAD is the commit containing this authorization;
5. read AI_START_HERE.md;
6. read AI_HINTS.md;
7. read the complete CAMPAIGN-0681 handoff, manifest, namespace resolution, and authorization records;
8. verify WP-0691 is complete;
9. verify the Practical Worker Onboarding Addendum contains 198 lines and is not truncated;
10. verify every exact manifest-listed work-package path exists;
11. use only campaign/0681-estate-operationalization;
12. stop on any demonstrated contradiction, truncation, missing requirement, or protected gate.

## Execution Boundary

Codex may implement the authorized campaign work and open the campaign pull request at the required review boundary.

Codex may not merge that pull request or represent protected acceptance as granted.
