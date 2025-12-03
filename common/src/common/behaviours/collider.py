from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Any

import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.physics_world import PhysicsWorld
from common.utils import clamp, deserialize_vec2, serialize_vec2


@dataclass
class CircleCollisionShape:
    radius: float


@dataclass
class RectCollisionShape:
    size: pg.Vector2


CollisionShape = RectCollisionShape | CircleCollisionShape


class Collider(Behaviour):
    _shape: CollisionShape
    _bounding_rect: pg.Rect | None
    _last_position: pg.Vector2

    def on_init(self) -> Any:
        self._offset = pg.Vector2(0, 0)
        self._last_position = self.transform.position
        self._prev_bouding_rect = self.get_bounding_rect()
        self._cached_world: PhysicsWorld | None = None

        self.shape = RectCollisionShape(pg.Vector2(100, 100))

    def on_pre_start(self) -> Any:
        from common.behaviours.physics_world import PhysicsWorld

        assert self.game

        self._bounding_rect = None
        self.world.register_collider(self)

    @property
    def shape(self) -> CollisionShape:
        return self._shape

    @shape.setter
    def shape(self, shape: CollisionShape):
        self._shape = shape
        self._update_bounding_rect()
        self.world.update_collider_rect(self, self._bounding_rect, self._bounding_rect)

    def _update_bounding_rect(self):
        pos = pg.Vector2(self.transform.position) + self._offset

        if isinstance(self._shape, RectCollisionShape):
            size = self._shape.size
            self._bounding_rect = pg.Rect(
                int(pos.x), int(pos.y), int(size.x), int(size.y)
            )
        elif isinstance(self._shape, CircleCollisionShape):
            r = self._shape.radius
            self._bounding_rect = pg.Rect(
                int(pos.x - r),
                int(pos.y - r),
                int(r * 2),
                int(r * 2),
            )
        else:
            raise TypeError("Unknown collision shape type.")

        return self._bounding_rect

    @property
    def world(self):
        assert self.game
        world = self._cached_world
        if world is None:
            world = self.game.scene.get_behaviour_in_children(PhysicsWorld)
            if not world:
                world = self.game.scene.add_child().add_behaviour(PhysicsWorld)
            self._cached_world = world
        return world

    def get_bounding_rect(self, offset: pg.Vector2 | None = None) -> pg.Rect:
        if self._bounding_rect is None:
            rect = self._update_bounding_rect()
        else:
            rect = self._bounding_rect

        if offset is not None:
            rect = pg.Rect(pg.Vector2(rect.x, rect.y) + offset, rect.size)

        return rect

    def on_tick(self, tick_id: int) -> Any:
        current_pos = self.transform.position
        if current_pos == self._last_position:
            return

        self._last_position = current_pos
        new_rect = self.get_bounding_rect()
        self.world.update_collider_rect(self, self._prev_bouding_rect, new_rect)
        self._prev_bouding_rect = new_rect

    def on_serialize(self, out_dict: dict):
        serialize_vec2(out_dict, "offset", self._offset or pg.Vector2(0, 0))
        if isinstance(self.shape, CircleCollisionShape):
            shape_dict = {"type": "circle", "radius": self.shape.radius}
        else:
            shape_dict = {
                "type": "rect",
            }
            serialize_vec2(shape_dict, "size", self.shape.size)

        out_dict["shape"] = shape_dict

    def on_deserialize(self, in_dict: dict):
        self._offset = deserialize_vec2(in_dict, "offset")

        shape_dict = in_dict.get("shape")
        if not shape_dict:
            return

        shape_type = shape_dict.get("type")
        if shape_type == "circle":
            self.shape = CircleCollisionShape(in_dict.get("radius", 0))
        elif shape_type == "rect":
            self.shape = RectCollisionShape(deserialize_vec2(shape_dict, "size"))


def shape_collides(
    shape_a: tuple[pg.Vector2, CollisionShape],
    shape_b: tuple[pg.Vector2, CollisionShape],
):
    pos_a, sh_a = shape_a
    pos_b, sh_b = shape_b

    if isinstance(sh_a, RectCollisionShape) and isinstance(sh_b, RectCollisionShape):
        rect_a = pg.Rect(pos_a.x, pos_a.y, sh_a.size.x, sh_a.size.y)
        rect_b = pg.Rect(pos_b.x, pos_b.y, sh_b.size.x, sh_b.size.y)
        return rect_a.colliderect(rect_b)

    if isinstance(sh_a, CircleCollisionShape) and isinstance(
        sh_b, CircleCollisionShape
    ):
        center_a = pos_a + pg.Vector2(sh_a.radius, sh_a.radius)
        center_b = pos_b + pg.Vector2(sh_b.radius, sh_b.radius)
        dist_sq = center_a.distance_squared_to(center_b)
        rad_sum = sh_a.radius + sh_b.radius
        return dist_sq <= rad_sum * rad_sum

    if isinstance(sh_a, CircleCollisionShape) and isinstance(sh_b, RectCollisionShape):
        return _circle_rect_collision(pos_a, sh_a, pos_b, sh_b)

    if isinstance(sh_a, RectCollisionShape) and isinstance(sh_b, CircleCollisionShape):
        return _circle_rect_collision(pos_b, sh_b, pos_a, sh_a)

    raise TypeError("Unknown collision shape combination.")


def _circle_rect_collision(
    cpos: pg.Vector2,
    circle: CircleCollisionShape,
    rpos: pg.Vector2,
    rect: RectCollisionShape,
):
    cx, cy = cpos.x + circle.radius, cpos.y + circle.radius

    nearest_x = clamp(cx, rpos.x, rpos.x + rect.size.x)
    nearest_y = clamp(cy, rpos.y, rpos.y + rect.size.y)

    dx = cx - nearest_x
    dy = cy - nearest_y

    return (dx * dx + dy * dy) <= (circle.radius * circle.radius)
