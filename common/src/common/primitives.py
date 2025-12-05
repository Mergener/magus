from __future__ import annotations

import pygame as pg

Vector2 = pg.Vector2


class Rect:
    def __init__(self, center: Vector2, size: Vector2):
        self._center = Vector2(center)
        self._size = Vector2(size)

    @property
    def center(self):
        return self._center

    @center.setter
    def center(self, value: Vector2):
        self._center = value.copy()

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value: Vector2):
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
        return Vector2(
            self.center.x - self.half_width,
            self.center.y + self.half_height,
        )

    @property
    def bottomleft(self):
        return Vector2(
            self.center.x - self.half_width,
            self.center.y - self.half_height,
        )

    @property
    def topright(self):
        return Vector2(
            self.center.x + self.half_width,
            self.center.y + self.half_height,
        )

    @property
    def bottomright(self):
        return Vector2(
            self.center.x + self.half_width,
            self.center.y - self.half_height,
        )

    def copy(self):
        return Rect(self.center, self.size)

    def move(self, offset: Vector2):
        return Rect(self.center + offset, self.size)

    def contains_point(self, p: Vector2):
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
