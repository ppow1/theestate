# WP-0205 Mission Control, Projects, and Roadmap Controls

WP-0200 staged vocabulary available and used: action classes, authority classes, confirmation requirements, local-only posture, read/write artifacts, command hooks, output paths, failure behavior, and disabled/prohibited semantics.

Safety rules: summary surfaces are never sources of truth; warnings become drafts only; requests are not approvals; notes do not change canonical status; refresh reports paths; copy controls do not execute.

## Controls
- **Mission Control / Refresh Mission Control payload** (`mission.refresh_payload`): Confirmed local refresh with output paths. Authority: safe local generated-artifact update. Confirmation: explicit Steward confirmation. Local only. Mission summaries remain non-authoritative.
- **Mission Control / Inspect source lane** (`mission.inspect_source_lane`): Read source artifacts behind lane or warning. Authority: safe read-only. Confirmation: none. Local only. Mission summaries remain non-authoritative.
- **Mission Control / Open source artifact** (`mission.open_source_artifact`): Show local path/link for source. Authority: safe read-only. Confirmation: none. Local only. Source artifact is authoritative, summary is not.
- **Mission Control / Create follow-up draft from warning** (`mission.warning_to_draft`): Draft proposal/observation only. Authority: Steward-confirmed local mutation. Confirmation: explicit Steward confirmation. Local only. Draft is not executable work.
- **Mission Control / Request Chief Architect review** (`mission.request_ca_review`): Draft or queue review request. Authority: authority-gated institutional action. Confirmation: authority route confirmation. Local only. Request is not review completion.
- **Projects / Inspect active project/work package** (`projects.inspect_active`): Open pending/completion/source artifacts. Authority: safe read-only. Confirmation: none. Local only. Projects summary remains non-authoritative.
- **Projects / Open dependency evidence** (`projects.open_dependency_evidence`): Inspect graph/pipeline evidence. Authority: safe read-only. Confirmation: none. Local only. Dependency summary is not approval.
- **Projects / Copy next-action command** (`projects.copy_next_action`): Copy known next command only. Authority: safe read-only. Confirmation: none. Local only. Copied command does not execute.
- **Projects / Create blocker note draft** (`projects.create_blocker_note`): Draft local blocker note only. Authority: Steward-confirmed local mutation. Confirmation: explicit Steward confirmation. Local only. Does not change canonical status.
- **Projects / Request review or prioritization** (`projects.request_prioritization`): Authority-gated request, not approval. Authority: authority-gated institutional action. Confirmation: authority route confirmation. Local only. Request is not approval.
- **Roadmap / Inspect roadmap evidence** (`roadmap.inspect_evidence`): Read roadmap source evidence. Authority: safe read-only. Confirmation: none. Local only. Roadmap summary remains non-authoritative.
- **Roadmap / Draft work-package proposal from roadmap item** (`roadmap.draft_wp_proposal`): Draft proposal only. Authority: Steward-confirmed local mutation. Confirmation: explicit Steward confirmation. Local only. Proposal grants no execution authority.
- **Roadmap / Export roadmap snapshot** (`roadmap.export_snapshot`): Local snapshot export. Authority: safe local generated-artifact update. Confirmation: explicit confirmation. Local only. Snapshot is non-authoritative.
- **Roadmap / Request prioritization review** (`roadmap.request_prioritization_review`): Authority-gated prioritization request. Authority: authority-gated institutional action. Confirmation: authority route confirmation. Local only. Request is not prioritization decision.
- **Roadmap / Mark local review note** (`roadmap.mark_local_review_note`): Local UI/runtime marker only. Authority: Steward-confirmed local mutation. Confirmation: explicit Steward confirmation. Local only. Not canonical roadmap closure.
