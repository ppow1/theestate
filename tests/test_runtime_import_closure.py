import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("runtime_import_closure", ROOT / "tools/runtime_import_closure.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_absolute_from_and_relative_transitive_resolution(tmp_path):
    write(tmp_path, "estate/__init__.py", "")
    write(tmp_path, "estate/core/__init__.py", "")
    write(tmp_path, "estate/core/entry.py", "from estate.core.absolute import X\nfrom .one import Y\n")
    write(tmp_path, "estate/core/absolute.py", "from .two import Z\nX=Z\n")
    write(tmp_path, "estate/core/one.py", "from ..core.two import Z\nY=Z\n")
    write(tmp_path, "estate/core/two.py", "Z=1\n")
    records, unresolved = MODULE.static_closure(tmp_path, "estate.core.entry")
    assert not unresolved
    assert {x["module"] for x in records} == {"estate.core.entry", "estate.core.absolute", "estate.core.one", "estate.core.two"}


def test_multilevel_relative_and_external_imports_are_safe(tmp_path):
    write(tmp_path, "estate/__init__.py", "")
    write(tmp_path, "estate/core/__init__.py", "")
    write(tmp_path, "estate/core/pkg/__init__.py", "")
    write(tmp_path, "estate/core/pkg/entry.py", "import json\nfrom ...leaf import VALUE\n")
    write(tmp_path, "estate/leaf.py", "VALUE=1\n")
    records, unresolved = MODULE.static_closure(tmp_path, "estate.core.pkg.entry")
    assert not unresolved
    assert "estate.leaf" in {x["module"] for x in records}


def test_cycles_terminate(tmp_path):
    write(tmp_path, "estate/__init__.py", "")
    write(tmp_path, "estate/a.py", "from .b import VALUE\n")
    write(tmp_path, "estate/b.py", "from .a import VALUE\n")
    records, unresolved = MODULE.static_closure(tmp_path, "estate.a")
    assert not unresolved and len(records) == 2


def test_missing_local_module_blocks(tmp_path):
    write(tmp_path, "estate/__init__.py", "")
    write(tmp_path, "estate/a.py", "from .missing import VALUE\n")
    records, unresolved = MODULE.static_closure(tmp_path, "estate.a")
    assert records and unresolved


def test_estate_skills_is_reached_from_gateway():
    records, unresolved = MODULE.static_closure(ROOT / "src", "estate.core.resident_gateway")
    assert not unresolved
    assert any(x["module"] == "estate.core.estate_skills" for x in records)


def test_manifest_membership_and_target_presence(tmp_path):
    write(tmp_path, "estate/__init__.py", "")
    write(tmp_path, "estate/a.py", "")
    records, unresolved = MODULE.static_closure(tmp_path, "estate.a")
    assert not unresolved and records[0]["path"] == "estate/a.py"
