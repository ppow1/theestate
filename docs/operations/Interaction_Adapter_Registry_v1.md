# Interaction Adapter Registry v1

## Purpose

The Interaction Adapter Registry is the Estate's local-first catalog for UI, voice, notification, conversation, command palette, and activity-console integration points. Its purpose is to let interaction surfaces discover registered adapters without hard-coding provider assumptions.

The registry is intentionally bounded: it describes adapters and their governance boundaries, but it does not implement external providers, store secrets, or create cloud dependencies.

## Registry Artifact

- Canonical registry data: `data/registry/interaction_adapters.json`
- Helper loader: `src/estate/core/interaction_adapters.py`

Each adapter entry includes:

- `adapter_id`
- `display_name`
- `adapter_type`
- `status`
- `local_first`
- `provider`
- `configuration_required`
- `secrets_required`
- `authority_boundary`
- `source_of_truth_boundary`
- `related_workspace`
- `notes`

## Initial Adapter Categories

The v1 registry covers these adapter categories:

| Adapter type | Role |
| --- | --- |
| `ui_workspace` | Presents Estate workspace or panel surfaces. |
| `notification_transport` | Delivers notifications without owning routing authority. |
| `voice_stt` | Converts speech to text for local voice workflows. |
| `voice_tts` | Converts text to speech for local voice workflows. |
| `conversation_surface` | Provides resident or character conversation surfaces. |
| `command_palette_command` | Exposes command palette actions or discovery commands. |
| `activity_event_provider` | Supplies activity-console or operations-board event summaries. |

## Behavior Rules

- Adapters are optional unless an existing subsystem explicitly requires them.
- Missing adapters must degrade gracefully. Registry loading returns an `ok: false` result for a missing registry, and lookup helpers return no adapters rather than forcing a hard failure.
- Adapter IDs must be unique. Duplicate IDs are rejected by the helper loader.
- Interaction adapters may display, transport, capture, or summarize interactions, but they may not become the source of truth for institutional records.
- UI and voice adapters must route significant actions back to auditable Estate artifacts through Alfred, mailboxes, work packages, audit artifacts, or other governed Estate services.
- Secrets are never stored in the registry. Any adapter that requires secrets must obtain them from the runtime environment or an approved local secret mechanism outside this artifact.

## Authority and Source-of-Truth Boundaries

Interaction adapters do not bypass Alfred, mailboxes, or governance authority. The registry records two explicit boundaries for every adapter:

1. `authority_boundary` describes what the adapter may do and which governed path must handle authoritative action.
2. `source_of_truth_boundary` describes which Estate artifacts remain canonical when the adapter displays, transports, or captures information.

This keeps interaction surfaces interchangeable while preserving Estate institutional records and auditability.

## Operational Use

Use `load_interaction_adapter_registry()` to load and validate the registry, `get_interaction_adapter()` for a single adapter, and `adapters_by_type()` for category filtering. Callers should treat an absent adapter as an unavailable optional capability unless their subsystem has separately declared it required.
