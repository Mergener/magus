import importlib
import os
import pkgutil
import sys


def _auto_import_submodules(package_name: str):
    try:
        package = importlib.import_module(package_name)
        search_paths = package.__path__
    except (ImportError, AttributeError):
        base = getattr(sys, "_MEIPASS", os.getcwd())
        search_paths = [os.path.join(base, *package_name.split("."))]

    for _, name, _ in pkgutil.walk_packages(search_paths, package_name + "."):
        if name in sys.modules:
            continue

        try:
            importlib.import_module(name)
        except Exception as e:
            print(f"Failed to import {name}: {e.__class__.__name__}: {e}")


_auto_import_submodules(__name__)
