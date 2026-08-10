"""Installed staged Office action registry foundation for WP-0200.

This file is proposed code only. It is not imported by active runtime until a future install-handoff.
"""
from dataclasses import dataclass, field
from enum import Enum


class AuthorityClass(str, Enum):
    SAFE_READ_ONLY = "safe_read_only"
    SAFE_LOCAL_GENERATED_ARTIFACT_UPDATE = "safe_local_generated_artifact_update"
    STEWARD_CONFIRMED_LOCAL_MUTATION = "steward_confirmed_local_mutation"
    AUTHORITY_GATED_INSTITUTIONAL_ACTION = "authority_gated_institutional_action"
    PROHIBITED_UNTIL_FUTURE_GOVERNANCE = "prohibited_until_future_governance"


class ConfirmationRequirement(str, Enum):
    NONE = "none"
    CONFIRM_GENERATED_ARTIFACT = "confirm_generated_artifact"
    PREVIEW_BEFORE_WRITE = "preview_before_write"
    EXPLICIT_AUTHORITY_ROUTE = "explicit_authority_route"
    UNAVAILABLE_WITH_REASON = "unavailable_with_reason"


class HookMode(str, Enum):
    COPY_ONLY = "copy_only"
    EXECUTABLE_AFTER_FUTURE_AUTHORITY = "executable_after_future_authority"
    HANDLER_REFERENCE_ONLY = "handler_reference_only"


@dataclass(frozen=True)
class CommandHook:
    hook_id: str
    command_text: str = ""
    mode: HookMode = HookMode.COPY_ONLY
    execution_allowed: bool = False
    expected_outputs: tuple[str, ...] = ()
    working_directory: str = "repository root"
    environment: tuple[str, ...] = ("PYTHONPATH=src",)
    timeout_seconds: int = 120
    failure_behavior: str = "show stderr/stdout and do not mutate institutional state"


@dataclass(frozen=True)
class OfficeAction:
    action_id: str
    label: str
    target_tab: str
    description: str
    action_class: str
    authority_class: AuthorityClass
    confirmation: ConfirmationRequirement
    local_only: bool = True
    reads_artifacts: tuple[str, ...] = ()
    writes_artifacts: tuple[str, ...] = ()
    command_hook: CommandHook | None = None
    expected_output_paths: tuple[str, ...] = ()
    validation_command: str | None = None
    failure_behavior: str = "fail closed; report error; preserve source artifacts"
    audit_logging: str = "record action id, actor, confirmation, command hook, and output paths in local audit artifact when installed"
    disabled_reason: str | None = None

    def __post_init__(self):
        if self.authority_class in {AuthorityClass.AUTHORITY_GATED_INSTITUTIONAL_ACTION, AuthorityClass.PROHIBITED_UNTIL_FUTURE_GOVERNANCE} and self.confirmation == ConfirmationRequirement.NONE:
            raise ValueError("authority-gated and prohibited actions cannot be no-confirmation actions")
        if self.authority_class == AuthorityClass.SAFE_READ_ONLY and self.writes_artifacts:
            raise ValueError("safe read-only actions cannot declare writes_artifacts")
        if self.command_hook and self.command_hook.execution_allowed and self.command_hook.mode == HookMode.COPY_ONLY:
            raise ValueError("copy-only command hooks cannot be executable")


def bulk_confirmation_summary(actions: list[OfficeAction]) -> dict:
    return {
        "action_count": len(actions),
        "authority_classes": sorted({a.authority_class.value for a in actions}),
        "writes_artifacts": sorted({p for a in actions for p in a.writes_artifacts}),
        "expected_output_paths": sorted({p for a in actions for p in a.expected_output_paths}),
        "requires_authority_route": any(a.confirmation == ConfirmationRequirement.EXPLICIT_AUTHORITY_ROUTE for a in actions),
    }


SAMPLE_ACTIONS = [
    OfficeAction("office.snapshot.inspect", "Inspect Office snapshot schema", "home", "Read rendered snapshot manifest metadata.", "inspect", AuthorityClass.SAFE_READ_ONLY, ConfirmationRequirement.NONE, reads_artifacts=("runtime/steward/command_center.html",)),
    OfficeAction("office.snapshot.export", "Export Office snapshot", "home", "Generate a local browser ZIP snapshot with sensitivity warning.", "export", AuthorityClass.SAFE_LOCAL_GENERATED_ARTIFACT_UPDATE, ConfirmationRequirement.CONFIRM_GENERATED_ARTIFACT, writes_artifacts=("browser download: office-snapshot.zip",), expected_output_paths=("browser download: office-snapshot.zip",)),
    OfficeAction("office.layout.save", "Save active workspace profile", "settings", "Preview and write a local workspace preference.", "local_mutation", AuthorityClass.STEWARD_CONFIRMED_LOCAL_MUTATION, ConfirmationRequirement.PREVIEW_BEFORE_WRITE, writes_artifacts=("runtime/steward/operations_center_settings.json",)),
    OfficeAction("office.review.request", "Request CA review", "work-packages", "Route a review request without marking review complete.", "request_review", AuthorityClass.AUTHORITY_GATED_INSTITUTIONAL_ACTION, ConfirmationRequirement.EXPLICIT_AUTHORITY_ROUTE),
    OfficeAction("office.package.execute", "Execute pending work package", "work-packages", "Unavailable until future governance/tooling exists.", "execute", AuthorityClass.PROHIBITED_UNTIL_FUTURE_GOVERNANCE, ConfirmationRequirement.UNAVAILABLE_WITH_REASON, disabled_reason="Pending work package execution is explicitly prohibited from Office Wave 1."),
    OfficeAction("office.validation.copy_command", "Copy validation command", "validation", "Copy validation command text; do not execute.", "copy_command", AuthorityClass.SAFE_READ_ONLY, ConfirmationRequirement.NONE, command_hook=CommandHook("copy.validation", "PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json")),
    OfficeAction("office.attention.briefing", "Generate Steward attention briefing", "attention", "Ask Alfred to aggregate attention and render an on-demand briefing without becoming the event bus.", "generate_briefing", AuthorityClass.SAFE_LOCAL_GENERATED_ARTIFACT_UPDATE, ConfirmationRequirement.CONFIRM_GENERATED_ARTIFACT, writes_artifacts=("runtime/office/steward_attention_items.json", "runtime/office/steward_attention_briefing.json", "operations/briefings/steward_attention_briefing.md"), command_hook=CommandHook("attention.briefing", "PYTHONPATH=src python -m estate.cli.main steward-attention briefing --kind on_demand --json", mode=HookMode.HANDLER_REFERENCE_ONLY, expected_outputs=("runtime/office/steward_attention_briefing.json",)), expected_output_paths=("runtime/office/steward_attention_briefing.json", "operations/briefings/steward_attention_briefing.md")),
    OfficeAction("office.attention.action", "Persist attention item action", "attention", "Record snooze, acknowledge, delegate, dismiss, or resolve for an attention item through the existing Office action transport.", "attention_action", AuthorityClass.STEWARD_CONFIRMED_LOCAL_MUTATION, ConfirmationRequirement.PREVIEW_BEFORE_WRITE, writes_artifacts=("runtime/office/steward_attention_actions.json", "runtime/office/steward_attention_items.json"), command_hook=CommandHook("attention.action", "PYTHONPATH=src python -m estate.cli.main steward-attention action --item-id <id> --action acknowledge --json", mode=HookMode.HANDLER_REFERENCE_ONLY, expected_outputs=("runtime/office/steward_attention_actions.json",)), expected_output_paths=("runtime/office/steward_attention_actions.json",)),
    OfficeAction("office.attention.acknowledge", "Acknowledge Steward attention in Office", "attention", "Use the canonical Steward attention action mechanism and refresh the visual annunciator projection.", "attention_action", AuthorityClass.STEWARD_CONFIRMED_LOCAL_MUTATION, ConfirmationRequirement.PREVIEW_BEFORE_WRITE, writes_artifacts=("runtime/office/steward_attention_actions.json", "runtime/office/steward_attention_items.json", "runtime/office/steward_annunciator.json"), command_hook=CommandHook("attention.acknowledge", "Office action endpoint: attention.acknowledge", mode=HookMode.HANDLER_REFERENCE_ONLY, expected_outputs=("runtime/office/steward_annunciator.json",)), expected_output_paths=("runtime/office/steward_annunciator.json",)),
]
