from __future__ import annotations

from estate.core.planning_provider import PlanningProvider, StubPlanningProvider


class PlanningProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, PlanningProvider] = {}

    def register(self, provider: PlanningProvider) -> None:
        self._providers[provider.provider_id] = provider

    def resolve(self, provider_id: str) -> PlanningProvider:
        try:
            return self._providers[provider_id]
        except KeyError as exc:
            raise KeyError(f"planning provider '{provider_id}' is not registered") from exc

    def list_provider_ids(self) -> list[str]:
        return sorted(self._providers)


def default_planning_provider_registry() -> PlanningProviderRegistry:
    registry = PlanningProviderRegistry()
    registry.register(StubPlanningProvider())
    return registry
