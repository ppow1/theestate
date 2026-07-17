# CAMPAIGN-0681 — Canonical Repair and Superseding Launch Authorization

Status: Authorized
Campaign: CAMPAIGN-0681 — Estate Operationalization
Authorizing office: Chief Architect
Authorization timestamp: 2026-07-17T15:11:37-04:00
Repository: ppow1/theestate
Base branch: main
Authorized campaign branch: campaign/0681-estate-operationalization

## Superseding Baseline

Previous repaired launch baseline:

fadea83d678bb50c30cacd62aa12f5c6010b8e02

Additional canonical repair commit:

92b0932afed51bbd570f22cb109548656e545fb4

The additional repair:

1. supplies executable package-specific validation commands for WP-0688
   through WP-0690 and WP-0692 through WP-0707;
2. preserves the manifest rule that missing validation commands are blocking;
3. updates the manifest to reference this superseding authorization lineage;
4. explicitly authorizes bounded reuse of integrated CAMPAIGN-0670 artifacts;
5. explicitly preserves CAMPAIGN-0670's unaccepted status;
6. corrects WP-0688 language so acceptance is not inferred.

## CAMPAIGN-0670 Boundary

CAMPAIGN-0670 is not accepted by this authorization.

CAMPAIGN-0681 may use only the bounded artifact-reuse authority recorded in:

collaboration/campaigns/CAMPAIGN_0681_CAMPAIGN_0670_BOUNDED_REUSE_AUTHORIZATION.md

Any activity requiring CAMPAIGN-0670 protected acceptance remains blocked.

## Execution Authorization

Codex is authorized to launch CAMPAIGN-0681 from a clean descendant of:

92b0932afed51bbd570f22cb109548656e545fb4

Codex must use only:

campaign/0681-estate-operationalization

Codex must:

1. repeat full preflight;
2. verify every manifest package has an executable validation-command section;
3. execute every package's listed validation command;
4. run and record affected-subsystem tests;
5. preserve exact command output in each completion receipt;
6. execute WP-0688, WP-0689, and WP-0690 as bounded commits;
7. stop at protected gate G1;
8. not infer CAMPAIGN-0670 acceptance;
9. not merge, deploy, accept, close, spend, staff, or disclose automatically.

The commit containing this authorization is the current authorized launch commit.
