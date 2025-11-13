import importlib
import os
from typing import cast


def _import_all_submodules(package_name: str):
    package = importlib.import_module(package_name)
    base_dir = os.path.dirname(cast(str, package.__file__))
    for root, _, files in os.walk(base_dir):
        for file in files:
            if not file.endswith(".py") or file in ["__init__.py", "__main__.py"]:
                continue
            rel_path = os.path.relpath(os.path.join(root, file), base_dir)
            module_name = os.path.splitext(rel_path.replace(os.sep, "."))[0]
            importlib.import_module(f"{package_name}.{module_name}")


_import_all_submodules(__name__)
