from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pygame as pg
from pygame.transform import scale

from common.behaviour import Behaviour
from common.behaviours.physics_world import PhysicsWorld
from common.utils import (
    Rect,
    clamp,
    deserialize_vec2,
    memberwise_multiply,
    serialize_vec2,
)


@dataclass
class CircleCollisionShape:
    radius: float


@dataclass
class RectCollisionShape:
    size: pg.Vector2


CollisionShape = RectCollisionShape | CircleCollisionShape


class Collider(Behaviour):
    def on_init(self):
        self._offset = pg.Vector2(0, 0)
        self._shape: CollisionShape = RectCollisionShape(pg.Vector2(100, 100))
        self._bounding_rect = None
        self._last_world_bounding_rect = None
        self._last_position = self.transform.position.copy()
        self._last_scale = self.transform.scale.copy()
        self._last_rotation = self.transform.rotation
        self._world = None

    def on_pre_start(self):
        self._refresh_bounding_rect()
        self._resolve_world()
        assert self.world
        self.world.register_collider(self)

    @property
    def base_shape(self):
        return self._shape

    @base_shape.setter
    def base_shape(self, shape: CollisionShape):
        self._shape = shape
        self._refresh_bounding_rect()

    @property
    def scaled_shape(self):
        scale = self.transform.scale
        s = self._shape
        if isinstance(s, RectCollisionShape):
            size = memberwise_multiply(s.size, scale)
            return RectCollisionShape(size)
        r = max(scale.x, scale.y)
        return CircleCollisionShape(s.radius * r)

    @scaled_shape.setter
    def scaled_shape(self, shape: CollisionShape):
        scale = self.transform.scale
        if isinstance(shape, RectCollisionShape):
            if scale.x != 0:
                shape.size.x /= scale.x

            if scale.y != 0:
                shape.size.y /= scale.y
        else:
            r = max(scale.x, scale.y)
            shape.radius /= r
        self.base_shape = shape

    def _refresh_bounding_rect(self):
        pos = self.transform.position + self._offset

        scaled_shape = self.scaled_shape
        if isinstance(scaled_shape, RectCollisionShape):
            self._bounding_rect = Rect(pos, scaled_shape.size)
        elif isinstance(scaled_shape, CircleCollisionShape):
            r = scaled_shape.radius
            size = pg.Vector2(r * 2, r * 2)
            self._bounding_rect = Rect(pos, size)
        else:
            self._bounding_rect = Rect(pg.Vector2(0, 0), pg.Vector2(0, 0))

        world = self.world
        if world is not None:
            world.update_collider_rect(
                self, self._last_world_bounding_rect, self._bounding_rect
            )
            self._last_world_bounding_rect = self._bounding_rect.copy()

        return self._bounding_rect

    @property
    def world(self):
        if not self.game:
            return None

        self._resolve_world()

        return self._world

    def _resolve_world(self):
        assert self.game
        if self._world is None:
            w = self.game.scene.get_behaviour_in_children(PhysicsWorld)
            if not w:
                w = self.game.scene.add_child().add_behaviour(PhysicsWorld)
            self._world = w

    def get_bounding_rect(self, offset: pg.Vector2 | None = None) -> Rect:
        rect = self._bounding_rect or self._refresh_bounding_rect()
        if offset is not None:
            return Rect(rect.center + offset, rect.size)
        return rect.copy()

    def on_tick(self, tick_id: int):
        p = self.transform.position
        r = self.transform.rotation
        s = self.transform.scale
        if (
            p != self._last_position
            or r != self._last_rotation
            or s != self._last_scale
        ):
            self._refresh_bounding_rect()
            self._last_position = p.copy()
            self._last_rotation = r
            self._last_scale = s.copy()

    def on_serialize(self, out_dict: dict):
        serialize_vec2(out_dict, "offset", self._offset)
        s = self._shape

        if isinstance(s, CircleCollisionShape):
            out_dict["shape"] = {"type": "circle", "radius": s.radius}
        else:
            d = {"type": "rect"}
            serialize_vec2(d, "size", s.size)
            out_dict["shape"] = d

    def on_deserialize(self, in_dict: dict):
        self._offset = deserialize_vec2(in_dict, "offset")
        sd = in_dict.get("shape")
        if not sd:
            return

        t = sd.get("type")
        if t == "circle":
            self.base_shape = CircleCollisionShape(sd.get("radius", 0))
        elif t == "rect":
            self.base_shape = RectCollisionShape(deserialize_vec2(sd, "size"))

    def on_debug_render(self):
        from common.behaviours.camera import Camera

        camera = Camera.main
        if camera is None or self.game is None or self.game.display is None:
            return

        bounding_rect = self.get_bounding_rect()
        display = self.game.display
        shape = self.scaled_shape
        world_to_screen_scale = camera.world_to_screen_scale()

        shape_surface = pg.Surface(
            world_to_screen_scale * bounding_rect.size, pg.SRCALPHA
        )
        bounding_rect_surface = pg.Surface(
            world_to_screen_scale * bounding_rect.size, pg.SRCALPHA
        )

        if isinstance(shape, RectCollisionShape):
            pg.draw.rect(
                shape_surface,
                pg.Color(0, 0, 255, 75),
                pg.Rect(pg.Vector2(0, 0), world_to_screen_scale * shape.size),
            )
        elif isinstance(shape, CircleCollisionShape):
            radius = world_to_screen_scale * shape.radius
            pg.draw.circle(
                shape_surface,
                pg.Color(0, 0, 255, 75),
                pg.Vector2(radius, radius),
                radius,
            )

        if self._last_world_bounding_rect:
            pg.draw.rect(
                bounding_rect_surface,
                pg.Color(255, 0, 0, 75),
                pg.Rect(
                    pg.Vector2(0, 0),
                    camera.world_to_screen_scale()
                    * self._last_world_bounding_rect.size,
                ),
            )

        display.blit(
            bounding_rect_surface,
            camera.world_to_screen_space(bounding_rect.bottomleft),
        )
        display.blit(
            shape_surface, camera.world_to_screen_space(bounding_rect.bottomleft)
        )

    def on_destroy(self):
        if self._world and self._last_world_bounding_rect:
            self._world.unregister_collider(self)


def shape_collides(
    a: tuple[pg.Vector2, CollisionShape], b: tuple[pg.Vector2, CollisionShape]
):
    pos_a, sh_a = a
    pos_b, sh_b = b

    if isinstance(sh_a, RectCollisionShape) and isinstance(sh_b, RectCollisionShape):
        return _rect_rect(pos_a, sh_a.size, pos_b, sh_b.size)

    if isinstance(sh_a, CircleCollisionShape) and isinstance(
        sh_b, CircleCollisionShape
    ):
        return _circle_circle(pos_a, sh_a.radius, pos_b, sh_b.radius)

    if isinstance(sh_a, CircleCollisionShape) and isinstance(sh_b, RectCollisionShape):
        return _circle_rect(pos_a, sh_a.radius, pos_b, sh_b.size)

    if isinstance(sh_a, RectCollisionShape) and isinstance(sh_b, CircleCollisionShape):
        return _circle_rect(pos_b, sh_b.radius, pos_a, sh_a.size)

    raise TypeError


def _rect_rect(
    pos_a: pg.Vector2, size_a: pg.Vector2, pos_b: pg.Vector2, size_b: pg.Vector2
):
    dx = abs(pos_a.x - pos_b.x)
    dy = abs(pos_a.y - pos_b.y)
    return dx <= (size_a.x + size_b.x) * 0.5 and dy <= (size_a.y + size_b.y) * 0.5


def _circle_circle(pos_a: pg.Vector2, ra: float, pos_b: pg.Vector2, rb: float):
    d = pos_a.distance_squared_to(pos_b)
    rs = ra + rb
    return d <= rs * rs


def _circle_rect(cpos: pg.Vector2, r: float, rpos: pg.Vector2, rsize: pg.Vector2):
    cx, cy = cpos.x, cpos.y
    rx, ry = rpos.x, rpos.y
    hw, hh = rsize.x * 0.5, rsize.y * 0.5

    left = rx - hw
    right = rx + hw
    bottom = ry - hh
    top = ry + hh

    nx = clamp(cx, left, right)
    ny = clamp(cy, bottom, top)

    dx = cx - nx
    dy = cy - ny
    return dx * dx + dy * dy <= r * r
