"""Staged Work Packages action definitions for WP-0202. Proposed only."""

PROHIBITED_BEHAVIOR = "execute_pending_work_package"


def action_is_non_executing(action):
    return action.get("does_not_execute_pending_work_packages") and action.get("command_hook_or_handler_reference") != PROHIBITED_BEHAVIOR
