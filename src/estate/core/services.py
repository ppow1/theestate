from estate.core.registry import load_registry

def list_services():
    return load_registry("services")

def list_capabilities():
    return load_registry("capabilities")

def list_providers():
    return load_registry("providers")
