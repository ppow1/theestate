# Open WebUI registration contract

The installed Open WebUI is version 0.10.2. Its supported mechanism is the persisted `Tool` model loaded through `open_webui.utils.plugin.load_tool_module_by_id`, with model associations in `model.info.meta.toolIds`. The grounding policy uses a persisted `Function` of type `filter`, associated through `model.info.meta.filterIds`.

The deployment script uses the Open WebUI model layer to create or update both records, is safe to rerun, and does not write runtime state. The bridge Tool is associated only with `estate/grace`; other resident models receive neither ID.

The Tool receives Open WebUI's authenticated `__user__` context and propagates its subject as the `sub` claim with the fixed Grace read office, exact issuer, active boolean, and bridge authority source.
