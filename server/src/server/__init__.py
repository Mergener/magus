import importlib.util
import os
import sys

base_dir = os.path.dirname(__file__)
package_name = __name__

for root, _, files in os.walk(base_dir):
    for file in files:
        if not file.endswith(".py") or file in ("__init__.py", "__main__.py"):
            continue

        file_path = os.path.join(root, file)
        rel_path = os.path.relpath(file_path, base_dir)
        module_name = os.path.splitext(rel_path.replace(os.sep, "."))[0]
        full_name = f"{package_name}.{module_name}"

        spec = importlib.util.spec_from_file_location(full_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[full_name] = module
            spec.loader.exec_module(module)
