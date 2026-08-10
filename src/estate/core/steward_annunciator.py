"""Local presentation boundary for the canonical Steward attention aggregate.

This module owns durable presentation bookkeeping only. Attention items and their
actions remain owned by ``steward_attention`` and their source systems.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from estate.core.steward_attention import aggregate_attention

ANNUNCIATOR_SCHEMA_VERSION = "steward_annunciator_state.v1"
ANNUNCIATOR_PATH = Path("runtime/office/steward_annunciator.json")
ACTIONABLE = {"urgent", "decision_required", "attention_soon"}
SEVERITY_RANK = {"urgent": 0, "decision_required": 1, "attention_soon": 2}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def _write(root: Path, payload: dict[str, Any]) -> None:
    path = root / ANNUNCIATOR_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class Presenter(Protocol):
    def announce(self, item: dict[str, Any]) -> None: ...


class WindowsPresenter:
    """Small local adapter: MessageBeep plus Windows System.Speech TTS."""

    def ding(self) -> dict[str, Any]:
        if os.name != "nt":
            raise RuntimeError("WindowsPresenter requires Windows")
        import winsound

        # MessageBeep uses the current interactive user's Windows default sound
        # endpoint; it does not select or estimate a Bluetooth device.
        result = winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        return {"api": "winsound.MessageBeep", "flag": "MB_ICONEXCLAMATION", "returned": result}

    def speak(self, text: str) -> dict[str, Any]:
        if os.name != "nt":
            raise RuntimeError("WindowsPresenter requires Windows")
        env = os.environ.copy()
        env["ESTATE_ANNUNCIATOR_TEXT"] = str(text)
        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$s.Speak($env:ESTATE_ANNUNCIATOR_TEXT)"
        )
        result = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                                check=False, capture_output=True, text=True, env=env)
        if result.returncode:
            raise RuntimeError(f"System.Speech failed ({result.returncode}): {result.stderr.strip()}")
        return {"api": "System.Speech.Synthesis.SpeechSynthesizer.Speak", "returncode": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}

    def announce(self, item: dict[str, Any]) -> None:
        self.ding()
        self.speak(announcement_text(item))


def run_live_test(text: str = "The Estate needs your input on Project 5") -> dict[str, Any]:
    """Run one explicit live ding and one live local TTS call; never used by tests."""
    presenter = WindowsPresenter()
    result: dict[str, Any] = {
        "mode": "LIVE",
        "text": text,
        "process": {"user": os.environ.get("USERNAME"), "session_name": os.environ.get("SESSIONNAME"), "session_id": None},
        "endpoint_policy": "current interactive user's Windows default audio endpoint",
        "endpoint_discovery": "not resolved by the presenter; no endpoint override is made",
        "ding": {"success": False},
        "tts": {"success": False},
    }
    try:
        import ctypes
        result["process"]["session_id"] = ctypes.windll.kernel32.WTSGetActiveConsoleSessionId()
    except Exception:
        pass
    try:
        result["ding"] = {"success": True, **presenter.ding()}
    except Exception as exc:
        result["ding"] = {"success": False, "exception": f"{type(exc).__name__}: {exc}"}
    try:
        result["tts"] = {"success": True, **presenter.speak(text)}
    except Exception as exc:
        result["tts"] = {"success": False, "exception": f"{type(exc).__name__}: {exc}"}
    result["success"] = result["ding"]["success"] and result["tts"]["success"]
    return result


def announcement_text(item: dict[str, Any]) -> str:
    title = str(item.get("title") or "an attention item")
    if title.lower().endswith("needs attention"):
        subject = title[:-len("needs attention")].strip()
        return f"The Estate needs your input on {subject}".rstrip()
    return f"The Estate needs your input on {title}".rstrip()


def _actionable(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [i for i in items if i.get("classification") in ACTIONABLE and i.get("status") == "open"]


def _item_signature(item: dict[str, Any]) -> dict[str, Any]:
    """Capture stable attention state without volatile timestamps or aggregates."""
    return {
        "classification": item.get("classification"),
        "status": item.get("status"),
        "requested_steward_action": item.get("requested_steward_action"),
    }


def _item_signatures(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item["id"]): _item_signature(item) for item in items if item.get("id")}


def _should_announce(previous: dict[str, Any] | None, current: dict[str, Any]) -> bool:
    if current.get("classification") not in ACTIONABLE or current.get("status") != "open":
        return False
    if previous is None:
        return True
    previous_classification = previous.get("classification")
    if previous_classification not in ACTIONABLE:
        return True
    return SEVERITY_RANK[current["classification"]] < SEVERITY_RANK[previous_classification]


def _baseline_state(previous: dict[str, Any], items: list[dict[str, Any]], now: str | None = None) -> dict[str, Any]:
    active = _actionable(items)
    severity = min((i["classification"] for i in active), key=lambda c: SEVERITY_RANK[c], default=None)
    return {
        **previous,
        "schema_version": ANNUNCIATOR_SCHEMA_VERSION,
        "generated_at": now or _now(),
        "consumer_boundary": "presenter-only; canonical attention and Office actions remain authoritative",
        "baseline_established": True,
        "active": bool(active),
        "severity": severity,
        "severity_rank": SEVERITY_RANK.get(severity),
        "severity_label": {"urgent": "URGENT", "decision_required": "DECISION REQUIRED", "attention_soon": "ATTENTION SOON"}.get(severity),
        "items": [{"id": i["id"], "title": i["title"], "summary": i["summary"], "classification": i["classification"], "requested_steward_action": i["requested_steward_action"], "announcement": announcement_text(i)} for i in active],
        "active_item_ids": sorted(i["id"] for i in active),
        "observed_items": _item_signatures(items),
        "pending_presentations": {},
        "last_run": {"new_item_count": 0, "presented_count": 0, "failure_count": 0, "failures": [], "baseline": True},
    }


def establish_startup_baseline(root: str | Path | None = None, *, now: str | None = None) -> dict[str, Any]:
    """Persist current attention as watcher baseline without invoking a presenter."""
    base = Path(root) if root is not None else Path.cwd()
    previous = _read(base / ANNUNCIATOR_PATH)
    aggregate = aggregate_attention(base, write=True)
    state = _baseline_state(previous, aggregate.get("items", []), now=now)
    _write(base, state)
    return state


def sync_annunciator_state(root: str | Path | None = None) -> dict[str, Any]:
    """Refresh only the durable visual projection after an existing attention action."""
    base = Path(root) if root is not None else Path.cwd()
    previous = _read(base / ANNUNCIATOR_PATH)
    active = _actionable(aggregate_attention(base, write=True).get("items", []))
    severity = min((i["classification"] for i in active), key=lambda c: SEVERITY_RANK[c], default=None)
    state = dict(previous)
    state.update({
        "schema_version": ANNUNCIATOR_SCHEMA_VERSION,
        "generated_at": _now(),
        "active": bool(active),
        "severity": severity,
        "severity_rank": SEVERITY_RANK.get(severity),
        "severity_label": {"urgent": "URGENT", "decision_required": "DECISION REQUIRED", "attention_soon": "ATTENTION SOON"}.get(severity),
        "items": [{"id": i["id"], "title": i["title"], "summary": i["summary"], "classification": i["classification"], "requested_steward_action": i["requested_steward_action"], "announcement": announcement_text(i)} for i in active],
        "active_item_ids": sorted(i["id"] for i in active),
    })
    _write(base, state)
    return state


def watch_attention(root: str | Path | None = None, *, interval_seconds: float = 15.0,
                    max_cycles: int | None = None, presenter: Presenter | None = None) -> dict[str, Any]:
    """Run the existing attention aggregate poll in the signed-in user session."""
    if interval_seconds < 1:
        raise ValueError("interval_seconds must be at least 1 second")
    establish_startup_baseline(root)
    cycles = []
    index = 0
    while max_cycles is None or index < max_cycles:
        state = present_attention(root, presenter=presenter)
        cycles.append({"cycle": index + 1, "active": state["active"], "new_item_count": state["last_run"]["new_item_count"], "presented_count": state["last_run"]["presented_count"], "failure_count": state["last_run"]["failure_count"]})
        index += 1
        if max_cycles is not None and index >= max_cycles:
            break
        time.sleep(interval_seconds)
    return {"state": "stopped", "cycles_run": len(cycles), "interval_seconds": interval_seconds, "cycles": cycles}


def present_attention(root: str | Path | None = None, *, presenter: Presenter | None = None,
                      now: str | None = None) -> dict[str, Any]:
    """Poll canonical attention, announce only unseen actionable items, and persist state."""
    base = Path(root) if root is not None else Path.cwd()
    previous = _read(base / ANNUNCIATOR_PATH)
    aggregate = aggregate_attention(base, write=True)
    all_items = [i for i in aggregate.get("items", []) if i.get("id")]
    active = _actionable(aggregate.get("items", []))
    active_ids = {i["id"] for i in active}
    presented = dict(previous.get("presented", {}))
    events = list(previous.get("events", []))
    observed = previous.get("observed_items") if isinstance(previous.get("observed_items"), dict) else {
        str(i["id"]): _item_signature(i) for i in previous.get("items", []) if i.get("id")
    }
    pending = previous.get("pending_presentations") if isinstance(previous.get("pending_presentations"), dict) else {}
    failures: list[dict[str, Any]] = []
    new_items = [
        i for i in active
        if _should_announce(observed.get(str(i["id"])), _item_signature(i))
        or (str(i["id"]) in pending and pending[str(i["id"])] == _item_signature(i))
    ]
    adapter = presenter or WindowsPresenter()
    for item in sorted(new_items, key=lambda i: (SEVERITY_RANK[i["classification"]], i["title"])):
        item_id = str(item["id"])
        try:
            adapter.announce(item)
            presented[item_id] = {"presented_at": now or _now(), "classification": item["classification"]}
            pending.pop(item_id, None)
            events.append({"event": "presented", "item_id": item_id, "severity": item["classification"], "at": now or _now()})
        except Exception as exc:  # presenter failure must not hide the visual alarm
            pending[item_id] = _item_signature(item)
            failure = {"event": "presenter_failure", "item_id": item_id, "error": str(exc), "at": now or _now()}
            failures.append(failure)
            events.append(failure)
    # Bound history while retaining durable fingerprints for all currently active items.
    events = events[-100:]
    severity = min((i["classification"] for i in active), key=lambda c: SEVERITY_RANK[c], default=None)
    state = {
        "schema_version": ANNUNCIATOR_SCHEMA_VERSION,
        "generated_at": now or _now(),
        "consumer_boundary": "presenter-only; canonical attention and Office actions remain authoritative",
        "active": bool(active),
        "severity": severity,
        "severity_rank": SEVERITY_RANK.get(severity),
        "severity_label": {"urgent": "URGENT", "decision_required": "DECISION REQUIRED", "attention_soon": "ATTENTION SOON"}.get(severity),
        "focus_policy": {"steals_keyboard_focus": False, "steals_mouse_focus": False, "always_visible_consumer": "edge_or_corner_alarm"},
        "items": [{"id": i["id"], "title": i["title"], "summary": i["summary"], "classification": i["classification"], "requested_steward_action": i["requested_steward_action"], "announcement": announcement_text(i)} for i in active],
        "active_item_ids": sorted(active_ids),
        "presented": presented,
        "baseline_established": bool(previous.get("baseline_established")),
        "observed_items": _item_signatures(all_items),
        "pending_presentations": pending,
        "events": events,
        "last_run": {"new_item_count": len(new_items), "presented_count": len(new_items) - len(failures), "failure_count": len(failures), "failures": failures},
    }
    _write(base, state)
    return state


def format_annunciator(state: dict[str, Any]) -> str:
    return json.dumps({"active": state.get("active"), "severity": state.get("severity"), "items": state.get("items", []), "last_run": state.get("last_run", {})}, indent=2, sort_keys=True)
