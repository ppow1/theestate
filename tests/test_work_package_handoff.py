from pathlib import Path

from estate.core.work_package_handoff import (
    build_codex_command,
    detect_mode,
    format_handoff_list,
    handoff_for_path,
    list_pending_handoffs,
)


def _write_package(root: Path, name: str, body: str) -> Path:
    path = root / "collaboration" / "work_packages" / "pending" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_build_codex_command_exact_format():
    assert build_codex_command("SERIES", "collaboration/work_packages/pending/WP-1_SERIES_demo.md") == (
        "SERIES TASK\n\n"
        "Read:\n"
        "collaboration/work_packages/pending/WP-1_SERIES_demo.md\n\n"
        "and do exactly what it says."
    )


def test_detect_mode_for_series_parallel_and_architecture_first():
    assert detect_mode("WP-1_SERIES_demo.md") == "SERIES"
    assert detect_mode("WP-2_PARALLEL_demo.md") == "PARALLEL"
    assert detect_mode("WP-3_ARCHITECTURE_FIRST_demo.md") == "ARCHITECTURE_FIRST"


def test_handoff_for_path_extracts_title_mode_dependencies_and_command(tmp_path):
    package = _write_package(
        tmp_path,
        "WP-9_ARCHITECTURE_FIRST_registry.md",
        "# ARCHITECTURE-FIRST TASK WP-9 — Registry\n\n## Mode\nARCHITECTURE-FIRST. Depends on review.\n",
    )

    handoff = handoff_for_path(package, repo_root=tmp_path)

    assert handoff.title == "ARCHITECTURE-FIRST TASK WP-9 — Registry"
    assert handoff.mode == "ARCHITECTURE_FIRST"
    assert handoff.path == "collaboration/work_packages/pending/WP-9_ARCHITECTURE_FIRST_registry.md"
    assert handoff.dependency_notes == ("ARCHITECTURE-FIRST. Depends on review.",)
    assert handoff.command.startswith("ARCHITECTURE_FIRST TASK\n\nRead:\n")


def test_list_pending_handoffs_and_format_includes_human_readable_fields(tmp_path):
    pending = tmp_path / "collaboration" / "work_packages" / "pending"
    _write_package(tmp_path, "WP-1_SERIES_alpha.md", "# Series Alpha\n")
    _write_package(tmp_path, "WP-2_PARALLEL_beta.md", "# Parallel Beta\n## Dependencies\nWP-1 accepted.\n")
    _write_package(tmp_path, "WP-3_ARCHITECTURE_FIRST_gamma.md", "# Architecture Gamma\n")
    (pending / "README.md").write_text("Ignored", encoding="utf-8")

    handoffs = list_pending_handoffs(pending_dir=pending, repo_root=tmp_path)
    formatted = format_handoff_list(handoffs)

    assert [h.mode for h in handoffs] == ["SERIES", "PARALLEL", "ARCHITECTURE_FIRST"]
    assert "Title: Series Alpha" in formatted
    assert "Mode: PARALLEL" in formatted
    assert "Dependencies: WP-1 accepted." in formatted
    assert "ARCHITECTURE_FIRST TASK" in formatted
