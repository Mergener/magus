from typing import Any

import pygame as pg


def overrides_method(base_class: type, instance: object, method_name: str):
    base_method = getattr(base_class, method_name)
    instance_method = getattr(instance.__class__, method_name)
    return instance_method is not base_method


def memberwise_multiply(v1: pg.Vector2, v2: pg.Vector2):
    return pg.Vector2(v1.x * v2.x, v1.y * v2.y)


def notnull[T](value: T | None) -> T:
    assert value is not None
    return value


def get_object_attribute_from_dotted_path(obj: Any, path: str, level: int) -> str:
    parts = path.split(".")
    current = obj

    for part in parts:
        if isinstance(current, dict):
            if part not in current:
                return f"<unknown:{path}>"
            current = current[part]
        else:
            if not hasattr(current, part):
                return f"<unknown:{path}>"
            current = getattr(current, part)

    if isinstance(current, list):
        idx = max(0, min(level - 1, len(current) - 1))
        return str(current[idx])

    return str(current)
