"""Install/update the WP-4233 Open WebUI Tool through Open WebUI's own model layer.

Run with A:\\AI\\OpenWebUI\\.venv\\Scripts\\python.exe while Open WebUI is stopped
or use the HTTP API installer in the deployment runbook. This script never edits
runtime persistence and never registers a mutation operation.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

GRACE_MODEL_ID = "estate/grace-grounded-test"
GRACE_TOOL_ID = "grace_runtime_bridge"
GRACE_FILTER_ID = "grace_runtime_grounding"


def merge_grace_bridge_metadata(meta: dict | None) -> dict:
    """Return model metadata with the Grace bridge associations preserved."""
    merged = dict(meta or {})
    tool_ids = list(merged.get("toolIds") or [])
    filter_ids = list(merged.get("filterIds") or [])
    if GRACE_TOOL_ID not in tool_ids:
        tool_ids.append(GRACE_TOOL_ID)
    if GRACE_FILTER_ID not in filter_ids:
        filter_ids.append(GRACE_FILTER_ID)
    merged["toolIds"] = tool_ids
    merged["filterIds"] = filter_ids
    return merged


async def install(source: str | Path) -> dict:
    from open_webui.models.functions import FunctionForm, FunctionMeta, Functions
    from open_webui.models.tools import ToolForm, ToolMeta, Tools
    from open_webui.models.users import Users
    from open_webui.utils.plugin import load_tool_module_by_id
    from open_webui.utils.tools import get_tool_specs

    content = Path(source).read_text(encoding="utf-8")
    tool_id = GRACE_TOOL_ID
    module, _ = await load_tool_module_by_id(tool_id, content=content)
    specs = get_tool_specs(module)
    user = await Users.get_first_user()
    if user is None:
        raise RuntimeError("Open WebUI has no administrator user")
    form = ToolForm(id=tool_id, name="Grace authoritative runtime bridge", content=content,
                    meta=ToolMeta(description="Read-only Grace Momentum runtime operations"))
    existing = await Tools.get_tool_by_id(tool_id)
    if existing is None:
        result = await Tools.insert_new_tool(user.id, form, specs)
        action = "created"
    else:
        result = await Tools.update_tool_by_id(tool_id, {"name": form.name, "content": content, "specs": specs, "meta": form.meta.model_dump()})
        action = "updated"
    return {"action": action, "tool_id": tool_id, "operation_count": len(specs), "operations": [s["name"] for s in specs], "user_id": user.id, "result": result.model_dump() if result else None}


async def install_grounding_filter(source: str | Path) -> dict:
    from open_webui.models.functions import FunctionForm, FunctionMeta, Functions
    from open_webui.models.users import Users
    from open_webui.utils.plugin import load_function_module_by_id

    content = Path(source).read_text(encoding="utf-8")
    function_id = GRACE_FILTER_ID
    module, function_type, frontmatter = await load_function_module_by_id(function_id, content=content)
    user = await Users.get_first_user()
    if user is None:
        raise RuntimeError("Open WebUI has no administrator user")
    form = FunctionForm(id=function_id, name="Grace runtime grounding policy", content=content,
                        meta=FunctionMeta(description="Prevents ungrounded operational claims in the Grace model", manifest=frontmatter))
    existing = await Functions.get_function_by_id(function_id)
    if existing is None:
        result = await Functions.insert_new_function(user.id, function_type, form)
        action = "created"
    else:
        result = await Functions.update_function_by_id(function_id, {"name": form.name, "content": content, "meta": form.meta.model_dump(), "is_active": True, "is_global": False})
        action = "updated"
    if result is not None and action == "created":
        result = await Functions.update_function_by_id(function_id, {"is_active": True, "is_global": False})
    return {"action": action, "function_id": function_id, "type": function_type, "active": True, "global": False, "user_id": user.id, "result": result.model_dump() if result else None}


async def associate_grace_model(model_id: str = GRACE_MODEL_ID) -> dict:
    """Bind the persisted bridge and filter to the selected Grace custom model."""
    from open_webui.models.models import ModelForm, ModelMeta, Models

    model = await Models.get_model_by_id(model_id)
    if model is None:
        raise RuntimeError(f"Open WebUI model not found: {model_id}")
    if model.base_model_id not in {"estate/grace", model_id}:
        raise RuntimeError(
            f"Open WebUI model {model_id} is not backed by estate/grace: "
            f"{model.base_model_id!r}"
        )
    metadata = merge_grace_bridge_metadata(model.meta.model_dump())
    updated = await Models.update_model_by_id(
        model_id,
        ModelForm(
            id=model.id,
            base_model_id=model.base_model_id,
            name=model.name,
            params=model.params,
            meta=ModelMeta(**metadata),
            is_active=model.is_active,
        ),
    )
    return {
        "action": "associated",
        "model_id": model_id,
        "base_model_id": model.base_model_id,
        "tool_ids": metadata["toolIds"],
        "filter_ids": metadata["filterIds"],
        "updated": updated is not None,
    }


if __name__ == "__main__":
    import json
    root = Path(__file__).parents[1]
    print(json.dumps(asyncio.run(install(root / "deploy" / "openwebui" / "tools" / "grace_runtime_bridge.py")), indent=2, default=str))
    print(json.dumps(asyncio.run(install_grounding_filter(root / "deploy" / "openwebui" / "functions" / "grace_runtime_grounding.py")), indent=2, default=str))
    print(json.dumps(asyncio.run(associate_grace_model()), indent=2, default=str))
