"""WP-4222 staged, read-only dashboard integration."""

from .integration import IntegrationError, ProviderRegistry, compose_dashboard, load_manifest

__all__ = ["IntegrationError", "ProviderRegistry", "compose_dashboard", "load_manifest"]
