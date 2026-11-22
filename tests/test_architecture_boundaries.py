"""Architecture boundary tests enforcing AGENTS.md hard boundaries."""

from __future__ import annotations

import ast
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parent.parent / "core"
FORBIDDEN_TOP_LEVEL_MODULES = {"bpy", "mathutils", "bmesh", "executor"}


def _iter_core_python_files() -> list[Path]:
    return sorted(CORE_DIR.rglob("*.py"))


def test_core_directory_has_no_forbidden_imports() -> None:
    py_files = _iter_core_python_files()
    assert py_files, "Expected core/ to contain Python modules"

    violations: list[str] = []
    for py_file in py_files:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top in FORBIDDEN_TOP_LEVEL_MODULES:
                        violations.append(f"{py_file.name}:{node.lineno} imports {alias.name}")
                    if alias.name == "os.path":
                        violations.append(f"{py_file.name}:{node.lineno} imports os.path (use pathlib.Path)")
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                top = module_name.split(".")[0]
                if top in FORBIDDEN_TOP_LEVEL_MODULES:
                    violations.append(f"{py_file.name}:{node.lineno} imports from {module_name}")
                if module_name == "os.path":
                    violations.append(f"{py_file.name}:{node.lineno} imports from os.path (use pathlib.Path)")

    assert not violations, f"Architecture violations in core/: {violations}"


def test_no_hardcoded_old_addon_folder_in_core_or_executor() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    for folder in ("core", "executor"):
        folder_path = repo_root / folder
        if not folder_path.exists():
            continue
        for py_file in folder_path.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            assert "Material_Converter 1" not in content, (
                f"{py_file.name} still hardcodes 'Material_Converter 1'"
            )
