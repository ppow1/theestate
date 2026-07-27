"""Deterministic, read-only engineering campaign recommendations."""

from .engine import RecommendationError, compare, explain, recommend, validate_inputs

__all__ = ["RecommendationError", "compare", "explain", "recommend", "validate_inputs"]
