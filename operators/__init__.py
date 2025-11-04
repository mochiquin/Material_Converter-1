import os
import importlib

def register_operators():
    # Pobierz ścieżkę folderu operators
    operators_path = os.path.dirname(__file__)
    operators_files = [
        f[:-3] for f in os.listdir(operators_path)
        if f.endswith('.py') and f != '__init__.py'
    ]

    # Import i rejestracja operatorów
    for module_name in operators_files:
        module_path = f"{__package__}.{module_name}"
        module = importlib.import_module(module_path)
        if hasattr(module, "register"):
            module.register()

def unregister_operators():
    # Pobierz ścieżkę folderu operators
    operators_path = os.path.dirname(__file__)
    operators_files = [
        f[:-3] for f in os.listdir(operators_path)
        if f.endswith('.py') and f != '__init__.py'
    ]

    # Wyrejestrowanie operatorów
    for module_name in operators_files:
        module_path = f"{__package__}.{module_name}"
        module = importlib.import_module(module_path)
        if hasattr(module, "unregister"):
            module.unregister()
