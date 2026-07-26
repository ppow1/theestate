"""WP-4221 deterministic, advisory dashboard projection."""

from .projection import DashboardError, build_snapshot, operator_summary, validate_snapshot

__all__ = ["DashboardError", "build_snapshot", "operator_summary", "validate_snapshot"]
