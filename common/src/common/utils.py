from __future__ import annotations

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
        self._center = pg.Vector2(center)
        self._size = pg.Vector2(size)

    @property
    def center(self):
        return self._center

    @center.setter
    def center(self, value: pg.Vector2):
        self._center = value.copy()

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value: pg.Vector2):
        self._size = value.copy()

    @property
    def x(self):
        return self.center.x

    @x.setter
    def x(self, v):
        self.center.x = v

    @property
    def y(self):
        return self.center.y

    @y.setter
    def y(self, v):
        self.center.y = v

    @property
    def width(self):
        return self.size.x

    @property
    def height(self):
        return self.size.y

    @property
    def half_width(self):
        return self.size.x * 0.5

    @property
    def half_height(self):
        return self.size.y * 0.5

    @property
    def topleft(self):
        return pg.Vector2(
            self.center.x - self.half_width,
            self.center.y + self.half_height,
        )

    @property
    def bottomleft(self):
        return pg.Vector2(
            self.center.x - self.half_width,
            self.center.y - self.half_height,
        )

    @property
    def topright(self):
        return pg.Vector2(
            self.center.x + self.half_width,
            self.center.y + self.half_height,
        )

    @property
    def bottomright(self):
        return pg.Vector2(
            self.center.x + self.half_width,
            self.center.y - self.half_height,
        )

    def copy(self):
        return Rect(self.center, self.size)

    def move(self, offset: pg.Vector2):
        return Rect(self.center + offset, self.size)

    def contains_point(self, p: pg.Vector2):
        dx = abs(p.x - self.center.x)
        dy = abs(p.y - self.center.y)
        return dx <= self.half_width and dy <= self.half_height

    def intersects(self, other: Rect):
        dx = abs(self.center.x - other.center.x)
        dy = abs(self.center.y - other.center.y)
        return dx <= (self.half_width + other.half_width) and dy <= (
            self.half_height + other.half_height
        )

    def __str__(self):
        return f"Rect(cx={self.x}, cy={self.y}, w={self.width}, h={self.height})"
