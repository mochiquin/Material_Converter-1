"""Tests verifying operator dispatch contracts and Octane entry point consistency."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OCTANE_DIR = REPO_ROOT / "octane"
INIT_FILE = REPO_ROOT / "__init__.py"
NODES_SCRIPT = REPO_ROOT / "scripts" / "nodes.py"


def _get_top_level_functions(file_path: Path) -> set[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_octane_modules_expose_required_entry_points() -> None:
    expected_entrypoints: dict[str, str] = {
        "basic_octane.py": "create_basic",
        "trans_octane.py": "create_trans",
        "glass_octane.py": "create_glass",
        "glass_caustics_octane.py": "create_caustics_glass",
        "archviz_glass_octane.py": "create_archviz_glass",
        "metal_octane.py": "create_metal",
        "textures_octane.py": "import_textures",
        "remove_octane.py": "remove_nodes",
        "convert_active_octane.py": "convert_active",
        "convert_selected_octane.py": "convert_selected",
        "convert_all_octane.py": "get_materials_to_convert",
        "mapping_octane.py": "add_mapping",
    }

    for file_name, func_name in expected_entrypoints.items():
        py_file = OCTANE_DIR / file_name
        assert py_file.exists(), f"Expected {file_name} to exist in octane/"
        funcs = _get_top_level_functions(py_file)
        assert func_name in funcs, (
            f"Expected {file_name} to define top-level function '{func_name}', found: {sorted(funcs)}"
        )


def test_init_operator_dispatch_matches_octane_entrypoints() -> None:
    tree = ast.parse(INIT_FILE.read_text(encoding="utf-8"), filename=str(INIT_FILE))

    operator_calls: list[tuple[str, str, str]] = []
    # Search for classes inheriting from Operator and extract (operator_name, script_name, called_method)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if not any("Operator" in getattr(base, "id", "") or "Operator" in getattr(base, "attr", "") for base in node.bases):
            continue

        for item in node.body:
            if not isinstance(item, ast.FunctionDef) or item.name != "execute":
                continue
            script_name = None
            for stmt in ast.walk(item):
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == "script_name":
                            if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                                script_name = stmt.value.value
                if isinstance(stmt, ast.Call):
                    # Look for module.<func>(context)
                    func = stmt.func
                    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "module":
                        operator_calls.append((node.name, script_name or "<dynamic>", func.attr))

    assert operator_calls, "Expected to find operator module calls in __init__.py"

    call_map = {op_name: (script, method) for op_name, script, method in operator_calls}
    assert call_map["MATERIAL_OT_create_basic"] == ("basic.py", "create_basic")
    assert call_map["MATERIAL_OT_create_trans"] == ("trans.py", "create_trans")
    assert call_map["MATERIAL_OT_create_glass"] == ("glass.py", "create_glass")
    assert call_map["MATERIAL_OT_create_caustics_glass"] == ("glass_caustics.py", "create_caustics_glass")
    assert call_map["MATERIAL_OT_create_archviz_glass"] == ("archviz_glass.py", "create_archviz_glass")
    assert call_map["MATERIAL_OT_create_metal"] == ("metal.py", "create_metal")
    assert call_map["MATERIAL_OT_import_textures"] == ("textures.py", "import_textures")
    assert call_map["MATERIAL_OT_add_mapping"] == ("mapping.py", "add_mapping")
    assert call_map["MATERIAL_OT_remove_nodes_confirm"] == ("remove.py", "remove_nodes")


def test_scripts_nodes_does_not_compare_bl_idname_to_string_ao_type() -> None:
    content = NODES_SCRIPT.read_text(encoding="utf-8")
    assert 'node.bl_idname == "AO_Type"' not in content, (
        'scripts/nodes.py should compare node.bl_idname against variable AO_Type, not string literal "AO_Type"'
    )
