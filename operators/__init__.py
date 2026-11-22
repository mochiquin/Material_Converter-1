"""Operator package registration."""

from __future__ import annotations

import importlib
from pathlib import Path


def register_operators() -> None:
    operators_path = Path(__file__).resolve().parent
    operator_files = [
        p.stem for p in operators_path.iterdir() if p.suffix == ".py" and p.name != "__init__.py"
    ]
    for module_name in operator_files:
        module = importlib.import_module(f"{__package__}.{module_name}")
        if hasattr(module, "register"):
            module.register()


def unregister_operators() -> None:
    operators_path = Path(__file__).resolve().parent
    operator_files = [
        p.stem for p in operators_path.iterdir() if p.suffix == ".py" and p.name != "__init__.py"
    ]
    for module_name in operator_files:
        module = importlib.import_module(f"{__package__}.{module_name}")
        if hasattr(module, "unregister"):
            module.unregister()
