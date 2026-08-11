"""Read-only access to the Estate's approved Codex seat mapping."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from estate.core.codex_bridge import CODEX_SEAT_HOMES


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
                # No authenticated browser identities are currently proven by Estate records.
                "interactive_chrome_profile": None,
                "automation_chromium_profile": None,
            }
        )
    if seat_id is not None and not seats:
        raise ValueError(f"unknown Codex seat: {seat_id}")
    return {"version": 1, "read_only": True, "seats": seats}
