from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PENDING_DIR = REPO_ROOT / "collaboration" / "work_packages" / "pending"
MODE_PREFIXES = ("ARCHITECTURE_FIRST", "PARALLEL", "SERIES")


@dataclass(frozen=True)
class CodexHandoff:
    title: str
    mode: str
    path: str
    dependency_notes: tuple[str, ...]
    command: str


def detect_mode(path: str | Path) -> str:
    name = Path(path).name
    for mode in MODE_PREFIXES:
        token = f"_{mode}_"
        if token in name:
            return mode
    raise ValueError(f"Cannot detect Codex mode from filename: {name}")


def _title_from_markdown(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return fallback


def _dependency_notes_from_markdown(text: str) -> tuple[str, ...]:
    notes: list[str] = []
    capture_next = False
    for line in text.splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if lower.startswith("##"):
            capture_next = "depend" in lower
            continue
        if "depends on" in lower or "depends conceptually" in lower or lower.startswith("depends"):
            notes.append(stripped.lstrip("- "))
            continue
        if capture_next and stripped:
            notes.append(stripped.lstrip("- "))
    return tuple(dict.fromkeys(notes))


def build_codex_command(mode: str, path: str) -> str:
    return f"{mode} TASK\n\nRead:\n{path}\n\nand do exactly what it says."


def handoff_for_path(path: str | Path, repo_root: str | Path = REPO_ROOT) -> CodexHandoff:
    package_path = Path(path)
    root = Path(repo_root)
    display_path = package_path.relative_to(root).as_posix() if package_path.is_absolute() else package_path.as_posix()
    full_path = package_path if package_path.is_absolute() else root / package_path
    text = full_path.read_text(encoding="utf-8")
    mode = detect_mode(package_path)
    return CodexHandoff(
        title=_title_from_markdown(text, package_path.stem),
        mode=mode,
        path=display_path,
        dependency_notes=_dependency_notes_from_markdown(text),
        command=build_codex_command(mode, display_path),
    )


def list_pending_handoffs(pending_dir: str | Path = DEFAULT_PENDING_DIR, repo_root: str | Path = REPO_ROOT) -> list[CodexHandoff]:
    pending_path = Path(pending_dir)
    root = Path(repo_root)
    handoffs = []
    for path in sorted(pending_path.glob("*.md")):
        if path.name == "README.md":
            continue
        try:
            handoffs.append(handoff_for_path(path, repo_root=root))
        except ValueError:
            continue
    return handoffs


def format_handoff_list(handoffs: list[CodexHandoff]) -> str:
    if not handoffs:
        return "No pending work package Codex handoffs found."

    sections = ["Pending Codex Work Package Handoffs"]
    for handoff in handoffs:
        sections.extend([
            "",
            f"Title: {handoff.title}",
            f"Mode: {handoff.mode}",
            f"Path: {handoff.path}",
            "Dependencies: " + ("; ".join(handoff.dependency_notes) if handoff.dependency_notes else "None noted."),
            "Command:",
            handoff.command,
        ])
    return "\n".join(sections)
