# WP-0206 Mailboxes, Recalls, and Notifications Controls

WP-0200 staged vocabulary available and used: action classes, authority classes, confirmation requirements, local-only posture, read/write artifacts, command hooks, output paths, failure behavior, and disabled/prohibited semantics.

Safety rules: local acknowledgement is not source closure; drafts are not sent; route requests are not completions; recall acknowledgement is not decision; bulk actions need affected-item summaries and second confirmation; no destructive deletion controls exist.

## Controls
- **Mailboxes / Open mailbox** (`mailboxes.open_mailbox`): Inspect mailbox index/source artifacts. Authority: safe read-only. Confirmation: none. Local only. Local view is not source closure.
- **Mailboxes / Inspect message** (`mailboxes.inspect_message`): Read content/status/source/waiting state. Authority: safe read-only. Confirmation: none. Local only. Inspection is not acknowledgement.
- **Mailboxes / Draft reply** (`mailboxes.draft_reply`): Preview reply draft only. Authority: Steward-confirmed local mutation. Confirmation: explicit Steward confirmation. Local only. Draft is not sent reply.
- **Mailboxes / Local acknowledge** (`mailboxes.local_acknowledge`): Local acknowledgement marker where supported. Authority: Steward-confirmed local mutation. Confirmation: explicit Steward confirmation. Local only. Local acknowledgement is not authoritative closure.
- **Mailboxes / Route to resident or review queue** (`mailboxes.route_to_resident`): Draft/queue authority route request. Authority: authority-gated institutional action. Confirmation: authority route confirmation. Local only. Route request is not completion.
- **Mailboxes / Export mailbox snapshot** (`mailboxes.export_snapshot`): Local-only snapshot with sensitivity warning. Authority: safe local generated-artifact update. Confirmation: explicit confirmation. Local only. Export is local-only.
- **Recalls / Inspect recall** (`recalls.inspect_recall`): Read recall lifecycle/transport/ack/source links. Authority: safe read-only. Confirmation: none. Local only. Inspection is not decision.
- **Recalls / Copy delivery command** (`recalls.copy_delivery_command`): Copy local delivery command only. Authority: safe read-only. Confirmation: none. Local only. Copied command does not execute.
- **Recalls / Local acknowledge recall** (`recalls.local_acknowledge`): Local ack where supported. Authority: Steward-confirmed local mutation. Confirmation: explicit Steward confirmation. Local only. Acknowledgement is not recall decision.
- **Recalls / Request Steward decision** (`recalls.request_steward_decision`): Draft/queue decision request. Authority: authority-gated institutional action. Confirmation: authority route confirmation. Local only. Request is not decision.
- **Recalls / Export recall audit bundle** (`recalls.export_audit_bundle`): Local audit bundle with sensitivity warning. Authority: safe local generated-artifact update. Confirmation: explicit confirmation. Local only. Bundle is local-only.
- **Notifications / Filter notifications** (`notifications.filter`): Filter current notifications. Authority: safe read-only. Confirmation: none. Local only. Filter state is local view only.
- **Notifications / Inspect notification source** (`notifications.inspect_source`): Open source artifact/report. Authority: safe read-only. Confirmation: none. Local only. Inspection is not acknowledgement.
- **Notifications / Local acknowledge notification** (`notifications.local_acknowledge`): Local acknowledgement marker. Authority: Steward-confirmed local mutation. Confirmation: explicit Steward confirmation. Local only. Local ack is not authoritative closure.
- **Notifications / Bulk local acknowledge low severity** (`notifications.bulk_local_ack_low`): Second-confirmation bulk local ack design. Authority: Steward-confirmed local mutation. Confirmation: second confirmation plus affected-item summary. Local only. Bulk local ack is reversible local state only.
- **Notifications / Create follow-up draft** (`notifications.create_follow_up_draft`): Draft WP/observation/reply/review request. Authority: Steward-confirmed local mutation or authority-gated route. Confirmation: confirmation based on target. Local only. Draft/request is not completed action.
