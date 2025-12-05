from __future__ import annotations

from typing import Any

import pygame as pg

from common.primitives import Vector2


def overrides_method(base_class: type, instance: object, method_name: str):
    base_method = getattr(base_class, method_name)
    instance_method = getattr(instance.__class__, method_name)
    return instance_method is not base_method


def memberwise_multiply(v1: Vector2, v2: Vector2):
    return Vector2(v1.x * v2.x, v1.y * v2.y)


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


def serialize_vec2(v: Vector2, out_dict: dict | None = None):
    if out_dict is None:
        out_dict = {}

    out_dict["x"] = v.x
    out_dict["y"] = v.y

    return out_dict


def deserialize_vec2(in_dict: dict | None, fallback: Vector2 | None = None):
    if in_dict is None:
        in_dict = {}

    if fallback is None:
        fallback = Vector2(0, 0)

    x = in_dict.get("x", fallback.x)
    y = in_dict.get("y", fallback.y)

    return Vector2(x, y)


def clamp(value: float, min_v: float, max_v: float):
    return max(min_v, min(value, max_v))
