import json
from estate.core.registry import load_registry, save_registry
from estate.core.discovery import observe_ai_environment
from estate.core.ledger import create_change

def next_provider_id(providers):
    nums = []
    for provider in providers:
        pid = provider.get("id", "")
        if pid.startswith("PRV-"):
            try:
                nums.append(int(pid.split("-")[1]))
            except Exception:
                pass
    return f"PRV-{(max(nums) + 1 if nums else 1):06d}"

def sync_ollama_providers():
    observations, obs_path = observe_ai_environment()
    models = observations.get("ollama", {}).get("models", [])

    providers = load_registry("providers")
    existing_names = {p.get("name") for p in providers}
    created = []

    for model in models:
        provider_name = f"Ollama {model['name']}"
        if provider_name in existing_names:
            continue

        provider = {
            "id": next_provider_id(providers),
            "name": provider_name,
            "service": "Reasoning Service",
            "capability": "CAP-000007",
            "status": "Observed",
            "location": "Ollama local runtime",
            "policy": "Observed local Ollama model. Pending formal routing policy.",
            "observed_from": str(obs_path),
            "model": model
        }
        providers.append(provider)
        existing_names.add(provider_name)
        created.append(provider)

    save_registry("providers", providers)

    summary = "No new Ollama model providers were found during sync."
    if created:
        summary = "Synced observed Ollama models into provider registry:
" + "
".join(
            f"- {p['id']} {p['name']}" for p in created
        )

    ec_id = create_change(
        title="Synced observed Ollama model providers",
        summary=summary
    )

    return created, ec_id
