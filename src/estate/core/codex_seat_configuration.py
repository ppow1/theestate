"""Read-only access to the Estate's approved Codex seat mapping."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from estate.core.codex_bridge import CODEX_SEAT_HOMES

CODEX_AUTOMATION_CHROMIUM_ROOT = Path(
    "A:/AI/Tools/EstateStreamDeckPlugin/runtime/codex-desk-chromium-profiles"
)


def codex_seat_configuration(seat_id: str | None = None) -> dict[str, Any]:
    """Return approved seat homes and non-secret browser identity mappings."""
    seats = []
    for logical_seat, home in CODEX_SEAT_HOMES.items():
        if seat_id is not None and logical_seat != seat_id:
            continue
        seats.append(
            {
                "seat_id": logical_seat,
                "codex_home": str(Path(home)),
                "execution_surface": "codex-cli",
                # Proven Patricia interactive Chrome identities; names only, no auth state.
                "interactive_chrome_profile": {
                    "C1": "Profile 3",
                    "C2": "Profile 4",
                    "C3": "Profile 5",
                }[logical_seat],
                "automation_chromium_profile": str(
                    CODEX_AUTOMATION_CHROMIUM_ROOT / logical_seat
                ),
            }
        )
    if seat_id is not None and not seats:
        raise ValueError(f"unknown Codex seat: {seat_id}")
    return {"version": 1, "read_only": True, "seats": seats}
