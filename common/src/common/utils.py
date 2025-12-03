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


def serialize_vec2(out_dict: dict, name: str, v: pg.Vector2):
    out_dict[name] = {"x": v.x, "y": v.y}


def deserialize_vec2(in_dict: dict, name: str, fallback: pg.Vector2 | None = None):
    if fallback is None:
        fallback = pg.Vector2(0, 0)

    vec_dict = in_dict.get(name)
    if not isinstance(vec_dict, dict):
        return fallback

    x = vec_dict.get("x", fallback.x)
    y = vec_dict.get("y", fallback.x)

    return pg.Vector2(x, y)


def clamp(value: float, min_v: float, max_v: float):
    return max(min_v, min(value, max_v))


class Rect:
    def __init__(self, center: pg.Vector2, size: pg.Vector2):
        # self._pygame_rect =
        pass
