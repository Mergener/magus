from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.physics_world import PhysicsWorld
from common.utils import Rect, clamp, deserialize_vec2, serialize_vec2


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
        self._last_position = self.transform.position.copy()
        self._shape = RectCollisionShape(pg.Vector2(100, 100))
        self._bounding_rect = None
        self._prev_bouding_rect = None
        self._cached_world = None

    def on_pre_start(self):
        self._bounding_rect = None
        self.world.register_collider(self)

    def on_start(self):
        self.shape = self._shape
        self._update_bounding_rect()

    @property
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, shape: CollisionShape):
        self._shape = shape
        self._prev_bouding_rect = self._update_bounding_rect()
        if self.game:
            self.world.update_collider_rect(
                self, self._bounding_rect, self._bounding_rect
            )

    @property
    def scaled_shape(self):
        scale = self.transform.scale
        s = self._shape
        if isinstance(s, RectCollisionShape):
            size = pg.Vector2(s.size.x * scale.x, s.size.y * scale.y)
            return RectCollisionShape(size)
        r = max(scale.x, scale.y)
        return CircleCollisionShape(s.radius * r)

    @scaled_shape.setter
    def scaled_shape(self, shape: CollisionShape):
        scale = self.transform.scale
        if isinstance(shape, RectCollisionShape):
            shape.size.x /= scale.x
            shape.size.y /= scale.y
        else:
            r = max(scale.x, scale.y)
            shape.radius /= r
        self.shape = shape

    def _update_bounding_rect(self):
        pos = self.transform.position + self._offset

        if isinstance(self._shape, RectCollisionShape):
            self._bounding_rect = Rect(pos, self._shape.size)
        else:
            r = self._shape.radius
            size = pg.Vector2(r * 2, r * 2)
            self._bounding_rect = Rect(pos, size)

        return self._bounding_rect

    @property
    def world(self):
        assert self.game
        if self._cached_world is None:
            w = self.game.scene.get_behaviour_in_children(PhysicsWorld)
            if not w:
                w = self.game.scene.add_child().add_behaviour(PhysicsWorld)
            self._cached_world = w
        return self._cached_world

    def get_bounding_rect(self, offset: pg.Vector2 | None = None) -> Rect:
        rect = self._bounding_rect or self._update_bounding_rect()
        if offset is not None:
            return Rect(rect.center + offset, rect.size)
        return rect

    def on_tick(self, tick_id: int):
        p = self.transform.position
        if p == self._last_position:
            return
        self._last_position = p.copy()
        new_rect = self.get_bounding_rect()
        self.world.update_collider_rect(self, self._prev_bouding_rect, new_rect)
        self._prev_bouding_rect = new_rect

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
            self.shape = CircleCollisionShape(sd.get("radius", 0))
        elif t == "rect":
            self.shape = RectCollisionShape(deserialize_vec2(sd, "size"))

    def on_debug_render(self):
        from common.behaviours.camera import Camera

        camera = Camera.main
        if camera is None or self.game is None or self.game.display is None:
            return

        surface = self.game.display

        rect = self.get_bounding_rect()
        tl = rect.topleft
        w, h = rect.size

        pts = [
            tl,
            pg.Vector2(tl.x + w, tl.y),
            pg.Vector2(tl.x + w, tl.y - h),
            pg.Vector2(tl.x, tl.y - h),
        ]
        pts = [camera.world_to_screen_space(p) for p in pts]

        s = pg.Surface(surface.get_size(), pg.SRCALPHA)
        pg.draw.polygon(s, (255, 0, 0, 50), pts)
        surface.blit(s, (0, 0))

        shape = self.shape
        pos = self.transform.position

        if isinstance(shape, RectCollisionShape):
            hw = shape.size.x * 0.5
            hh = shape.size.y * 0.5
            pts2 = [
                pg.Vector2(pos.x - hw, pos.y + hh),
                pg.Vector2(pos.x + hw, pos.y + hh),
                pg.Vector2(pos.x + hw, pos.y - hh),
                pg.Vector2(pos.x - hw, pos.y - hh),
            ]
            pts2 = [camera.world_to_screen_space(p) for p in pts2]
            s2 = pg.Surface(surface.get_size(), pg.SRCALPHA)
            pg.draw.polygon(s2, (0, 0, 255, 75), pts2)
            surface.blit(s2, (0, 0))

        elif isinstance(shape, CircleCollisionShape):
            center = camera.world_to_screen_space(pos)
            radius = camera.world_to_screen_scale(shape.radius)
            s2 = pg.Surface(surface.get_size(), pg.SRCALPHA)
            pg.draw.circle(s2, (0, 0, 255, 75), center, radius)
            surface.blit(s2, (0, 0))


def shape_collides(a, b):
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


def _rect_rect(pos_a, size_a, pos_b, size_b):
    dx = abs(pos_a.x - pos_b.x)
    dy = abs(pos_a.y - pos_b.y)
    return dx <= (size_a.x + size_b.x) * 0.5 and dy <= (size_a.y + size_b.y) * 0.5


def _circle_circle(pos_a, ra, pos_b, rb):
    d = pos_a.distance_squared_to(pos_b)
    rs = ra + rb
    return d <= rs * rs


def _circle_rect(cpos, r, rpos, rsize):
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
