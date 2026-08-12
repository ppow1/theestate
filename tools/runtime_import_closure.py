"""Deterministic Estate-local import closure for a runtime entry point."""
from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
from collections import deque
from pathlib import Path


def module_path(root: Path, name: str) -> Path | None:
    rel = Path(*name.split("."))
    file_path = root / (str(rel) + ".py")
    if file_path.is_file():
        return file_path
    init_path = root / rel / "__init__.py"
    return init_path if init_path.is_file() else None


def package_name(root: Path, path: Path) -> str:
    return ".".join(path.relative_to(root).with_suffix("").parts).removesuffix(".__init__")


def resolve_from(root: Path, importer: str, level: int, module: str | None, names: list[str]) -> list[tuple[str, str]]:
    base = importer.split(".")[:-1]
    for _ in range(max(level - 1, 0)):
        if base:
            base.pop()
    prefix = ".".join(base)
    qualified = ".".join(part for part in (prefix, module or "") if part)
    result: list[tuple[str, str]] = []
    if module is not None and (qualified.startswith("estate.") or qualified == "estate"):
        result.append((f"from level={level} {module or ''}", qualified))
    for name in names:
        candidate = ".".join(part for part in (qualified, name) if part)
        if candidate.startswith("estate.") and module_path(root, candidate):
            result.append((f"from level={level} {module or ''} import {name}", candidate))
    return result


def imports_for(root: Path, path: Path) -> list[tuple[str, str]]:
    importer = package_name(root, path)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "estate" or alias.name.startswith("estate."):
                    result.append((f"import {alias.name}", alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                result.extend(resolve_from(root, importer, node.level, node.module, [a.name for a in node.names]))
            elif node.module and (node.module == "estate" or node.module.startswith("estate.")):
                result.append((f"from {node.module}", node.module))
                for alias in node.names:
                    candidate = f"{node.module}.{alias.name}"
                    if module_path(root, candidate):
                        result.append((f"from {node.module} import {alias.name}", candidate))
    return result


def static_closure(source_root: Path, entry: str) -> tuple[list[dict], list[str]]:
    queue: deque[tuple[str, Path, str | None]] = deque()
    entry_path = module_path(source_root, entry)
    if not entry_path:
        return [], [entry]
    queue.append((entry, entry_path, None))
    seen: set[str] = set()
    records: list[dict] = []
    unresolved: list[str] = []
    while queue:
        name, path, importer = queue.popleft()
        if name in seen:
            continue
        seen.add(name)
        records.append({"module": name, "path": path.relative_to(source_root).as_posix(), "importer": importer, "source_exists": True})
        for statement, child in imports_for(source_root, path):
            child_path = module_path(source_root, child)
            if child_path:
                queue.append((child, child_path, name))
            elif child.startswith("estate."):
                unresolved.append(f"{name}: {statement} -> {child}")
    return sorted(records, key=lambda x: x["module"]), sorted(set(unresolved))


def dynamic_modules(source_root: Path, entry: str) -> tuple[list[str], str | None]:
    code = (
        "import json,sys; import " + entry + "; "
        "print(json.dumps(sorted({n for n,m in sys.modules.items() if getattr(m, '__file__', None) "
        "and str(getattr(m, '__file__')).replace('\\\\','/').startswith(sys.argv[1].replace('\\\\','/') )})))"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(source_root) + os.pathsep + env.get("PYTHONPATH", "")
    completed = subprocess.run([sys.executable, "-c", code, str(source_root)], capture_output=True, text=True, timeout=30, env=env)
    if completed.returncode:
        return [], completed.stderr.strip() or completed.stdout.strip()
    try:
        return json.loads(completed.stdout), None
    except json.JSONDecodeError as exc:
        return [], f"dynamic output invalid: {exc}: {completed.stdout[-500:]}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--target-root", required=True, type=Path)
    parser.add_argument("--entry", default="estate.core.resident_gateway")
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    target_root = args.target_root.resolve()
    manifest = {
        line.lstrip("\ufeff").replace("\\", "/").removeprefix("src/")
        for line in args.manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    records, unresolved = static_closure(source_root, args.entry)
    dynamic, dynamic_error = dynamic_modules(source_root, args.entry)
    static_names = {r["module"] for r in records}
    dynamic_names = set(dynamic)
    dynamic_missing_static = sorted(dynamic_names - static_names - {"estate", "estate.core"})
    for name in dynamic_missing_static:
        path = module_path(source_root, name)
        if path:
            records.append({"module": name, "path": path.relative_to(source_root).as_posix(), "importer": "<dynamic>", "source_exists": True})
    records = sorted({r["module"]: r for r in records}.values(), key=lambda x: x["module"])
    for record in records:
        rel = record["path"]
        target_path = target_root / rel
        record["target_exists"] = target_path.is_file()
        record["manifest_member"] = rel in manifest
        record["source_sha256"] = __import__("hashlib").sha256((source_root / rel).read_bytes()).hexdigest().upper()
        record["target_sha256"] = __import__("hashlib").sha256(target_path.read_bytes()).hexdigest().upper() if target_path.is_file() else None
    static_missing_dynamic = sorted(static_names - dynamic_names)
    missing_target = sorted(r["path"] for r in records if not r["target_exists"])
    omitted_manifest = sorted(r["path"] for r in records if not r["manifest_member"])
    payload = {"entry": args.entry, "static": records, "dynamic_modules": sorted(dynamic_names), "dynamic_error": dynamic_error, "unresolved": unresolved, "dynamic_missing_static": dynamic_missing_static, "static_missing_dynamic": static_missing_dynamic, "missing_target": missing_target, "omitted_manifest": omitted_manifest, "status": "IMPORT_CLOSURE_PASS" if not unresolved and not dynamic_error and not omitted_manifest else "IMPORT_CLOSURE_BLOCKED"}
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "IMPORT_CLOSURE_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
